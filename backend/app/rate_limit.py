import logging
from typing import Optional

import redis
from fastapi import HTTPException, status

from .application.ports.rate_limit import RateLimitStore
from .config import settings
from .infrastructure.redis.rate_limit_store import (
    RateLimitStoreError,
    RedisRateLimitStore,
)


logger = logging.getLogger(__name__)


_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    url = settings.redis_url
    if not url:
        logger.warning("REDIS_URL not configured; IP rate limiting disabled")
        return None

    url = url.strip()
    if (url.startswith('"') and url.endswith('"')) or (
        url.startswith("'") and url.endswith("'")
    ):
        url = url[1:-1]

    try:
        _redis_client = redis.Redis.from_url(url, decode_responses=False)
        _redis_client.ping()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to initialize Redis client: %s", exc)
        _redis_client = None

    return _redis_client


def get_rate_limit_store() -> Optional[RateLimitStore]:
    """Build the rate-limit store, or ``None`` when Redis is unavailable.

    The policy treats ``None`` as a hard failure (HTTP 500); a store that fails
    mid-operation raises ``RateLimitStoreError`` and degrades gracefully.
    """

    client = get_redis_client()
    if client is None:
        return None
    return RedisRateLimitStore(client)


def enforce_ip_rate_limit(ip: Optional[str], *, scope: str = "chat") -> None:
    """Enforce a simple fixed-window rate limit per IP using Redis.

    If the store is unavailable, this function raises HTTPException 500.
    Raises HTTPException 429 when the limit is exceeded.
    """

    if not ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IP address is required for accessing the endpoint",
        )

    store = get_rate_limit_store()
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    short_window = settings.rate_limit_short_window_seconds
    long_window = settings.rate_limit_long_window_seconds
    short_max = settings.rate_limit_short_ip_requests
    long_max = settings.rate_limit_long_ip_requests

    key_short, key_long = store.ip_keys(scope, ip)

    try:
        count_short = store.incr(key_short)
        store.expire(key_short, short_window)
        count_long = store.incr(key_long)
        store.expire(key_long, long_window)

        if count_short > short_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this IP. Please try again later.",
            )

        if count_long > long_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this IP. Please try again later.",
            )
    except HTTPException:
        raise
    except RateLimitStoreError as exc:
        # On store errors, degrade gracefully and do not block the request.
        logger.error("IP rate limiting failed: %s", exc)


def enforce_session_quota(session_id: str, *, scope: str) -> None:
    store = get_rate_limit_store()
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    long_window = settings.rate_limit_long_window_seconds
    long_max = settings.session_rate_limit_long_ip_requests

    key_long = store.session_quota_key(scope, session_id)

    try:
        count_long = store.incr(key_long)
        store.expire(key_long, long_window)

        if count_long > long_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this session. Please try again later.",
            )
    except HTTPException:
        raise
    except RateLimitStoreError as exc:
        logger.error("Session rate limiting failed: %s", exc)


def enforce_session_cooldown(session_id: str, *, scope: str) -> None:
    store = get_rate_limit_store()
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    window = settings.session_cooldown_window_seconds
    threshold = settings.session_cooldown_threshold
    cooldown = settings.session_cooldown_duration_seconds

    key_count, key_block = store.cooldown_keys(scope, session_id)

    try:
        if store.get(key_block):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cooldown in effect for this session. Please wait before sending more questions.",
            )

        count = store.incr(key_count)
        store.expire(key_count, window)

        if count > threshold:
            store.setex(key_block, cooldown, b"1")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cooldown in effect for this session. Please wait before sending more questions.",
            )
    except HTTPException:
        raise
    except RateLimitStoreError as exc:
        logger.error("Session cooldown enforcement failed: %s", exc)
