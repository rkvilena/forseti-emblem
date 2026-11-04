"""Route tests for the embedding-retry endpoint (Phase 9, item 5).

A throwaway FastAPI app exposes only the wiki router with the registered
exception handlers, and its database dependency is overridden with an in-memory
SQLite session, so no Postgres, Redis, or OpenAI is required. The embedding
provider is replaced with an in-memory fake.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.exception_handlers import register_exception_handlers
from app.application.ingestion.service import ChapterIngestionService
from app.db import Base, get_db
from app.domain.embedding_status import (
    EMBEDDING_STATUS_PENDING,
    EMBEDDING_STATUS_SEARCHABLE,
)
from app.routes import wiki

from fakes import FakeEmbeddingProvider


EMBEDDING = [0.1] * 1536

_CHAPTER_DATA = {
    "infobox": {
        "title": "Prologue: A Beginning",
        "fields": [{"label": "Game", "value": "Fire Emblem"}],
    },
    "summary": "A short summary.",
    "sections": [{"title": "Overview", "content": ["line one", "line two"]}],
}


class _BrokenEmbeddingProvider:
    """An embedding provider that always fails."""

    def embed(self, text: str) -> list[float]:
        raise RuntimeError("no embeddings")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("no embeddings")


@pytest.fixture
def app_and_session() -> Iterator[tuple[TestClient, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)

    def _override_get_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(wiki.router)
    app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client, testing_session
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _seed_pending_chapter(testing_session: sessionmaker[Session]) -> int:
    db = testing_session()
    try:
        chapter = ChapterIngestionService(db).ingest(
            pageid=42,
            title="Prologue",
            chapter_data=_CHAPTER_DATA,
            generate_embeddings=False,
        )
        assert chapter.embedding_status == EMBEDDING_STATUS_PENDING
        return chapter.id
    finally:
        db.close()


def test_retry_route_returns_searchable(
    app_and_session: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, testing_session = app_and_session
    chapter_id = _seed_pending_chapter(testing_session)
    monkeypatch.setattr(
        "app.infrastructure.openai.OpenAIEmbeddingProvider",
        lambda: FakeEmbeddingProvider(vector=EMBEDDING),
    )

    response = client.post(f"/chapters/{chapter_id}/embeddings/retry")

    assert response.status_code == 200
    body = response.json()
    assert body["chapter_id"] == chapter_id
    assert body["embedding_status"] == EMBEDDING_STATUS_SEARCHABLE
    assert body["chunks_count"] > 0


def test_retry_route_missing_chapter_returns_404(
    app_and_session: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = app_and_session

    response = client.post("/chapters/9999/embeddings/retry")

    assert response.status_code == 404


def test_retry_route_provider_failure_returns_503(
    app_and_session: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, testing_session = app_and_session
    chapter_id = _seed_pending_chapter(testing_session)
    monkeypatch.setattr(
        "app.infrastructure.openai.OpenAIEmbeddingProvider",
        lambda: _BrokenEmbeddingProvider(),
    )

    response = client.post(f"/chapters/{chapter_id}/embeddings/retry")

    assert response.status_code == 503
