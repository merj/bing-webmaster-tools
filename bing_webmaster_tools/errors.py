from enum import IntEnum
from typing import Optional


class ApiErrorCode(IntEnum):
    """Known API error codes from Bing Webmaster API"""

    ALREADY_EXISTS = 12
    DEPRECATED = 16
    INTERNAL_ERROR = 1
    INVALID_API_KEY = 3
    INVALID_PARAMETER = 8
    INVALID_URL = 7
    NONE = 0
    NOT_ALLOWED = 13
    NOT_AUTHORIZED = 14
    NOT_FOUND = 11
    THROTTLE_HOST = 5
    THROTTLE_USER = 4
    TOO_MANY_SITES = 9
    UNEXPECTED_STATE = 15
    UNKNOWN_ERROR = 2
    USER_BLOCKED = 6
    USER_NOT_FOUND = 10


class BingWebmasterError(Exception):
    """Raised when the API returns an error"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[ApiErrorCode] = None,
        raw_content: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.raw_content = raw_content


class AuthenticationError(BingWebmasterError):
    """Raised when authentication fails"""


class RateLimitError(BingWebmasterError):
    """Raised when rate limit is exceeded"""


class ValidationError(BingWebmasterError):
    """Raised when input validation fails"""
