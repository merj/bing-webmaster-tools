#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def submit_sitemap(site_url: str, sitemap_url: str, verbose: bool = False) -> None:
    """Submit an XML sitemap to Bing Webmaster Tools.

    Args:
        site_url: The site URL in Bing Webmaster Tools
        sitemap_url: The URL of the sitemap to submit
        verbose: Enable verbose logging if True

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            if verbose:
                print(f"Submitting sitemap: {sitemap_url}")
                print(f"For site: {site_url}")

            # Submit the sitemap
            await client.submission.submit_feed(site_url, sitemap_url)
            print(f"Successfully submitted sitemap: {sitemap_url}")

    except Exception as e:
        print(f"Error submitting sitemap: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit XML sitemap to Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-l", "--sitemap-url", type=str, required=True, help="URL of the sitemap to submit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show submission details and verification")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(submit_sitemap(args.site_url, args.sitemap_url, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
