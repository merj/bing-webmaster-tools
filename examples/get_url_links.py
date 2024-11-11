#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from typing import Dict, List
from urllib.parse import urlparse

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings
from bing_webmaster_tools.models import LinkDetail


async def get_all_url_links(
    client: BingWebmasterClient, site_url: str, link_url: str, page: int = 0, max_pages: int = 100
) -> List[LinkDetail]:
    """Get all inbound links

    Args:
        client: BingWebmasterClient instance
        site_url: The site URL in Webmaster Tools
        link_url: The URL to get inbound links for
        page: Current paginated page number
        max_pages: Maximum number of paginated pages to process

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    if page >= max_pages:
        logging.warning(f"Reached maximum page limit of {max_pages}")
        return []

    link_details = await client.links.get_url_links(site_url, link_url, page=page)

    # If we have detail records, there might be more pages
    if link_details and link_details.details:
        next_page = await get_all_url_links(client, site_url, link_url, page + 1, max_pages)
        return link_details.details + next_page

    return link_details.details if link_details else []


async def analyze_inbound_links(site_url: str, link_url: str, max_pages: int = 100, verbose: bool = False) -> None:
    """Analyze inbound links for a specific URL.

    Args:
        site_url: The site URL in Webmaster Tools
        link_url: The URL to analyze links for
        max_pages: Maximum number of pages to retrieve
        verbose: Enable verbose output

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            links = await get_all_url_links(client, site_url, link_url, max_pages=max_pages)

            if not links:
                print(f"\nNo inbound links found for: {link_url}")
                return

            # Analyze link data
            domains: Dict[str, int] = {}
            anchor_texts: Dict[str, int] = {}

            for link in links:
                # Group by domain
                domain = urlparse(link.url).netloc
                domains[domain] = domains.get(domain, 0) + 1

                # Group by anchor text
                anchor = link.anchor_text.strip() or "[No Anchor Text]"
                anchor_texts[anchor] = anchor_texts.get(anchor, 0) + 1

            # Print summary
            print(f"\nInbound Link Analysis for: {link_url}")
            print(f"Total Inbound Links: {len(links):,}")
            print(f"Unique Domains: {len(domains):,}")
            print(f"Unique Anchor Texts: {len(anchor_texts):,}")

            # Print top domains
            print("\nTop Linking Domains:")
            sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains[:10]:
                print(f"  {domain}: {count:,} links")

            # Print top anchor texts
            print("\nTop Anchor Texts:")
            sorted_anchors = sorted(anchor_texts.items(), key=lambda x: x[1], reverse=True)
            for anchor, count in sorted_anchors[:10]:
                if len(anchor) > 50:
                    anchor = anchor[:47] + "..."
                print(f'  "{anchor}": {count:,} occurrences')

            # Print full details if verbose
            if verbose:
                print("\nDetailed Link Information:")
                for link in links:
                    print(f"\nSource URL: {link.url}")
                    print(f"Anchor Text: {link.anchor_text or '[No Anchor Text]'}")

    except Exception as e:
        print(f"Error analyzing inbound links: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze inbound links from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-l", "--link-url", type=str, required=True, help="URL to analyze inbound links for")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum number of pages to retrieve (default: 100)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed link information")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(analyze_inbound_links(args.site_url, args.link_url, args.max_pages, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
