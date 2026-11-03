"""Shared fixtures for chat endpoint characterization tests.

These fixtures reproduce the in-memory fake Redis pipeline used by
``test_rate_limit.py`` so no live Postgres, Redis, or OpenAI is required.
They are intentionally identical in behavior to the module-local fakes in the
existing tests; module-local fixtures take precedence when both exist.
"""

import pytest
from fastapi.testclient import TestClient

from app import rate_limit
from app.config import settings
from app.main import app


class FakePipeline:
    """In-memory stand-in for a Redis pipeline used in characterization tests."""

    def __init__(self, store: dict[str, int]):
        self.store = store
        self.ops: list[tuple[str, str | int]] = []

    def __enter__(self) -> "FakePipeline":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def incr(self, key: str) -> None:
        self.ops.append(("incr", key))

    def expire(self, key: str, ttl: int) -> None:
        self.ops.append(("expire", ttl))

    def execute(self) -> list[int | bool]:
        results: list[int | bool] = []
        for op, arg in self.ops:
            if op == "incr":
                key = arg  # type: ignore[assignment]
                current = self.store.get(key, 0) + 1
                self.store[key] = current
                results.append(current)
            elif op == "expire":
                results.append(True)
        return results


class FakeRedisClient:
    """Minimal fake Redis client backed by a dict store."""

    def __init__(self, store: dict[str, int]):
        self.store = store

    def get(self, key: str) -> bytes | None:
        value = self.store.get(key)
        if value is None:
            return None
        return b"1"

    def setex(self, key: str, ttl: int, value: bytes) -> None:
        self.store[key] = 1

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self.store)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Patch ``get_redis_client`` with a fake client and return its backing store."""
    store: dict[str, int] = {}
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: FakeRedisClient(store))
    return store


@pytest.fixture
def permissive_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Relax cost controls so tests reach the behavior under characterization."""
    monkeypatch.setattr(settings, "turnstile_enabled", False)
    monkeypatch.setattr(settings, "rate_limit_short_ip_requests", 1000)
    monkeypatch.setattr(settings, "rate_limit_long_ip_requests", 1000)
    monkeypatch.setattr(settings, "session_rate_limit_long_ip_requests", 1000)
    monkeypatch.setattr(settings, "session_cooldown_threshold", 1000)


@pytest.fixture
def client(
    fake_redis: dict[str, int], permissive_settings: None
) -> TestClient:
    """A TestClient wired to fake Redis with permissive limits."""
    return TestClient(app)
