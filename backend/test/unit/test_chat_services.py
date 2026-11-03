"""Unit tests for the chat application services (Phase 3).

The use cases are exercised in isolation with fakes for retrieval and the
completion provider; no live Postgres, Redis, or OpenAI is required.
"""

import inspect
from types import SimpleNamespace
from typing import Any

import pytest

from app.application.chat import service
from app.application.chat.commands import PlainChatCommand, RagChatCommand
from app.application.chat.results import ChatResult, SourceReference, Usage
from app.config import settings


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


def test_plain_service_maps_usage_and_defaults_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured.update(kwargs)
        return "answer", {
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
        }

    monkeypatch.setattr(service, "chat_completion", _fake_completion)

    result = service.PlainChatService().execute(
        PlainChatCommand(
            message="Hi",
            system_prompt=None,
            context=None,
            temperature=0.3,
        )
    )

    assert result == ChatResult(
        response="answer",
        model=settings.openai_chat_model,
        usage=Usage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
    )
    assert captured["system_prompt"] == service.FIRE_EMBLEM_SYSTEM_PROMPT
    assert captured["user_message"] == "Hi"
    assert captured["context"] is None


def test_plain_service_honors_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured.update(kwargs)
        return "answer", None

    monkeypatch.setattr(service, "chat_completion", _fake_completion)

    result = service.PlainChatService().execute(
        PlainChatCommand(
            message="Hi",
            system_prompt="be terse",
            context="manual context",
            temperature=0.7,
        )
    )

    assert captured["system_prompt"] == "be terse"
    assert captured["context"] == "manual context"
    assert captured["temperature"] == 0.7
    assert result.usage is None


def test_rag_service_falls_back_without_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "retrieve_similar_chunks", lambda **_: [])

    result = service.RagChatService(None).execute(  # type: ignore[arg-type]
        RagChatCommand(
            message="anything",
            top_k=1,
            temperature=0.3,
            system_prompt=None,
        )
    )

    assert result.response == "Not found in provided context."
    assert result.usage is None
    assert result.sources is None


def test_rag_service_retrieves_builds_context_and_filters_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chapter = _chapter()
    captured: dict[str, Any] = {}

    def _fake_retrieve(**kwargs: Any) -> list[SimpleNamespace]:
        captured["retrieve"] = kwargs
        return [_chunk(chapter)]

    def _fake_build(chunks: Any, **kwargs: Any) -> str:
        captured["build_chunks"] = chunks
        return "CTX"

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured["completion"] = kwargs
        return "answer", None

    monkeypatch.setattr(service, "retrieve_similar_chunks", _fake_retrieve)
    monkeypatch.setattr(service, "build_context_from_chunks", _fake_build)
    monkeypatch.setattr(service, "chat_completion", _fake_completion)

    result = service.RagChatService(db="DB").execute(  # type: ignore[arg-type]
        RagChatCommand(
            message="Tell me about Prologue",
            top_k=3,
            temperature=0.4,
            system_prompt=None,
        )
    )

    assert captured["retrieve"] == {
        "db": "DB",
        "query": "Tell me about Prologue",
        "top_k": 3,
    }
    assert captured["completion"]["context"] == "CTX"
    assert result.response == "answer"
    assert result.sources == [
        SourceReference(
            title="Prologue",
            infobox_title="Prologue: A Beginning",
            game="Fire Emblem: The Blazing Blade",
            pageid=101,
            source_url="https://example.test/prologue",
        )
    ]


def test_rag_service_deduplicates_sources_and_omits_unreferenced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chapter = _chapter()
    monkeypatch.setattr(
        service,
        "retrieve_similar_chunks",
        lambda **_: [_chunk(chapter), _chunk(chapter)],
    )
    monkeypatch.setattr(
        service, "build_context_from_chunks", lambda chunks, **_: "CTX"
    )
    monkeypatch.setattr(service, "chat_completion", lambda **_: ("answer", None))

    referenced = service.RagChatService("DB").execute(  # type: ignore[arg-type]
        RagChatCommand(
            message="Tell me about Prologue",
            top_k=2,
            temperature=0.3,
            system_prompt=None,
        )
    )
    assert referenced.sources is not None
    assert len(referenced.sources) == 1

    unreferenced = service.RagChatService("DB").execute(  # type: ignore[arg-type]
        RagChatCommand(
            message="What should I do here?",
            top_k=2,
            temperature=0.3,
            system_prompt=None,
        )
    )
    assert unreferenced.sources is None


def test_service_module_imports_no_fastapi() -> None:
    source = inspect.getsource(service)

    assert "import fastapi" not in source
    assert "from fastapi" not in source
