"""Outbound webhook delivery for batch screening results."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_BACKOFF_SECONDS = 1.0


def deliver_webhook(
    url: str,
    payload: dict[str, Any],
    *,
    retries: int = DEFAULT_RETRIES,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
) -> bool:
    """POST `payload` as JSON to `url`, retrying transient failures with backoff.

    Returns True on a 2xx response, False if all attempts fail. Never raises —
    a webhook subscriber being down shouldn't fail the screening job itself.
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = httpx.post(url, json=payload, timeout=timeout)
            if response.is_success:
                return True
            last_error = RuntimeError(f"webhook returned status {response.status_code}")
        except httpx.HTTPError as exc:
            last_error = exc

        if attempt < retries:
            time.sleep(backoff_seconds * attempt)

    logger.warning("webhook delivery to %s failed after %d attempts: %s", url, retries, last_error)
    return False
