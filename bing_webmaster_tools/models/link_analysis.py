from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class DeepLinkWeight(IntEnum):
    DISABLED = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3


class LinkCount(BingModel):
    count: int
    url: str


class LinkCounts(BingModel):
    links: List[LinkCount]
    total_pages: int


class LinkDetail(BingModel):
    anchor_text: str
    url: str


class LinkDetails(BingModel):
    details: List[LinkDetail]
    total_pages: int


class DeepLink(BingModel):
    type: str = Field(..., alias="__type")
    position: int
    title: str
    url: str
    weight: int


class DeepLinkAlgoUrl(BingModel):
    type: str = Field(..., alias="__type")
    deep_link_count: int
    impressions: int
    url: str


class DeepLinkBlock(BingModel):
    date_fields = BingModel.date_fields | {"block_date"}

    type: str = Field(..., alias="__type")
    market: str
    search_url: str
    deep_link_url: str
    block_date: datetime


class ConnectedSite(BingModel):
    date_fields = BingModel.date_fields | {"verified_date", "submission_date"}

    type: str = Field(..., alias="__type")
    url: str
    verification_status: str
    verification_status_details: Optional[str]
    verified_date: Optional[datetime]
    submission_date: datetime
