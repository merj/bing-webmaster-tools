import json
import os
from typing import Any, AsyncGenerator, Dict
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
import pytest_asyncio
from dotenv import find_dotenv, load_dotenv

from bing_webmaster_tools import BingWebmasterClient, Settings

# Load settings from a .env file if there is one. Variables already set in the
# environment take precedence, so they can also come from the shell or CI secrets.
load_dotenv(find_dotenv())

# The site URL the cassettes are recorded with: the real test site is replaced with it before
# anything is saved, so cassettes never contain the real site.
ANONYMIZED_SITE = "https://example.test"


@pytest.fixture(scope="session")
def replaying(record_mode: str, disable_recording: bool) -> bool:
    """Whether the tests replay recorded cassettes instead of calling the live API.

    This is the default: pytest-recording's default record mode, "none", only replays cassettes.
    Recording needs another mode, such as `--record-mode=rewrite`.
    """
    return record_mode == "none" and not disable_recording


@pytest.fixture(scope="session")
def vcr_config(test_site) -> Dict[str, Any]:  # noqa: C901
    """VCR configuration fixture."""
    parsed_test_site = urlparse(test_site)
    test_domain = parsed_test_site.netloc
    anonymized_domain = urlparse(ANONYMIZED_SITE).netloc

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
            processed_body = json.dumps(_process_json(body))
            response["body"]["string"] = processed_body.encode("utf-8")
        except json.JSONDecodeError:
            # If not JSON, try to anonymize the raw string
            response["body"]["string"] = _replace_domain(response["body"]["string"]).encode("utf-8")

        return response

    return {
        "filter_headers": ["authorization", "apikey", "user-agent", "x-request-origin", "cookie", "host"],
        "filter_query_parameters": ["apikey"],
        "before_record_request": _anonymize_test_site,
        "before_record_response": _anonymize_test_site_response,
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
    }


@pytest_asyncio.fixture(scope="session")
async def client(replaying: bool) -> AsyncGenerator[BingWebmasterClient, None]:
    """Fixture providing a configured BingWebmasterClient.

    When replaying, the client uses a placeholder API key instead of BING_WEBMASTER_API_KEY. The
    cassettes don't contain the key, so replaying doesn't need a real one, and a request that
    isn't replayed fails with InvalidApiKey instead of acting on a real account.
    """
    settings = Settings(api_key="placeholder-api-key-for-replay") if replaying else Settings.from_env()
    async with BingWebmasterClient(settings=settings) as client:
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
async def test_site(client: BingWebmasterClient, replaying: bool) -> str:
    """Fixture providing the URL of the test site.

    When replaying, this is the anonymized site the cassettes were recorded with, so the
    replayed responses contain the same URLs the tests build, and no live check is needed.
    When recording, it is BING_WEBMASTER_TEST_SITE, checked against the account first.
    """
    if replaying:
        return ANONYMIZED_SITE

    site = get_required_env_var("BING_WEBMASTER_TEST_SITE")
    await _verify_site(client, site)
    return site.rstrip("/")
