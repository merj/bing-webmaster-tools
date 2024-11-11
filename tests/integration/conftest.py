import asyncio
import json
import os
from typing import Any, AsyncGenerator, Dict
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
import pytest_asyncio
from dotenv import find_dotenv, load_dotenv

from bing_webmaster_tools import BingWebmasterClient, Settings

load_dotenv(find_dotenv(raise_error_if_not_found=True))


@pytest.fixture(scope="session")
def vcr_config(test_site) -> Dict[str, Any]:  # noqa: C901
    """VCR configuration fixture."""
    parsed_test_site = urlparse(test_site)
    test_domain = parsed_test_site.netloc
    anonymized_domain = "example.test"

    def _replace_domain(text: str) -> str:
        """Replace domain in any string."""
        return text.replace(test_domain, anonymized_domain)

    def _process_json(obj):
        if isinstance(obj, dict):
            return {k: _process_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_process_json(item) for item in obj]
        elif isinstance(obj, str):
            return _replace_domain(obj)
        return obj

    def _anonymize_test_site(request):
        # Anonymize URL parameters
        if "?" in request.uri:
            url_parts = request.uri.split("?", 1)
            base_url = url_parts[0]
            query_params = parse_qs(url_parts[1])

            # Anonymize all parameter values
            for key in query_params:
                query_params[key] = [_replace_domain(v) for v in query_params[key]]

            request.uri = f"{base_url}?{urlencode(query_params, doseq=True)}"

        # Anonymize request body if present
        if request.body:
            try:
                body = json.loads(request.body)
                request.body = json.dumps(_process_json(body))
            except json.JSONDecodeError:
                # If not JSON, try to anonymize the raw string
                request.body = _replace_domain(request.body)

        return request

    def _anonymize_test_site_response(response):
        if not response["body"]["string"]:
            return response

        try:
            body = json.loads(response["body"]["string"])
            response["body"]["string"] = json.dumps(_process_json(body))
        except json.JSONDecodeError:
            # If not JSON, try to anonymize the raw string
            response["body"]["string"] = _replace_domain(response["body"]["string"])

        return response

    return {
        "filter_headers": ["authorization", "apikey", "user-agent", "x-request-origin", "cookie", "host"],
        "filter_query_parameters": ["apikey"],
        "before_record_request": _anonymize_test_site,
        "before_record_response": _anonymize_test_site_response,
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
    site = get_required_env_var("BING_WEBMASTER_TEST_SITE")
    await _verify_site(client, site)
    return site.rstrip("/")
