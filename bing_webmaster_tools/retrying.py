import logging
from typing import Callable, TypeVar

import tenacity as tc
from pydantic import BaseModel
from typing_extensions import ParamSpec

logger = logging.getLogger(__name__)


class RetryConfig(BaseModel):
    """Configuration for the retry with exponential backoff."""

    num_retries: int
    min_wait: int
    max_wait: int
    multiplier: float
    exp_base: int
    should_retry: Callable[[BaseException], bool] = lambda _: True


P = ParamSpec("P")
T = TypeVar("T")


def get_retry_decorator(config: RetryConfig) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Get a retry decorator with the specified configuration."""
    return tc.retry(
        retry=tc.retry_if_exception(config.should_retry),
        stop=tc.stop_after_attempt(config.num_retries),
        wait=tc.wait_exponential(
            min=config.min_wait,
            max=config.max_wait,
            multiplier=config.multiplier,
            exp_base=config.exp_base,
        ),
        after=lambda retry_state: _log_retry_error_attempt(retry_state, num_retries=config.num_retries),
        reraise=True,
    )


def _log_retry_error_attempt(retry_state: tc.RetryCallState, num_retries: int) -> None:
    if not retry_state.outcome:
        return

    exc = retry_state.outcome.exception()
    logger.warning(f"Error: {exc.__class__.__name__}: {exc}")
    if retry_state.attempt_number < num_retries:
        current_attempt, num_attempts = retry_state.attempt_number + 1, num_retries
        logger.warning(
            f"Retrying (attempt {current_attempt}/{num_attempts}), " f"waiting for {retry_state.upcoming_sleep}s"
        )
