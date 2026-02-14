import pytest
from fastapi import HTTPException

from app import rate_limit
from app.config import settings


class FakePipeline:
    """In-memory stand-in for a Redis pipeline used in rate limit tests."""

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
        self.ops.append(("expire", key))

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
    """Minimal fake Redis client exposing a pipeline backed by a dict store."""

    def __init__(self, store: dict[str, int]):
        self.store = store

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self.store)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Provide a fake Redis client and shared store for each test."""
    store: dict[str, int] = {}
    client = FakeRedisClient(store)
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: client)
    return store


@pytest.fixture
def restore_rate_limits() -> None:
    """Save and restore global rate limit settings around a test."""
    short_max = settings.rate_limit_short_ip_requests
    long_max = settings.rate_limit_long_ip_requests

    def restore() -> None:
        settings.rate_limit_short_ip_requests = short_max
        settings.rate_limit_long_ip_requests = long_max

    try:
        yield
    finally:
        restore()


def test_within_limits_does_not_raise(
    fake_redis: dict[str, int], restore_rate_limits: None
) -> None:
    """Calls under both short and long limits must not raise HTTPException."""
    settings.rate_limit_short_ip_requests = 3
    settings.rate_limit_long_ip_requests = 10

    ip = "1.2.3.4"
    for _ in range(3):
        rate_limit.enforce_ip_rate_limit(ip, scope="chat")


def test_exceed_short_window_raises(
    fake_redis: dict[str, int], restore_rate_limits: None
) -> None:
    """Third call beyond short-window threshold must raise HTTP 429."""
    settings.rate_limit_short_ip_requests = 2
    settings.rate_limit_long_ip_requests = 25

    ip = "5.6.7.8"
    rate_limit.enforce_ip_rate_limit(ip, scope="chat")
    rate_limit.enforce_ip_rate_limit(ip, scope="chat")

    with pytest.raises(HTTPException) as exc_info:
        rate_limit.enforce_ip_rate_limit(ip, scope="chat")

    assert exc_info.value.status_code == 429


def test_exceed_long_window_raises(
    fake_redis: dict[str, int], restore_rate_limits: None
) -> None:
    """Third call beyond long-window threshold must raise HTTP 429."""
    settings.rate_limit_short_ip_requests = 100
    settings.rate_limit_long_ip_requests = 2

    ip = "9.9.9.9"
    rate_limit.enforce_ip_rate_limit(ip, scope="chat_rag")
    rate_limit.enforce_ip_rate_limit(ip, scope="chat_rag")

    with pytest.raises(HTTPException) as exc_info:
        rate_limit.enforce_ip_rate_limit(ip, scope="chat_rag")

    assert exc_info.value.status_code == 429


def test_no_ip_skips_limiting(
    fake_redis: dict[str, int], restore_rate_limits: None
) -> None:
    """Passing ip=None should be a no-op and not raise."""
    with pytest.raises(HTTPException) as exc_info:
        rate_limit.enforce_ip_rate_limit(None, scope="chat_rag")

    assert exc_info.value.status_code == 400


def test_no_redis_client_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """If Redis is unavailable, rate limiting should degrade to a no-op."""
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: None)
    rate_limit.enforce_ip_rate_limit("1.2.3.4", scope="chat")
