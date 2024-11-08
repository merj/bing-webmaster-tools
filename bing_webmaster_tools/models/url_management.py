from datetime import datetime

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class QueryParameter(BingModel):
    type: str = Field(..., alias="__type")
    date: datetime
    is_enabled: bool
    parameter: str
    source: int
