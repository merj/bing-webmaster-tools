import asyncio
import functools
import logging
import re
import warnings
from datetime import datetime, timedelta, timezone
from time import time
from typing import Any, Awaitable, Callable, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import ParamSpec, TypeAlias


class RateLimiter:
    """Rate limiter implementation."""

    def __init__(self, rate: int, period: float = 1.0):
        self.rate = rate
        self.period = period
        self.tokens: float = float(rate)  # Make tokens float explicitly
        self.updated_at = time()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token from the rate limiter."""
        async with self.lock:
            now = time()
            elapsed = now - self.updated_at
            self.tokens = min(float(self.rate), self.tokens + elapsed * (self.rate / self.period))

            self.updated_at = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) * (self.period / self.rate)
                await asyncio.sleep(sleep_time)
                self.tokens = 1
                self.updated_at = time()

            self.tokens -= 1


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def parse_timestamp_from_api(value: Any) -> datetime:
    """Parse a .NET JSON date string, such as ``/Date(1728975600000-0700)/``, into an aware datetime.

    The number is milliseconds since the Unix epoch, in UTC. The optional offset is the time zone the
    value was written in, and the result keeps it, so ``.date()`` gives the day Bing means. Without an
    offset the result is in UTC. Bing currently dates daily figures at midnight UTC with no offset;
    older responses used midnight Pacific time (``-0700`` or ``-0800``). The result never depends on
    the time zone of the machine running the code.
    """
    if not isinstance(value, str):
        raise ValueError(f"Expected {value} to be string")
    match = re.search(r"/Date\((-?\d+)(?:([+-])(\d{2})(\d{2}))?\)/", value)
    if not match:
        raise ValueError(f"Unable to parse date: {value}")
    # Epoch arithmetic rather than fromtimestamp(), which fails on Windows for dates before 1970,
    # and Bing sends .NET's DateTime.MinValue (/Date(-62135596800000)/) for "never".
    instant = _EPOCH + timedelta(milliseconds=int(match.group(1)))
    if match.group(2) is None:
        return instant
    sign = 1 if match.group(2) == "+" else -1
    offset = timedelta(hours=int(match.group(3)), minutes=int(match.group(4)))
    try:
        return instant.astimezone(timezone(sign * offset))
    except OverflowError:
        # DateTime.MinValue with a negative offset falls before year 1; keep it in UTC
        return instant


def format_date_for_api(dt: datetime) -> str:
    """Format datetime in .NET JSON date format."""
    return f"/Date({int(dt.timestamp() * 1000)}+0000)/"


TModel = TypeVar("TModel", bound=BaseModel)

ModelLike: TypeAlias = Union[dict, TModel]


def to_model_instance(input_params: Any, model_cls: Type[TModel]) -> TModel:
    """Convert input parameters to an instance of the specified Pydantic model.

    Args:
        input_params (Any): The input parameters to convert.
        model_cls (Type[TModel]): The Pydantic model class to convert to.

    Returns:
        TModel: An instance of the specified model.

    Raises:
        ValueError: If the 'params' property is not an instance of the specified Model class.

    """
    if not input_params:
        return model_cls()

    params = input_params
    if isinstance(params, model_cls):
        return params

    if isinstance(params, dict):
        return model_cls(**params)

    raise ValueError(f"The 'params' property should be an instance of {model_cls.__name__} or a dictionary.")


P = ParamSpec("P")
T = TypeVar("T")


logger = logging.getLogger(__name__)


def deprecated(
    message: Optional[str] = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Mark async methods as deprecated.

    Args:
        message: Optional custom deprecation message

    Example:
        @deprecated("Use new_async_method() instead")
        async def old_async_method(): ...

    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            warning_message = message or f"{func.__name__} is deprecated and will be removed in a future version."
            warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
            logger.warning(f"Called deprecated method {func.__name__}: {warning_message}")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
