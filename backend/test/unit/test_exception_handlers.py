"""Handler tests for centralized exception translation (Phase 8).

A throwaway FastAPI app is built with the registered handlers and routes that
raise each application exception, so every mapping and response body can be
asserted without Postgres, Redis, or OpenAI. A final test drives a real chat
route to prove the main app registers the same handlers.
"""

from __future__ import annotations

import inspect
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.exception_handlers import register_exception_handlers
from app.domain.exceptions import (
    ChapterNotFoundError,
    ConfigurationError,
    DuplicateChapterError,
    EmbeddingError,
    InvalidChatRequest,
    ProviderUnavailableError,
    RetrievalError,
)


def _build_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/invalid-chat")
    def _invalid_chat() -> None:
        raise InvalidChatRequest("message must not be empty")

    @app.get("/duplicate")
    def _duplicate() -> None:
        raise DuplicateChapterError(
            "Chapter 'Prologue' for game 'Fire Emblem' already exists",
            chapter_title="Prologue",
            game="Fire Emblem",
        )

    @app.get("/not-found")
    def _not_found() -> None:
        raise ChapterNotFoundError("chapter not found", title="Prologue")

    @app.get("/provider")
    def _provider() -> None:
        raise ProviderUnavailableError("upstream said: quota exceeded sk-123")

    @app.get("/embedding")
    def _embedding() -> None:
        raise EmbeddingError("upstream embedding failure")

    @app.get("/retrieval")
    def _retrieval() -> None:
        raise RetrievalError("db connection reset")

    @app.get("/configuration")
    def _configuration() -> None:
        raise ConfigurationError("OPENAI_API_KEY is not set")

    @app.get("/unexpected")
    def _unexpected() -> None:
        raise RuntimeError("secret provider detail sk-do-not-leak")

    return TestClient(app, raise_server_exceptions=False)


def test_each_application_exception_has_exactly_one_handler() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    # FastAPI pre-registers its own defaults (validation/HTTP errors); every
    # application exception plus the generic ``Exception`` must have a handler.
    # A dict key is unique, so presence also means "exactly one handler".
    registered = set(app.exception_handlers)
    assert {
        InvalidChatRequest,
        DuplicateChapterError,
        ChapterNotFoundError,
        ProviderUnavailableError,
        EmbeddingError,
        RetrievalError,
        ConfigurationError,
        Exception,
    } <= registered


# --------------------------------------------------------------------------- #
# Mappings
# --------------------------------------------------------------------------- #


def test_invalid_chat_request_maps_to_400() -> None:
    response = _build_client().get("/invalid-chat")

    assert response.status_code == 400
    assert response.json() == {"detail": "message must not be empty"}


def test_duplicate_chapter_maps_to_409_with_structured_detail() -> None:
    response = _build_client().get("/duplicate")

    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "message": "Chapter 'Prologue' for game 'Fire Emblem' already exists",
            "chapter_title": "Prologue",
            "game": "Fire Emblem",
        }
    }


def test_chapter_not_found_maps_to_404() -> None:
    response = _build_client().get("/not-found")

    assert response.status_code == 404
    assert response.json()["detail"] == "chapter not found"


def test_provider_unavailable_maps_to_503_without_leaking_details() -> None:
    response = _build_client().get("/provider")

    assert response.status_code == 503
    assert response.json()["detail"] == "The service is temporarily unavailable."
    assert "sk-123" not in response.text
    assert "quota exceeded" not in response.text


def test_embedding_error_maps_to_503_without_leaking_details() -> None:
    response = _build_client().get("/embedding")

    assert response.status_code == 503
    assert response.json()["detail"] == "The service is temporarily unavailable."
    assert "upstream embedding failure" not in response.text


def test_retrieval_error_maps_to_generic_500() -> None:
    response = _build_client().get("/retrieval")

    assert response.status_code == 500
    assert "db connection reset" not in response.text


def test_configuration_error_maps_to_generic_500() -> None:
    response = _build_client().get("/configuration")

    assert response.status_code == 500
    assert response.json()["detail"] == "The service is not configured correctly."
    assert "OPENAI_API_KEY" not in response.text


def test_unexpected_error_maps_to_generic_500_with_request_id() -> None:
    response = _build_client().get("/unexpected")

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "An unexpected error occurred. Please try again later."
    )
    assert "sk-do-not-leak" not in response.text
    assert response.headers["X-Request-ID"]


# --------------------------------------------------------------------------- #
# The real app and route hygiene
# --------------------------------------------------------------------------- #


def test_chat_route_translates_provider_failure(client: TestClient) -> None:
    from app.application.chat.dependencies import get_plain_chat_service
    from app.main import app

    def _raise() -> Any:
        raise ProviderUnavailableError("boom")

    app.dependency_overrides[get_plain_chat_service] = _raise
    try:
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
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_chat_routes_have_no_blanket_except() -> None:
    from app.routes import chat

    source = inspect.getsource(chat)

    assert "except Exception" not in source
    assert "HTTPException" not in source


def test_wiki_controller_no_longer_catches_duplicate() -> None:
    from app.controllers import wiki_controller

    source = inspect.getsource(wiki_controller)

    assert "except DuplicateChapterError" not in source
    assert "HTTPException" not in source
