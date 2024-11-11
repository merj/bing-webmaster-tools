#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_feeds(site_url: str, verbose: bool = False) -> None:
    """Get all RSS feeds, XML sitemaps, etc for a site.

    Args:
        site_url: The site URL to get feeds for
        verbose: Enable verbose logging if True

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get all feeds
            feeds = await client.submission.get_feeds(site_url)

            if not feeds:
                print("No feeds found")
                return

            print(f"\nFound {len(feeds)} feeds:")
            for feed in feeds:
                print(f"\nFeed URL: {feed.url}")
                print(f"Status: {feed.status}")
                print(f"URL Count: {feed.url_count:,}")

                if verbose:
                    print(f"File Size: {feed.file_size:,} bytes")
                    print(f"Compressed: {feed.compressed}")
                    print(f"Type: {feed.feed_type}")
                    print(f"Last Crawled: {feed.last_crawled.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Submitted: {feed.submitted.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"Error getting feeds: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="List feeds from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show additional sitemap details")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_feeds(args.site_url, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
