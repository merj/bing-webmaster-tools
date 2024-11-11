#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from typing import Dict, List

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings
from bing_webmaster_tools.models import UrlWithCrawlIssues


async def get_crawl_issues(site_url: str) -> None:
    """Get all page issues for a site.

    Args:
        site_url: The site URL to get issues for

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get issues
            issues = await client.crawling.get_crawl_issues(site_url)

            if not issues:
                print("\nNo issues found")
                return

            # Group issues by type
            issues_by_type: Dict[UrlWithCrawlIssues.CrawlIssues, List[str]] = {}

            print(f"\nFound {len(issues)} issues:")
            for issue in issues:
                print(f"\nIssue: {issue}")

                if issue.issues not in issues_by_type:
                    issues_by_type[issue.issues] = []
                issues_by_type[issue.issues].append(issue.url)

            print(f"\nFound {len(issues)} URLs with crawl issues:")
            for issue_type, urls in issues_by_type.items():
                print(f"\nIssue Type: {issue_type.name}")
                print(f"# Affected URLs: {len(urls)}")

    except Exception as e:
        print(f"Error getting issue pages: {e}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="List issue pages from Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        asyncio.run(get_crawl_issues(args.site_url))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
