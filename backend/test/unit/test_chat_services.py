"""Unit tests for the chat application services (Phase 3; ports wired in 5).

The use cases are exercised in isolation with in-memory fakes for the provider
ports; no live Postgres, Redis, or OpenAI is required.
"""

import inspect
from types import SimpleNamespace
from typing import Any

from app.application.chat import service
from app.application.chat.commands import PlainChatCommand, RagChatCommand
from app.application.chat.results import ChatResult, SourceReference, Usage
from app.config import settings
from app.services import answer_generation
from app.services.answer_generation import AnswerGenerator
from app.services.retrieval import RetrievalOptions

from fakes import FakeAnswerProvider, FakeRetriever


def _chapter(**overrides: Any) -> SimpleNamespace:
    data: dict[str, Any] = {
        "id": 1,
        "title": "Prologue",
        "infobox_title": "Prologue: A Beginning",
        "game": "Fire Emblem: The Blazing Blade",
        "objective": "Seize the gate",
        "units_gained": None,
        "boss": "Brigand Leader",
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


def test_plain_service_maps_usage_and_defaults_system_prompt() -> None:
    provider = FakeAnswerProvider(
        text="answer",
        model=settings.openai_chat_model,
        usage=Usage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
    )

    result = service.PlainChatService(answer_generator=AnswerGenerator(provider)).execute(
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
    call = provider.calls[0]
    assert call["system_prompt"] == answer_generation.FIRE_EMBLEM_SYSTEM_PROMPT
    assert call["question"] == "Hi"
    assert call["context"] is None


def test_plain_service_honors_overrides() -> None:
    provider = FakeAnswerProvider(text="answer")

    result = service.PlainChatService(answer_generator=AnswerGenerator(provider)).execute(
        PlainChatCommand(
            message="Hi",
            system_prompt="be terse",
            context="manual context",
            temperature=0.7,
        )
    )

    call = provider.calls[0]
    assert call["system_prompt"] == "be terse"
    assert call["context"] == "manual context"
    assert call["temperature"] == 0.7
    assert result.usage is None


def test_rag_service_falls_back_without_chunks() -> None:
    result = service.RagChatService(  # type: ignore[arg-type]
        None,
        retriever=FakeRetriever([]),
        answer_generator=AnswerGenerator(FakeAnswerProvider()),
    ).execute(
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


def test_rag_service_retrieves_builds_context_and_filters_sources() -> None:
    chapter = _chapter()
    retriever = FakeRetriever([_chunk(chapter)])
    provider = FakeAnswerProvider(text="answer")

    result = service.RagChatService(  # type: ignore[arg-type]
        "DB",
        retriever=retriever,
        answer_generator=AnswerGenerator(provider),
    ).execute(
        RagChatCommand(
            message="Tell me about Prologue",
            top_k=3,
            temperature=0.4,
            system_prompt=None,
        )
    )

    assert retriever.calls[0]["db"] == "DB"
    assert retriever.calls[0]["query"] == "Tell me about Prologue"
    assert retriever.calls[0]["options"] == RetrievalOptions(top_k=3)
    assert "Prologue" in (provider.calls[0]["context"] or "")
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


def test_rag_service_deduplicates_sources_and_omits_unreferenced() -> None:
    chapter = _chapter()
    provider = FakeAnswerProvider(text="answer")

    def _service() -> service.RagChatService:
        return service.RagChatService(  # type: ignore[arg-type]
            "DB",
            retriever=FakeRetriever([_chunk(chapter), _chunk(chapter)]),
            answer_generator=AnswerGenerator(provider),
        )

    referenced = _service().execute(
        RagChatCommand(
            message="Tell me about Prologue",
            top_k=2,
            temperature=0.3,
            system_prompt=None,
        )
    )
    assert referenced.sources is not None
    assert len(referenced.sources) == 1

    unreferenced = _service().execute(
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
