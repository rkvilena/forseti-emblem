"""Tests for the shared chat request-admission policy (Phase 1).

Covers the ``RequestContext`` session-cookie helper and the ordered admission
policy that both chat endpoints now share. These run alongside the Phase-0
characterization tests, which must stay green without edits.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.application.chat.results import ChatResult
from app.config import settings
from app.controllers import chat_controller
from app.security import request_admission
from app.security.request_admission import RequestContext


class _FakeResponse:
    """Captures ``set_cookie`` calls for ``RequestContext`` unit tests."""

    def __init__(self) -> None:
        self.cookies_set: list[dict[str, object]] = []

    def set_cookie(self, **kwargs: object) -> None:
        self.cookies_set.append(kwargs)


def _fake_request(cookies: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(
        cookies=cookies,
        client=SimpleNamespace(host="203.0.113.7"),
    )


def _context(cookies: dict[str, str]) -> tuple[RequestContext, _FakeResponse]:
    response = _FakeResponse()
    return RequestContext.from_request(_fake_request(cookies), response), response


def _silence_admission_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace Redis-backed gates with no-ops for direct admission tests."""
    monkeypatch.setattr(
        request_admission, "enforce_ip_rate_limit", lambda *a, **k: None
    )
    monkeypatch.setattr(
        request_admission, "enforce_session_quota", lambda *a, **k: None
    )
    monkeypatch.setattr(
        request_admission, "enforce_session_cooldown", lambda *a, **k: None
    )
    monkeypatch.setattr(settings, "turnstile_enabled", False)


def _rag_payload(message: str) -> dict[str, object]:
    return {
        "message": message,
        "top_k": 1,
        "temperature": 0.3,
        "system_prompt": None,
        "turnstile_token": "dummy",
    }


def test_get_or_create_session_id_reuses_existing_cookie() -> None:
    context, response = _context({settings.session_cookie_name: "existing-session"})

    assert context.get_or_create_session_id() == "existing-session"
    assert response.cookies_set == []


def test_get_or_create_session_id_creates_and_writes_once() -> None:
    context, response = _context({})

    session_id = context.get_or_create_session_id()

    assert session_id
    assert len(response.cookies_set) == 1
    written = response.cookies_set[0]
    assert written["key"] == settings.session_cookie_name
    assert written["value"] == session_id
    assert written["httponly"] is True
    assert written["samesite"] == "lax"
    assert written["path"] == "/"
    assert written["secure"] == settings.is_production
    assert written["max_age"] == max(1, int(settings.session_cookie_ttl_seconds))


def test_admission_reuses_one_session_id_for_quota_and_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, response = _context({})
    seen: dict[str, list[str]] = {"quota": [], "cooldown": []}
    monkeypatch.setattr(
        request_admission, "enforce_ip_rate_limit", lambda *a, **k: None
    )
    monkeypatch.setattr(
        request_admission,
        "enforce_session_quota",
        lambda sid, *, scope: seen["quota"].append(sid),
    )
    monkeypatch.setattr(
        request_admission,
        "enforce_session_cooldown",
        lambda sid, *, scope: seen["cooldown"].append(sid),
    )
    monkeypatch.setattr(settings, "turnstile_enabled", False)

    request_admission.admit_chat_request(
        context,
        scope="chat",
        message="Hello",
        turnstile_token=None,
        verify_turnstile=lambda **_: (True, None),
    )

    assert seen["quota"] == seen["cooldown"]
    assert len(seen["quota"]) == 1
    assert len(response.cookies_set) == 1


def test_admission_rejects_empty_message() -> None:
    context, _ = _context({})

    with pytest.raises(HTTPException) as exc_info:
        request_admission.admit_chat_request(
            context,
            scope="chat",
            message="   ",
            turnstile_token=None,
            verify_turnstile=lambda **_: (True, None),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "message must not be empty"


def test_admission_rejects_over_length_message() -> None:
    context, _ = _context({})
    too_long = "x" * (settings.request_max_chars + 1)

    with pytest.raises(HTTPException) as exc_info:
        request_admission.admit_chat_request(
            context,
            scope="chat",
            message=too_long,
            turnstile_token=None,
            verify_turnstile=lambda **_: (True, None),
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == f"message must be at most {settings.request_max_chars} characters"
    )


def test_admission_clamps_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    context, _ = _context({})
    _silence_admission_dependencies(monkeypatch)

    admitted = request_admission.admit_chat_request(
        context,
        scope="chat_rag",
        message="Hello",
        turnstile_token=None,
        verify_turnstile=lambda **_: (True, None),
        top_k=settings.rag_top_k_max + 5,
    )

    assert admitted == settings.rag_top_k_max


def test_admission_requires_turnstile_token_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, _ = _context({})
    _silence_admission_dependencies(monkeypatch)
    monkeypatch.setattr(settings, "turnstile_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        request_admission.admit_chat_request(
            context,
            scope="chat",
            message="Hello",
            turnstile_token=None,
            verify_turnstile=lambda **_: (True, None),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "turnstile token is required"


def test_admission_maps_failed_verification_to_403(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, _ = _context({})
    _silence_admission_dependencies(monkeypatch)
    monkeypatch.setattr(settings, "turnstile_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        request_admission.admit_chat_request(
            context,
            scope="chat",
            message="Hello",
            turnstile_token="bad",
            verify_turnstile=lambda **_: (False, "Turnstile verification failed"),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Turnstile verification failed"


def test_admission_maps_unconfigured_secret_to_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, _ = _context({})
    _silence_admission_dependencies(monkeypatch)
    monkeypatch.setattr(settings, "turnstile_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        request_admission.admit_chat_request(
            context,
            scope="chat",
            message="Hello",
            turnstile_token="dummy",
            verify_turnstile=lambda **_: (
                False,
                "turnstile_secret_key is not configured",
            ),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "turnstile_secret_key is not configured"


def test_first_rag_request_sets_single_session_cookie(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The route normally reaches the DB; stub the controller so admission is the
    # only thing under test and the request completes successfully.
    monkeypatch.setattr(
        chat_controller,
        "chat_rag",
        lambda **_: ChatResult(response="ok", model="test", usage=None),
    )

    response = client.post("/chat/rag", json=_rag_payload("Hello"))

    assert response.status_code == 200
    set_cookies = response.headers.get_list("set-cookie")
    session_headers = [
        header
        for header in set_cookies
        if header.startswith(f"{settings.session_cookie_name}=")
    ]
    assert len(session_headers) == 1


def test_admission_returns_none_for_plain_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, _ = _context({})
    _silence_admission_dependencies(monkeypatch)

    admitted: Any = request_admission.admit_chat_request(
        context,
        scope="chat",
        message="Hello",
        turnstile_token=None,
        verify_turnstile=lambda **_: (True, None),
    )

    assert admitted is None

