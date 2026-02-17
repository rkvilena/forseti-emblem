import logging
from typing import Optional

import redis
from fastapi import HTTPException, Request, Response, status

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


def enforce_ip_rate_limit(ip: Optional[str], *, scope: str = "chat") -> None:
    """Enforce a simple fixed-window rate limit per IP using Redis.

    If Redis or IP is unavailable, this function becomes a no-op.
    Raises HTTPException 429 when the limit is exceeded.
    """

    if not ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IP address is required for accessing the endpoint",
        )

    client = get_redis_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    short_window = settings.rate_limit_short_window_seconds
    long_window = settings.rate_limit_long_window_seconds
    short_max = settings.rate_limit_short_ip_requests
    long_max = settings.rate_limit_long_ip_requests

    key_short = f"rate:{scope}:s:{ip}"
    key_long = f"rate:{scope}:l:{ip}"

    try:
        with client.pipeline() as pipe:
            pipe.incr(key_short)
            pipe.expire(key_short, short_window)
            pipe.incr(key_long)
            pipe.expire(key_long, long_window)
            count_short, _, count_long, _ = pipe.execute()

        if isinstance(count_short, int) and count_short > short_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this IP. Please try again later.",
            )

        if isinstance(count_long, int) and count_long > long_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this IP. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        # On Redis errors, degrade gracefully and do not block the request.
        logger.error("IP rate limiting failed: %s", exc)


def enforce_session_quota(request: Request, response: Response, *, scope: str) -> None:
    client = get_redis_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        import secrets

        session_id = secrets.token_urlsafe(18)
        max_age = max(1, int(settings.session_cookie_ttl_seconds))
        secure = bool(settings.is_production)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            max_age=max_age,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )

    long_window = settings.rate_limit_long_window_seconds
    long_max = settings.session_rate_limit_long_ip_requests

    key_long = f"session:{scope}:{session_id}"

    try:
        with client.pipeline() as pipe:
            pipe.incr(key_long)
            pipe.expire(key_long, long_window)
            count_long, _ = pipe.execute()

        if isinstance(count_long, int) and count_long > long_max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for this session. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Session rate limiting failed: %s", exc)


def enforce_session_cooldown(
    request: Request, response: Response, *, scope: str
) -> None:
    client = get_redis_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rate limiting backend is unavailable",
        )

    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        import secrets

        session_id = secrets.token_urlsafe(18)
        max_age = max(1, int(settings.session_cookie_ttl_seconds))
        secure = bool(settings.is_production)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            max_age=max_age,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )

    window = settings.session_cooldown_window_seconds
    threshold = settings.session_cooldown_threshold
    cooldown = settings.session_cooldown_duration_seconds

    key_count = f"cooldown:{scope}:c:{session_id}"
    key_block = f"cooldown:{scope}:b:{session_id}"

    try:
        if client.get(key_block):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cooldown in effect for this session. Please wait before sending more questions.",
            )

        with client.pipeline() as pipe:
            pipe.incr(key_count)
            pipe.expire(key_count, window)
            count, _ = pipe.execute()

        if isinstance(count, int) and count > threshold:
            client.setex(key_block, cooldown, b"1")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cooldown in effect for this session. Please wait before sending more questions.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Session cooldown enforcement failed: %s", exc)
