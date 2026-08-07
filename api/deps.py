"""Shared FastAPI dependencies: API-key auth and per-key rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import Depends, Header, HTTPException, status

from api.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if not x_api_key or x_api_key not in settings.api_key_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )
    return x_api_key


class _FixedWindowRateLimiter:
    """Per-key fixed-window counter. Single-process only — see Settings.rate_limit_per_minute."""

    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
        self._lock = Lock()
        self._windows: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))  # key -> (window_start, count)

    def check(self, key: str) -> None:
        window = int(time.time() // 60)
        with self._lock:
            window_start, count = self._windows[key]
            if window_start != window:
                window_start, count = window, 0
            count += 1
            self._windows[key] = (window_start, count)
        if count > self._limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": "60"},
            )


_rate_limiter = _FixedWindowRateLimiter(settings.rate_limit_per_minute)


def enforce_rate_limit(api_key: str = Depends(require_api_key)) -> None:
    """Depends on `require_api_key` so auth runs first and buckets share the validated key."""
    _rate_limiter.check(api_key)
