import logging
from typing import List, Optional

from pydantic import NonNegativeInt, validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.content_management import (
    FilterProperties,
    UrlInfo,
    UrlTrafficInfo,
)
from bing_webmaster_tools.services.api_client import ApiClient
from bing_webmaster_tools.services.submission import SubmissionService
from bing_webmaster_tools.utils import deprecated

logger = logging.getLogger(__name__)


class ContentManagementService:
    """Service for managing and analyzing content in Bing Webmaster Tools.

    This service handles operations related to URL information, traffic analysis,
    and content submission including:
    - URL information retrieval
    - Traffic statistics
    - Content submission
    - URL hierarchy analysis
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the content management service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)
        self._submission_service = SubmissionService(client)

    @validate_call
    async def get_url_info(self, site_url: str, url: str) -> UrlInfo:
        """Retrieve detailed information for a specific URL.

        Args:
            site_url: The URL of the site
            url: The specific URL to get information for

        Returns:
            UrlInfo: Detailed information about the URL

        Raises:
            BingWebmasterError: If URL information cannot be retrieved

        """
        self._logger.debug(f"Retrieving URL info for {url} on {site_url}")
        response = await self._client.request("GET", "GetUrlInfo", params={"siteUrl": site_url, "url": url})

        api_response = ApiResponse.from_api_response(response=response, model=UrlInfo)

        self._logger.info(f"Retrieved URL info for {url}")
        return api_response.data

    @validate_call
    async def get_children_url_info(
        self,
        site_url: str,
        url: str,
        page: NonNegativeInt = 0,
        filter_properties: Optional[FilterProperties] = None,
    ) -> List[UrlInfo]:
        """Retrieve information for child URLs of a specific URL.

        Args:
            site_url: The URL of the site
            url: The parent URL to get child URL information for
            page: The page number of results to retrieve
            filter_properties: Properties to filter the results

        Returns:
            List[UrlInfo]: List of URL information for child URLs

        Raises:
            BingWebmasterError: If child URL information cannot be retrieved

        """
        self._logger.debug(f"Retrieving child URL info for {url} on {site_url}")

        filter_properties = filter_properties or FilterProperties()
        data = {
            "siteUrl": site_url,
            "url": url,
            "page": page,
            "filterProperties": filter_properties.model_dump(by_alias=True),
        }
        self._logger.debug(f"Retrieving child URL info for {url} on {site_url}")
        response = await self._client.request("POST", "GetChildrenUrlInfo", data=data)

        api_response = ApiResponse.from_api_response(response=response, model=UrlInfo, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} child URLs info for {url}")
        return api_response.data

    @validate_call
    async def get_url_traffic_info(self, site_url: str, url: str) -> UrlTrafficInfo:
        """Get traffic details for a single page.

        Args:
            site_url: The URL of the site
            url: The specific URL to get traffic info for

        Returns:
            UrlTrafficInfo: Traffic information for the URL

        Raises:
            BingWebmasterError: If traffic information cannot be retrieved

        """
        self._logger.debug(f"Retrieving traffic info for {url} on {site_url}")
        response = await self._client.request("GET", "GetUrlTrafficInfo", params={"siteUrl": site_url, "url": url})

        api_response = ApiResponse.from_api_response(response=response, model=UrlTrafficInfo)

        self._logger.info(f"Retrieved traffic info for {url}")
        return api_response.data

    @validate_call
    async def get_children_url_traffic_info(
        self, site_url: str, url: str, page: NonNegativeInt = 0
    ) -> List[UrlTrafficInfo]:
        """Get traffic details for child URLs of a directory.

        Args:
            site_url: The URL of the site
            url: The URL of the directory
            page: The page number of results to retrieve

        Returns:
            List[UrlTrafficInfo]: List of traffic information for child URLs

        Raises:
            BingWebmasterError: If child traffic information cannot be retrieved

        """
        self._logger.debug(f"Retrieving child URL traffic info for {url} on {site_url}")
        response = await self._client.request(
            "GET",
            "GetChildrenUrlTrafficInfo",
            params={"siteUrl": site_url, "url": url, "page": page},
        )

        api_response = ApiResponse.from_api_response(response=response, model=UrlTrafficInfo, is_list=True)

        self._logger.info(f"Retrieved traffic info for {len(api_response.data)} child URLs of {url}")
        return api_response.data

    @deprecated(
        "ContentManagementService.submit_content() is deprecated and will be removed in a future version. "
        "Please use SubmissionService.submit_content() instead."
    )
    @validate_call
    async def submit_content(
        self, site_url: str, url: str, http_message: str, structured_data: str, dynamic_serving: int
    ) -> None:
        """Submit content for a specific URL.

        DEPRECATED: This method is deprecated and will be removed in a future version.
        Please use SubmissionService.submit_content() instead.

        Args:
            site_url: The URL of the site
            url: The specific URL to submit content for
            http_message: The HTTP message (base64 encoded)
            structured_data: Structured data (base64 encoded)
            dynamic_serving: Dynamic serving type (0-5)

        Raises:
            BingWebmasterError: If content submission fails

        """
        # Proxy to the SubmissionService's method
        await self._submission_service.submit_content(
            site_url=site_url,
            url=url,
            http_message=http_message,
            structured_data=structured_data,
            dynamic_serving=dynamic_serving,
        )
