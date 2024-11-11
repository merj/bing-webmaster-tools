from datetime import datetime

import pytest

from bing_webmaster_tools import BingWebmasterError
from bing_webmaster_tools.client import BingWebmasterClient
from bing_webmaster_tools.models.regional_settings import CountryRegionSettings, CountryRegionSettingsType


@pytest.mark.asyncio
class TestRegionalSettingsService:
    """Tests for the regional settings service."""

    # @pytest.mark.vcr
    async def test_get_country_region_settings(self, client: BingWebmasterClient, test_site: str):
        """Test retrieving country/region settings."""
        settings = await client.regional.get_country_region_settings(test_site)

        assert isinstance(settings, list)
        if settings:
            assert isinstance(settings[0], CountryRegionSettings)

    # @pytest.mark.vcr
    @pytest.mark.parametrize(
        "settings",
        [
            {
                "date": datetime(2024, 7, 1),
                "two_letter_iso_country_code": "us",
                "settings_type": CountryRegionSettingsType.PAGE,
                "url": "https://example.com/us-page",
            },
            {
                "date": datetime(2024, 7, 1),
                "two_letter_iso_country_code": "gb",
                "settings_type": CountryRegionSettingsType.DIRECTORY,
                "url": "https://example.com/uk-section/",
            },
            {
                "date": datetime(2024, 7, 1),
                "two_letter_iso_country_code": "de",
                "settings_type": CountryRegionSettingsType.SUBDOMAIN,
                "url": "https://de.example.com",
            },
        ],
    )
    async def test_country_region_settings_lifecycle(
        self,
        client: BingWebmasterClient,
        test_site: str,
        settings: dict,
    ):
        """Test the complete lifecycle of country/region settings."""
        # Create settings instance
        settings = CountryRegionSettings(**settings)

        try:
            # Add settings
            await client.regional.add_country_region_settings(test_site, settings)

            # Verify settings were added
            current_settings = await client.regional.get_country_region_settings(test_site)
            matching_settings = next(
                (
                    s
                    for s in current_settings
                    if s.url == settings.url and s.two_letter_iso_country_code == settings.two_letter_iso_country_code
                ),
                None,
            )
            assert matching_settings is not None
            assert matching_settings[0].settings_type == settings.settings_type
            assert matching_settings[0].date == settings.date

        finally:
            # Cleanup
            await client.regional.remove_country_region_settings(test_site, settings)

            # Verify settings were removed
            current_settings = await client.regional.get_country_region_settings(test_site)
            matching_settings = next(
                (
                    s
                    for s in current_settings
                    if s.url == settings.url and s.two_letter_iso_country_code == settings.two_letter_iso_country_code
                ),
                None,
            )
            assert matching_settings is None

    #     @pytest.mark.vcr
    async def test_remove_nonexistent_settings(self, client: BingWebmasterClient, test_site: str):
        """Test removing settings that don't exist."""
        settings = CountryRegionSettings(
            date=datetime(2024, 7, 1),
            two_letter_iso_country_code="us",
            settings_type=CountryRegionSettingsType.PAGE,
            url="https://example.com/nonexistent",
        )

        with pytest.raises(BingWebmasterError):
            await client.regional.remove_country_region_settings(test_site, settings)
