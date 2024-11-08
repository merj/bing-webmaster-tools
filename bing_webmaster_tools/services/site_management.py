import logging
from typing import List, cast

from pydantic import validate_call

from bing_webmaster_tools.models.base import ApiResponse
from bing_webmaster_tools.models.site_management import Site, SiteMoveSettings, SiteRole
from bing_webmaster_tools.services.api_client import ApiClient
from bing_webmaster_tools.utils import ModelLike, to_model_instance


class SiteManagementService:
    """Service for managing sites in Bing Webmaster Tools.

    This service handles operations related to site management including:
    - Adding and removing sites
    - Site verification
    - Managing site roles and access
    - Site move operations
    """

    def __init__(self, client: ApiClient) -> None:
        """Initialize the site management service.

        Args:
            client: API client implementing the ApiClient protocol

        """
        self._client = client
        self._logger = logging.getLogger(__name__)

    @validate_call
    async def get_sites(self) -> List[Site]:
        """Retrieve all sites in the user's Bing Webmaster Tools account.

        Returns:
            List[Site]: List of sites associated with the account

        Raises:
            BingWebmasterError: If the API request fails

        """
        self._logger.debug("Retrieving user sites")
        response = await self._client.request("GET", "GetUserSites")

        api_response = ApiResponse.from_api_response(response=response, model=Site, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} sites")
        return api_response.data

    @validate_call
    async def add_site(self, site_url: str) -> None:
        """Add a new site to Bing Webmaster Tools.

        Args:
            site_url: The URL of the site to add

        Raises:
            BingWebmasterError: If the site cannot be added

        """
        self._logger.debug(f"Adding site: {site_url}")
        await self._client.request("POST", "AddSite", data={"siteUrl": site_url})
        self._logger.info(f"Successfully added site: {site_url}")

    @validate_call
    async def verify_site(self, site_url: str) -> bool:
        """Attempt to verify ownership of a site.

        Args:
            site_url: The URL of the site to verify

        Returns:
            bool: True if verification was successful

        Raises:
            BingWebmasterError: If verification fails

        """
        self._logger.debug(f"Verifying site: {site_url}")
        response = await self._client.request("POST", "VerifySite", data={"siteUrl": site_url})

        is_verified = response.get("d", False)
        self._logger.info(f"Site verification {'successful' if is_verified else 'failed'}: {site_url}")

        return cast(bool, is_verified)

    @validate_call
    async def get_site_roles(self, site_url: str, include_all_subdomains: bool = False) -> List[SiteRole]:
        """Get all roles assigned for a specific site.

        Args:
            site_url: The URL of the site
            include_all_subdomains: Whether to include roles for all subdomains

        Returns:
            List[SiteRole]: List of role assignments for the site

        Raises:
            BingWebmasterError: If the roles cannot be retrieved

        """
        self._logger.debug(f"Retrieving roles for site: {site_url}")
        params = {"siteUrl": site_url, "includeAllSubdomains": include_all_subdomains}
        response = await self._client.request("GET", "GetSiteRoles", params=params)

        api_response = ApiResponse.from_api_response(response=response, model=SiteRole, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} roles for site: {site_url}")
        return api_response.data

    @validate_call
    async def add_site_roles(
        self,
        site_url: str,
        delegated_url: str,
        user_email: str,
        authentication_code: str,
        is_administrator: bool,
        is_read_only: bool,
    ) -> None:
        """Delegate site access to a user.

        Args:
            site_url: The URL of your site
            delegated_url: The URL being delegated
            user_email: The email of the user to delegate access to
            authentication_code: The authentication code
            is_administrator: Whether the user should have administrator privileges
            is_read_only: Whether the user should have read-only access

        Raises:
            BingWebmasterError: If the role assignment fails

        """
        self._logger.debug(f"Adding site roles for {user_email} on {site_url}")
        data = {
            "siteUrl": site_url,
            "delegatedUrl": delegated_url,
            "userEmail": user_email,
            "authenticationCode": authentication_code,
            "isAdministrator": is_administrator,
            "isReadOnly": is_read_only,
        }
        await self._client.request("POST", "AddSiteRoles", data=data)
        self._logger.info(f"Successfully added site roles for {user_email} on {site_url}")

    @validate_call
    async def remove_site(self, site_url: str) -> None:
        """Remove a site from Bing Webmaster Tools.

        Args:
            site_url: The URL of the site to remove

        Raises:
            BingWebmasterError: If the site cannot be removed

        """
        self._logger.debug(f"Removing site: {site_url}")
        await self._client.request("POST", "RemoveSite", data={"siteUrl": site_url})
        self._logger.info(f"Successfully removed site: {site_url}")

    @validate_call
    async def remove_site_role(self, site_url: str, site_role: ModelLike[SiteRole]) -> None:
        """Remove a user's site access.

        Args:
            site_url: The URL of the site
            site_role: The site role to remove

        Raises:
            BingWebmasterError: If the role cannot be removed

        """
        site_role_model = to_model_instance(site_role, SiteRole)
        self._logger.debug(f"Removing site role for {site_role_model.email} on {site_url}")
        data = {"siteUrl": site_url, "siteRole": site_role_model.model_dump(by_alias=True)}
        await self._client.request("POST", "RemoveSiteRole", data=data)
        self._logger.info(f"Successfully removed site role for {site_role_model.email}")

    @validate_call
    async def submit_site_move(self, site_url: str, settings: ModelLike[SiteMoveSettings]) -> None:
        """Submit a site move request.

        Args:
            site_url: The URL of the site
            settings: The site move settings containing move configuration

        Raises:
            BingWebmasterError: If the site move submission fails

        """
        settings_model = to_model_instance(settings, SiteMoveSettings)
        self._logger.debug(f"Submitting site move for {site_url}")
        data = {"siteUrl": site_url, "settings": settings_model.model_dump(by_alias=True)}
        await self._client.request("POST", "SubmitSiteMove", data=data)
        self._logger.info(f"Successfully submitted site move for {site_url}")

    @validate_call
    async def get_site_moves(self, site_url: str) -> List[SiteMoveSettings]:
        """Get site move information for a specific site.

        Args:
            site_url: The URL of the site

        Returns:
            List[SiteMoveSettings]: List of site move settings

        Raises:
            BingWebmasterError: If the site move information cannot be retrieved

        """
        self._logger.debug(f"Retrieving site moves for {site_url}")
        response = await self._client.request("GET", "GetSiteMoves", params={"siteUrl": site_url})

        api_response = ApiResponse.from_api_response(response=response, model=SiteMoveSettings, is_list=True)

        self._logger.info(f"Retrieved {len(api_response.data)} site moves for {site_url}")
        return api_response.data
