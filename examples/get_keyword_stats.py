#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_keyword_stats(query: str, country: str = "gb", language: str = "en-GB") -> None:
    """Get keyword statistics for a single keyword over a time period from Bing Webmaster Tools.

    Args:
        query: The keyword to analyze impressions for
        country: Two-letter country code (e.g., "gb", "us")
        language: Language-country code (e.g., "en-GB", "en-US")

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            keyword_stats = await client.keywords.get_keyword_stats(
                query=query,
                country=country,
                language=language,
            )

            if len(keyword_stats) == 0:
                print(f"\nNo data found for keyword: {query}")
                return

            print(f"\nKeyword Stats for '{query}':")
            for keyword_stat in keyword_stats:
                print(f"Date: {keyword_stat.date:}")
                print(f"Impressions: {keyword_stat.impressions:,}")
                print(f"Broad Impressions: {keyword_stat.broad_impressions:,}")

    except Exception as e:
        print(f"Error getting keyword stats: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Get keyword stats from Bing Webmaster Tools")

    parser.add_argument("-q", "--query", type=str, required=True, help="Keyword to analyze")
    parser.add_argument("-c", "--country", type=str, default="gb", help="Country code (default: gb)")
    parser.add_argument("-l", "--language", type=str, default="en-GB", help="Language code (default: en-GB)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_keyword_stats(args.query, args.country, args.language))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
