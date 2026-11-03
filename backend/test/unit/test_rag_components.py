"""Unit tests for the decomposed RAG pipeline components (Phase 4).

Each step of the pipeline -- retrieval, context building, answer generation, and
source selection -- is exercised in isolation. No live Postgres, Redis, or OpenAI
is required: the retrieval query is faked and the embedding call is patched.
"""

import inspect
from types import SimpleNamespace
from typing import Any

import pytest

from app.services import answer_generation
from app.services import retrieval as retrieval_module
from app.services.answer_generation import AnswerGenerator
from app.services.context_builder import (
    ContextBudget,
    ContextBuilder,
    build_context_from_chunks,
)
from app.services.retrieval import (
    RetrievalOptions,
    Retriever,
    retrieve_similar_chunks,
)
from app.services.source_selector import SourceSelector, select_sources


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


def _chunk(
    chapter: SimpleNamespace,
    *,
    text: str = "The chapter begins.",
    chunk_index: int = 0,
    section_title: str | None = "Overview",
    kind: str = "section",
) -> SimpleNamespace:
    return SimpleNamespace(
        kind=kind,
        chunk_index=chunk_index,
        section_title=section_title,
        text=text,
        chapter=chapter,
    )


# --------------------------------------------------------------------------- #
# Retrieval
# --------------------------------------------------------------------------- #


class _FakeQuery:
    def __init__(self, limits: list[int], results: list[Any]) -> None:
        self._limits = limits
        self._results = results

    def options(self, *args: Any, **kwargs: Any) -> "_FakeQuery":
        return self

    def filter(self, *args: Any, **kwargs: Any) -> "_FakeQuery":
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> "_FakeQuery":
        return self

    def limit(self, value: int) -> "_FakeQuery":
        self._limits.append(value)
        return self

    def all(self) -> list[Any]:
        return self._results


class _FakeDB:
    def __init__(self, limits: list[int], results: list[Any]) -> None:
        self._limits = limits
        self._results = results

    def query(self, model: Any) -> _FakeQuery:
        return _FakeQuery(self._limits, self._results)


def test_retrieval_options_defaults_are_threaded() -> None:
    options = RetrievalOptions(top_k=5)

    assert options.top_k == 5
    assert options.similarity_threshold is None
    assert options.chapter_filter is None


def test_retrieval_applies_top_k_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retrieval_module, "create_embedding", lambda _: [0.0] * 4)
    limits: list[int] = []
    db = _FakeDB(limits, results=[])

    result = retrieve_similar_chunks(
        db,  # type: ignore[arg-type]
        "question",
        RetrievalOptions(top_k=3),
    )

    assert result == []
    assert limits == [3]


def test_retriever_delegates_to_retrieve_similar_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake(db: Any, query: str, options: RetrievalOptions) -> list[Any]:
        captured["db"] = db
        captured["query"] = query
        captured["options"] = options
        return []

    monkeypatch.setattr(retrieval_module, "retrieve_similar_chunks", _fake)

    result = Retriever().retrieve(
        db="DB",  # type: ignore[arg-type]
        query="q",
        options=RetrievalOptions(top_k=2),
    )

    assert result == []
    assert captured == {
        "db": "DB",
        "query": "q",
        "options": RetrievalOptions(top_k=2),
    }



# --------------------------------------------------------------------------- #
# Context builder
# --------------------------------------------------------------------------- #


def test_context_builder_formats_identical_string() -> None:
    chunk = _chunk(_chapter())

    context = build_context_from_chunks([chunk])

    assert context == (
        "[Chapter: Prologue | kind=section | section=Overview | idx=0]\n"
        "[Meta: game=Fire Emblem: The Blazing Blade | objective=Seize the gate"
        " | boss=Brigand Leader]\n"
        "The chapter begins."
    )


def test_context_builder_preserves_chunk_order() -> None:
    first = _chunk(_chapter(title="First"), text="one", chunk_index=0)
    second = _chunk(_chapter(id=2, title="Second"), text="two", chunk_index=1)

    context = build_context_from_chunks([first, second])

    assert context.index("First") < context.index("Second")


def test_context_builder_respects_char_budget() -> None:
    chunk = _chunk(_chapter(), text="x" * 100)

    assert build_context_from_chunks([chunk], ContextBudget(max_chars=10)) == ""
    assert build_context_from_chunks([chunk], ContextBudget(max_chars=8000)) != ""


def test_context_budget_defaults() -> None:
    budget = ContextBudget()

    assert budget.max_chars == 8000
    assert budget.max_chunks is None


def test_context_builder_class_delegates() -> None:
    chunk = _chunk(_chapter())

    assert ContextBuilder().build([chunk]) == build_context_from_chunks([chunk])


# --------------------------------------------------------------------------- #
# Source selector
# --------------------------------------------------------------------------- #


def test_source_selector_deduplicates_chapters() -> None:
    chapter = _chapter()
    chunks = [_chunk(chapter, chunk_index=0), _chunk(chapter, chunk_index=1)]

    sources = select_sources(chunks, "Tell me about Prologue")

    assert len(sources) == 1
    assert sources[0].title == "Prologue"
    assert sources[0].pageid == 101


def test_source_selector_filters_unreferenced_chapter() -> None:
    chunks = [_chunk(_chapter())]

    assert select_sources(chunks, "What should I do here?") == []
    assert select_sources(chunks, "Tell me about Prologue") != []


def test_source_selector_matches_on_game_and_strips_brackets() -> None:
    chapter = _chapter(
        title="Chapter 1", infobox_title="Chapter 1", game="[Fire Emblem]"
    )
    chunks = [_chunk(chapter)]

    sources = select_sources(chunks, "Which Fire Emblem game is this?")

    assert len(sources) == 1
    assert sources[0].title == "Chapter 1"


def test_source_selector_class_delegates() -> None:
    chunks = [_chunk(_chapter())]

    assert (
        SourceSelector().select(chunks, "Tell me about Prologue")
        == select_sources(chunks, "Tell me about Prologue")
    )



# --------------------------------------------------------------------------- #
# Answer generation
# --------------------------------------------------------------------------- #


def test_generate_answer_uses_default_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured.update(kwargs)
        return "answer", None

    monkeypatch.setattr(answer_generation, "chat_completion", _fake_completion)

    text, usage = AnswerGenerator().generate(
        question="Hi",
        context="CTX",
        temperature=0.3,
    )

    assert text == "answer"
    assert usage is None
    assert captured["system_prompt"] == answer_generation.FIRE_EMBLEM_SYSTEM_PROMPT
    assert captured["user_message"] == "Hi"
    assert captured["context"] == "CTX"


def test_generate_answer_honors_prompt_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured.update(kwargs)
        return "answer", None

    monkeypatch.setattr(answer_generation, "chat_completion", _fake_completion)

    answer_generation.generate_answer(
        question="Hi",
        context=None,
        temperature=0.7,
        system_prompt="be terse",
    )

    assert captured["system_prompt"] == "be terse"
    assert captured["temperature"] == 0.7


# --------------------------------------------------------------------------- #
# Module hygiene
# --------------------------------------------------------------------------- #


def test_source_selector_has_no_orm_getattr() -> None:
    from app.services import source_selector

    source = inspect.getsource(source_selector)

    assert "getattr(" not in source

