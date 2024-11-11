import logging
from typing import List

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.crawling import CrawlSettings, CrawlStats, UrlWithCrawlIssues
from bing_webmaster_tools.services.api_client import ApiClient
from bing_webmaster_tools.utils import ModelLike, to_model_instance

logger = logging.getLogger(__name__)


class CrawlingService:
    """Service for managing how Bing crawls and indexes a website.

    This service handles crawl-related operations including:
    - Crawl settings management
    - Crawl statistics retrieval
    - Crawl issue identification
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the crawling service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_crawl_settings(self, site_url: str) -> CrawlSettings:
        """Retrieve crawl settings for a specific site.

        Args:
            site_url: The URL of the site to get crawl settings for

        Returns:
            CrawlSettings: The current crawl settings for the site

        Raises:
            BingWebmasterError: If settings cannot be retrieved

        """
        self._logger.debug(f"Retrieving crawl settings for {site_url}")
        response = await self._client.request("GET", "GetCrawlSettings", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=CrawlSettings)

        self._logger.info(f"Retrieved crawl settings for {site_url}")
        return api_response.data

    @validate_call
    async def save_crawl_settings(self, site_url: str, crawl_settings: ModelLike[CrawlSettings]) -> None:
        """Save new crawl settings for a specific site.

        Args:
            site_url: The URL of the site
            crawl_settings: The new crawl settings to apply

        Raises:
            BingWebmasterError: If settings cannot be saved

        """
        crawl_settings_model = to_model_instance(crawl_settings, CrawlSettings)
        self._logger.debug(f"Saving crawl settings for {site_url}")
        data = {
            "siteUrl": site_url,
            "crawlSettings": crawl_settings_model.model_dump(by_alias=True),
        }
        await self._client.request("POST", "SaveCrawlSettings", data=data)

        if crawl_settings_model.crawl_boost_available is True or crawl_settings_model.crawl_boost_enabled is True:
            # Validate that crawl boost settings are available for the site
            settings = await self.get_crawl_settings(site_url)

            if settings.crawl_boost_available != crawl_settings_model.crawl_boost_available:
                self._logger.warning(
                    "Crawl boost available setting was not saved because it is not available for this site."
                )

            if settings.crawl_boost_enabled != crawl_settings_model.crawl_boost_enabled:
                self._logger.warning(
                    "Crawl boost enabled setting was not saved because it is not available for this site."
                )

        self._logger.info(f"Successfully saved crawl settings for {site_url}")

    @validate_call
    async def get_crawl_stats(self, site_url: str) -> List[CrawlStats]:
        """Retrieve crawl statistics for a specific site within a date range.

        Args:
            site_url: The URL of the site

        Returns:
            List[CrawlStats]: List of daily crawl statistics

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving crawl stats for {site_url}")

        response = await self._client.request("GET", "GetCrawlStats", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=CrawlStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} days of crawl statistics")
        return api_response.data

    @validate_call
    async def get_crawl_issues(self, site_url: str) -> List[UrlWithCrawlIssues]:
        """Get a list of URLs with crawl issues for a specific site.

        This helps identify pages that Bing's crawler had trouble accessing
        or processing.

        Args:
            site_url: The URL of the site

        Returns:
            List[UrlWithCrawlIssues]: List of URLs with their associated crawl issues

        Raises:
            BingWebmasterError: If issues cannot be retrieved

        """
        self._logger.debug(f"Retrieving crawl issues for {site_url}")
        response = await self._client.request("GET", "GetCrawlIssues", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=UrlWithCrawlIssues, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} URLs with crawl issues")
        return api_response.data
