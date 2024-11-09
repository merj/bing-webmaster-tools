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
        assert len(stats) > 0
        assert all(isinstance(stat, KeywordStats) for stat in stats)

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

        assert isinstance(keyword_data, Keyword)
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
        assert len(related_keywords) > 0
        assert all(isinstance(keyword, Keyword) for keyword in related_keywords)

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
        assert len(stats) > 0
        assert all(isinstance(stat, KeywordStats) for stat in stats)

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
