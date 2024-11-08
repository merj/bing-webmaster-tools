from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Bing Webmaster Tools API client.

    Settings can be initialized either through environment variables prefixed with BING_WEBMASTER_
    or passed directly to the constructor.

    Environment variables:
        BING_WEBMASTER_API_KEY: API key for authentication
        BING_WEBMASTER_BASE_URL: Base URL for the API (optional)
        BING_WEBMASTER_TIMEOUT: Request timeout in seconds (optional)
        BING_WEBMASTER_MAX_RETRIES: Maximum number of retry attempts (optional)
        BING_WEBMASTER_RATE_LIMIT_CALLS: Number of calls allowed per period (optional)
        BING_WEBMASTER_RATE_LIMIT_PERIOD: Rate limit period in seconds (optional)
        BING_WEBMASTER_DISABLE_DESTRUCTIVE_OPERATIONS: Disable destructive operations (optional)

    Examples:
        # From environment variables
        settings = Settings()

        # Manual configuration
        settings = Settings(api_key="your-key-here")

        # Mixed configuration
        settings = Settings(
            api_key="your-key-here",
            timeout=60
        )

    """

    model_config = SettingsConfigDict(env_prefix="BING_WEBMASTER_")

    api_key: SecretStr = Field(..., description="Bing Webmaster API key for authentication")
    base_url: str = Field(
        "https://ssl.bing.com/webmaster/api.svc/json",
        description="Base URL for the Bing Webmaster API",
    )
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum number of retry attempts for failed requests")
    rate_limit_calls: Optional[int] = Field(5, ge=1, description="Number of API calls allowed per rate limit period")
    rate_limit_period: Optional[int] = Field(1, ge=1, description="Rate limit period in seconds")
    disable_destructive_operations: bool = Field(False, description="Whether to disable operations that modify data")

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables.

        Returns:
            Settings: Configuration loaded from environment variables

        Raises:
            ValidationError: If required settings are missing or invalid

        """
        return cls()

    def get_api_key(self) -> str:
        """Get the API key as a string.

        Returns:
            str: The API key

        """
        return self.api_key.get_secret_value()
