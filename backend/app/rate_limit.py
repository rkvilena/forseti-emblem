import logging
from typing import Optional

import redis
from fastapi import HTTPException, status

from .config import settings


logger = logging.getLogger(__name__)


_redis_client: Optional["redis.Redis[bytes]"] = None


def get_redis_client() -> Optional["redis.Redis[bytes]"]:
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    url = settings.redis_url
    if not url:
        logger.warning("REDIS_URL not configured; IP rate limiting disabled")
        return None

    try:
        _redis_client = redis.Redis.from_url(url, decode_responses=False)
        # Lightweight health check
        _redis_client.ping()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to initialize Redis client: %s", exc)
        _redis_client = None

    return _redis_client


def enforce_ip_rate_limit(ip: Optional[str], *, scope: str = "chat") -> None:
    """Enforce a simple fixed-window rate limit per IP using Redis.

    If Redis or IP is unavailable, this function becomes a no-op.
    Raises HTTPException 429 when the limit is exceeded.
    """

    if not ip:
        # Could be None for some proxy setups; skip limiting in that case.
        return

    client = get_redis_client()
    if client is None:
        return

    max_requests = settings.rate_limit_ip_requests
    window_seconds = settings.rate_limit_ip_window_seconds

    key = f"rate:{scope}:{ip}"

    try:
        # Use INCR with EXPIRE for a fixed window
        with client.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = pipe.execute()

        if isinstance(count, int) and count > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this IP. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        # On Redis errors, degrade gracefully and do not block the request.
        logger.error("IP rate limiting failed: %s", exc)
