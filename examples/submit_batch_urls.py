#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from bing_webmaster_tools import BingWebmasterClient
from bing_webmaster_tools.config import Settings


async def submit_url_batch(client: BingWebmasterClient, site_url: str, urls: List[str]) -> None:
    """Submit a batch of URLs to Bing Webmaster Tools for indexing.

    Args:
        client: An initialized BingWebmasterClient instance
        site_url: The URL of the site in Bing Webmaster Tools
        urls: List of URLs to submit for indexing (maximum 500 URLs per batch)

    Note:
        The number of URLs that can be submitted is limited by your daily and
        monthly quotas. Check quota limits before submitting large batches.

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        await client.submission.submit_url_batch(site_url, urls)
        print(f"Successfully submitted batch of {len(urls)} URLs")
    except Exception as e:
        print(f"Error submitting batch: {e}", file=sys.stderr)
        raise


def chunk_urls(urls: List[str], chunk_size: int = 500) -> List[List[str]]:
    """Split URLs into chunks of specified size.

    Args:
        urls: List of URLs to chunk
        chunk_size: Maximum size of each chunk

    Returns:
        List of URL chunks

    """
    return [urls[i : i + chunk_size] for i in range(0, len(urls), chunk_size)]


async def process_url_file(input_file: Path, site_url: str) -> None:
    """Process URLs from input file and submit them in batches.

    Args:
        input_file: Path to input file containing URLs
        site_url: The site URL to submit URLs for

    """
    try:
        # Read and clean URLs from file
        with input_file.open() as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            print("No URLs found in input file", file=sys.stderr)
            sys.exit(1)

        print(f"Found {len(urls)} URLs to process")

        # Split URLs into batches of 500
        batches = chunk_urls(urls)
        print(f"Split into {len(batches)} batches")

        # Submit batches
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get quota information first
            quota = await client.submission.get_url_submission_quota(site_url)
            print(f"Daily quota remaining: {quota.daily_quota}")
            print(f"Monthly quota remaining: {quota.monthly_quota}")

            total_urls = len(urls)
            if total_urls > quota.monthly_quota:
                print(
                    f"Warning: Total URLs ({total_urls}) exceeds monthly quota ({quota.monthly_quota})", file=sys.stderr
                )
                response = input("Continue anyway? [y/N] ").lower()
                if response != "y":
                    sys.exit(1)

            for batch in batches:
                await submit_url_batch(client, site_url, batch)

        print("URL submission completed successfully!")

    except Exception as e:
        print(f"Error processing URLs: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch submit URLs to Bing Webmaster Tools")

    parser.add_argument("-i", "--input", type=Path, required=True, help="Input file containing one URL per line")
    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(process_url_file(args.input, args.site_url))


if __name__ == "__main__":
    main()
