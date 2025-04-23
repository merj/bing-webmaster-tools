from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class BlockReason(IntEnum):
    ADULT_CONTENT = 1
    COPYRIGHT = 2
    ILLEGAL_CONTENT = 3
    OTHER = 4


class BlockedUrl(BingModel):
    type: str = Field("BlockedUrl:#Microsoft.Bing.Webmaster.Api", alias="__type")
    date: datetime
    entity_type: "BlockedUrl.BlockedUrlEntityType"
    request_type: "BlockedUrl.BlockedUrlRequestType"
    url: str

    class BlockedUrlEntityType(IntEnum):
        PAGE = 0
        DIRECTORY = 1

    class BlockedUrlRequestType(IntEnum):
        CACHE_ONLY = 0
        FULL_REMOVAL = 1


class PagePreview(BingModel):
    date_fields = BingModel.date_fields | {"block_date"}

    type: str = Field(..., alias="__type")
    url: str
    block_reason: BlockReason
    block_date: Optional[datetime] = None
