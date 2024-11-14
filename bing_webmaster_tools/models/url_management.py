from datetime import datetime
from typing import Annotated

from pydantic import Field, StringConstraints

from bing_webmaster_tools.models.base import BingModel


class QueryParameter(BingModel):
    type: str = Field(..., alias="__type")
    date: datetime
    is_enabled: bool
    parameter: str
    source: int


QueryParamStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        pattern=r"^[A-Za-z0-9\-_.~:]+$",  # Only unreserved letter and colon
    ),
]
