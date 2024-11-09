import logging
from datetime import datetime
from typing import List, Optional

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.keyword_analysis import Keyword, KeywordStats
from bing_webmaster_tools.services.api_client import ApiClient

logger = logging.getLogger(__name__)


class KeywordAnalysisService:
    """Service for analyzing keyword performance in Bing search results.

    This service handles:
    - Keyword performance tracking
    - Related keyword discovery
    - Keyword statistics analysis
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the keyword analysis service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_keyword(
        self, query: str, country: str, language: str, start_date: datetime, end_date: datetime
    ) -> Optional[Keyword]:
        """Get keyword impressions for a selected period.

        Args:
            query: The keyword query
            country: The country code
            language: The language code
            start_date: The start date of the period
            end_date: The end date of the period

        Returns:
            Optional[Keyword]: Keyword impression data, or None if no data available

        Raises:
            BingWebmasterError: If keyword data cannot be retrieved

        """
        self._logger.debug(f"Retrieving keyword data for '{query}'")
        params = {
            "q": query,
            "country": country,
            "language": language,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
        }

        response = await self._client.request("GET", "GetKeyword", params=params)
        keyword_data = response.get("d", {})

        if not keyword_data or not keyword_data.get("Query"):
            self._logger.warning(f"No keyword data returned for query: {query}")
            return None

        api_response = ApiResponse.from_api_response(response={"d": keyword_data}, model=Keyword)

        self._logger.info(f"Retrieved keyword data for '{query}'")
        return api_response.data

    @validate_call
    async def get_keyword_stats(self, query: str, country: str, language: str) -> List[KeywordStats]:
        """Retrieve keyword statistics for a specific query.

        Args:
            query: The keyword query
            country: The country code (i.e. gb)
            language: The language and country code (i.e. en-GB)

        Returns:
            List[KeywordStats]: List of keyword statistics

        Raises:
            BingWebmasterError: If statistics cannot be retrieved

        """
        self._logger.debug(f"Retrieving keyword stats for '{query}'")
        params = {"q": query, "country": country, "language": language}

        response = await self._client.request("GET", "GetKeywordStats", params=params)

        api_response = ApiResponse.from_api_response(response=response, model=KeywordStats, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} keyword stats for '{query}'")
        return api_response.data

    @validate_call
    async def get_related_keywords(
        self, query: str, country: str, language: str, start_date: datetime, end_date: datetime
    ) -> List[Keyword]:
        """Get keyword impressions for related keywords in the selected period.

        Args:
            query: The base keyword query
            country: The country code
            language: The language code
            start_date: The start date of the period
            end_date: The end date of the period

        Returns:
            List[Keyword]: List of related keywords and their impression data

        Raises:
            BingWebmasterError: If related keywords cannot be retrieved

        """
        self._logger.debug(f"Retrieving related keywords for '{query}'")
        params = {
            "q": query,
            "country": country,
            "language": language,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
        }

        response = await self._client.request("GET", "GetRelatedKeywords", params=params)

        api_response = ApiResponse.from_api_response(response=response, model=Keyword, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} related keywords for '{query}'")
        return api_response.data
