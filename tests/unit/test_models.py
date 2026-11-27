"""How models treat fields Bing sends that they don't declare, and what goes back in request bodies."""

import pytest

from bing_webmaster_tools.models.crawling import CrawlSettings
from bing_webmaster_tools.models.traffic_analysis import RankAndTrafficStats

from .conftest import SITE, net_date

pytestmark = pytest.mark.unit

CRAWL_SETTINGS = {
    "__type": "CrawlSettings:#Microsoft.Bing.Webmaster.Api",
    "CrawlBoostAvailable": False,
    "CrawlBoostEnabled": False,
    "CrawlRate": [5] * 24,
}


def test_undeclared_fields_are_kept_in_model_extra():
    parsed = CrawlSettings.model_validate({**CRAWL_SETTINGS, "SomethingNew": 1})
    assert parsed.model_extra == {"SomethingNew": 1}


def test_every_model_reads_the_wcf_type_hint():
    parsed = RankAndTrafficStats.model_validate(
        {
            "__type": "RankAndTrafficStats:#Microsoft.Bing.Webmaster.Api",
            "Clicks": 1,
            "Date": net_date(1795305600000, None),
            "Impressions": 2,
        }
    )
    assert parsed.type == "RankAndTrafficStats:#Microsoft.Bing.Webmaster.Api"
    assert not parsed.model_extra


def test_request_bodies_leave_out_undeclared_fields():
    settings = CrawlSettings.model_validate({**CRAWL_SETTINGS, "SomethingNew": 1})
    assert settings.to_api_dict() == CRAWL_SETTINGS


async def test_services_send_request_models_without_undeclared_fields(services, api):
    await services.crawling.save_crawl_settings(SITE, {**CRAWL_SETTINGS, "SomethingNew": 1})
    assert api.last.data == {"siteUrl": SITE, "crawlSettings": CRAWL_SETTINGS}
