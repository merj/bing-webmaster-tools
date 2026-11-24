"""Every response recorded in the integration cassettes parses, and parses completely.

The cassettes hold real Bing responses (domain anonymised). Parsing each one with the model its
endpoint returns catches two kinds of drift the integration tests miss: a field typed wrongly (it
fails validation) and a field the model doesn't declare (it lands in model_extra instead of being
silently dropped).
"""

import json
from pathlib import Path
from typing import Iterator, Tuple, Type
from urllib.parse import urlparse

import pytest
import yaml

from bing_webmaster_tools.models.base import BingModel
from bing_webmaster_tools.models.content_blocking import BlockedUrl, PagePreview
from bing_webmaster_tools.models.crawling import CrawlSettings, CrawlStats, UrlWithCrawlIssues
from bing_webmaster_tools.models.keyword_analysis import Keyword, KeywordStats
from bing_webmaster_tools.models.link_analysis import ConnectedSite, LinkCounts, LinkDetails
from bing_webmaster_tools.models.site_management import Site
from bing_webmaster_tools.models.url_management import QueryParameter

pytestmark = pytest.mark.unit

CASSETTES = Path(__file__).parent.parent / "integration" / "cassettes"

RESPONSE_MODELS: dict[str, Type[BingModel]] = {
    "GetBlockedUrls": BlockedUrl,
    "GetActivePagePreviewBlocks": PagePreview,
    "GetCrawlSettings": CrawlSettings,
    "GetCrawlStats": CrawlStats,
    "GetCrawlIssues": UrlWithCrawlIssues,
    "GetKeyword": Keyword,
    "GetRelatedKeywords": Keyword,
    "GetKeywordStats": KeywordStats,
    "GetLinkCounts": LinkCounts,
    "GetUrlLinks": LinkDetails,
    "GetConnectedPages": ConnectedSite,
    "GetUserSites": Site,
    "GetQueryParameters": QueryParameter,
}


def recorded_responses() -> Iterator[Tuple[str, str, object]]:
    for path in sorted(CASSETTES.rglob("*.yaml")):
        cassette = yaml.safe_load(path.read_text(encoding="utf-8"))
        for i, interaction in enumerate(cassette["interactions"]):
            endpoint = urlparse(interaction["request"]["uri"]).path.rsplit("/", 1)[-1]
            if endpoint not in RESPONSE_MODELS or interaction["response"]["status"]["code"] != 200:
                continue
            body = interaction["response"]["body"]["string"]
            payload = json.loads(body.decode() if isinstance(body, bytes) else body).get("d")
            # GetKeyword answers "no data" with Query null; get_keyword() returns None for it
            no_keyword_data = endpoint == "GetKeyword" and not (payload or {}).get("Query")
            if payload and not no_keyword_data:
                yield f"{path.stem}#{i}:{endpoint}", endpoint, payload


RECORDED = list(recorded_responses())


def test_cassettes_cover_some_endpoints():
    assert len({endpoint for _, endpoint, _ in RECORDED}) >= 8


@pytest.mark.parametrize("endpoint, payload", [(e, p) for _, e, p in RECORDED], ids=[i for i, _, _ in RECORDED])
def test_recorded_response_parses_without_unknown_fields(endpoint, payload):
    model = RESPONSE_MODELS[endpoint]
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        parsed = model.model_validate(item)
        assert not parsed.model_extra, f"{model.__name__} is missing fields Bing sends: {sorted(parsed.model_extra)}"
        for value in parsed.__dict__.values():
            for nested in value if isinstance(value, list) else [value]:
                if isinstance(nested, BingModel):
                    assert (
                        not nested.model_extra
                    ), f"{type(nested).__name__} is missing fields Bing sends: {sorted(nested.model_extra)}"
