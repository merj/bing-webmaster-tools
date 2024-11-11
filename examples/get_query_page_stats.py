#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_query_page_stats(site_url: str, query: str, verbose: bool = False) -> None:
    """Get query page statistics from Bing Webmaster Tools.

    Args:
        site_url: The site URL to analyze
        query: The search query to analyze
        verbose: Enable verbose output with additional details

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get query page stats
            stats = await client.traffic.get_query_page_stats(site_url, query)

            if not stats:
                print(f"\nNo statistics found for query: {query}")
                return

            # Calculate summary metrics
            total_clicks = sum(stat.clicks for stat in stats)
            total_impressions = sum(stat.impressions for stat in stats)
            avg_position = sum(stat.avg_impression_position for stat in stats) / len(stats) if stats else 0

            # Print summary
            print(f"\nStatistics for query: {query}")
            print(f"Total pages ranked: {len(stats)}")
            print(f"Total clicks: {total_clicks:,}")
            print(f"Total impressions: {total_impressions:,}")
            print(f"Average position: {avg_position:.1f}")

            if total_impressions > 0:
                ctr = (total_clicks / total_impressions) * 100
                print(f"Overall CTR: {ctr:.2f}%")

            # Print per-page details if verbose
            if verbose:
                print("\nPer-page statistics:")
                sorted_stats = sorted(stats, key=lambda x: x.impressions, reverse=True)
                for stat in sorted_stats:
                    print(f"\nPage query: {stat.query}")
                    print(f"  Clicks: {stat.clicks:,}")
                    print(f"  Impressions: {stat.impressions:,}")
                    print(f"  Avg Click Position: {stat.avg_click_position:.1f}")
                    print(f"  Avg Impression Position: {stat.avg_impression_position:.1f}")
                    if stat.impressions > 0:
                        page_ctr = (stat.clicks / stat.impressions) * 100
                        print(f"  CTR: {page_ctr:.2f}%")

    except Exception as e:
        print(f"Error getting query page statistics: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Get query page statistics from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-q", "--query", type=str, required=True, help="Search query to analyze")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed per-page statistics")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_query_page_stats(args.site_url, args.query, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
