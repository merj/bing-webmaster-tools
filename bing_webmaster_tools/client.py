import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, NoReturn, Optional, cast

import aiohttp

from bing_webmaster_tools.config import Settings
from bing_webmaster_tools.errors import (
    ApiErrorCode,
    AuthenticationError,
    BingWebmasterError,
    RateLimitError,
)
from bing_webmaster_tools.retrying import RetryConfig, get_retry_decorator
from bing_webmaster_tools.services.content_blocking import ContentBlockingService
from bing_webmaster_tools.services.content_management import ContentManagementService
from bing_webmaster_tools.services.crawling import CrawlingService
from bing_webmaster_tools.services.keyword_analysis import KeywordAnalysisService
from bing_webmaster_tools.services.link_analysis import LinkAnalysisService
from bing_webmaster_tools.services.regional_settings import RegionalSettingsService
from bing_webmaster_tools.services.site_management import SiteManagementService
from bing_webmaster_tools.services.submission import SubmissionService
from bing_webmaster_tools.services.traffic_analysis import TrafficAnalysisService
from bing_webmaster_tools.services.url_management import UrlManagementService
from bing_webmaster_tools.utils import RateLimiter, format_date_for_api

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        """Encode datetime objects as formatted strings compatible with the API."""
        if isinstance(obj, datetime):
            return format_date_for_api(obj)
        return super().default(obj)


