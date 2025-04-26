import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.content_blocking import BlockedUrl, BlockReason, PagePreview
from bing_webmaster_tools.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class ContentBlockingService:
    """Service for managing content blocking in Bing Webmaster Tools.

    This service handles:
    - URL blocking configuration
    - Page preview blocking
    - Content restriction management
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the content blocking service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_blocked_urls(self, site_url: str) -> List[BlockedUrl]:
        """Get a list of blocked pages/directories for a site.

        Args:
            site_url: The URL of the site

        Returns:
            List[BlockedUrl]: List of blocked URLs and their settings

        Raises:
            BingWebmasterError: If blocked URLs cannot be retrieved

        """
        self._logger.debug(f"Retrieving blocked URLs for {site_url}")
        response = await self._client.request("GET", "GetBlockedUrls", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=BlockedUrl, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} blocked URLs")
        return api_response.data

    @validate_call
    async def add_blocked_url(
        self,
        site_url: str,
        blocked_url: str,
        entity_type: BlockedUrl.BlockedUrlEntityType = BlockedUrl.BlockedUrlEntityType.PAGE,
        request_type: BlockedUrl.BlockedUrlRequestType = BlockedUrl.BlockedUrlRequestType.CACHE_ONLY,
        date: Optional[datetime] = None,
    ) -> None:
        """Add a blocked URL to a site.

        Args:
            site_url: The URL of the site
            blocked_url: The URL to be blocked
            entity_type: The type of entity to block (Page or Directory)
            request_type: The type of request (CacheOnly or FullRemoval)
            date: The date the URL was blocked (default: minimum datetime)

        Raises:
            BingWebmasterError: If URL cannot be blocked

        """
        self._logger.debug(f"Adding blocked URL: {blocked_url}")

        # The API seems to always ignore the date field, so we make it optional
        blocked_url_data = BlockedUrl(
            date=date or datetime.now(timezone.utc),
            entity_type=entity_type,
            request_type=request_type,
            url=blocked_url,
        )

        data = {"siteUrl": site_url, "blockedUrl": blocked_url_data.model_dump(by_alias=True)}

        await self._client.request("POST", "AddBlockedUrl", data=data)
        self._logger.info(f"Successfully blocked URL: {blocked_url}")

    @validate_call
    async def remove_blocked_url(
        self,
        site_url: str,
        blocked_url: str,
        entity_type: BlockedUrl.BlockedUrlEntityType = BlockedUrl.BlockedUrlEntityType.PAGE,
        request_type: BlockedUrl.BlockedUrlRequestType = BlockedUrl.BlockedUrlRequestType.FULL_REMOVAL,
        date: Optional[datetime] = None,
    ) -> None:
        """Remove a blocked URL from a site.

        Args:
            site_url: The URL of the site
            blocked_url: The URL to be unblocked
            entity_type: The type of entity to unblock (Page or Directory)
            request_type: The type of request (CacheOnly or FullRemoval)
            date: The date the URL was blocked

        Raises:
            BingWebmasterError: If URL cannot be unblocked

        """
        self._logger.debug(f"Removing blocked URL: {blocked_url}")

        # The API seems to always ignore the date field, so we make it optional
        blocked_url_data = BlockedUrl(
            date=date or datetime.now(timezone.utc),
            entity_type=entity_type,
            request_type=request_type,
            url=blocked_url,
        )

        data = {"siteUrl": site_url, "blockedUrl": blocked_url_data.model_dump(by_alias=True)}

        await self._client.request("POST", "RemoveBlockedUrl", data=data)
        self._logger.info(f"Successfully unblocked URL: {blocked_url}")

    @validate_call
    async def get_active_page_preview_blocks(self, site_url: str) -> List[PagePreview]:
        """Get active page preview blocks for a site.

        Args:
            site_url: The URL of the site

        Returns:
            List[PagePreview]: List of active page preview blocks

        Raises:
            BingWebmasterError: If preview blocks cannot be retrieved

        """
        self._logger.debug(f"Retrieving page preview blocks for {site_url}")
        response = await self._client.request("GET", "GetActivePagePreviewBlocks", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=PagePreview, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} page preview blocks")
        return api_response.data

    @validate_call
    async def add_page_preview_block(self, site_url: str, url: str, reason: BlockReason) -> None:
        """Add a page preview block.

        Args:
            site_url: The URL of the site
            url: The URL to block from page preview
            reason: The reason for blocking the page preview

        Raises:
            BingWebmasterError: If preview block cannot be added

        """
        self._logger.debug(f"Adding page preview block for {url}")
        data = {"siteUrl": site_url, "url": url, "reason": reason.value}

        await self._client.request("POST", "AddPagePreviewBlock", data=data)
        self._logger.info(f"Successfully added page preview block for {url}")

    @validate_call
    async def remove_page_preview_block(self, site_url: str, url: str) -> None:
        """Remove a page preview block.

        Args:
            site_url: The URL of the site
            url: The URL to remove the page preview block from

        Raises:
            BingWebmasterError: If preview block cannot be removed

        """
        self._logger.debug(f"Removing page preview block for {url}")
        data = {"siteUrl": site_url, "url": url}

        await self._client.request("POST", "RemovePagePreviewBlock", data=data)
        self._logger.info(f"Successfully removed page preview block for {url}")
