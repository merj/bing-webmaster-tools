import pytest

from bing_webmaster_tools.client import BingWebmasterClient


@pytest.mark.asyncio
class TestUrlManagementService:
    """Tests for the URL management service."""

    @pytest.mark.parametrize(
        "query_parameter",
        [
            "sort",
            "order",
            "param:with:colons",
            "param-with-dashes",
            "param_with_underscores",
        ],
    )
    @pytest.mark.vcr
    async def test_query_parameter_lifecycle(
        self,
        client: BingWebmasterClient,
        test_site: str,
        query_parameter: str,
    ):
        """Test the complete lifecycle of a query parameter."""

        try:
            # Verify initially empty
            parameters = await client.urls.get_query_parameters(test_site)
            assert len(parameters) == 0

            # Add parameter
            await client.urls.add_query_parameter(test_site, query_parameter)

            # Verify parameter was added
            parameters = await client.urls.get_query_parameters(test_site)
            assert len(parameters) == 1
            added_param = parameters[0]
            assert added_param.parameter == query_parameter
            assert added_param.is_enabled  # Parameters should be enabled by default

            # Disable parameter
            await client.urls.enable_disable_query_parameter(test_site, query_parameter, False)

            # Verify parameter was disabled
            parameters = await client.urls.get_query_parameters(test_site)
            assert len(parameters) == 1
            disabled_param = parameters[0]
            assert disabled_param.parameter == query_parameter
            assert not disabled_param.is_enabled

            # Enable parameter
            await client.urls.enable_disable_query_parameter(test_site, query_parameter, True)

            # Verify parameter was enabled
            parameters = await client.urls.get_query_parameters(test_site)
            assert len(parameters) == 1
            enabled_param = parameters[0]
            assert enabled_param.parameter == query_parameter
            assert enabled_param.is_enabled

        finally:
            # Cleanup - remove parameter
            await client.urls.remove_query_parameter(test_site, query_parameter)

            # Verify back to empty
            parameters = await client.urls.get_query_parameters(test_site)
            assert len(parameters) == 0

    @pytest.mark.parametrize(
        "invalid_parameter",
        [
            "invalid@param",  # Contains invalid character
            "",  # Empty string
            " ",  # Whitespace
        ],
    )
    @pytest.mark.vcr
    async def test_add_invalid_parameter(
        self,
        client: BingWebmasterClient,
        test_site: str,
        invalid_parameter: str,
    ):
        """Test adding invalid query parameters."""
        with pytest.raises(ValueError):  # Service validates parameter format
            await client.urls.add_query_parameter(test_site, invalid_parameter)
