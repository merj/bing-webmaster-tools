from datetime import datetime

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class QueryStats(BingModel):
    type: str = Field(..., alias="__type")
    avg_click_position: int
    avg_impression_position: int
    clicks: int
    date: datetime
    impressions: int
    query: str


class DetailedQueryStats(BingModel):
    type: str = Field(..., alias="__type")
    clicks: int
    date: datetime
    impressions: int
    position: int


class RankAndTrafficStats(BingModel):
    type: str = Field(..., alias="__type")
    clicks: int
    date: datetime
    impressions: int
