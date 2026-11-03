"""Characterization tests for chat routes without Redis (Phase 0).

Documents the current hard dependency: when ``get_redis_client`` returns
``None`` the IP rate-limit gate raises HTTP 500 before any controller runs.
"""

import pytest
from fastapi.testclient import TestClient

from app import rate_limit
from app.config import settings
from app.main import app


@pytest.fixture
def no_redis_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: None)
    monkeypatch.setattr(settings, "turnstile_enabled", False)


def test_chat_returns_500_without_redis(no_redis_client: None) -> None:
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Hello",
            "context": None,
            "system_prompt": None,
            "temperature": 0.3,
            "turnstile_token": "dummy",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Rate limiting backend is unavailable"


def test_chat_rag_returns_500_without_redis(no_redis_client: None) -> None:
    client = TestClient(app)

    response = client.post(
        "/chat/rag",
        json={
            "message": "Hello",
            "top_k": 1,
            "temperature": 0.3,
            "system_prompt": None,
            "turnstile_token": "dummy",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Rate limiting backend is unavailable"
