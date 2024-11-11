#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_blocked_pages(site_url: str) -> None:
    """Get all blocked pages for a site.

    Args:
        site_url: The site URL to get sitemaps for
        verbose: Enable verbose logging if True

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get blocked URLs
            blocked = await client.blocking.get_blocked_urls(site_url)

            if not blocked:
                print("\nNo blocked URLs found")
                return

            print(f"\nFound {len(blocked)} blocked URLs:")
            for url in blocked:
                print(f"\nURL: {url.url}")
                print(f"Type: {'DIRECTORY' if url.entity_type == 1 else 'PAGE'}")
                print(f"Date: {url.date.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"Error getting blocked pages: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="List blocked pages from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_blocked_pages(args.site_url))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
