import logging
from typing import List

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.url_management import QueryParameter, QueryParamStr
from bing_webmaster_tools.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class UrlManagementService:
    """Service for managing URL parameters and normalization in Bing Webmaster Tools.

    This service handles:
    - Query parameter management
    - URL normalization settings
    - Parameter enable/disable operations
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the URL management service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_query_parameters(self, site_url: str) -> List[QueryParameter]:
        """Get a list of URL normalization parameters for a site.

        URL parameters are used to identify which URL parameters should be
        considered for URL normalization (e.g., sorting, filtering parameters
        that don't change the content).

        Args:
            site_url: The URL of the site

        Returns:
            List[QueryParameter]: List of query parameters configuration

        Raises:
            BingWebmasterError: If parameters cannot be retrieved

        """
        self._logger.debug(f"Retrieving query parameters for {site_url}")
        response = await self._client.request("GET", "GetQueryParameters", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=QueryParameter, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} query parameters")
        return api_response.data

    @validate_call
    async def add_query_parameter(self, site_url: str, query_parameter: QueryParamStr) -> None:
        """Add a URL normalization parameter for a site.

        Args:
            site_url: The URL of the site
            query_parameter: The query parameter to add

        Raises:
            BingWebmasterError: If parameter cannot be added

        """
        self._logger.debug(f"Adding query parameter '{query_parameter}' for {site_url}")
        data = {"siteUrl": site_url, "queryParameter": query_parameter}

        await self._client.request("POST", "AddQueryParameter", data=data)
        self._logger.info(f"Successfully added query parameter: {query_parameter}")

    @validate_call
    async def remove_query_parameter(self, site_url: str, query_parameter: str) -> None:
        """Remove a URL normalization parameter from a site.

        Args:
            site_url: The URL of the site
            query_parameter: The query parameter to remove

        Raises:
            BingWebmasterError: If parameter cannot be removed

        """
        self._logger.debug(f"Removing query parameter '{query_parameter}' from {site_url}")
        data = {"siteUrl": site_url, "queryParameter": query_parameter}

        await self._client.request("POST", "RemoveQueryParameter", data=data)
        self._logger.info(f"Successfully removed query parameter: {query_parameter}")

    @validate_call
    async def enable_disable_query_parameter(self, site_url: str, query_parameter: str, is_enabled: bool) -> None:
        """Enable or disable a URL normalization parameter for a site.

        Args:
            site_url: The URL of the site
            query_parameter: The query parameter to enable/disable
            is_enabled: True to enable, False to disable

        Raises:
            BingWebmasterError: If parameter state cannot be updated

        """
        self._logger.debug(
            f"{'Enabling' if is_enabled else 'Disabling'} " f"query parameter '{query_parameter}' for {site_url}"
        )
        data = {"siteUrl": site_url, "queryParameter": query_parameter, "isEnabled": is_enabled}

        await self._client.request("POST", "EnableDisableQueryParameter", data=data)
        self._logger.info(
            f"Successfully {'enabled' if is_enabled else 'disabled'} " f"query parameter: {query_parameter}"
        )
