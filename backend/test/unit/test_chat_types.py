"""Tests for the typed chat commands and results (Phase 2).

Exercises the explicit contract between the routes and the chat controller:
the application-layer command/result types, and the mapping from a typed
``ChatResult`` back onto the public HTTP response. No live Postgres, Redis, or
OpenAI is required.
"""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.chat.commands import PlainChatCommand, RagChatCommand
from app.application.chat.results import ChatResult, SourceReference, Usage
from app.config import settings
from app.controllers import chat_controller


def _chapter(**overrides: Any) -> SimpleNamespace:
    data: dict[str, Any] = {
        "id": 1,
        "title": "Prologue",
        "infobox_title": "Prologue: A Beginning",
        "game": "Fire Emblem: The Blazing Blade",
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


def _rag_payload() -> dict[str, object]:
    return {
        "message": "Tell me about Prologue",
        "top_k": 1,
        "temperature": 0.3,
        "system_prompt": None,
        "turnstile_token": "dummy",
    }


def test_plain_chat_command_is_frozen() -> None:
    command = PlainChatCommand(
        message="hello",
        system_prompt=None,
        context=None,
        temperature=0.3,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(command, "message", "changed")


def test_rag_chat_command_carries_explicit_fields() -> None:
    command = RagChatCommand(
        message="hello",
        top_k=3,
        temperature=0.5,
        system_prompt="be terse",
    )

    assert command.message == "hello"
    assert command.top_k == 3
    assert command.temperature == 0.5
    assert command.system_prompt == "be terse"


def test_chat_plain_returns_typed_result_with_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_controller,
        "chat_completion",
        lambda **_: (
            "answer",
            {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        ),
    )

    result = chat_controller.chat_plain(
        PlainChatCommand(
            message="Hi",
            system_prompt=None,
            context=None,
            temperature=0.3,
        )
    )

    assert isinstance(result, ChatResult)
    assert result.response == "answer"
    assert result.model == settings.openai_chat_model
    assert result.usage == Usage(
        prompt_tokens=1,
        completion_tokens=2,
        total_tokens=3,
    )
    assert result.sources is None


def test_chat_rag_returns_typed_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    chapter = _chapter()
    monkeypatch.setattr(
        chat_controller, "retrieve_similar_chunks", lambda **_: [_chunk(chapter)]
    )
    monkeypatch.setattr(
        chat_controller, "chat_completion", lambda **_: ("answer", None)
    )

    result = chat_controller.chat_rag(
        db=None,  # type: ignore[arg-type]
        command=RagChatCommand(
            message="Tell me about Prologue",
            top_k=1,
            temperature=0.3,
            system_prompt=None,
        ),
    )

    assert isinstance(result, ChatResult)
    assert result.response == "answer"
    assert result.usage is None
    assert result.sources == [
        SourceReference(
            title="Prologue",
            infobox_title="Prologue: A Beginning",
            game="Fire Emblem: The Blazing Blade",
            pageid=101,
            source_url="https://example.test/prologue",
        )
    ]


def test_chat_rag_fallback_returns_none_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_controller, "retrieve_similar_chunks", lambda **_: [])

    result = chat_controller.chat_rag(
        db=None,  # type: ignore[arg-type]
        command=RagChatCommand(
            message="anything",
            top_k=1,
            temperature=0.3,
            system_prompt=None,
        ),
    )

    assert result.response == "Not found in provided context."
    assert result.usage is None
    assert result.sources is None


def test_route_maps_typed_result_to_http_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    typed = ChatResult(
        response="answer",
        model="test-model",
        usage=Usage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        sources=[
            SourceReference(
                title="Prologue",
                infobox_title=None,
                game="Fire Emblem",
                pageid=7,
                source_url="https://example.test/p",
            )
        ],
    )
    monkeypatch.setattr(chat_controller, "chat_rag", lambda **_: typed)

    response = client.post("/chat/rag", json=_rag_payload())

    assert response.status_code == 200
    assert response.json() == {
        "response": "answer",
        "model": "test-model",
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
        },
        "sources": [
            {
                "title": "Prologue",
                "infobox_title": None,
                "game": "Fire Emblem",
                "pageid": 7,
                "source_url": "https://example.test/p",
            }
        ],
    }
