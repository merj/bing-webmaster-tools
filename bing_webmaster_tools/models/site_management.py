from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import Field

from bing_webmaster_tools.models.base import BingModel


class SiteMoveScope(IntEnum):
    DOMAIN = 0
    HOST = 1
    DIRECTORY = 2


class SiteMoveType(IntEnum):
    LOCAL = 0
    GLOBAL = 1


class Site(BingModel):
    type: str = Field(..., alias="__type")
    authentication_code: str
    dns_verification_code: str
    is_verified: bool
    url: str


class SiteRole(BingModel):
    type: str = Field(..., alias="__type")
    date: datetime
    delegated_code: Optional[str] = None
    delegated_code_owner_email: Optional[str] = None
    delegator_email: Optional[str] = None
    email: str
    expired: bool
    role: "SiteRole.UserRole"
    site: str
    verification_site: str

    class UserRole(IntEnum):
        ADMINISTRATOR = 0
        READ_ONLY = 1
        READ_WRITE = 2


class SiteMoveSettings(BingModel):
    type: str = Field("SiteMoveSettings:#Microsoft.Bing.Webmaster.Api", alias="__type")
    date: datetime
    move_scope: SiteMoveScope
    move_type: SiteMoveType
    source_url: str = Field(..., pattern=r"^https?://")  # URL validation
    target_url: str = Field(..., pattern=r"^https?://")  # URL validation
