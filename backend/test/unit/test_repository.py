"""Unit tests for the chapter repository (Phase 7).

The persistence methods run against an in-memory SQLite database, so no live
Postgres is required. The vector query is exercised through a fake session
(pgvector's ``cosine_distance`` is not available on SQLite), verifying the
``top_k`` limit is applied by ``retrieve_similar_chunks``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ingestion.models import ChapterDraft, ChunkDraft
from app.db import Base
from app.infrastructure.persistence.repository import ChapterRepository
from app.models import Chapter, ChapterChunk
from app.services.retrieval import RetrievalOptions


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _draft(**overrides: Any) -> ChapterDraft:
    data: dict[str, Any] = {
        "pageid": 42,
        "title": "Prologue",
        "infobox_title": "Prologue: A Beginning",
        "game": "Fire Emblem",
        "objective": "Seize the gate",
        "units_allowed": 12,
        "units_gained": "2",
        "boss": "Brigand",
        "source_url": "https://example.test/Prologue",
        "raw_infobox": {"title": "Prologue: A Beginning"},
        "chunks": [
            ChunkDraft(
                text="line one",
                kind="section",
                section_title="Overview",
                chunk_index=0,
            ),
            ChunkDraft(
                text="line two",
                kind="section",
                section_title="Overview",
                chunk_index=1,
            ),
        ],
    }
    data.update(overrides)
    return ChapterDraft(**data)


# --------------------------------------------------------------------------- #
# find_by_page_id / find_by_title_and_game
# --------------------------------------------------------------------------- #


def test_find_by_page_id_returns_chapter_or_none(db: Session) -> None:
    repo = ChapterRepository(db)
    repo.save_new_chapter(_draft(pageid=7))

    found = repo.find_by_page_id(7)
    assert found is not None
    assert found.pageid == 7
    assert repo.find_by_page_id(999) is None


def test_find_by_title_and_game_filters_by_game(db: Session) -> None:
    repo = ChapterRepository(db)
    repo.save_new_chapter(
        _draft(pageid=1, title="Chapter 1", infobox_title=None, game="Fire Emblem")
    )

    assert repo.find_by_title_and_game("Chapter 1", "Fire Emblem") is not None
    assert repo.find_by_title_and_game("Chapter 1", "Other Game") is None
    assert repo.find_by_title_and_game("Chapter 1", None) is not None
    assert repo.find_by_title_and_game("Missing", None) is None


# --------------------------------------------------------------------------- #
# list_documented_chapters
# --------------------------------------------------------------------------- #


def test_list_documented_chapters_orders_unknown_game_last(db: Session) -> None:
    repo = ChapterRepository(db)
    repo.save_new_chapter(
        _draft(pageid=1, title="B", infobox_title=None, game="Game B")
    )
    repo.save_new_chapter(
        _draft(pageid=2, title="A", infobox_title=None, game="Game A")
    )
    repo.save_new_chapter(_draft(pageid=3, title="U", infobox_title=None, game=None))

    titles = [chapter.title for chapter in repo.list_documented_chapters()]

    assert titles == ["A", "B", "U"]


# --------------------------------------------------------------------------- #
# save_new_chapter
# --------------------------------------------------------------------------- #


def test_save_new_chapter_persists_chapter_and_chunks(db: Session) -> None:
    chapter = ChapterRepository(db).save_new_chapter(_draft())

    assert chapter.id is not None
    assert chapter.pageid == 42
    assert chapter.boss == "Brigand"
    assert len(chapter.chunks) == 2
    assert db.query(Chapter).count() == 1
    assert db.query(ChapterChunk).count() == 2


def test_save_new_chapter_rolls_back_on_commit_failure(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rolled_back: list[str] = []
    real_rollback = db.rollback

    def _boom() -> None:
        raise RuntimeError("commit failed")

    def _rollback() -> None:
        rolled_back.append("rollback")
        real_rollback()

    monkeypatch.setattr(db, "commit", _boom)
    monkeypatch.setattr(db, "rollback", _rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        ChapterRepository(db).save_new_chapter(_draft())

    assert rolled_back == ["rollback"]
    assert db.query(Chapter).count() == 0
    assert db.query(ChapterChunk).count() == 0


# --------------------------------------------------------------------------- #
# replace_chapter_with_draft
# --------------------------------------------------------------------------- #


def test_replace_chapter_with_draft_replaces_chunks_and_fields(db: Session) -> None:
    repo = ChapterRepository(db)
    original = repo.save_new_chapter(_draft())
    original_id = original.id

    updated = _draft(
        boss="New Boss",
        chunks=[
            ChunkDraft(
                text="only line",
                kind="section",
                section_title="Overview",
                chunk_index=0,
            )
        ],
    )
    result = repo.replace_chapter_with_draft(original_id, updated)

    assert result.id == original_id
    assert result.boss == "New Boss"
    assert len(result.chunks) == 1
    assert db.query(Chapter).count() == 1
    assert db.query(ChapterChunk).count() == 1


def test_replace_chapter_with_missing_id_raises(db: Session) -> None:
    with pytest.raises(LookupError):
        ChapterRepository(db).replace_chapter_with_draft(12345, _draft())


# --------------------------------------------------------------------------- #
# retrieve_similar_chunks (query construction)
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


class _FakeSession:
    def __init__(self, limits: list[int], results: list[Any]) -> None:
        self._limits = limits
        self._results = results

    def query(self, model: Any) -> _FakeQuery:
        return _FakeQuery(self._limits, self._results)


def test_retrieve_similar_chunks_applies_top_k_limit() -> None:
    limits: list[int] = []
    db = _FakeSession(limits, results=["chunk"])

    result = ChapterRepository(db).retrieve_similar_chunks(  # type: ignore[arg-type]
        [0.1, 0.2, 0.3],
        RetrievalOptions(top_k=4),
    )

    assert result == ["chunk"]
    assert limits == [4]
