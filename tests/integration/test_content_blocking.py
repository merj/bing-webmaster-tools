from datetime import datetime, timezone

import pytest

from bing_webmaster_tools.client import BingWebmasterClient
from bing_webmaster_tools.models.content_blocking import BlockedUrl, BlockReason


@pytest.mark.asyncio
class TestContentBlockingService:
    """Tests for the content blocking service."""

    @pytest.mark.vcr
    async def test_get_blocked_urls(self, client: BingWebmasterClient, test_site: str):
        """Test retrieving blocked URLs."""
        blocked_urls = await client.blocking.get_blocked_urls(test_site)
        assert isinstance(blocked_urls, list)
        if blocked_urls:  # If there are any blocked URLs
            blocked_url = blocked_urls[0]
            assert isinstance(blocked_url, BlockedUrl)
            assert blocked_url.url
            assert isinstance(blocked_url.entity_type, BlockedUrl.BlockedUrlEntityType)
            assert isinstance(blocked_url.request_type, BlockedUrl.BlockedUrlRequestType)

    @pytest.mark.vcr
    async def test_block_url_lifecycle(self, client: BingWebmasterClient, test_site: str):
        """Test the complete lifecycle of blocking and unblocking a URL."""
        test_url = f"{test_site}/test-block-example"

        fixed_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Add blocked URL
        await client.blocking.add_blocked_url(
            site_url=test_site,
            blocked_url=test_url,
            entity_type=BlockedUrl.BlockedUrlEntityType.PAGE,
            date=fixed_date,
        )

        # Verify URL is blocked
        blocked_urls = await client.blocking.get_blocked_urls(test_site)
        blocked_test_urls = [u for u in blocked_urls if u.url == test_url]
        assert len(blocked_test_urls) == 1
        assert blocked_test_urls[0].entity_type == BlockedUrl.BlockedUrlEntityType.PAGE

        # Remove blocked URL
        await client.blocking.remove_blocked_url(
            site_url=test_site,
            blocked_url=test_url,
            entity_type=BlockedUrl.BlockedUrlEntityType.PAGE,
            date=fixed_date,
        )

        # Verify URL is no longer blocked
        blocked_urls = await client.blocking.get_blocked_urls(test_site)
        assert not any(u.url == test_url for u in blocked_urls)

    @pytest.mark.vcr
    async def test_page_preview_block_lifecycle(self, client: BingWebmasterClient, test_site: str):
        """Test the complete lifecycle of page preview blocking."""
        test_url = f"{test_site}/test-preview-example"

        # Add preview block
        await client.blocking.add_page_preview_block(site_url=test_site, url=test_url, reason=BlockReason.OTHER)

        # Verify block exists
        preview_blocks = await client.blocking.get_active_page_preview_blocks(test_site)
        blocked_test_urls = [b for b in preview_blocks if b.url == test_url]
        assert len(blocked_test_urls) == 1
        assert blocked_test_urls[0].block_reason == BlockReason.OTHER

        # Remove preview block
        await client.blocking.remove_page_preview_block(site_url=test_site, url=test_url)

        # Verify block is removed
        preview_blocks = await client.blocking.get_active_page_preview_blocks(test_site)
        assert not any(b.url == test_url for b in preview_blocks)

    @pytest.mark.parametrize(
        "entity_type",
        [BlockedUrl.BlockedUrlEntityType.PAGE, BlockedUrl.BlockedUrlEntityType.DIRECTORY],
    )
    @pytest.mark.vcr
    async def test_block_url_with_different_entity_types(
        self,
        client: BingWebmasterClient,
        test_site: str,
        entity_type: BlockedUrl.BlockedUrlEntityType,
    ):
        """Test blocking URLs with different entity types."""
        fixed_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Add trailing slash for directory type
        # (the API returns it with a trailing slash for some reason)
        test_url = (
            f"{test_site}/test-block-{entity_type.name.lower()}"
            if entity_type == BlockedUrl.BlockedUrlEntityType.PAGE
            else f"{test_site}/test-block-{entity_type.name.lower()}/"
        )

        try:
            # Add blocked URL
            await client.blocking.add_blocked_url(
                site_url=test_site,
                blocked_url=test_url,
                entity_type=entity_type,
                date=fixed_date,
            )

            # Verify URL is blocked with correct entity type
            blocked_urls = await client.blocking.get_blocked_urls(test_site)
            blocked_test_urls = [u for u in blocked_urls if u.url == test_url]
            assert len(blocked_test_urls) == 1
            assert blocked_test_urls[0].entity_type == entity_type

        finally:
            # Cleanup
            await client.blocking.remove_blocked_url(
                site_url=test_site,
                blocked_url=test_url,
                entity_type=entity_type,
                date=fixed_date,
            )
