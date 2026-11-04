"""Health check implementation.

Two independent endpoints are provided:

* :func:`liveness` - lightweight process-level health.  It is safe to expose in
  all environments because it never touches the database or external services.
* :func:`readiness` - dependency-aware readiness check.  It verifies that the
  PostgreSQL database, the ``pgvector`` extension, and Redis are reachable.  The
  result (healthy *or* unhealthy) is cached for a short interval so frequent
  probe traffic does not hammer the dependencies.

The module deliberately does not expose any other endpoints or side effects; it
is pure FastAPI routers and a small in-memory cache.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Literal

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db, pgvector_available
from .rate_limit import get_redis_client


router = APIRouter(tags=["system"])

# How long a readiness result (healthy *or* unhealthy) is reused before the
# dependencies are checked again.  The probe intervals themselves (liveness 90s
# / readiness 60s) are deployment settings, not application settings, and are
# intentionally not encoded here.
_READINESS_CACHE_TTL_SECONDS = 30.0


@router.get("/health/live", name="health_liveness")
def liveness() -> dict[str, Literal["ok"]]:
    """Return a simple liveness response.

    The response never accesses the database or Redis; it merely indicates that
    the FastAPI application process is up.
    """
    return {"status": "ok"}


# --- Readiness cache infrastructure -------------------------------------


@dataclass
class ReadinessCache:
    """Cached readiness snapshot."""

    status: Literal["ok", "not_ready"]
    dependencies: dict[str, Literal["ok", "error"]]
    last_checked: float


class _ReadinessService:
    """Dependency-aware readiness checks with a small, lock-protected cache.

    The ``db`` and ``redis`` arguments are typed as ``Any`` so tests can inject
    lightweight doubles without depending on the concrete SQLAlchemy session or
    Redis client types.
    """

    def __init__(self, cache_ttl_seconds: float) -> None:
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: ReadinessCache | None = None
        self._lock = threading.Lock()

    def _check_database(self, db: Any) -> Literal["ok", "error"]:
        """Verify the database is reachable with a lightweight query."""
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            return "error"
        return "ok"

    def _check_pgvector(self) -> Literal["ok", "error"]:
        """Verify the ``vector`` extension is installed server-side."""
        try:
            if not pgvector_available():
                return "error"
        except Exception:
            return "error"
        return "ok"

    def _check_redis(self, redis_client: Any) -> Literal["ok", "error"]:
        """Verify Redis is reachable; ``None``/``False``/exceptions all fail."""
        try:
            if redis_client is None:
                return "error"
            if redis_client.ping() is False:
                return "error"
        except Exception:
            return "error"
        return "ok"

    def _check_dependencies(self, db: Any, redis_client: Any) -> ReadinessCache:
        # Each dependency is evaluated independently so one failure never
        # prevents the others from being checked.
        dependencies: dict[str, Literal["ok", "error"]] = {
            "database": self._check_database(db),
            "pgvector": self._check_pgvector(),
            "redis": self._check_redis(redis_client),
        }

        overall_status: Literal["ok", "not_ready"]
        overall_status = (
            "ok"
            if all(dependency == "ok" for dependency in dependencies.values())
            else "not_ready"
        )

        return ReadinessCache(
            status=overall_status,
            dependencies=dependencies,
            last_checked=time.monotonic(),
        )

    def get(self, db: Any, redis_client: Any) -> ReadinessCache:
        """Return a cached readiness snapshot, refreshing it when stale."""
        now = time.monotonic()
        with self._lock:
            if (
                self._cache is not None
                and (now - self._cache.last_checked) <= self._cache_ttl_seconds
            ):
                return self._cache
            # Cache miss (or expired) - recompute and cache the result.
            self._cache = self._check_dependencies(db, redis_client)
            return self._cache


_readiness_service = _ReadinessService(cache_ttl_seconds=_READINESS_CACHE_TTL_SECONDS)


@router.get("/health/ready", name="health_readiness")
def readiness(
    db: Session = Depends(get_db),
    redis_client: redis.Redis | None = Depends(get_redis_client),
) -> dict[str, object]:
    """Return a dependency-aware readiness response.

    The response includes a concise status and a mapping of dependency health.
    If any required dependency fails, a ``503 Service Unavailable`` is returned.
    The response never includes raw exception details.
    """
    result = _readiness_service.get(db, redis_client)
    response: dict[str, object] = {
        "status": result.status,
        "dependencies": result.dependencies,
    }
    if result.status == "ok":
        return response
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=response,
    )
