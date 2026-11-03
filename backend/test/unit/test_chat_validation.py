"""Characterization tests for chat request validation (Phase 0).

Freezes the current 400/422 behavior of ``POST /chat`` and ``POST /chat/rag``
so later refactors can be told apart from behavior changes.
"""

from fastapi.testclient import TestClient

from app.config import settings


def _plain_payload(message: str) -> dict[str, object]:
    return {
        "message": message,
        "context": None,
        "system_prompt": None,
        "temperature": 0.3,
        "turnstile_token": "dummy",
    }


def _rag_payload(message: str) -> dict[str, object]:
    return {
        "message": message,
        "top_k": 1,
        "temperature": 0.3,
        "system_prompt": None,
        "turnstile_token": "dummy",
    }


def test_chat_rejects_whitespace_only_message(client: TestClient) -> None:
    response = client.post("/chat", json=_plain_payload("   "))

    assert response.status_code == 400
    assert response.json()["detail"] == "message must not be empty"


def test_chat_rag_rejects_whitespace_only_message(client: TestClient) -> None:
    response = client.post("/chat/rag", json=_rag_payload("   "))

    assert response.status_code == 400
    assert response.json()["detail"] == "message must not be empty"


def test_empty_string_message_is_rejected_by_schema(client: TestClient) -> None:
    # Characterization: a truly empty string fails Pydantic ``min_length=1``
    # (422), not the route-level empty check (400). Documented in Phase 0 notes.
    response = client.post("/chat", json=_plain_payload(""))

    assert response.status_code == 422


def test_chat_rejects_over_length_message(client: TestClient) -> None:
    too_long = "x" * (settings.request_max_chars + 1)

    response = client.post("/chat", json=_plain_payload(too_long))

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == f"message must be at most {settings.request_max_chars} characters"
    )


def test_chat_rag_rejects_over_length_message(client: TestClient) -> None:
    too_long = "x" * (settings.request_max_chars + 1)

    response = client.post("/chat/rag", json=_rag_payload(too_long))

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == f"message must be at most {settings.request_max_chars} characters"
    )
