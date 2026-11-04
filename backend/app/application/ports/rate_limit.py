"""Port for the external key/value store that backs rate limiting."""

from __future__ import annotations

from typing import Protocol


class RateLimitStore(Protocol):
    """Raw counter operations used by the rate-limit policy.

    The policy owns the thresholds and the allow/block decisions; this port only
    performs the raw store operations and owns how the keys are named, so the
    policy never embeds Redis key strings directly.
    """

    def incr(self, key: str) -> int:
        """Increment ``key`` by one and return the new value."""

        ...

    def expire(self, key: str, ttl: int) -> None:
        """Set a time-to-live in seconds on ``key``."""

        ...

    def get(self, key: str) -> bytes | None:
        """Return the raw value stored at ``key`` (``None`` when absent)."""

        ...

    def setex(self, key: str, ttl: int, value: bytes) -> None:
        """Store ``value`` at ``key`` with a time-to-live in seconds."""

        ...

    def ip_keys(self, scope: str, ip: str) -> tuple[str, str]:
        """Return the ``(short, long)`` window keys for an IP in ``scope``."""

        ...

    def session_quota_key(self, scope: str, session_id: str) -> str:
        """Return the quota key for a session in ``scope``."""

        ...

    def cooldown_keys(self, scope: str, session_id: str) -> tuple[str, str]:
        """Return the ``(count, block)`` cooldown keys for a session in ``scope``."""

        ...
