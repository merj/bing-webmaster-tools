"""The HTTP layer of BingWebmasterClient.request, against a local aiohttp test server.

A real server on localhost (aiohttp's own TestServer) rather than a mocking library, so the tests
exercise the actual request encoding, status handling and retries, and keep working across aiohttp
releases.
"""

import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, List

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer

from bing_webmaster_tools import AuthenticationError, BingWebmasterClient, BingWebmasterError, RateLimitError, Settings

pytestmark = [
    pytest.mark.unit,
    # The test server runs on localhost; pytest --block-network blocks every other host
    pytest.mark.block_network(allowed_hosts=[r"127\.0\.0\.1", "localhost", r"::1"]),
]


class FakeBing:
    """Serves queued responses for any endpoint and records the requests it received."""

    def __init__(self) -> None:
        self.queue: List[Callable[[], web.Response]] = []
        self.repeat: Callable[[], web.Response] = lambda: web.json_response({"d": None})
        self.requests: List[dict] = []

    def then(self, status: int = 200, payload: Any = None, body: str = "") -> "FakeBing":
        self.queue.append(lambda: self._response(status, payload, body))
        return self

    def always(self, status: int = 200, payload: Any = None, body: str = "") -> "FakeBing":
        self.repeat = lambda: self._response(status, payload, body)
        return self

    @staticmethod
    def _response(status: int, payload: Any, body: str) -> web.Response:
        if payload is not None:
            return web.json_response(payload, status=status)
        return web.Response(status=status, text=body)

    async def handle(self, request: web.Request) -> web.Response:
        self.requests.append(
            {
                "method": request.method,
                "endpoint": request.match_info["endpoint"],
                "query": dict(request.query),
                "body": await request.text(),
            }
        )
        return self.queue.pop(0)() if self.queue else self.repeat()


@pytest_asyncio.fixture
async def bing() -> AsyncGenerator[tuple, None]:
    fake = FakeBing()
    app = web.Application()
    app.router.add_route("*", "/json/{endpoint}", fake.handle)
    server = TestServer(app)
    await server.start_server()
    try:
        yield fake, str(server.make_url("/json"))
    finally:
        await server.close()


def client_for(base_url: str, **overrides: Any) -> BingWebmasterClient:
    overrides.setdefault("rate_limit_calls", None)
    overrides.setdefault("rate_limit_period", None)
    client = BingWebmasterClient(Settings(api_key="secret-key", base_url=base_url, **overrides))
    return client


async def test_sends_api_key_and_converts_params(bing):
    fake, base = bing
    fake.then(payload={"d": []})
    async with client_for(base) as client:
        await client.request("GET", "GetQueryStats", params={"siteUrl": "https://a.test/", "flag": True, "x": None})

    req = fake.requests[0]
    assert req["method"] == "GET" and req["endpoint"] == "GetQueryStats"
    assert req["query"]["apikey"] == "secret-key"
    assert req["query"]["siteUrl"] == "https://a.test/"
    assert req["query"]["flag"] == "true"  # booleans go lowercase, as .NET expects
    assert "x" not in req["query"]  # None params are dropped


async def test_posts_json_body_with_net_dates(bing):
    fake, base = bing
    fake.then(payload={"d": None})
    async with client_for(base) as client:
        when = datetime(2024, 10, 15, 7, 0, tzinfo=timezone.utc)
        await client.request("POST", "SubmitUrl", data={"siteUrl": "https://a.test/", "date": when})

    body = json.loads(fake.requests[0]["body"])
    assert body["date"] == "/Date(1728975600000+0000)/"


async def test_invalid_api_key_raises_authentication_error_without_retrying(bing):
    fake, base = bing
    fake.always(status=400, payload={"ErrorCode": 3, "Message": "Invalid API key"})
    async with client_for(base, max_retries=3) as client:
        with pytest.raises(AuthenticationError):
            await client.request("GET", "GetQueryStats")
    assert len(fake.requests) == 1


async def test_server_error_then_success_returns_payload(bing):
    fake, base = bing
    fake.then(status=500, body="oops").then(payload={"d": [1]})
    async with client_for(base, max_retries=2) as client:
        assert await client.request("GET", "GetQueryStats") == {"d": [1]}
    assert len(fake.requests) == 2


async def test_non_json_success_body_is_an_error(bing):
    fake, base = bing
    fake.then(status=200, body="<html>")
    async with client_for(base) as client:
        with pytest.raises(BingWebmasterError, match="Invalid JSON"):
            await client.request("GET", "GetQueryStats")


async def test_destructive_operations_can_be_disabled(bing):
    fake, base = bing
    async with client_for(base, disable_destructive_operations=True) as client:
        with pytest.raises(BingWebmasterError, match="Destructive operations are disabled"):
            await client.request("POST", "SubmitUrl", data={})
    assert fake.requests == []


async def test_get_children_url_info_is_a_read_despite_post(bing):
    fake, base = bing
    fake.then(payload={"d": []})
    async with client_for(base, disable_destructive_operations=True) as client:
        assert await client.request("POST", "GetChildrenUrlInfo", data={}) == {"d": []}


async def test_unknown_error_codes_keep_the_message(bing):
    fake, base = bing
    fake.then(status=400, payload={"ErrorCode": 99, "Message": "ERROR!!! Something new"})
    async with client_for(base, max_retries=0) as client:
        with pytest.raises(BingWebmasterError, match="Something new") as exc:
            await client.request("GET", "GetQueryStats")
    assert exc.value.error_code is None


async def test_throttling_is_retried_then_raised(bing):
    fake, base = bing
    fake.always(status=400, payload={"ErrorCode": 4, "Message": "ThrottleUser"})
    async with client_for(base, max_retries=1) as client:
        with pytest.raises(RateLimitError):
            await client.request("GET", "GetQueryStats")
    # max_retries=1: the first attempt plus one retry
    assert len(fake.requests) == 2


async def test_max_retries_zero_means_a_single_attempt(bing):
    fake, base = bing
    fake.always(status=500, body="oops")
    async with client_for(base, max_retries=0) as client:
        with pytest.raises(BingWebmasterError):
            await client.request("GET", "GetQueryStats")
    assert len(fake.requests) == 1


async def test_api_key_is_not_logged(bing, caplog):
    fake, base = bing
    caplog.set_level("DEBUG")
    fake.then(payload={"d": []})
    async with client_for(base) as client:
        await client.request("GET", "GetQueryStats", params={"siteUrl": "https://a.test/"})
    ours = [r.getMessage() for r in caplog.records if r.name.startswith("bing_webmaster_tools")]
    assert ours, "expected the client to log the request at DEBUG"
    assert not any("secret-key" in line for line in ours)


async def test_retired_method_gets_a_clear_error(bing):
    fake, base = bing
    fake.then(status=404, body="")
    async with client_for(base, max_retries=0) as client:
        with pytest.raises(BingWebmasterError, match="no method 'GetSiteMoves'.*retired") as exc:
            await client.request("GET", "GetSiteMoves", params={"siteUrl": "https://a.test/"})
    assert exc.value.status_code == 404
