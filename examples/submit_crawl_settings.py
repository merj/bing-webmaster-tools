#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from typing import List

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings
from bing_webmaster_tools.models.crawling import CrawlSettings


async def display_crawl_settings(client: BingWebmasterClient, site_url: str) -> CrawlSettings:
    """Retrieve and display current crawl settings for a site.

    Args:
        client: An initialized BingWebmasterClient instance
        site_url: The URL of the site to get crawl settings for

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    settings = await client.crawling.get_crawl_settings(site_url)

    print("Current Crawl Settings:")
    print(f"Crawl Boost Available: {settings.crawl_boost_available}")
    print(f"Crawl Boost Enabled: {settings.crawl_boost_enabled}")
    print("Crawl Rate by Hour (1-10):")

    # Display crawl rates in a 24-hour format
    for hour, rate in enumerate(settings.crawl_rate):
        print(f"{hour:02d}:00 - {rate}")

    return settings


async def update_settings(
    site_url: str,
    rate: List[int],
    enable_boost: bool,
) -> None:
    """Update crawl settings for a site."""
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get and display initial settings
            current_settings = await display_crawl_settings(client, site_url)
            print()  # Add blank line after current settings

            # Prepare new settings
            new_settings = CrawlSettings(
                crawl_boost_available=current_settings.crawl_boost_available,
                crawl_boost_enabled=enable_boost if enable_boost is not None else current_settings.crawl_boost_enabled,
                crawl_rate=rate if rate else current_settings.crawl_rate,
            )

            # Save new settings
            await client.crawling.save_crawl_settings(site_url, new_settings)

            print("Updated Crawl Settings:")
            print(f"Crawl Boost Available: {new_settings.crawl_boost_available}")
            print(f"Crawl Boost Enabled: {new_settings.crawl_boost_enabled}")
            print("Crawl Rate by Hour (1-10):")
            for hour, new_rate in enumerate(new_settings.crawl_rate):
                print(f"{hour:02d}:00 - {new_rate}")

    except Exception as e:
        print(f"Error updating crawl settings: {e}", file=sys.stderr)
        raise


def validate_crawl_rates(rates_str: str) -> List[int]:
    """Validate and convert crawl rates string to list."""
    try:
        rates = [int(r) for r in rates_str.split(",")]

        # Validate number of rates
        if len(rates) != 24:
            raise ValueError("Must provide exactly 24 hourly rates")

        # Validate rate values
        if not all(1 <= r <= 10 for r in rates):
            raise ValueError("All rates must be between 1 and 10")

        return rates
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Update crawl settings in Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument(
        "-r",
        "--rates",
        type=validate_crawl_rates,
        help="24 comma-separated hourly crawl rates (1-10), e.g., '5,5,5,...'",
    )
    parser.add_argument("--enable-boost", action="store_true", help="Enable crawl boost")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(update_settings(args.site_url, args.rates, args.enable_boost))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
