"""Characterization tests for RAG chat behavior (Phase 0).

Covers the retrieval fallback, ``top_k`` clamping, and source filtering in
``GET /chat/rag`` as they behave today. Retrieval and OpenAI are replaced with
in-memory fakes by overriding the chat dependency providers, so no live
Postgres, Redis, or OpenAI is needed.
"""

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.chat import service
from app.application.chat.dependencies import get_rag_chat_service
from app.application.chat.results import ChatResult
from app.application.chat.service import RagChatService
from app.config import settings
from app.main import app
from app.services.answer_generation import AnswerGenerator

from fakes import FakeAnswerProvider, FakeRetriever


def _rag_payload(message: str, top_k: int = 1) -> dict[str, object]:
    return {
        "message": message,
        "top_k": top_k,
        "temperature": 0.3,
        "system_prompt": None,
        "turnstile_token": "dummy",
    }


def _chapter(**overrides: Any) -> SimpleNamespace:
    data: dict[str, Any] = {
        "id": 1,
        "title": "Prologue",
        "infobox_title": "Prologue: A Beginning",
        "game": "Fire Emblem: The Blazing Blade",
        "objective": None,
        "units_gained": None,
        "boss": None,
        "pageid": 101,
        "source_url": "https://example.test/prologue",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _chunk(chapter: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        kind="section",
        chunk_index=0,
        section_title="Overview",
        text="The chapter begins.",
        chapter=chapter,
    )


def _override_rag(chunks: list[Any]) -> None:
    """Replace the RAG use case with one built from in-memory fakes."""

    def _factory() -> RagChatService:
        return RagChatService(  # type: ignore[arg-type]
            None,
            retriever=FakeRetriever(chunks),
            answer_generator=AnswerGenerator(FakeAnswerProvider(text="answer")),
        )

    app.dependency_overrides[get_rag_chat_service] = _factory


@pytest.fixture(autouse=True)
def _clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_rag_returns_fallback_when_no_chunks(client: TestClient) -> None:
    _override_rag([])

    response = client.post("/chat/rag", json=_rag_payload("anything"))

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "Not found in provided context."
    assert body["usage"] is None
    assert body["sources"] is None


def test_rag_clamps_top_k_above_max(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, int] = {}

    def _capture_execute(self: Any, command: Any) -> ChatResult:
        captured["top_k"] = command.top_k
        return ChatResult(response="ok", model="test", usage=None)

    monkeypatch.setattr(service.RagChatService, "execute", _capture_execute)

    response = client.post(
        "/chat/rag", json=_rag_payload("Hello", top_k=settings.rag_top_k_max + 5)
    )

    assert response.status_code == 200
    assert captured["top_k"] == settings.rag_top_k_max


def test_rag_returns_source_when_title_appears_in_message(
    client: TestClient,
) -> None:
    chapter = _chapter()
    _override_rag([_chunk(chapter)])

    response = client.post(
        "/chat/rag", json=_rag_payload("Tell me about Prologue")
    )

    assert response.status_code == 200
    assert response.json()["sources"] == [
        {
            "title": "Prologue",
            "infobox_title": "Prologue: A Beginning",
            "game": "Fire Emblem: The Blazing Blade",
            "pageid": 101,
            "source_url": "https://example.test/prologue",
        }
    ]


def test_rag_returns_source_when_game_appears_in_message(
    client: TestClient,
) -> None:
    chapter = _chapter(
        title="Chapter 1",
        infobox_title="Chapter 1",
        game="Fire Emblem",
    )
    _override_rag([_chunk(chapter)])

    response = client.post(
        "/chat/rag", json=_rag_payload("Which Fire Emblem game is this?")
    )

    assert response.status_code == 200
    assert response.json()["sources"] is not None
    assert response.json()["sources"][0]["title"] == "Chapter 1"


def test_rag_omits_sources_when_no_reference_in_message(
    client: TestClient,
) -> None:
    chapter = _chapter()
    _override_rag([_chunk(chapter)])

    response = client.post("/chat/rag", json=_rag_payload("What should I do here?"))

    assert response.status_code == 200
    assert response.json()["sources"] is None
