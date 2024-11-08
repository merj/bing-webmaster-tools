import logging
from typing import List

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.regional_settings import CountryRegionSettings
from bing_webmaster_tools.services.api_client import ApiClient
from bing_webmaster_tools.utils import ModelLike, to_model_instance

logger = logging.getLogger(__name__)


class RegionalSettingsService:
    """Service for managing country and region-specific settings in Bing Webmaster Tools.

    This service handles:
    - Country/region settings retrieval
    - Regional configuration management
    - Geographic targeting settings
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the regional settings service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_country_region_settings(self, site_url: str) -> List[CountryRegionSettings]:
        """Retrieve country/region settings for a specific site.

        Args:
            site_url: The URL of the site to get settings for

        Returns:
            List[CountryRegionSettings]: List of country/region settings

        Raises:
            BingWebmasterError: If settings cannot be retrieved

        """
        self._logger.debug(f"Retrieving country/region settings for {site_url}")
        response = await self._client.request("GET", "GetCountryRegionSettings", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=CountryRegionSettings, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} country/region settings")
        return api_response.data

    @validate_call
    async def add_country_region_settings(self, site_url: str, settings: ModelLike[CountryRegionSettings]) -> None:
        """Add country/region settings for a specific site.

        Args:
            site_url: The URL of the site
            settings: The country/region settings to add

        Raises:
            BingWebmasterError: If settings cannot be added

        """
        settings_model = to_model_instance(settings, CountryRegionSettings)
        self._logger.debug(f"Adding country/region settings for {site_url}")
        data = {
            "siteUrl": site_url,
            "settings": settings_model.model_dump(by_alias=True),
        }

        await self._client.request("POST", "AddCountryRegionSettings", data=data)
        self._logger.info("Successfully added country/region settings")

    @validate_call
    async def remove_country_region_settings(self, site_url: str, settings: ModelLike[CountryRegionSettings]) -> None:
        """Remove country/region settings from a specific site.

        Args:
            site_url: The URL of the site
            settings: The country/region settings to remove

        Raises:
            BingWebmasterError: If settings cannot be removed

        """
        settings_model = to_model_instance(settings, CountryRegionSettings)
        self._logger.debug(f"Removing country/region settings for {site_url}")
        data = {"siteUrl": site_url, "settings": settings_model.model_dump(by_alias=True)}

        await self._client.request("POST", "RemoveCountryRegionSettings", data=data)
        self._logger.info("Successfully removed country/region settings")
