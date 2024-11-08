import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import find_dotenv, load_dotenv

from bing_webmaster_tools import BingWebmasterClient, Settings

load_dotenv(find_dotenv(raise_error_if_not_found=True))

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )


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


TEST_SITE = get_required_env_var("TEST_SITE_URL")
LIVE_SITE = get_required_env_var("LIVE_SITE_URL")


async def _verify_site(client: BingWebmasterClient, site_url: str) -> None:
    """Verify that a site is available in the account."""
    sites = await client.sites.get_sites()
    site_urls = {s.url for s in sites}
    if not sites or site_url not in site_urls:
        raise Exception(f"Site {site_url} not found in account")


@pytest_asyncio.fixture(scope="session")
async def test_site(client: BingWebmasterClient) -> str:
    """Fixture providing a test site URL from the account."""
    await _verify_site(client, TEST_SITE)
    return TEST_SITE


@pytest_asyncio.fixture(scope="session")
async def live_site(client: BingWebmasterClient) -> str:
    """Fixture providing a live site URL from the account."""
    # TODO: disallow destructive operations here
    await _verify_site(client, LIVE_SITE)
    return LIVE_SITE
