#!/usr/bin/env python3
"""Script for managing URL query parameters in Bing Webmaster Tools."""

import argparse
import asyncio
import logging
import sys
from collections import defaultdict
from typing import Any, Dict, Optional

from bing_webmaster_tools import BingWebmasterClient, Settings


async def get_query_parameters(site_url: str, verbose: bool = False) -> None:  # noqa: C901
    """Retrieve and display URL query parameters configured for a site in Bing Webmaster Tools.

    This function fetches the query parameters that are used for URL normalization,
    such as sorting and filtering parameters that don't change the content. It provides
    a summary of enabled and disabled parameters along with their details.

    Args:
        site_url: The URL of the site in Bing Webmaster Tools
        verbose: If True, displays additional parameter details

    Requires BING_WEBMASTER_API_KEY environment variable to be set.

    """
    try:
        async with BingWebmasterClient(Settings.from_env()) as client:
            # Get all query parameters
            params = await client.urls.get_query_parameters(site_url)

            if not params:
                print("\nNo query parameters configured")
                return

            # Calculate statistics
            stats: Dict[str, Dict[str, Any]] = {
                "enabled": {"count": 0, "params": []},
                "disabled": {"count": 0, "params": []},
                "total": len(params),
            }

            # Group parameters by status
            for param in params:
                status = "enabled" if param.is_enabled else "disabled"
                stats[status]["count"] += 1
                stats[status]["params"].append(param)

            # Print summary
            print("\nQuery Parameters Summary:")
            print(f"Total Parameters: {stats['total']}")
            print(f"Enabled Parameters: {stats['enabled']['count']}")
            print(f"Disabled Parameters: {stats['disabled']['count']}")

            # Print enabled parameters
            if stats["enabled"]["count"] > 0:
                print("\nEnabled Parameters:")
                for param in stats["enabled"]["params"]:
                    print(f"  - {param.parameter}")
                    if verbose:
                        print(f"    Last Modified: {param.date.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Source: {param.source}")

            # Print disabled parameters
            if stats["disabled"]["count"] > 0:
                print("\nDisabled Parameters:")
                for param in stats["disabled"]["params"]:
                    print(f"  - {param.parameter}")
                    if verbose:
                        print(f"    Last Modified: {param.date.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Source: {param.source}")

            # Group by last modified date if verbose
            if verbose:
                print("\nParameters by Last Modified Date:")
                params_by_date = defaultdict(list)
                for param in params:
                    date_str = param.date.strftime("%Y-%m-%d")
                    params_by_date[date_str].append(param)

                for date_str, date_params in sorted(params_by_date.items()):
                    print(f"\n{date_str}:")
                    for param in date_params:
                        status = "enabled" if param.is_enabled else "disabled"
                        print(f"  - {param.parameter} ({status})")

    except Exception as e:
        logging.error("Error retrieving query parameters: %s", str(e))
        raise


async def manage_parameter(
    site_url: str,
    parameter: str,
    *,
    remove: bool = False,
    enable: Optional[bool] = None,
) -> None:
    """Manage URL query parameters in Bing Webmaster Tools.

    This function handles adding, removing, enabling, and disabling query parameters
    used for URL normalization in Bing Webmaster Tools.

    Args:
        site_url: The URL of the site in Bing Webmaster Tools
        parameter: The query parameter to manage (e.g., "sort", "page", "filter")
        remove: If True, removes the parameter instead of adding it
        enable: If provided, enables (True) or disables (False) the parameter.
               If None, performs add/remove operation instead.

    Raises:
        BingWebmasterError: If there's an error managing the parameter
        AuthenticationError: If the API key is invalid
        RateLimitError: If the API rate limit is exceeded
        ValueError: If the parameter contains invalid characters

    """
    try:
        # Validate parameter (should only contain unreserved letters and colon)
        if not all(c.isalnum() or c == ":" for c in parameter):
            raise ValueError("Query parameter may only contain letters, numbers, and colon (:)")

        async with BingWebmasterClient(Settings.from_env()) as client:
            if enable is not None:
                # Enable/disable existing parameter
                await client.urls.enable_disable_query_parameter(site_url, parameter, enable)
                action = "enabled" if enable else "disabled"
                logging.info("Successfully %s parameter: %s", action, parameter)
                print(f"Successfully {action} parameter: {parameter}")
            else:
                # Add/remove parameter
                if remove:
                    await client.urls.remove_query_parameter(site_url, parameter)
                    logging.info("Successfully removed parameter: %s", parameter)
                    print(f"Successfully removed parameter: {parameter}")
                else:
                    await client.urls.add_query_parameter(site_url, parameter)
                    logging.info("Successfully added parameter: %s", parameter)
                    print(f"Successfully added parameter: {parameter}")

            # Get updated parameters to show new state
            params = await client.urls.get_query_parameters(site_url)
            param_status = None
            for param in params:
                if param.parameter == parameter:
                    param_status = "enabled" if param.is_enabled else "disabled"
                    break

            if param_status:
                print(f"Parameter status: {param_status}")
                print(f"Last modified: {param.date.strftime('%Y-%m-%d %H:%M:%S')}")

    except ValueError as e:
        logging.error("Invalid parameter format: %s", str(e))
        raise
    except Exception as e:
        logging.error("Error managing parameter: %s", str(e))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage URL query parameters in Bing Webmaster Tools")

    parser.add_argument("-s", "--site-url", type=str, required=True, help="Site URL in Bing Webmaster Tools")

    # Create a mutually exclusive group for operations
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all query parameters with status summary")
    group.add_argument("--add", metavar="PARAM", help="Add a new query parameter")
    group.add_argument("--remove", metavar="PARAM", help="Remove a query parameter")
    group.add_argument("--enable", metavar="PARAM", help="Enable a query parameter")
    group.add_argument("--disable", metavar="PARAM", help="Disable a query parameter")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show additional details including modification dates and grouping by date",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        if args.list:
            asyncio.run(get_query_parameters(args.site_url, args.verbose))
        elif args.add:
            asyncio.run(manage_parameter(args.site_url, args.add))
        elif args.remove:
            asyncio.run(manage_parameter(args.site_url, args.remove, remove=True))
        elif args.enable:
            asyncio.run(manage_parameter(args.site_url, args.enable, enable=True))
        elif args.disable:
            asyncio.run(manage_parameter(args.site_url, args.disable, enable=False))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
