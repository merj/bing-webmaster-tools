from datetime import datetime

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class ContentSubmissionQuota(BingModel):
    type: str = Field(..., alias="__type")
    daily_quota: int
    monthly_quota: int


class UrlSubmissionQuota(BingModel):
    type: str = Field(..., alias="__type")
    daily_quota: int
    monthly_quota: int


class Feed(BingModel):
    date_fields = BingModel.date_fields | {"last_crawled", "submitted"}

    type: str = Field(..., alias="__type")
    compressed: bool
    file_size: int
    last_crawled: datetime
    status: str
    submitted: datetime
    # Feed has duplicate type field
    feed_type: str = Field(..., alias="Type")
    url: str
    url_count: int


class FetchedUrlDetails(BingModel):
    type: str = Field(..., alias="__type")
    date: datetime
    document: str
    headers: str
    status: str
    url: str


class FetchedUrl(BingModel):
    type: str = Field(..., alias="__type")
    date: datetime
    expired: bool
    fetched: bool
    url: str
