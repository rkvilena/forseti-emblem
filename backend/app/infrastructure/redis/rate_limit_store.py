"""Redis-backed implementation of the ``RateLimitStore`` port."""

from __future__ import annotations

from typing import Any


class RateLimitStoreError(Exception):
    """Raised when the rate-limit store cannot service an operation.

    Adapters translate the underlying client/client errors into this single type
    so the policy can decide how to react without importing Redis exceptions.
    """


class RedisRateLimitStore:
    """Wrap a Redis client with the raw operations the policy needs.

    The store owns key naming and translates any client failure into a single
    :class:`RateLimitStoreError`. It holds no thresholds or allow/block rules.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def incr(self, key: str) -> int:
        try:
            return int(self._client.incr(key))
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitStoreError(str(exc)) from exc

    def expire(self, key: str, ttl: int) -> None:
        try:
            self._client.expire(key, ttl)
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitStoreError(str(exc)) from exc

    def get(self, key: str) -> bytes | None:
        try:
            return self._client.get(key)
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitStoreError(str(exc)) from exc

    def setex(self, key: str, ttl: int, value: bytes) -> None:
        try:
            self._client.setex(key, ttl, value)
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitStoreError(str(exc)) from exc

    def ip_keys(self, scope: str, ip: str) -> tuple[str, str]:
        return f"rate:{scope}:s:{ip}", f"rate:{scope}:l:{ip}"

    def session_quota_key(self, scope: str, session_id: str) -> str:
        return f"session:{scope}:{session_id}"

    def cooldown_keys(self, scope: str, session_id: str) -> tuple[str, str]:
        return (
            f"cooldown:{scope}:c:{session_id}",
            f"cooldown:{scope}:b:{session_id}",
        )
