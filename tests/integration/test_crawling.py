import random

import pytest

from bing_webmaster_tools.client import BingWebmasterClient
from bing_webmaster_tools.models.crawling import CrawlSettings, CrawlStats, UrlWithCrawlIssues


@pytest.mark.asyncio
class TestCrawlingService:
    """Tests for the crawling service."""

    @pytest.mark.vcr
    async def test_get_crawl_settings(self, client: BingWebmasterClient, test_site: str):
        """Test retrieving crawl settings."""
        settings = await client.crawling.get_crawl_settings(test_site)

        assert isinstance(settings, CrawlSettings)
        assert len(settings.crawl_rate) == 24  # Should always have 24 hourly rates

    @pytest.mark.vcr
    async def test_save_crawl_settings(self, client: BingWebmasterClient, test_site: str):
        """Test saving crawl settings.

        Note: The Bing API ignores crawl_boost_available and crawl_boost_enabled settings,
        so we can't effectively test those values are saved.
        """
        # Create RNG with fixed seed for VCR consistency
        rng = random.Random(42)

        # Generate new crawl rates between 1 and 10
        new_crawl_rate = [rng.randint(1, 10) for _ in range(24)]

        modified_settings = CrawlSettings(
            crawl_rate=new_crawl_rate,
            crawl_boost_available=True,  # These will be ignored by the API
            crawl_boost_enabled=True,  # These will be ignored by the API
        )

        # Save new settings
        await client.crawling.save_crawl_settings(test_site, modified_settings)

        # Verify settings were saved exactly as specified
        saved_settings = await client.crawling.get_crawl_settings(test_site)
        assert isinstance(saved_settings, CrawlSettings)
        assert saved_settings.crawl_rate == new_crawl_rate

    @pytest.mark.vcr
    async def test_get_crawl_issues(self, client: BingWebmasterClient, test_site: str):
        """Test retrieving crawl issues from a live site that has actual crawl data."""
        issues = await client.crawling.get_crawl_issues(test_site)

        assert isinstance(issues, list)

        if len(issues) > 0:
            assert isinstance(issues[0], UrlWithCrawlIssues)

    @pytest.mark.vcr
    async def test_get_crawl_stats(self, client: BingWebmasterClient, test_site: str):
        """Test retrieving crawl statistics from a live site."""
        stats = await client.crawling.get_crawl_stats(test_site)

        assert isinstance(stats, list)

        if len(stats) > 0:
            assert isinstance(stats[0], CrawlStats)
