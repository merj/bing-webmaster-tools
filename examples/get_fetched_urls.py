#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_fetched_urls(site_url: str) -> None:
    """Get all fetched pages for a site.

    Args:
        site_url: The site URL to get fetched URLs for

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get fetched URLs
            fetched = await client.submission.get_fetched_urls(site_url)

            if not fetched:
                print("\nNo fetched URLs found")
                return

            print(f"\nFound {len(fetched)} fetched URLs:")
            for url in fetched:
                print(f"\nURL: {url.url}")

    except Exception as e:
        print(f"Error getting fetched pages: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="List fetched pages from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_fetched_urls(args.site_url))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
