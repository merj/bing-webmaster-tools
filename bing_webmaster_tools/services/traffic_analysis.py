import logging
from typing import List

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.traffic_analysis import (
    DetailedQueryStats,
    QueryStats,
    RankAndTrafficStats,
)
from bing_webmaster_tools.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class TrafficAnalysisService:
    """Service for analyzing traffic data from Bing Webmaster Tools.

    This service handles traffic and ranking analysis operations including:
    - Page statistics
    - Query statistics
    - Ranking data
    - Traffic trends
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the traffic analysis service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_page_stats(self, site_url: str) -> List[QueryStats]:
        """Get detailed traffic statistics for top pages.

        Args:
            site_url: The URL of the site

        Returns:
            List[QueryStats]: List of query statistics for top pages

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving page stats for {site_url}")
        response = await self._client.request("GET", "GetPageStats", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=QueryStats, is_list=True)

        self._logger.info(f"Retrieved stats for {len(api_response.data)} pages")
        return api_response.data

    @validate_call
    async def get_page_query_stats(self, site_url: str, page: str) -> List[QueryStats]:
        """Get detailed traffic statistics for a specific page.

        Args:
            site_url: The URL of the site
            page: The specific page URL to get statistics for

        Returns:
            List[QueryStats]: List of query statistics for the specified page

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving query stats for page {page}")
        response = await self._client.request("GET", "GetPageQueryStats", params={"siteUrl": site_url, "page": page})

        api_response = ApiResponse.from_api_response(response=response, model=QueryStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} query stats for page {page}")
        return api_response.data

    @validate_call
    async def get_query_stats(self, site_url: str) -> List[QueryStats]:
        """Get detailed traffic statistics for top queries.

        Args:
            site_url: The URL of the site

        Returns:
            List[QueryStats]: List of statistics for top queries

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving query stats for {site_url}")
        response = await self._client.request("GET", "GetQueryStats", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=QueryStats, is_list=True)

        self._logger.info(f"Retrieved stats for {len(api_response.data)} queries")
        return api_response.data

    @validate_call
    async def get_query_page_stats(self, site_url: str, query: str) -> List[QueryStats]:
        """Get detailed traffic statistics for pages matching a specific query.

        Args:
            site_url: The URL of the site
            query: The search query to get statistics for

        Returns:
            List[QueryStats]: List of page statistics for the query

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving page stats for query: {query}")
        response = await self._client.request("GET", "GetQueryPageStats", params={"siteUrl": site_url, "query": query})

        api_response = ApiResponse.from_api_response(response=response, model=QueryStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} page stats for query: {query}")
        return api_response.data

    @validate_call
    async def get_query_page_detail_stats(self, site_url: str, query: str, page: str) -> List[DetailedQueryStats]:
        """Get detailed statistics for a specific query and page combination.

        Args:
            site_url: The URL of the site
            query: The search query
            page: The specific page URL

        Returns:
            List[DetailedQueryStats]: List of detailed statistics

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving detailed stats for query '{query}' on page {page}")
        response = await self._client.request(
            "GET",
            "GetQueryPageDetailStats",
            params={"siteUrl": site_url, "query": query, "page": page},
        )

        api_response = ApiResponse.from_api_response(response=response, model=DetailedQueryStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} detailed stats")
        return api_response.data

    @validate_call
    async def get_rank_and_traffic_stats(self, site_url: str) -> List[RankAndTrafficStats]:
        """Get ranking and traffic statistics for a site.

        Args:
            site_url: The URL of the site

        Returns:
            List[RankAndTrafficStats]: List of ranking and traffic statistics

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving rank and traffic stats for {site_url}")
        response = await self._client.request("GET", "GetRankAndTrafficStats", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=RankAndTrafficStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} rank and traffic stats")
        return api_response.data

    @validate_call
    async def get_query_traffic_stats(self, site_url: str, query: str) -> List[RankAndTrafficStats]:
        """Get detailed traffic statistics for a specific query.

        Args:
            site_url: The URL of the site
            query: The search query to get statistics for

        Returns:
            List[RankAndTrafficStats]: List of traffic statistics for the query

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving traffic stats for query: {query}")
        response = await self._client.request(
            "GET", "GetQueryTrafficStats", params={"siteUrl": site_url, "query": query}
        )

        api_response = ApiResponse.from_api_response(response=response, model=RankAndTrafficStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} traffic stats for query: {query}")
        return api_response.data
