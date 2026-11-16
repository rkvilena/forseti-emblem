"""Route tests for the documented-chapters listing endpoint.

A throwaway FastAPI app exposes only the wiki router with the registered
exception handlers, and its database dependency is overridden with an in-memory
SQLite session, so no Postgres, Redis, or OpenAI is required.
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
from app.db import Base, get_db
from app.models import Chapter
from app.routes import wiki


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


def _seed_chapter(
    testing_session: sessionmaker[Session],
    *,
    pageid: int,
    title: str,
    source_url: str | None,
) -> int:
    db = testing_session()
    try:
        chapter = Chapter(
            pageid=pageid,
            title=title,
            game="Fire Emblem",
            source_url=source_url,
            raw_infobox={},
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter.id
    finally:
        db.close()


def _chapters_by_title(body: dict) -> dict[str, dict]:
    return {
        chapter["title"]: chapter
        for group in body["games"]
        for chapter in group["chapters"]
    }


def test_chapters_route_returns_source_url(
    app_and_session: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = app_and_session
    source_url = "https://fireemblem.fandom.com/wiki/Prologue"
    _seed_chapter(
        testing_session,
        pageid=1,
        title="Prologue",
        source_url=source_url,
    )

    response = client.get("/chapters")

    assert response.status_code == 200
    chapters = _chapters_by_title(response.json())
    assert chapters["Prologue"]["source_url"] == source_url


def test_chapters_route_returns_null_source_url_when_missing(
    app_and_session: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, testing_session = app_and_session
    _seed_chapter(
        testing_session,
        pageid=2,
        title="Chapter 1",
        source_url=None,
    )

    response = client.get("/chapters")

    assert response.status_code == 200
    chapters = _chapters_by_title(response.json())
    assert chapters["Chapter 1"]["source_url"] is None
