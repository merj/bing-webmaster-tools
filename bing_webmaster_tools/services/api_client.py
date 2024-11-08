from typing import Any, Dict, Optional, Protocol


class ApiClient(Protocol):
    """Protocol defining the required API client interface for services."""

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the API."""
        ...
