"""Reusable retry policy for flaky network / UI operations."""
from __future__ import annotations

from config.settings import settings
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .logger import get_logger

log = get_logger(__name__)

# Transient failures worth retrying: timeouts and navigation/protocol errors.
RETRYABLE = (PlaywrightTimeout, PlaywrightError)


def _log_retry(state) -> None:
    exc = state.outcome.exception() if state.outcome else None
    log.warning(
        f"Attempt {state.attempt_number} failed ({type(exc).__name__}); retrying..."
    )


def resilient(func):
    """Decorator: retry a callable with exponential backoff on transient errors."""
    return retry(
        retry=retry_if_exception_type(RETRYABLE),
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.retry_backoff_s, min=1, max=30),
        before_sleep=_log_retry,
        reraise=True,
    )(func)
