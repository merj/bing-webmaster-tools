"""Offline fixtures for unit tests: no API key, no network, no cassettes.

Services only depend on the ApiClient protocol (``request(method, endpoint, params=, data=)``), so
``FakeApiClient`` stands in for the HTTP client: each test queues the JSON body Bing would send and
then inspects the request the service made.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from bing_webmaster_tools import BingWebmasterClient, Settings


@dataclass
class Call:
    method: str
    endpoint: str
    params: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]


@dataclass
class FakeApiClient:
    responses: List[Dict[str, Any]] = field(default_factory=list)
    calls: List[Call] = field(default_factory=list)

    def returns(self, d: Any) -> "FakeApiClient":
        """Queue a response body; Bing wraps every JSON payload in {"d": ...}."""
        self.responses.append({"d": d})
        return self

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.calls.append(Call(method, endpoint, params, data))
        if not self.responses:
            return {"d": None}
        return self.responses.pop(0)

    @property
    def last(self) -> Call:
        return self.calls[-1]


@pytest.fixture
def api() -> FakeApiClient:
    return FakeApiClient()


@pytest.fixture
def services(api: FakeApiClient) -> BingWebmasterClient:
    """A real client whose services are wired to the fake transport."""
    client = BingWebmasterClient(Settings(api_key="unit-test"))
    for name in (
        "blocking",
        "content",
        "crawling",
        "keywords",
        "links",
        "regional",
        "sites",
        "submission",
        "traffic",
        "urls",
    ):
        getattr(client, name)._client = api
    return client


SITE = "https://www.example.com/"


def net_date(ms: int, offset: Optional[str] = "-0700") -> str:
    """A .NET JSON date as Bing sends it, e.g. /Date(1728975600000-0700)/."""
    return f"/Date({ms}{offset or ''})/"