class BingWebmasterClient:
    """An async client for interacting with the Bing Webmaster API.

    This client provides:
    - Automatic session management via async context manager
    - Rate limiting
    - Exponential backoff retries for transient failures
    - Comprehensive error handling
    - JSON response validation

    Attributes:
        settings (Settings): Configuration settings for the client

    Example:
        async with BingWebmasterClient(settings) as client:
            response = await client.sites.get_sites()

        # Or manual initialization:
        client = BingWebmasterClient(settings)
        await client.init()
        try:
            response = await client.request("GET", "endpoint")
        finally:
            await client.close()

    """

    def __init__(self, settings: Settings):
        """Initialize the Bing Webmaster API client.

        Args:
            settings: Client configuration settings.

        """
        self.settings = settings
        self._rate_limiter: Optional[RateLimiter] = None

        if self.settings.rate_limit_calls is not None and self.settings.rate_limit_period is not None:
            self._rate_limiter = RateLimiter(self.settings.rate_limit_calls, self.settings.rate_limit_period)

        # The retry config waits for 1s, 2s, 4s
        self._retry_decorator = get_retry_decorator(
            RetryConfig(
                num_retries=self.settings.max_retries,
                min_wait=1,
                max_wait=30,
                multiplier=1.0,
                exp_base=2,
                should_retry=self._is_transient_error,
            ),
        )

        self._session: Optional[aiohttp.ClientSession] = None

        self.blocking = ContentBlockingService(self)
        self.content = ContentManagementService(self)
        self.crawling = CrawlingService(self)
        self.keywords = KeywordAnalysisService(self)
        self.links = LinkAnalysisService(self)
        self.regional = RegionalSettingsService(self)
        self.sites = SiteManagementService(self)
        self.submission = SubmissionService(self)
        self.traffic = TrafficAnalysisService(self)
        self.urls = UrlManagementService(self)

    async def __aenter__(self) -> "BingWebmasterClient":
        """Initialize the client using a context manager.

        Returns:
            BingWebmasterClient: The initialized client instance.

        Example:
            async with BingWebmasterClient() as client:
                # use client here

        """
        await self.init()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Close the client when exiting the context manager.

        Args:
            exc_type: The type of the exception that was raised, if any
            exc: The instance of the exception that was raised, if any
            tb: The traceback of the exception that was raised, if any

        """
        await self.close()

    async def init(self) -> None:
        """Initialize the client manually if not using context manager.

        Creates an aiohttp ClientSession with configured timeout and headers.
        This method is idempotent - calling it multiple times will only create
        one session.

        Example:
            client = BingWebmasterClient()
            await client.init()

        """
        if self._session is None:  # Prevent multiple session creation
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.settings.timeout),
                headers={"Content-Type": "application/json; charset=utf-8"},
            )

    async def close(self) -> None:
        """Close the client manually if not using context manager.

        Closes the underlying aiohttp ClientSession. This method is idempotent -
        calling it multiple times is safe.

        Example:
            await client.close()

        """
        if self._session is not None:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the underlying aiohttp ClientSession.

        Raises:
            RuntimeError: If client is not initialized

        Returns:
            aiohttp.ClientSession: The active session

        """
        if self._session is None:
            raise RuntimeError("Client not initialized - use 'async with' context manager")
        return self._session

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Bing Webmaster API.

        This method handles:
        - Authentication via API key
        - Rate limiting
        - Retry logic for transient failures
        - Response validation
        - Error parsing and raising appropriate exceptions

        Args:
            method: HTTP method ("GET", "POST", etc.)
            endpoint: API endpoint path
            params: Optional query parameters
            data: Optional request body data (will be JSON-encoded)

        Returns:
            Dict[str, Any]: Parsed JSON response from the API

        Raises:
            RuntimeError: If client is not initialized
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            BingWebmasterError: For other API errors including network issues

        Example:
            response = await client.request(
                "GET",
                "sites/list",
                params={"page": 1}
            )

        """
        if self.settings.disable_destructive_operations and self._is_destructive_operation(method, endpoint):
            raise BingWebmasterError(
                "Destructive operations are disabled. Set 'disable_destructive_operations' to False."
            )

        url = f"{self.settings.base_url}/{endpoint}"

        request_params = self._convert_params(params)
        request_params["apikey"] = self.settings.get_api_key()

        # Convert params to API format
        params = params.copy() if params is not None else {}
        params["apikey"] = self.settings.get_api_key()

        data_json: Optional[str] = None
        if data is not None:
            data_json = json.dumps(data, cls=DateTimeEncoder)

        logger.debug(f"Sending request to: {url}, method: {method}, params: {request_params}")

        @self._retry_decorator
        async def _request() -> Dict[str, Any]:
            try:
                async with self.session.request(
                    method,
                    url,
                    params=request_params,
                    data=data_json,
                    raise_for_status=False,  # Handle status manually
                ) as response:
                    content = await response.text()  # Read content first

                    # For successful responses, ensure we have valid JSON
                    if response.status == 200:
                        try:
                            return cast(Dict[str, Any], json.loads(content))
                        except json.JSONDecodeError as exc:
                            raise BingWebmasterError(
                                message="Invalid JSON in successful response",
                                status_code=response.status,
                                raw_content=content,
                            ) from exc

                    # Handle error responses
                    self._handle_error_response(content, response.status)

            except aiohttp.ClientError as exc:
                raise BingWebmasterError(f"Network error occurred: {exc}") from exc
            except asyncio.TimeoutError as exc:
                raise BingWebmasterError(f"Request timed out: {exc}") from exc

        if self._rate_limiter is not None:
            await self._rate_limiter.acquire()

        return await _request()

    @staticmethod
    def _is_destructive_operation(method: str, endpoint: str) -> bool:
        """Determine if an operation is destructive based on method and endpoint.

        Args:
            method: HTTP method
            endpoint: API endpoint path

        Returns:
            bool: True if operation is destructive, False otherwise

        """
        return method in {"POST", "PUT", "DELETE"} and endpoint != "GetChildrenUrlInfo"

    @staticmethod
    def _convert_params(params: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Convert parameters to API-compatible format.

        Handles:
        - Booleans to lowercase strings
        - None values removal
        - All values to strings
        """
        if not params:
            return {}

        def convert_value(value: Any) -> str:
            if isinstance(value, bool):
                return str(value).lower()
            return str(value)

        return {key: convert_value(value) for key, value in params.items() if value is not None}

    @staticmethod
    def _is_transient_error(exc: BaseException) -> bool:
        """Determine if an error is transient and should be retried.

        Used by the retry decorator to determine whether to retry a failed request.
        Considers rate limits and server errors as transient, while treating
        client errors (400, 401, 403, 404) as permanent failures.

        Args:
            exc: The exception that occurred

        Returns:
            bool: True if error should be retried, False otherwise

        """
        if isinstance(exc, RateLimitError):
            # Always retry rate limits
            return True

        if isinstance(exc, BingWebmasterError):
            status_code = exc.status_code

            # Always retry rate limits, server errors and unknown status codes
            if status_code is None or status_code == 429 or status_code >= 500:
                return True

        # Default to not retrying if we're unsure
        return False

    @staticmethod
    def _handle_error_response(content: str, status_code: int) -> NoReturn:
        """Parse error response and raise appropriate exception.

        Attempts to parse the error response as JSON and extract structured error
        information. Raises specific exceptions based on the error type.

        Args:
            content: Response content
            status_code: HTTP status code

        Raises:
            AuthenticationError: For authentication failures
            RateLimitError: When rate limit is exceeded
            BingWebmasterError: For other API errors

        Note:
            This method always raises an exception, hence the NoReturn type hint

        """
        try:
            error_data = json.loads(content)
        except json.JSONDecodeError as exc:
            # If we can't parse the error as JSON, use raw content
            raise BingWebmasterError(
                message=f"Invalid response format. Raw content: {content}", status_code=status_code
            ) from exc

        # Proper error code checking
        if isinstance(error_data, dict):
            error_code = None
            if "ErrorCode" in error_data and isinstance(error_data["ErrorCode"], int):
                try:
                    error_code = ApiErrorCode(error_data["ErrorCode"])
                except ValueError:
                    pass

            error_message = error_data.get("Message", content)

            if error_code == ApiErrorCode.INVALID_API_KEY:
                raise AuthenticationError(error_message, status_code=status_code, error_code=error_code)

            if error_code in {ApiErrorCode.THROTTLE_USER, ApiErrorCode.THROTTLE_HOST}:
                raise RateLimitError(error_message, status_code=status_code, error_code=error_code)

            raise BingWebmasterError(message=error_message, status_code=status_code, error_code=error_code)
        else:
            raise BingWebmasterError(
                message=f"Invalid error response format. Raw content: {content}",
                status_code=status_code,
            )
