from datetime import datetime

import pytest

from bing_webmaster_tools.client import BingWebmasterClient
from bing_webmaster_tools.models.content_blocking import BlockedUrl, BlockReason


@pytest.mark.asyncio
class TestContentBlockingService:
    """Tests for the content blocking service."""

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

    async def test_block_url_lifecycle(self, client: BingWebmasterClient, test_site: str):
        """Test the complete lifecycle of blocking and unblocking a URL."""
        test_url = f"{test_site}/test-block-{datetime.now().timestamp()}"

        # Add blocked URL
        await client.blocking.add_blocked_url(
            site_url=test_site,
            blocked_url=test_url,
            entity_type=BlockedUrl.BlockedUrlEntityType.PAGE,
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
        )

        # Verify URL is no longer blocked
        blocked_urls = await client.blocking.get_blocked_urls(test_site)
        assert not any(u.url == test_url for u in blocked_urls)

    async def test_page_preview_block_lifecycle(self, client: BingWebmasterClient, test_site: str):
        """Test the complete lifecycle of page preview blocking."""
        test_url = f"{test_site}/test-preview-{datetime.now().timestamp()}"

        # Add preview block
        await client.blocking.add_page_preview_block(
            site_url=test_site, url=test_url, reason=BlockReason.OTHER
        )

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
    async def test_block_url_with_different_entity_types(
        self,
        client: BingWebmasterClient,
        test_site: str,
        entity_type: BlockedUrl.BlockedUrlEntityType,
    ):
        """Test blocking URLs with different entity types."""
        test_url = f"{test_site}test-block-{entity_type.name.lower()}-{datetime.now().timestamp()}"

        try:
            # Add blocked URL
            await client.blocking.add_blocked_url(
                site_url=test_site, blocked_url=test_url, entity_type=entity_type
            )

            # Verify URL is blocked with correct entity type
            blocked_urls = await client.blocking.get_blocked_urls(test_site)
            blocked_test_urls = [u for u in blocked_urls if u.url == test_url]
            assert len(blocked_test_urls) == 1
            assert blocked_test_urls[0].entity_type == entity_type

        finally:
            # Cleanup
            await client.blocking.remove_blocked_url(
                site_url=test_site, blocked_url=test_url, entity_type=entity_type
            )
