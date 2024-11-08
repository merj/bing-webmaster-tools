import logging
from typing import List

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.submission import (
    ContentSubmissionQuota,
    Feed,
    FetchedUrl,
    FetchedUrlDetails,
    UrlSubmissionQuota,
)
from bing_webmaster_tools.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for submitting URLs and content to Bing for indexing.

    This service handles:
    - URL submission for indexing
    - Content submission
    - Feed management
    - Quota monitoring
    - URL fetch status tracking
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the submission service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def submit_url(self, site_url: str, url: str) -> None:
        """Submit a single URL for indexing.

        It is possible to submit only limited number of url. get_url_submission_quota
        should be called to determine how much urls can be submitted.

        Args:
            site_url: The URL of the site
            url: The specific URL to submit

        Raises:
            BingWebmasterError: If URL cannot be submitted

        """
        self._logger.debug(f"Submitting URL for indexing: {url}")
        await self._client.request("POST", "SubmitUrl", data={"siteUrl": site_url, "url": url})
        self._logger.info(f"Successfully submitted URL: {url}")

    @validate_call
    async def submit_url_batch(self, site_url: str, url_list: List[str]) -> None:
        """Submit multiple URLs for indexing in a single request.

        The max number of urls that can be submitted in a batch is 500 unless it exceeds the
        available quota. get_url_submission_quota should be called to determine how
        much urls can be submitted.

        Args:
            site_url: The URL of the site
            url_list: List of URLs to submit

        Raises:
            BingWebmasterError: If URLs cannot be submitted

        """
        if not url_list:
            raise ValueError("URL list cannot be empty")

        if len(url_list) > 500:  # API limit
            raise ValueError("Cannot submit more than 500 URLs in one batch")

        self._logger.debug(f"Submitting batch of {len(url_list)} URLs")
        await self._client.request("POST", "SubmitUrlBatch", data={"siteUrl": site_url, "urlList": url_list})
        self._logger.info(f"Successfully submitted {len(url_list)} URLs")

    @validate_call
    async def get_url_submission_quota(self, site_url: str) -> UrlSubmissionQuota:
        """Get information about URL submission quota and usage.

        Args:
            site_url: The URL of the site

        Returns:
            UrlSubmissionQuota: Current quota information

        Raises:
            BingWebmasterError: If quota information cannot be retrieved

        """
        self._logger.debug(f"Retrieving URL submission quota for {site_url}")
        response = await self._client.request("GET", "GetUrlSubmissionQuota", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=UrlSubmissionQuota)

        self._logger.info(f"Retrieved URL submission quota for {site_url}")
        return api_response.data

    @validate_call
    async def get_content_submission_quota(self, site_url: str) -> ContentSubmissionQuota:
        """Get information about content submission quota and usage.

        Args:
            site_url: The URL of the site

        Returns:
            ContentSubmissionQuota: Current quota information

        Raises:
            BingWebmasterError: If quota information cannot be retrieved

        """
        self._logger.debug(f"Retrieving content submission quota for {site_url}")
        response = await self._client.request("GET", "GetContentSubmissionQuota", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=ContentSubmissionQuota)

        self._logger.info(f"Retrieved content submission quota for {site_url}")
        return api_response.data

    @validate_call
    async def submit_feed(self, site_url: str, feed_url: str) -> None:
        """Submit a sitemap feed for indexing.

        Args:
            site_url: The URL of the site
            feed_url: The URL of the sitemap feed

        Raises:
            BingWebmasterError: If feed cannot be submitted

        """
        self._logger.debug(f"Submitting feed: {feed_url}")
        await self._client.request("POST", "SubmitFeed", data={"siteUrl": site_url, "feedUrl": feed_url})
        self._logger.info(f"Successfully submitted feed: {feed_url}")

    @validate_call
    async def remove_feed(self, site_url: str, feed_url: str) -> None:
        """Remove a previously submitted sitemap feed.

        Args:
            site_url: The URL of the site
            feed_url: The URL of the feed to remove

        Raises:
            BingWebmasterError: If feed cannot be removed

        """
        self._logger.debug(f"Removing feed: {feed_url}")
        await self._client.request("POST", "RemoveFeed", data={"siteUrl": site_url, "feedUrl": feed_url})
        self._logger.info(f"Successfully removed feed: {feed_url}")

    @validate_call
    async def get_feeds(self, site_url: str) -> List[Feed]:
        """Get all sitemap feeds for a site.

        Args:
            site_url: The URL of the site

        Returns:
            List[Feed]: List of feed information

        Raises:
            BingWebmasterError: If feeds cannot be retrieved

        """
        self._logger.debug(f"Retrieving feeds for {site_url}")
        response = await self._client.request("GET", "GetFeeds", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=Feed, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} feeds")
        return api_response.data

    @validate_call
    async def get_feed_details(self, site_url: str, feed_url: str) -> List[Feed]:
        """Get detailed information about a specific feed.

        Args:
            site_url: The URL of the site
            feed_url: The URL of the feed

        Returns:
            List[Feed]: Detailed feed information

        Raises:
            BingWebmasterError: If feed details cannot be retrieved

        """
        self._logger.debug(f"Retrieving details for feed: {feed_url}")
        response = await self._client.request(
            "GET", "GetFeedDetails", params={"siteUrl": site_url, "feedUrl": feed_url}
        )

        api_response = ApiResponse.from_api_response(response=response, model=Feed, is_list=True)

        self._logger.info(f"Retrieved details for feed: {feed_url}")
        return api_response.data

    @validate_call
    async def fetch_url(self, site_url: str, url: str) -> None:
        """Request Bing to fetch a specific URL immediately.

        Args:
            site_url: The URL of the site
            url: The URL to fetch

        Raises:
            BingWebmasterError: If URL cannot be fetched

        """
        self._logger.debug(f"Requesting immediate fetch of URL: {url}")
        await self._client.request("POST", "FetchUrl", data={"siteUrl": site_url, "url": url})
        self._logger.info(f"Successfully requested fetch of URL: {url}")

    @validate_call
    async def get_fetched_urls(self, site_url: str) -> List[FetchedUrl]:
        """Get a list of URLs that have been submitted for fetching.

        Args:
            site_url: The URL of the site

        Returns:
            List[FetchedUrl]: List of fetched URLs and their status

        Raises:
            BingWebmasterError: If fetched URLs cannot be retrieved

        """
        self._logger.debug(f"Retrieving fetched URLs for {site_url}")
        response = await self._client.request("GET", "GetFetchedUrls", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=FetchedUrl, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} fetched URLs")
        return api_response.data

    @validate_call
    async def get_fetched_url_details(self, site_url: str, url: str) -> FetchedUrlDetails:
        """Get detailed information about a specific fetched URL.

        Args:
            site_url: The URL of the site
            url: The specific URL to get details for

        Returns:
            FetchedUrlDetails: Detailed information about the fetch status

        Raises:
            BingWebmasterError: If URL details cannot be retrieved

        """
        self._logger.debug(f"Retrieving fetch details for URL: {url}")
        response = await self._client.request("GET", "GetFetchedUrlDetails", params={"siteUrl": site_url, "url": url})

        api_response = ApiResponse.from_api_response(response=response, model=FetchedUrlDetails)

        self._logger.info(f"Retrieved fetch details for URL: {url}")
        return api_response.data

    @validate_call
    async def submit_content(
        self,
        site_url: str,
        url: str,
        http_message: str,
        structured_data: str,
        dynamic_serving: int,
    ) -> None:
        """Submit content for a specific URL.

        Args:
            site_url: Site url E.g.: http://example.com
            url: Url to submit E.g.: http://example.com/url1.html
            http_message: HTTP message (base64 encoded)
            structured_data: Structured Data (base64 encoded)
            dynamic_serving: Device targeting (0-5).
                {none = 0, PC-laptop = 1, mobile = 2, AMP = 3, tablet = 4, non-visual browser = 5}

        Raises:
            BingWebmasterError: If content cannot be submitted

        """
        if not 0 <= dynamic_serving <= 5:
            raise ValueError("dynamic_serving must be between 0 and 5")

        data = {
            "siteUrl": site_url,
            "url": url,
            "httpMessage": http_message,
            "structuredData": structured_data,
            "dynamicServing": dynamic_serving,
        }

        await self._client.request("POST", "SubmitContent", data=data)
