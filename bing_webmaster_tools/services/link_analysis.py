import logging
from typing import List

from pydantic import NonNegativeInt, validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.link_analysis import (
    ConnectedSite,
    DeepLink,
    DeepLinkAlgoUrl,
    DeepLinkBlock,
    DeepLinkWeight,
    LinkCounts,
    LinkDetails,
)
from bing_webmaster_tools.services.api_client import ApiClient
from bing_webmaster_tools.utils import deprecated

logger = logging.getLogger(__name__)


class LinkAnalysisService:
    """Service for analyzing links in Bing Webmaster Tools.

    This service handles:
    - Inbound link analysis
    - Deep link management
    - Connected pages tracking
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the link analysis service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_link_counts(self, site_url: str, page: NonNegativeInt = 0) -> LinkCounts:
        """Retrieve link counts for a specific site.

        Args:
            site_url: The URL of the site
            page: The page number of results to retrieve

        Returns:
            LinkCounts: Summary of link counts

        Raises:
            BingWebmasterError: If link counts cannot be retrieved

        """
        self._logger.debug(f"Retrieving link counts for {site_url}")
        response = await self._client.request("GET", "GetLinkCounts", params={"siteUrl": site_url, "page": page})

        api_response = ApiResponse.from_api_response(response=response, model=LinkCounts)

        self._logger.info(f"Retrieved link counts for {site_url}")
        return api_response.data

    @validate_call
    async def get_url_links(self, site_url: str, link: str, page: NonNegativeInt = 0) -> LinkDetails:
        """Retrieve inbound links for a specific URL.

        Args:
            site_url: The URL of the site
            link: The specific URL to get inbound links for
            page: The page number of results to retrieve

        Returns:
            LinkDetails: Details about inbound links

        Raises:
            BingWebmasterError: If link details cannot be retrieved

        """
        self._logger.debug(f"Retrieving inbound links for {link}")
        response = await self._client.request(
            "GET", "GetUrlLinks", params={"siteUrl": site_url, "link": link, "page": page}
        )

        api_response = ApiResponse.from_api_response(response=response, model=LinkDetails)

        self._logger.info(f"Retrieved link details for {link}")
        return api_response.data

    @validate_call
    async def get_connected_pages(self, site_url: str) -> List[ConnectedSite]:
        """Get a list of pages connected to the site.

        Args:
            site_url: The URL of the site

        Returns:
            List[ConnectedSite]: List of connected sites

        Raises:
            BingWebmasterError: If connected pages cannot be retrieved

        """
        self._logger.debug(f"Retrieving connected pages for {site_url}")
        response = await self._client.request("GET", "GetConnectedPages", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=ConnectedSite, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} connected pages")
        return api_response.data

    @validate_call
    async def add_connected_page(self, site_url: str, master_url: str) -> None:
        """Add a page which has a link to your website.

        Args:
            site_url: The URL of your site
            master_url: The URL of the page to be connected

        Raises:
            BingWebmasterError: If page cannot be connected

        """
        self._logger.debug(f"Adding connected page: {master_url}")
        data = {"siteUrl": site_url, "masterUrl": master_url}
        await self._client.request("POST", "AddConnectedPage", data=data)
        self._logger.info(f"Successfully added connected page: {master_url}")

    @validate_call
    async def get_deep_link_blocks(self, site_url: str) -> List[DeepLinkBlock]:
        """Get deep link blocks for a site.

        Args:
            site_url: The URL of the site

        Returns:
            List[DeepLinkBlock]: List of deep link blocks

        Raises:
            BingWebmasterError: If blocks cannot be retrieved

        """
        self._logger.debug(f"Retrieving deep link blocks for {site_url}")
        response = await self._client.request("GET", "GetDeepLinkBlocks", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=DeepLinkBlock, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} deep link blocks")
        return api_response.data

    @validate_call
    async def add_deep_link_block(self, site_url: str, market: str, search_url: str, deep_link_url: str) -> None:
        """Add a deep link block.

        Args:
            site_url: The URL of the site
            market: The market code
            search_url: The search URL
            deep_link_url: The deep link URL to block

        Raises:
            BingWebmasterError: If block cannot be added

        """
        self._logger.debug(f"Adding deep link block for {deep_link_url}")
        data = {
            "siteUrl": site_url,
            "market": market,
            "searchUrl": search_url,
            "deepLinkUrl": deep_link_url,
        }
        await self._client.request("POST", "AddDeepLinkBlock", data=data)
        self._logger.info(f"Successfully added deep link block for {deep_link_url}")

    @validate_call
    async def remove_deep_link_block(self, site_url: str, market: str, search_url: str, deep_link_url: str) -> None:
        """Remove a deep link block.

        Args:
            site_url: The URL of the site
            market: The market code
            search_url: The search URL
            deep_link_url: The deep link URL to unblock

        Raises:
            BingWebmasterError: If block cannot be removed

        """
        self._logger.debug(f"Removing deep link block for {deep_link_url}")
        data = {
            "siteUrl": site_url,
            "market": market,
            "searchUrl": search_url,
            "deepLinkUrl": deep_link_url,
        }
        await self._client.request("POST", "RemoveDeepLinkBlock", data=data)
        self._logger.info(f"Successfully removed deep link block for {deep_link_url}")

    @deprecated("Get deep link functionality is deprecated in Bing Webmaster API. " "Use get_deep_link_block instead.")
    @validate_call
    async def get_deep_link(self, site_url: str, url: str) -> List[DeepLink]:
        """Get deep links for a specific algo URL. (Deprecated)

        Args:
            site_url: The URL of the site
            url: The specific URL to get deep links for

        Returns:
            List[DeepLink]: List of deep links

        Raises:
            BingWebmasterError: If deep links cannot be retrieved

        """
        self._logger.debug(f"Retrieving deep links for {url}")
        response = await self._client.request("GET", "GetDeepLink", params={"siteUrl": site_url, "url": url})

        api_response = ApiResponse.from_api_response(response=response, model=DeepLink, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} deep links")
        return api_response.data

    @deprecated("Deep links functionality is deprecated in Bing Webmaster API.")
    @validate_call
    async def get_deep_link_algo_urls(self, site_url: str) -> List[DeepLinkAlgoUrl]:
        """Get algo URLs with deep links. (Deprecated)

        Args:
            site_url: The URL of the site

        Returns:
            List[DeepLinkAlgoUrl]: List of algo URLs with deep links

        Raises:
            BingWebmasterError: If algo URLs cannot be retrieved

        """
        self._logger.debug(f"Retrieving deep link algo URLs for {site_url}")
        response = await self._client.request("GET", "GetDeepLinkAlgoUrls", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=DeepLinkAlgoUrl, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} deep link algo URLs")
        return api_response.data

    @deprecated(
        "Update deep link functionality is deprecated in Bing Webmaster API. " "Use add_deep_link_block instead."
    )
    @validate_call
    async def update_deep_link(self, site_url: str, algo_url: str, deep_link: str, weight: DeepLinkWeight) -> None:
        """Update deep link weight. (Deprecated)

        Args:
            site_url: The URL of the site
            algo_url: The algo URL
            deep_link: The deep link URL
            weight: The new weight for the deep link

        Raises:
            BingWebmasterError: If deep link cannot be updated

        """
        self._logger.debug(f"Updating deep link weight for {deep_link}")
        data = {
            "siteUrl": site_url,
            "algoUrl": algo_url,
            "deepLink": deep_link,
            "weight": weight.value,
        }
        await self._client.request("POST", "UpdateDeepLink", data=data)
        self._logger.info(f"Successfully updated deep link weight for {deep_link}")
