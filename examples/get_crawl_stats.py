#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def get_crawl_stats(
    site_url: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> None:
    """Get crawl statistics for a site within a date range.

    Args:
        site_url: The site URL to get crawl stats for
        start_date: Start date for stats (defaults to 30 days ago)
        end_date: End date for stats (defaults to today)

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get crawl statistics
            stats = await client.crawling.get_crawl_stats(site_url, start_date=start_date, end_date=end_date)

            if not stats:
                print("\nNo crawl statistics found")
                return

            print(f"\nFound crawl statistics from {start_date.date()} to {end_date.date()}:")
            for stat in stats:
                print(f"\nDate: {stat.date}")
                print("Crawl Statistics:")
                print(f"  Pages crawled: {stat.crawled_pages:,}")
                print(f"  Pages in index: {stat.in_index:,}")
                print(f"  Incoming links: {stat.in_links:,}")

                print("\nHTTP Status Codes:")
                print(f"  2xx responses: {stat.code_2xx:,}")
                print(f"  301 redirects: {stat.code_301:,}")
                print(f"  302 redirects: {stat.code_302:,}")
                print(f"  4xx errors: {stat.code_4xx:,}")
                print(f"  5xx errors: {stat.code_5xx:,}")
                print(f"  Other status codes: {stat.all_other_codes:,}")

                print("\nIssues:")
                print(f"  Blocked by robots.txt: {stat.blocked_by_robots_txt:,}")
                print(f"  Contains malware: {stat.contains_malware:,}")
                print(f"  Total crawl errors: {stat.crawl_errors:,}")
                print("-" * 50)

    except Exception as e:
        print(f"Error getting crawl statistics: {e}", file=sys.stderr)
        raise


def valid_date(date_str: str) -> datetime:
    """Convert string to datetime object.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        datetime: Parsed datetime object

    Raises:
        ArgumentTypeError: If date format is invalid

    """
    try:
        # Parse the date at the start of the day (midnight)
        return datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date format: {e}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Get crawl statistics from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("--start-date", type=valid_date, help="Start date in YYYY-MM-DD format (default: 30 days ago)")
    parser.add_argument("--end-date", type=valid_date, help="End date in YYYY-MM-DD format (default: today)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_crawl_stats(args.site_url, start_date=args.start_date, end_date=args.end_date))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
