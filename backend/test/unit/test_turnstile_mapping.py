"""Characterization tests for Turnstile behavior on the chat routes (Phase 0).

Freezes the current mapping: missing token -> 400, verification failure -> 403,
and an unconfigured secret -> 500.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.routes import chat as chat_routes


def _rag_payload(token: str | None) -> dict[str, object]:
    payload: dict[str, object] = {
        "message": "Hello",
        "top_k": 1,
        "temperature": 0.3,
        "system_prompt": None,
    }
    if token is not None:
        payload["turnstile_token"] = token
    return payload


def _plain_payload(token: str | None) -> dict[str, object]:
    payload: dict[str, object] = {
        "message": "Hello",
        "context": None,
        "system_prompt": None,
        "temperature": 0.3,
    }
    if token is not None:
        payload["turnstile_token"] = token
    return payload


@pytest.fixture
def turnstile_on(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    monkeypatch.setattr(settings, "turnstile_enabled", True)
    return client


def test_missing_token_returns_400_on_rag(turnstile_on: TestClient) -> None:
    response = turnstile_on.post("/chat/rag", json=_rag_payload(None))

    assert response.status_code == 400
    assert response.json()["detail"] == "turnstile token is required"


def test_missing_token_returns_400_on_chat(turnstile_on: TestClient) -> None:
    response = turnstile_on.post("/chat", json=_plain_payload(None))

    assert response.status_code == 400
    assert response.json()["detail"] == "turnstile token is required"


def test_failed_verification_returns_403(
    turnstile_on: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        chat_routes,
        "verify_turnstile_token",
        lambda **_: (False, "Turnstile verification failed"),
    )

    response = turnstile_on.post("/chat/rag", json=_rag_payload("bad-token"))

    assert response.status_code == 403
    assert response.json()["detail"] == "Turnstile verification failed"


def test_unconfigured_secret_returns_500(
    turnstile_on: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "turnstile_secret_key", "")

    response = turnstile_on.post("/chat/rag", json=_rag_payload("dummy"))

    assert response.status_code == 500
    assert response.json()["detail"] == "turnstile_secret_key is not configured"
