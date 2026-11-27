"""Every read-only method: the endpoint and parameters it sends, and how it parses Bing's answer.

Payloads follow the shapes the live API returned in November 2026 (values made up, example.com).
Each parsed model must declare every field in its payload: a field landing in model_extra means the
model has fallen behind the API.
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, NamedTuple, Optional

import pytest

from bing_webmaster_tools.errors import ApiErrorCode, BingWebmasterError
from bing_webmaster_tools.models.base import BingModel
from bing_webmaster_tools.models.crawling import UrlWithCrawlIssues

from .conftest import SITE, net_date

pytestmark = pytest.mark.unit

PAGE = "https://www.example.com/helmets/"
QUERY = "example helmet"
DAY = net_date(1795305600000, None)  # 2026-11-22T00:00Z, as Bing sends daily dates today
DAY_TS = 1795305600  # DAY as a POSIX timestamp: compared as an instant, so the check holds in any time zone
WEEK = net_date(1795132800000, None)  # 2026-11-20T00:00Z, a weekly bucket


def query_stats(query: str = QUERY) -> Dict[str, Any]:
    return {
        "__type": "QueryStats:#Microsoft.Bing.Webmaster.Api",
        "AvgClickPosition": -1,
        "AvgImpressionPosition": 4,
        "Clicks": 3,
        "Date": WEEK,
        "Impressions": 120,
        "Query": query,
    }


def rank_and_traffic() -> Dict[str, Any]:
    return {
        "__type": "RankAndTrafficStats:#Microsoft.Bing.Webmaster.Api",
        "Clicks": 206,
        "Date": DAY,
        "Impressions": 4932,
    }


def url_info() -> Dict[str, Any]:
    return {
        "__type": "UrlInfo:#Microsoft.Bing.Webmaster.Api",
        "AnchorCount": 12,
        "DiscoveryDate": DAY,
        "DocumentSize": 51234,
        "HttpStatus": 200,
        "IsPage": True,
        "LastCrawledDate": DAY,
        "TotalChildUrlCount": 0,
        "Url": PAGE,
    }


def url_traffic_info() -> Dict[str, Any]:
    return {
        "__type": "UrlTrafficInfo:#Microsoft.Bing.Webmaster.Api",
        "Clicks": 5,
        "Impressions": 80,
        "IsPage": True,
        "Url": PAGE,
    }


def feed() -> Dict[str, Any]:
    return {
        "__type": "Feed:#Microsoft.Bing.Webmaster.Api",
        "Compressed": False,
        "FileSize": 2048,
        "LastCrawled": DAY,
        "Status": "Success",
        "Submitted": DAY,
        "Type": "Sitemap",
        "Url": "https://www.example.com/sitemap.xml",
        "UrlCount": 431,
    }


class Case(NamedTuple):
    call: Callable[[Any], Any]
    endpoint: str
    params: Optional[Dict[str, Any]]
    payload: Any
    check: Callable[[Any], None]
    method: str = "GET"


def first(check: Callable[[Any], None]) -> Callable[[Any], None]:
    def run(result: List[Any]) -> None:
        assert isinstance(result, list) and result
        check(result[0])

    return run


CASES = {
    # traffic analysis
    "get_rank_and_traffic_stats": Case(
        lambda c: c.traffic.get_rank_and_traffic_stats(SITE),
        "GetRankAndTrafficStats",
        {"siteUrl": SITE},
        [rank_and_traffic()],
        first(lambda r: (r.clicks, r.impressions, r.date.timestamp()) == (206, 4932, DAY_TS) or pytest.fail(r)),
    ),
    "get_query_traffic_stats": Case(
        lambda c: c.traffic.get_query_traffic_stats(SITE, QUERY),
        "GetQueryTrafficStats",
        {"siteUrl": SITE, "query": QUERY},
        [rank_and_traffic()],
        first(lambda r: r.clicks == 206 or pytest.fail(r)),
    ),
    "get_query_stats": Case(
        lambda c: c.traffic.get_query_stats(SITE),
        "GetQueryStats",
        {"siteUrl": SITE},
        [query_stats()],
        first(lambda r: (r.query, r.avg_click_position, r.avg_impression_position) == (QUERY, -1, 4) or pytest.fail(r)),
    ),
    "get_page_stats": Case(
        lambda c: c.traffic.get_page_stats(SITE),
        "GetPageStats",
        {"siteUrl": SITE},
        [query_stats(PAGE)],  # Bing reuses QueryStats: the page URL comes back in Query
        first(lambda r: r.query == PAGE or pytest.fail(r)),
    ),
    "get_page_query_stats": Case(
        lambda c: c.traffic.get_page_query_stats(SITE, PAGE),
        "GetPageQueryStats",
        {"siteUrl": SITE, "page": PAGE},
        [query_stats()],
        first(lambda r: r.clicks == 3 or pytest.fail(r)),
    ),
    "get_query_page_stats": Case(
        lambda c: c.traffic.get_query_page_stats(SITE, QUERY),
        "GetQueryPageStats",
        {"siteUrl": SITE, "query": QUERY},
        [query_stats(PAGE)],
        first(lambda r: r.query == PAGE or pytest.fail(r)),
    ),
    "get_query_page_detail_stats": Case(
        lambda c: c.traffic.get_query_page_detail_stats(SITE, QUERY, PAGE),
        "GetQueryPageDetailStats",
        {"siteUrl": SITE, "query": QUERY, "page": PAGE},
        [
            {
                "__type": "DetailedQueryStats:#Microsoft.Bing.Webmaster.Api",
                "Clicks": 1,
                "Date": WEEK,
                "Impressions": 9,
                "Position": 3,
            }
        ],
        first(lambda r: r.position == 3 or pytest.fail(r)),
    ),
    # crawling
    "get_crawl_stats": Case(
        lambda c: c.crawling.get_crawl_stats(SITE),
        "GetCrawlStats",
        {"siteUrl": SITE},
        [
            {
                "__type": "CrawlStats:#Microsoft.Bing.Webmaster.Api",
                "AllOtherCodes": 12061,
                "BlockedByRobotsTxt": 0,
                "Code2xx": 58153,
                "Code301": 2568,
                "Code302": 4,
                "Code4xx": 963,
                "Code5xx": 4,
                "ConnectionTimeout": 2,
                "ContainsMalware": 0,
                "CrawlErrors": 1064,
                "CrawledPages": 13109,
                "Date": DAY,
                "DnsFailures": 1,
                "InIndex": 57200,
                "InLinks": 41595,
            }
        ],
        first(lambda r: (r.connection_timeout, r.dns_failures, r.crawled_pages) == (2, 1, 13109) or pytest.fail(r)),
    ),
    "get_crawl_issues": Case(
        lambda c: c.crawling.get_crawl_issues(SITE),
        "GetCrawlIssues",
        {"siteUrl": SITE},
        [
            {
                "__type": "UrlWithCrawlIssues:#Microsoft.Bing.Webmaster.Api",
                "HttpCode": 404,
                "InLinks": 3,
                "Issues": 20,  # CODE_4XX | BLOCKED_BY_ROBOTS_TXT
                "Url": PAGE,
            }
        ],
        first(
            lambda r: (
                (
                    UrlWithCrawlIssues.CrawlIssues.CODE_4XX in r.issues
                    and UrlWithCrawlIssues.CrawlIssues.BLOCKED_BY_ROBOTS_TXT in r.issues
                )
                or pytest.fail(r)
            )
        ),
    ),
    "get_crawl_settings": Case(
        lambda c: c.crawling.get_crawl_settings(SITE),
        "GetCrawlSettings",
        {"siteUrl": SITE},
        {
            "__type": "CrawlSettings:#Microsoft.Bing.Webmaster.Api",
            "CrawlBoostAvailable": False,
            "CrawlBoostEnabled": False,
            "CrawlRate": [5] * 24,
        },
        lambda r: r.crawl_rate == [5] * 24 or pytest.fail(r),
    ),
    # links
    "get_link_counts": Case(
        lambda c: c.links.get_link_counts(SITE, 0),
        "GetLinkCounts",
        {"siteUrl": SITE, "page": 0},
        {
            "__type": "LinkCounts:#Microsoft.Bing.Webmaster.Api",
            "Links": [{"__type": "LinkCount:#Microsoft.Bing.Webmaster.Api", "Count": 7, "Url": PAGE}],
            "TotalPages": 1,
        },
        lambda r: (r.total_pages, r.links[0].count) == (1, 7) or pytest.fail(r),
    ),
    "get_url_links": Case(
        lambda c: c.links.get_url_links(SITE, PAGE, 0),
        "GetUrlLinks",
        {"siteUrl": SITE, "link": PAGE, "page": 0},
        {
            "__type": "LinkDetails:#Microsoft.Bing.Webmaster.Api",
            "Details": [
                {
                    "__type": "LinkDetail:#Microsoft.Bing.Webmaster.Api",
                    "AnchorText": "helmets",
                    "Url": "https://ref.example.org/",
                }
            ],
            "TotalPages": 1,
        },
        lambda r: r.details[0].anchor_text == "helmets" or pytest.fail(r),
    ),
    "get_deep_link_blocks": Case(
        lambda c: c.links.get_deep_link_blocks(SITE),
        "GetDeepLinkBlocks",
        {"siteUrl": SITE},
        [],
        lambda r: r == [] or pytest.fail(r),
    ),
    # content
    "get_url_info": Case(
        lambda c: c.content.get_url_info(SITE, PAGE),
        "GetUrlInfo",
        {"siteUrl": SITE, "url": PAGE},
        url_info(),
        lambda r: (r.http_status, r.document_size) == (200, 51234) or pytest.fail(r),
    ),
    "get_url_traffic_info": Case(
        lambda c: c.content.get_url_traffic_info(SITE, PAGE),
        "GetUrlTrafficInfo",
        {"siteUrl": SITE, "url": PAGE},
        url_traffic_info(),
        lambda r: r.impressions == 80 or pytest.fail(r),
    ),
    "get_children_url_info": Case(
        lambda c: c.content.get_children_url_info(SITE, SITE, 0),
        "GetChildrenUrlInfo",
        None,
        [url_info()],
        first(lambda r: r.url == PAGE or pytest.fail(r)),
        method="POST",  # a read that Bing serves as POST
    ),
    "get_children_url_traffic_info": Case(
        lambda c: c.content.get_children_url_traffic_info(SITE, SITE, 0),
        "GetChildrenUrlTrafficInfo",
        {"siteUrl": SITE, "url": SITE, "page": 0},
        [url_traffic_info()],
        first(lambda r: r.clicks == 5 or pytest.fail(r)),
    ),
    # submission
    "get_url_submission_quota": Case(
        lambda c: c.submission.get_url_submission_quota(SITE),
        "GetUrlSubmissionQuota",
        {"siteUrl": SITE},
        {"__type": "UrlSubmissionQuota:#Microsoft.Bing.Webmaster.Api", "DailyQuota": 100, "MonthlyQuota": 3000},
        lambda r: r.daily_quota == 100 or pytest.fail(r),
    ),
    "get_content_submission_quota": Case(
        lambda c: c.submission.get_content_submission_quota(SITE),
        "GetContentSubmissionQuota",
        {"siteUrl": SITE},
        {"__type": "ContentSubmissionQuota:#Microsoft.Bing.Webmaster.Api", "DailyQuota": 10000, "MonthlyQuota": 300000},
        lambda r: r.monthly_quota == 300000 or pytest.fail(r),
    ),
    "get_feeds": Case(
        lambda c: c.submission.get_feeds(SITE),
        "GetFeeds",
        {"siteUrl": SITE},
        [feed()],
        first(lambda r: (r.feed_type, r.url_count) == ("Sitemap", 431) or pytest.fail(r)),
    ),
    "get_feed_details": Case(
        lambda c: c.submission.get_feed_details(SITE, "https://www.example.com/sitemap.xml"),
        "GetFeedDetails",
        {"siteUrl": SITE, "feedUrl": "https://www.example.com/sitemap.xml"},
        [feed()],
        first(lambda r: r.status == "Success" or pytest.fail(r)),
    ),
    "get_fetched_urls": Case(
        lambda c: c.submission.get_fetched_urls(SITE),
        "GetFetchedUrls",
        {"siteUrl": SITE},
        [
            {
                "__type": "FetchedUrl:#Microsoft.Bing.Webmaster.Api",
                "Date": DAY,
                "Expired": False,
                "Fetched": True,
                "Url": PAGE,
            }
        ],
        first(lambda r: r.fetched is True or pytest.fail(r)),
    ),
    "get_fetched_url_details": Case(
        lambda c: c.submission.get_fetched_url_details(SITE, PAGE),
        "GetFetchedUrlDetails",
        {"siteUrl": SITE, "url": PAGE},
        {
            "__type": "FetchedUrlDetails:#Microsoft.Bing.Webmaster.Api",
            "Date": DAY,
            "Document": "<html></html>",
            "Headers": "HTTP/1.1 200 OK",
            "Status": "OK",
            "Url": PAGE,
        },
        lambda r: r.status == "OK" or pytest.fail(r),
    ),
    # blocking
    "get_blocked_urls": Case(
        lambda c: c.blocking.get_blocked_urls(SITE),
        "GetBlockedUrls",
        {"siteUrl": SITE},
        [
            {
                "__type": "BlockedUrl:#Microsoft.Bing.Webmaster.Api",
                "Date": DAY,
                "DaysToExpire": 78,
                "EntityType": 0,
                "RequestType": 0,
                "Url": PAGE,
            }
        ],
        first(lambda r: r.days_to_expire == 78 or pytest.fail(r)),
    ),
    "get_active_page_preview_blocks": Case(
        lambda c: c.blocking.get_active_page_preview_blocks(SITE),
        "GetActivePagePreviewBlocks",
        {"siteUrl": SITE},
        [
            {
                "__type": "PagePreview:#Microsoft.Bing.Webmaster.Shared.DataContracts",
                "Action": 0,
                "BlockReason": 4,
                "Reason": "4",
                "RefreshReason": 0,
                "SiteUrl": SITE,
                "SubmitDate": DAY,
                "Url": PAGE,
                "UserId": "0123456789ABCDEF",
            }
        ],
        first(lambda r: (r.block_reason, r.submit_date.timestamp()) == (4, DAY_TS) or pytest.fail(r)),
    ),
    # regional, sites, url parameters
    "get_country_region_settings": Case(
        lambda c: c.regional.get_country_region_settings(SITE),
        "GetCountryRegionSettings",
        {"siteUrl": SITE},
        [
            {
                "__type": "CountryRegionSettings:#Microsoft.Bing.Webmaster.Api",
                "Date": DAY,
                "TwoLetterIsoCountryCode": "de",
                "Type": 1,
                "Url": "https://www.example.com/de/",
            }
        ],
        first(lambda r: r.two_letter_iso_country_code == "de" or pytest.fail(r)),
    ),
    "get_sites": Case(
        lambda c: c.sites.get_sites(),
        "GetUserSites",
        None,
        [
            {
                "__type": "Site:#Microsoft.Bing.Webmaster.Api",
                "AuthenticationCode": "ABC",
                "DnsVerificationCode": "DEF",
                "IsVerified": True,
                "Url": SITE,
            }
        ],
        first(lambda r: r.is_verified is True or pytest.fail(r)),
    ),
    "get_site_roles": Case(
        lambda c: c.sites.get_site_roles(SITE),
        "GetSiteRoles",
        {"siteUrl": SITE, "includeAllSubdomains": False},
        [
            {
                "__type": "SiteRoles:#Microsoft.Bing.Webmaster.Api",
                "Date": DAY,
                "DelegatedCode": None,
                "DelegatedCodeOwnerEmail": None,
                "DelegatorEmail": "owner@example.com",
                "Email": "reader@example.com",
                "Expired": False,
                "Role": 1,
                "Site": SITE,
                "VerificationSite": SITE,
            }
        ],
        first(lambda r: r.role == 1 or pytest.fail(r)),
    ),
    "get_query_parameters": Case(
        lambda c: c.urls.get_query_parameters(SITE),
        "GetQueryParameters",
        {"siteUrl": SITE},
        [
            {
                "__type": "QueryParameter:#Microsoft.Bing.Webmaster.Api",
                "Date": DAY,
                "IsEnabled": True,
                "Parameter": "sort",
                "Source": 0,
            }
        ],
        first(lambda r: r.parameter == "sort" or pytest.fail(r)),
    ),
    # keywords (no siteUrl)
    "get_keyword_stats": Case(
        lambda c: c.keywords.get_keyword_stats(QUERY, "us", "en-US"),
        "GetKeywordStats",
        {"q": QUERY, "country": "us", "language": "en-US"},
        [
            {
                "__type": "KeywordStats:#Microsoft.Bing.Webmaster.Api",
                "BroadImpressions": 900,
                "Date": WEEK,
                "Impressions": 150,
                "Query": QUERY,
            }
        ],
        first(lambda r: r.broad_impressions == 900 or pytest.fail(r)),
    ),
    "get_keyword": Case(
        lambda c: c.keywords.get_keyword(QUERY, "us", "en-US", datetime(2026, 10, 1), datetime(2026, 10, 31)),
        "GetKeyword",
        {"q": QUERY, "country": "us", "language": "en-US", "startDate": "2026-10-01", "endDate": "2026-10-31"},
        {
            "__type": "Keyword:#Microsoft.Bing.Webmaster.Api",
            "BroadImpressions": 900,
            "Impressions": 150,
            "Query": QUERY,
        },
        lambda r: r.impressions == 150 or pytest.fail(r),
    ),
    "get_keyword_no_data": Case(
        lambda c: c.keywords.get_keyword(QUERY, "us", "en-US", datetime(2026, 10, 1), datetime(2026, 10, 31)),
        "GetKeyword",
        {"q": QUERY, "country": "us", "language": "en-US", "startDate": "2026-10-01", "endDate": "2026-10-31"},
        {"__type": "Keyword:#Microsoft.Bing.Webmaster.Api", "BroadImpressions": 0, "Impressions": 0, "Query": None},
        lambda r: r is None or pytest.fail(r),
    ),
    "get_related_keywords": Case(
        lambda c: c.keywords.get_related_keywords(QUERY, "us", "en-US", datetime(2026, 10, 1), datetime(2026, 10, 31)),
        "GetRelatedKeywords",
        {"q": QUERY, "country": "us", "language": "en-US", "startDate": "2026-10-01", "endDate": "2026-10-31"},
        [
            {
                "__type": "Keyword:#Microsoft.Bing.Webmaster.Api",
                "BroadImpressions": 40,
                "Impressions": 10,
                "Query": "example helmets",
            }
        ],
        first(lambda r: r.query == "example helmets" or pytest.fail(r)),
    ),
}


def all_models(result: Any) -> List[BingModel]:
    found: List[BingModel] = []
    for item in result if isinstance(result, list) else [result]:
        if isinstance(item, BingModel):
            found.append(item)
            for value in item.__dict__.values():
                found += all_models(value) if isinstance(value, (list, BingModel)) else []
    return found


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
async def test_read_endpoint(case: Case, services, api):
    api.returns(case.payload)
    result = await case.call(services)

    assert api.last.method == case.method
    assert api.last.endpoint == case.endpoint
    if case.params is not None:
        assert api.last.params == case.params
    for model in all_models(result):
        assert not model.model_extra, f"{type(model).__name__} does not declare {sorted(model.model_extra)}"
    case.check(result)


def test_every_read_method_has_a_case():
    """A new get_* method on any service needs a case above."""
    import inspect

    from bing_webmaster_tools import BingWebmasterClient, Settings

    client = BingWebmasterClient(Settings(api_key="unit-test"))
    retired = {"get_deep_link", "get_deep_link_algo_urls", "get_site_moves", "get_connected_pages"}
    methods = {
        name
        for service in vars(client).values()
        if hasattr(service, "_client")
        for name, _ in inspect.getmembers(service, inspect.iscoroutinefunction)
        if name.startswith("get_")
    }
    assert methods - retired - set(CASES) == set()


async def test_get_children_url_info_sends_its_filter_in_the_body(services, api):
    api.returns([])
    await services.content.get_children_url_info(SITE, SITE, 2)
    assert api.last.data["siteUrl"] == SITE
    assert api.last.data["url"] == SITE
    assert api.last.data["page"] == 2


def test_weekly_dates_differ_by_seven_days():
    """Sanity check on the fixtures: WEEK is a Friday bucket two days before DAY."""
    from bing_webmaster_tools.utils import parse_timestamp_from_api

    assert parse_timestamp_from_api(DAY) - parse_timestamp_from_api(WEEK) == timedelta(days=2)


async def test_retired_site_moves_warn(services, api):
    api.returns([])
    with pytest.warns(DeprecationWarning, match="no longer served"):
        await services.sites.get_site_moves(SITE)


async def test_null_payload_means_no_data(services, api):
    """Bing sends {"d": null}, as well as an empty list, when it has nothing to return."""
    api.responses.append({"d": None})
    assert await services.traffic.get_query_stats(SITE) == []


async def test_check_site_verification(services, api):
    api.returns(True)
    assert await services.sites.check_site_verification(SITE) is True
    assert (api.last.method, api.last.endpoint, api.last.params) == ("GET", "CheckSiteVerification", {"siteUrl": SITE})


async def test_check_site_verification_unverified_is_false(services, api):
    async def unverified(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise BingWebmasterError("ERROR!!! SiteNotVerified", status_code=400, error_code=ApiErrorCode.SITE_NOT_VERIFIED)

    api.request = unverified  # type: ignore[method-assign]
    assert await services.sites.check_site_verification(SITE) is False
