"""Unit tests for the ingestion use case (Phase 6).

The use case runs against an in-memory SQLite database, so no live Postgres or
OpenAI is required; embedding is supplied by an in-memory fake. These tests
cover draft building, insert, duplicate detection, reingest replacement, the
embedding-failure degradation path, and rollback on a failed commit.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ingestion.models import ChapterDraft
from app.application.ingestion.service import ChapterIngestionService
from app.chapter_ingest import build_chapter_records_from_wikitext
from app.db import Base
from app.domain.embedding_status import (
    EMBEDDING_STATUS_PENDING,
    EMBEDDING_STATUS_SEARCHABLE,
)
from app.domain.exceptions import (
    ChapterNotFoundError,
    DuplicateChapterError,
    EmbeddingError,
)
from app.models import Chapter, ChapterChunk

from fakes import FakeEmbeddingProvider


EMBEDDING = [0.1] * 1536


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _chapter_data(
    *,
    infobox_title: str = "Prologue: A Beginning",
    game: str = "Fire Emblem",
    boss: str = "Brigand",
    sections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "infobox": {
            "title": infobox_title,
            "fields": [
                {"label": "Game", "value": game},
                {"label": "Objective", "value": "Seize the gate"},
                {"label": "Units Allowed", "value": "12 units"},
                {"label": "Units Gained", "value": "2"},
                {"label": "Boss", "value": boss},
            ],
        },
        "summary": "A short summary.",
        "sections": (
            sections
            if sections is not None
            else [{"title": "Overview", "content": ["line one", "line two"]}]
        ),
    }


class _BrokenEmbeddingProvider:
    """An embedding provider that always fails."""

    def embed(self, text: str) -> list[float]:
        raise RuntimeError("no embeddings")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("no embeddings")


# --------------------------------------------------------------------------- #
# Pure draft building
# --------------------------------------------------------------------------- #


def test_build_chapter_records_returns_pure_draft() -> None:
    draft = build_chapter_records_from_wikitext(42, "Prologue", _chapter_data())

    assert isinstance(draft, ChapterDraft)
    assert draft.pageid == 42
    assert draft.title == "Prologue"
    assert draft.infobox_title == "Prologue: A Beginning"
    assert draft.game == "Fire Emblem"
    assert draft.objective == "Seize the gate"
    assert draft.units_allowed == 12
    assert draft.units_gained == "2"
    assert draft.boss == "Brigand"
    assert draft.source_url == "https://fireemblem.fandom.com/wiki/Prologue"
    assert [chunk.kind for chunk in draft.chunks] == [
        "summary",
        "infobox",
        "infobox",
        "infobox",
        "infobox",
        "infobox",
        "section",
        "section",
    ]
    assert [chunk.chunk_index for chunk in draft.chunks] == list(range(8))
    assert all(chunk.embedding is None for chunk in draft.chunks)


# --------------------------------------------------------------------------- #
# Insert / duplicate
# --------------------------------------------------------------------------- #


def test_ingest_inserts_chapter_and_chunks(db: Session) -> None:
    chapter = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )

    assert chapter.id is not None
    assert chapter.pageid == 42
    assert chapter.title == "Prologue"
    assert len(chapter.chunks) == 8
    assert db.query(Chapter).count() == 1
    assert db.query(ChapterChunk).count() == 8


def test_ingest_rejects_duplicate_title_and_game(db: Session) -> None:
    # The duplicate key is the parsed (infobox) title + game, so the page title
    # is set to match the infobox title for the collision to occur.
    title = "Prologue: A Beginning"
    ChapterIngestionService(db).ingest(
        pageid=1,
        title=title,
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )

    with pytest.raises(DuplicateChapterError) as excinfo:
        ChapterIngestionService(db).ingest(
            pageid=2,
            title=title,
            chapter_data=_chapter_data(),
            generate_embeddings=False,
        )

    assert excinfo.value.chapter_title == "Prologue: A Beginning"
    assert excinfo.value.game == "Fire Emblem"
    assert db.query(Chapter).count() == 1


# --------------------------------------------------------------------------- #
# Reingest replacement
# --------------------------------------------------------------------------- #


def test_reingest_replaces_chunks_and_updates_metadata(db: Session) -> None:
    original = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )
    original_id = original.id

    updated = _chapter_data(
        boss="New Boss",
        sections=[{"title": "Overview", "content": ["only one line"]}],
    )
    result = ChapterIngestionService(db).reingest(
        pageid=42,
        title="Prologue",
        chapter_data=updated,
        generate_embeddings=False,
    )

    assert result.id == original_id
    assert result.boss == "New Boss"
    assert len(result.chunks) == 7
    assert db.query(Chapter).count() == 1
    assert db.query(ChapterChunk).count() == 7


def test_reingest_without_existing_inserts(db: Session) -> None:
    chapter = ChapterIngestionService(db).reingest(
        pageid=7,
        title="New Chapter",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )

    assert chapter.id is not None
    assert chapter.pageid == 7
    assert db.query(Chapter).count() == 1
    assert db.query(ChapterChunk).count() == 8


# --------------------------------------------------------------------------- #
# Embedding enrichment
# --------------------------------------------------------------------------- #


def test_embeddings_are_persisted_when_provider_succeeds(db: Session) -> None:
    provider = FakeEmbeddingProvider(vector=EMBEDDING)

    chapter = ChapterIngestionService(db, embedding_provider=provider).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )

    assert provider.embedded_batches
    assert len(provider.embedded_batches[0]) == len(chapter.chunks)
    assert chapter.chunks
    assert all(chunk.embedding is not None for chunk in chapter.chunks)


def test_embedding_failure_still_persists_chunks_without_embeddings(
    db: Session,
) -> None:
    chapter = ChapterIngestionService(
        db, embedding_provider=_BrokenEmbeddingProvider()
    ).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )

    assert chapter.id is not None
    assert chapter.chunks
    assert all(chunk.embedding is None for chunk in chapter.chunks)
    assert db.query(ChapterChunk).count() == 8


# --------------------------------------------------------------------------- #
# Embedding status
# --------------------------------------------------------------------------- #


def test_ingest_without_embeddings_marks_pending(db: Session) -> None:
    chapter = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )

    assert chapter.embedding_status == EMBEDDING_STATUS_PENDING
    assert all(chunk.embedding is None for chunk in chapter.chunks)


def test_ingest_with_embeddings_marks_searchable(db: Session) -> None:
    provider = FakeEmbeddingProvider(vector=EMBEDDING)

    chapter = ChapterIngestionService(db, embedding_provider=provider).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )

    assert chapter.embedding_status == EMBEDDING_STATUS_SEARCHABLE
    assert all(chunk.embedding is not None for chunk in chapter.chunks)


def test_embedding_failure_marks_chapter_pending(db: Session) -> None:
    chapter = ChapterIngestionService(
        db, embedding_provider=_BrokenEmbeddingProvider()
    ).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )

    assert chapter.embedding_status == EMBEDDING_STATUS_PENDING
    assert all(chunk.embedding is None for chunk in chapter.chunks)


def test_reingest_without_embeddings_marks_pending(db: Session) -> None:
    provider = FakeEmbeddingProvider(vector=EMBEDDING)
    ChapterIngestionService(db, embedding_provider=provider).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )

    updated = ChapterIngestionService(db).reingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )

    assert updated.embedding_status == EMBEDDING_STATUS_PENDING
    assert all(chunk.embedding is None for chunk in updated.chunks)


# --------------------------------------------------------------------------- #
# Embedding retry
# --------------------------------------------------------------------------- #


def test_retry_embeddings_fills_missing_and_marks_searchable(db: Session) -> None:
    chapter = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )
    assert chapter.embedding_status == EMBEDDING_STATUS_PENDING

    provider = FakeEmbeddingProvider(vector=EMBEDDING)
    result = ChapterIngestionService(db, embedding_provider=provider).retry_embeddings(
        chapter.id
    )

    assert result.embedding_status == EMBEDDING_STATUS_SEARCHABLE
    assert all(chunk.embedding is not None for chunk in result.chunks)
    assert len(provider.embedded_batches[0]) == len(result.chunks)


def test_retry_embeddings_embeds_only_missing_chunks(db: Session) -> None:
    chapter = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )
    total = len(chapter.chunks)
    chapter.chunks[0].embedding = EMBEDDING
    db.commit()

    provider = FakeEmbeddingProvider(vector=EMBEDDING)
    result = ChapterIngestionService(db, embedding_provider=provider).retry_embeddings(
        chapter.id
    )

    assert len(provider.embedded_batches[0]) == total - 1
    assert result.embedding_status == EMBEDDING_STATUS_SEARCHABLE
    assert all(chunk.embedding is not None for chunk in result.chunks)


def test_retry_embeddings_when_searchable_is_idempotent(db: Session) -> None:
    provider = FakeEmbeddingProvider(vector=EMBEDDING)
    chapter = ChapterIngestionService(db, embedding_provider=provider).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=True,
    )
    assert chapter.embedding_status == EMBEDDING_STATUS_SEARCHABLE

    retry_provider = FakeEmbeddingProvider(vector=EMBEDDING)
    result = ChapterIngestionService(
        db, embedding_provider=retry_provider
    ).retry_embeddings(chapter.id)

    assert result.embedding_status == EMBEDDING_STATUS_SEARCHABLE
    assert retry_provider.embedded_batches == []
    assert db.query(Chapter).count() == 1


def test_retry_embeddings_provider_failure_raises_and_stays_pending(
    db: Session,
) -> None:
    chapter = ChapterIngestionService(db).ingest(
        pageid=42,
        title="Prologue",
        chapter_data=_chapter_data(),
        generate_embeddings=False,
    )
    chapter_id = chapter.id

    with pytest.raises(EmbeddingError):
        ChapterIngestionService(
            db, embedding_provider=_BrokenEmbeddingProvider()
        ).retry_embeddings(chapter_id)

    db.expire_all()
    stored = db.get(Chapter, chapter_id)
    assert stored is not None
    assert stored.embedding_status == EMBEDDING_STATUS_PENDING
    assert all(chunk.embedding is None for chunk in stored.chunks)


def test_retry_embeddings_missing_chapter_raises(db: Session) -> None:
    with pytest.raises(ChapterNotFoundError):
        ChapterIngestionService(db).retry_embeddings(12345)


# --------------------------------------------------------------------------- #
# Transaction boundary
# --------------------------------------------------------------------------- #


def test_persistence_failure_rolls_back(
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
        ChapterIngestionService(db).ingest(
            pageid=42,
            title="Prologue",
            chapter_data=_chapter_data(),
            generate_embeddings=False,
        )

    assert rolled_back == ["rollback"]
    assert db.query(Chapter).count() == 0
    assert db.query(ChapterChunk).count() == 0
