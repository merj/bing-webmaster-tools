from datetime import datetime
from enum import IntEnum
from typing import List

from pydantic import Field, field_validator

from bing_webmaster_tools.models.base import BingModel


class CrawlSettings(BingModel):
    type: str = Field("CrawlSettings:#Microsoft.Bing.Webmaster.Api", alias="__type")
    crawl_boost_available: bool
    crawl_boost_enabled: bool
    crawl_rate: List[int] = Field(..., min_length=24, max_length=24)

    @field_validator("crawl_rate")
    @classmethod
    def validate_crawl_rate(cls, v: List[int]) -> List[int]:
        """Validate the crawl rate values are between 1 and 10."""
        if not all(1 <= x <= 10 for x in v):
            raise ValueError("All crawl rate values must be between 1 and 10")
        return v


class CrawlStats(BingModel):
    type: str = Field(..., alias="__type")
    all_other_codes: int
    blocked_by_robots_txt: int
    code_2xx: int
    code_301: int
    code_302: int
    code_4xx: int
    code_5xx: int
    contains_malware: int
    crawl_errors: int
    crawled_pages: int
    date: datetime
    in_index: int
    in_links: int


class UrlWithCrawlIssues(BingModel):
    type: str = Field(..., alias="__type")
    http_code: int
    issues: "UrlWithCrawlIssues.CrawlIssues"
    url: str
    in_links: int

    class CrawlIssues(IntEnum):
        BLOCKED_BY_ROBOTS_TXT = 16
        CODE_301 = 1
        CODE_302 = 2
        CODE_4XX = 4
        CODE_5XX = 8
        CONTAINS_MALWARE = 32
        DNS_ERRORS = 128
        IMPORTANT_URL_BLOCKED_BY_ROBOTS_TXT = 64
        NONE = 0
        TIME_OUT_ERRORS = 256
