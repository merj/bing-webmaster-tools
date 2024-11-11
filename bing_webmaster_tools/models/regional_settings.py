from datetime import datetime
from enum import IntEnum

from pydantic import Field, field_validator

from bing_webmaster_tools.models.base import BingModel


class CountryRegionSettingsType(IntEnum):
    PAGE = 0
    DIRECTORY = 1
    DOMAIN = 2
    SUBDOMAIN = 3


class CountryRegionSettings(BingModel):
    type: str = Field("CountryRegionSettings:#Microsoft.Bing.Webmaster.Api", alias="__type")
    date: datetime
    two_letter_iso_country_code: str = Field(..., min_length=2, max_length=2)
    settings_type: CountryRegionSettingsType = Field(..., alias="Type")
    url: str

    @field_validator("two_letter_iso_country_code")
    @classmethod
    def validate_lowercase(cls, v: str) -> str:
        """Validate that the ISO country code is lowercase."""
        if not v.islower():
            raise ValueError("ISO country code must be lowercase")
        return v
