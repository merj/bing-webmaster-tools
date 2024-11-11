import asyncio
import os
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from dotenv import find_dotenv, load_dotenv

from bing_webmaster_tools import BingWebmasterClient, Settings

load_dotenv(find_dotenv(raise_error_if_not_found=True))


@pytest.fixture(scope="session")
def vcr_config() -> Dict[str, Any]:
    """VCR configuration fixture."""
    return {
        # Filter out authorization headers and API keys
        "filter_headers": ["authorization", "apikey", "user-agent", "x-request-origin", "cookie", "host"],
        # Replace API key in query parameters
        "filter_query_parameters": ["apikey"],
        # Custom function to filter sensitive data from responses
        # "before_record_response": lambda response: {
        #     **response,
        #     "body": {
        #         # Filter sensitive fields from JSON responses
        #         # Add more fields as needed
        #         **response["body"],
        #         "api_key": "[FILTERED]" if "api_key" in response["body"] else response["body"].get("api_key"),
        #     }
        # },
        # We exclude headers and body because:
        # - Headers contain API keys we want to ignore
        # - The body might contain dynamic timestamps we don't want to match on
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
    }


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[BingWebmasterClient, None]:
    """Fixture providing a configured BingWebmasterClient."""
    async with BingWebmasterClient(settings=Settings.from_env()) as client:
        yield client


def get_required_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


async def _verify_site(client: BingWebmasterClient, site_url: str) -> None:
    """Verify that a site is available in the account."""
    sites = await client.sites.get_sites()
    site_urls = {s.url for s in sites}
    if not sites or site_url not in site_urls:
        raise Exception(f"Site {site_url} not found in account")


@pytest_asyncio.fixture(scope="session")
async def test_site(client: BingWebmasterClient) -> str:
    """Fixture providing a test site URL from the account."""
    site = get_required_env_var("BING_WEBMASTER_TEST_DEV_SITE")
    await _verify_site(client, site)
    return site.rstrip("/")
