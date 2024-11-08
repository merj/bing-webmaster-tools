from datetime import datetime
from enum import IntEnum

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class CrawlDateFilter(IntEnum):
    ANY = 0
    LAST_THREE_WEEKS = 4
    LAST_TWO_WEEKS = 2
    LAST_WEEK = 1


class DiscoveredDateFilter(IntEnum):
    ANY = 0
    LAST_MONTH = 2
    LAST_WEEK = 1


class DocFlagsFilters(IntEnum):
    ANY = 0
    IS_BLOCKED_BY_ROBOTS_TXT = 1
    IS_MALWARE = 2


class HttpCodeFilters(IntEnum):
    ALL_OTHERS = 64
    ANY = 0
    CODE_2XX = 1
    CODE_301 = 4
    CODE_302 = 8
    CODE_3XX = 2
    CODE_4XX = 16
    CODE_5XX = 32


class UrlInfo(BingModel):
    date_fields = BingModel.date_fields | {"discovery_date", "last_crawled_date"}

    type: str = Field(..., alias="__type")
    anchor_count: int
    discovery_date: datetime
    document_size: int
    http_status: int
    is_page: bool
    last_crawled_date: datetime
    total_child_url_count: int
    url: str


class UrlTrafficInfo(BingModel):
    type: str = Field(..., alias="__type")
    clicks: int
    impressions: int
    is_page: bool
    url: str


class FilterProperties(BingModel):
    type: str = Field("FilterProperties:#Microsoft.Bing.Webmaster.Api", alias="__type")
    crawl_date_filter: CrawlDateFilter = CrawlDateFilter.ANY
    discovered_date_filter: DiscoveredDateFilter = DiscoveredDateFilter.ANY
    doc_flags_filters: DocFlagsFilters = DocFlagsFilters.ANY
    http_code_filters: HttpCodeFilters = HttpCodeFilters.ANY
