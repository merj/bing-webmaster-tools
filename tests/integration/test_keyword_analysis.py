from datetime import datetime, timedelta

import pytest

from bing_webmaster_tools.models.keyword_analysis import Keyword, KeywordStats


@pytest.mark.asyncio
class TestKeywordAnalysisService:
    """Tests for the keyword analysis service."""

    async def test_get_keyword_stats(self, client):
        """Test retrieving keyword statistics."""
        # Test parameters
        test_query = "python"  # Example query
        country = "us"
        language = "en-US"

        stats = await client.keywords.get_keyword_stats(query=test_query, country=country, language=language)

        assert isinstance(stats, list)
        if stats:  # If there are any stats
            stat = stats[0]
            assert isinstance(stat, KeywordStats)
            assert isinstance(stat.impressions, int)
            assert isinstance(stat.broad_impressions, int)
            assert isinstance(stat.query, str)
            assert isinstance(stat.date, datetime)

    async def test_get_keyword(self, client, test_site):
        """Test retrieving keyword data for a specific period."""
        # Test parameters
        test_query = "python"
        country = "us"
        language = "en-US"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        keyword_data = await client.keywords.get_keyword(
            query=test_query,
            country=country,
            language=language,
            start_date=start_date,
            end_date=end_date,
        )

        if keyword_data:  # Data might be None if no stats available
            assert isinstance(keyword_data, Keyword)
            assert isinstance(keyword_data.impressions, int)
            assert isinstance(keyword_data.broad_impressions, int)
            assert isinstance(keyword_data.query, str)
            assert keyword_data.query == test_query

    async def test_get_related_keywords(self, client, test_site):
        """Test retrieving related keywords."""
        # Test parameters
        test_query = "python programming"
        country = "us"
        language = "en-US"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        related_keywords = await client.keywords.get_related_keywords(
            query=test_query,
            country=country,
            language=language,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(related_keywords, list)
        if related_keywords:  # If there are any related keywords
            keyword = related_keywords[0]
            assert isinstance(keyword, Keyword)
            assert isinstance(keyword.impressions, int)
            assert isinstance(keyword.broad_impressions, int)
            assert isinstance(keyword.query, str)

    @pytest.mark.parametrize(
        "country,language",
        [
            ("us", "en-US"),
            ("gb", "en-GB"),
            ("au", "en-AU"),
        ],
    )
    async def test_keyword_stats_different_locales(self, client, test_site, country: str, language: str):
        """Test keyword stats with different country/language combinations."""
        test_query = "python"

        stats = await client.keywords.get_keyword_stats(query=test_query, country=country, language=language)

        assert isinstance(stats, list)
        # Note: Some locales might not have data, so we don't assert length

    @pytest.mark.parametrize(
        "time_range",
        [
            timedelta(days=7),
            timedelta(days=30),
            timedelta(days=90),
        ],
    )
    async def test_keyword_data_different_periods(self, client, test_site, time_range: timedelta):
        """Test keyword data retrieval with different time ranges."""
        test_query = "python"
        country = "us"
        language = "en-US"
        end_date = datetime.now()
        start_date = end_date - time_range

        keyword_data = await client.keywords.get_keyword(
            query=test_query,
            country=country,
            language=language,
            start_date=start_date,
            end_date=end_date,
        )

        if keyword_data:
            assert isinstance(keyword_data, Keyword)

    async def test_multiple_queries_batch(self, client, test_site):
        """Test retrieving keyword stats for multiple queries."""
        test_queries = ["python", "programming", "coding"]
        country = "us"
        language = "en-US"

        for query in test_queries:
            stats = await client.keywords.get_keyword_stats(query=query, country=country, language=language)
            assert isinstance(stats, list)

    async def test_invalid_date_range(self, client, test_site):
        """Test behavior with invalid date range (future dates)."""
        test_query = "python"
        country = "us"
        language = "en-US"
        start_date = datetime.now() + timedelta(days=1)  # Future date
        end_date = start_date + timedelta(days=30)

        keyword_data = await client.keywords.get_keyword(
            query=test_query,
            country=country,
            language=language,
            start_date=start_date,
            end_date=end_date,
        )

        # Should return None or empty data for future dates
        assert keyword_data is None
