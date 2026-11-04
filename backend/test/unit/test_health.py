"""Unit tests for the health module (Phase 9 liveness/readiness).

Only ``app.health`` is exercised here.  The readiness service is created fresh
per test with a fake clock so the module-level singleton cache never leaks
between tests, and the database / Redis dependencies are replaced with
lightweight in-memory doubles (no live Postgres, Redis, or network required).
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app import health
from app.db import get_db
from app.main import app
from app.rate_limit import get_redis_client


class FakeClock:
    """Deterministic stand-in for ``time.monotonic``."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def monotonic(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeDb:
    """Minimal database double that can be made to fail."""

    def __init__(self, fail: bool = False, message: str = "boom") -> None:
        self.fail = fail
        self.message = message
        self.calls = 0

    def execute(self, *args: object, **kwargs: object) -> None:
        self.calls += 1
        if self.fail:
            raise RuntimeError(self.message)


class FakeRedis:
    """Minimal Redis double that can return ``True``/``False`` or raise."""

    def __init__(self, ping_result: bool = True, fail: bool = False) -> None:
        self.ping_result = ping_result
        self.fail = fail
        self.calls = 0

    def ping(self) -> bool:
        self.calls += 1
        if self.fail:
            raise RuntimeError("redis is down")
        return self.ping_result


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Patch ``app.health`` timing with a controllable clock."""
    clk = FakeClock()
    monkeypatch.setattr(health.time, "monotonic", clk.monotonic)
    return clk


@pytest.fixture
def pgvector_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend the pgvector extension is available."""
    monkeypatch.setattr(health, "pgvector_available", lambda: True)


def make_service() -> health._ReadinessService:
    """Build a fresh readiness service so tests never share the singleton."""
    return health._ReadinessService(cache_ttl_seconds=30.0)


def call_ready(
    monkeypatch: pytest.MonkeyPatch,
    *,
    db: object,
    redis_client: object,
    pgvector_error: bool = False,
) -> Response:
    """Hit ``GET /health/ready`` with injected dependencies and a fresh cache."""
    monkeypatch.setattr(health, "_readiness_service", make_service())
    monkeypatch.setattr(health, "pgvector_available", lambda: not pgvector_error)

    def override_db() -> Iterator[object]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis_client] = lambda: redis_client
    try:
        client = TestClient(app)
        return client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()


# --- Liveness ------------------------------------------------------------


def test_liveness_returns_ok() -> None:
    assert health.liveness() == {"status": "ok"}


def test_liveness_does_not_touch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*args: object, **kwargs: object) -> None:
        raise AssertionError("liveness must not touch dependencies")

    monkeypatch.setattr(health, "get_db", explode)
    monkeypatch.setattr(health, "get_redis_client", explode)
    monkeypatch.setattr(health, "pgvector_available", explode)

    assert health.liveness() == {"status": "ok"}


# --- Readiness (service level) ------------------------------------------


def test_healthy_readiness_returns_status_ok(
    clock: FakeClock, pgvector_ok: None
) -> None:
    result = make_service().get(FakeDb(), FakeRedis())

    assert result.status == "ok"
    assert result.dependencies == {
        "database": "ok",
        "pgvector": "ok",
        "redis": "ok",
    }


def test_failed_dependency_does_not_prevent_others(
    clock: FakeClock, pgvector_ok: None
) -> None:
    db = FakeDb(fail=True)
    redis_client = FakeRedis()

    result = make_service().get(db, redis_client)

    # The database failed, but the other dependencies were still evaluated.
    assert result.dependencies["database"] == "error"
    assert result.dependencies["pgvector"] == "ok"
    assert result.dependencies["redis"] == "ok"
    assert db.calls == 1
    assert redis_client.calls == 1


def test_redis_none_is_failure(clock: FakeClock, pgvector_ok: None) -> None:
    result = make_service().get(FakeDb(), None)

    assert result.status == "not_ready"
    assert result.dependencies["redis"] == "error"


def test_redis_false_is_failure(clock: FakeClock, pgvector_ok: None) -> None:
    result = make_service().get(FakeDb(), FakeRedis(ping_result=False))

    assert result.dependencies["redis"] == "error"


def test_redis_exception_is_failure(clock: FakeClock, pgvector_ok: None) -> None:
    result = make_service().get(FakeDb(), FakeRedis(fail=True))

    assert result.dependencies["redis"] == "error"


def test_two_calls_within_ttl_use_cache(
    clock: FakeClock, pgvector_ok: None
) -> None:
    service = make_service()
    db = FakeDb()
    redis_client = FakeRedis()

    first = service.get(db, redis_client)
    clock.advance(10.0)
    second = service.get(db, redis_client)

    assert first is second
    assert db.calls == 1
    assert redis_client.calls == 1


def test_cache_expires_after_ttl(clock: FakeClock, pgvector_ok: None) -> None:
    service = make_service()
    db = FakeDb()
    redis_client = FakeRedis()

    service.get(db, redis_client)
    clock.advance(31.0)
    service.get(db, redis_client)

    assert db.calls == 2
    assert redis_client.calls == 2


def test_unhealthy_result_is_cached(clock: FakeClock, pgvector_ok: None) -> None:
    service = make_service()
    db = FakeDb(fail=True)
    redis_client = FakeRedis()

    service.get(db, redis_client)
    clock.advance(10.0)
    second = service.get(db, redis_client)

    assert second.status == "not_ready"
    assert db.calls == 1


def test_response_does_not_expose_exception_text(
    clock: FakeClock, pgvector_ok: None
) -> None:
    secret = "SUPER_SECRET_DB_TOKEN_123"
    result = make_service().get(FakeDb(fail=True, message=secret), None)

    assert result.dependencies["database"] == "error"
    assert secret not in json.dumps(result.dependencies)


# --- Readiness (route level) --------------------------------------------


def test_ready_route_healthy_returns_200(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock, pgvector_ok: None
) -> None:
    response = call_ready(monkeypatch, db=FakeDb(), redis_client=FakeRedis())

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {"database": "ok", "pgvector": "ok", "redis": "ok"},
    }


def test_database_failure_returns_503(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    response = call_ready(
        monkeypatch,
        db=FakeDb(fail=True),
        redis_client=FakeRedis(),
        pgvector_error=False,
    )

    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"


def test_pgvector_failure_returns_503(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    response = call_ready(
        monkeypatch,
        db=FakeDb(),
        redis_client=FakeRedis(),
        pgvector_error=True,
    )

    assert response.status_code == 503
    assert response.json()["detail"]["dependencies"]["pgvector"] == "error"


def test_redis_failure_returns_503(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    response = call_ready(monkeypatch, db=FakeDb(), redis_client=None)

    assert response.status_code == 503
    assert response.json()["detail"]["dependencies"]["redis"] == "error"


def test_ready_route_does_not_expose_exception_text(
    monkeypatch: pytest.MonkeyPatch, clock: FakeClock
) -> None:
    secret = "SUPER_SECRET_DB_TOKEN_123"
    response = call_ready(
        monkeypatch,
        db=FakeDb(fail=True, message=secret),
        redis_client=FakeRedis(),
    )

    assert response.status_code == 503
    assert secret not in response.text
