from datetime import datetime

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class KeywordStats(BingModel):
    date: datetime
    broad_impressions: int
    impressions: int
    query: str


class Keyword(BingModel):
    type: str = Field(..., alias="__type")
    broad_impressions: int
    impressions: int
    query: str
