from datetime import datetime

import pytest

from bing_webmaster_tools.models.link_analysis import (
    LinkCount,
    LinkCounts,
    LinkDetail,
    LinkDetails,
)


@pytest.mark.asyncio
class TestLinkAnalysisService:
    """Tests for the link analysis service."""

    async def test_get_link_counts(self, client, test_site):
        """Test retrieving link counts."""
        link_counts = await client.links.get_link_counts(test_site, page=0)

        assert isinstance(link_counts, LinkCounts)
        assert isinstance(link_counts.total_pages, int)
        assert isinstance(link_counts.links, list)
        assert all(isinstance(link, LinkCount) for link in link_counts.links)

    async def test_get_url_links(self, client, test_site):
        """Test retrieving inbound links for a specific URL."""
        link_details = await client.links.get_url_links(
            site_url=test_site,
            link=test_site,  # Using site URL as test URL
            page=0,
        )

        assert isinstance(link_details, LinkDetails)
        assert isinstance(link_details.total_pages, int)
        assert isinstance(link_details.details, list)
        assert all(isinstance(detail, LinkDetail) for detail in link_details.details)

    async def test_connected_page_lifecycle(self, client, test_site):
        """Test the complete lifecycle of connected page management."""
        test_master_url = f"http://example.com/test-{datetime.now().timestamp()}"

        # Add connected page
        await client.links.add_connected_page(site_url=test_site, master_url=test_master_url)
        # Note: We can't guarantee the page will be visible immediately, so we cannot verify anything here

    @pytest.mark.parametrize("page_number", [0, 1, 2])
    async def test_link_counts_pagination(self, client, test_site, page_number: int):
        """Test link counts pagination."""
        link_counts = await client.links.get_link_counts(test_site, page=page_number)

        assert isinstance(link_counts, LinkCounts)
        assert isinstance(link_counts.total_pages, int)
        assert page_number <= link_counts.total_pages or not link_counts.links
        assert all(isinstance(link, LinkCount) for link in link_counts.links)

    @pytest.mark.parametrize("page_number", [0, 1, 2])
    async def test_url_links_pagination(self, client, test_site, page_number: int):
        """Test URL links pagination."""
        link_details = await client.links.get_url_links(site_url=test_site, link=test_site, page=page_number)

        assert isinstance(link_details, LinkDetails)
        assert isinstance(link_details.total_pages, int)
        assert page_number <= link_details.total_pages or not link_details.details

    async def test_get_link_counts_all_pages(self, client, test_site):
        """Test retrieving all pages of link counts."""
        page = 0
        all_links = []
        seen_urls = set()

        while True:
            link_counts = await client.links.get_link_counts(test_site, page=page)
            if not link_counts.links:
                break

            # Check for duplicates
            for link in link_counts.links:
                assert link.url not in seen_urls, "Duplicate URL found in pagination"
                seen_urls.add(link.url)

            all_links.extend(link_counts.links)
            page += 1

            if page >= link_counts.total_pages:
                break

        assert len(all_links) == len(seen_urls), "Duplicate links found"

    async def test_invalid_page_numbers(self, client, test_site):
        """Test behavior with invalid page numbers."""
        # Test with negative page number
        with pytest.raises(ValueError):
            await client.links.get_link_counts(test_site, page=-1)

        # Test with very large page number
        link_counts = await client.links.get_link_counts(test_site, page=9999)
        assert not link_counts.links  # Should be empty for non-existent pages
