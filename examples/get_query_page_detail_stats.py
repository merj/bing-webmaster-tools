#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_query_page_detail_stats(site_url: str, query: str, page: str, verbose: bool = False) -> None:
    """Get keyword and related keyword statistics from Bing Webmaster Tools and calculate trends.

    Retrieves detailed statistics for a specific keyword and page combination, including
    impressions, clicks, and position data over time.

    Args:
        site_url: The site URL in Bing Webmaster Tools
        query: The search query to analyze statistics for
        page: The specific page URL to get statistics for
        verbose: If True, displays additional statistics and daily details

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get detailed query page stats
            stats = await client.traffic.get_query_page_detail_stats(site_url=site_url, query=query, page=page)

            if not stats:
                print(f"\nNo detailed statistics found for query '{query}' on page: {page}")
                return

            # Calculate summary metrics
            total_clicks = sum(stat.clicks for stat in stats)
            total_impressions = sum(stat.impressions for stat in stats)
            avg_position = sum(stat.position for stat in stats) / len(stats) if stats else 0

            # Print summary
            print("\nDetailed Statistics:")
            print(f"Query: {query}")
            print(f"Page: {page}")
            print(f"Date Range: {min(stat.date for stat in stats).date()} to {max(stat.date for stat in stats).date()}")
            print("\nSummary Metrics:")
            print(f"Total Days: {len(stats)}")
            print(f"Total Clicks: {total_clicks:,}")
            print(f"Total Impressions: {total_impressions:,}")
            print(f"Average Position: {avg_position:.1f}")

            if total_impressions > 0:
                ctr = (total_clicks / total_impressions) * 100
                print(f"Overall CTR: {ctr:.2f}%")

            # Print daily details if verbose
            if verbose:
                print("\nDaily Statistics:")
                # Sort by date in descending order
                sorted_stats = sorted(stats, key=lambda x: x.date, reverse=True)
                for stat in sorted_stats:
                    print(f"\nDate: {stat.date.strftime('%Y-%m-%d')}")
                    print(f"  Position: {stat.position:.1f}")
                    print(f"  Clicks: {stat.clicks:,}")
                    print(f"  Impressions: {stat.impressions:,}")
                    if stat.impressions > 0:
                        daily_ctr = (stat.clicks / stat.impressions) * 100
                        print(f"  CTR: {daily_ctr:.2f}%")

            # Print trend analysis
            if len(stats) > 1:
                print("\nTrend Analysis:")
                # Sort by date for trend analysis
                sorted_stats = sorted(stats, key=lambda x: x.date)
                first_week = sorted_stats[:7]
                last_week = sorted_stats[-7:]

                # Calculate weekly averages
                first_week_pos = sum(s.position for s in first_week) / len(first_week)
                last_week_pos = sum(s.position for s in last_week) / len(last_week)

                pos_change = last_week_pos - first_week_pos
                pos_change_str = "improved" if pos_change < 0 else "declined"
                print(f"Position has {pos_change_str} by {abs(pos_change):.1f} places over the period")

    except Exception as e:
        print(f"Error getting detailed query page statistics: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Get detailed query page statistics from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-q", "--query", type=str, required=True, help="Search query to analyze")
    parser.add_argument("-p", "--page", type=str, required=True, help="Page URL to analyze")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show daily statistics")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_query_page_detail_stats(args.site_url, args.query, args.page, args.verbose))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
