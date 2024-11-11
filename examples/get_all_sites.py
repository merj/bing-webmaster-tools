#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_sites(verbose: bool = False) -> None:
    """Get all sites from Bing Webmaster Tools.

    Args:
        verbose: Enable verbose logging if True

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get all sites
            sites = await client.sites.get_sites()

            print(f"\nFound {len(sites)} sites:")
            for site in sites:
                print(f"\nSite URL: {site.url}")
                print(f"Verified: {site.is_verified}")
                if verbose:
                    print(f"Authentication Code: {site.authentication_code}")
                    print(f"DNS Verification Code: {site.dns_verification_code}")

    except Exception as e:
        print(f"Error getting sites: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="List all sites from Bing Webmaster Tools")

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging and show additional site details"
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_sites(args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
