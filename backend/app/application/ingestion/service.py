"""Chapter ingestion use case.

One operation, one transaction boundary. Fetching/parsing and embedding happen
outside the transaction; the service owns duplicate detection, the
insert-or-replace decision, and the single commit/rollback boundary. Both
``ingest`` and ``reingest`` share the same draft building, enrichment, and
persistence code, so a chapter can never be created one way and updated another.

Repositories are intentionally deferred to a later phase; the service talks to
the SQLAlchemy ``Session`` directly.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from sqlalchemy.orm import Session

from ...chapter_ingest import DuplicateChapterError, build_chapter_records_from_wikitext
from ...models import Chapter, ChapterChunk
from ..ports.embeddings import EmbeddingProvider
from .models import ChapterDraft, ChunkDraft


logger = logging.getLogger(__name__)


class ChapterIngestionService:
    """Persist a parsed chapter and its chunks in a single transaction."""

    def __init__(
        self,
        db: Session,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._db = db
        self._embedding_provider = embedding_provider

    def ingest(
        self,
        *,
        pageid: int,
        title: str,
        chapter_data: dict[str, Any],
        generate_embeddings: bool = True,
    ) -> Chapter:
        """Insert a new chapter, refusing an equivalent (title + game) one."""

        draft = build_chapter_records_from_wikitext(pageid, title, chapter_data)
        # Check duplicates before embedding so a rejected ingest costs no calls.
        self._ensure_not_duplicate(draft)
        draft = self._enrich_draft(draft, generate_embeddings)
        return self._persist_new(draft)

    def reingest(
        self,
        *,
        pageid: int,
        title: str,
        chapter_data: dict[str, Any],
        generate_embeddings: bool = True,
    ) -> Chapter:
        """Replace an existing chapter's metadata and chunks, or insert it."""

        existing = self._find_by_pageid(pageid)
        if existing is None:
            return self.ingest(
                pageid=pageid,
                title=title,
                chapter_data=chapter_data,
                generate_embeddings=generate_embeddings,
            )

        draft = build_chapter_records_from_wikitext(pageid, title, chapter_data)
        draft = self._enrich_draft(draft, generate_embeddings)
        return self._persist_replace(existing, draft)

    # ------------------------------------------------------------------ #
    # Draft building / enrichment (outside the transaction)
    # ------------------------------------------------------------------ #

    def _enrich_draft(
        self,
        draft: ChapterDraft,
        generate_embeddings: bool,
    ) -> ChapterDraft:
        if not generate_embeddings or not draft.chunks:
            return draft

        embeddings = self._embed_chunks(draft.chunks)
        if embeddings is None:
            return draft

        return replace(
            draft,
            chunks=[
                replace(chunk, embedding=embedding)
                for chunk, embedding in zip(draft.chunks, embeddings)
            ],
        )

    def _embed_chunks(self, chunks: list[ChunkDraft]) -> list[list[float]] | None:
        """Return one embedding per chunk, or ``None`` if the provider failed."""

        provider = self._resolve_embedding_provider()
        texts = [chunk.text for chunk in chunks]
        logger.info("Generating embeddings for %d chunks...", len(chunks))
        try:
            embeddings = provider.embed_batch(texts)
        except Exception as exc:
            # Embedding is best-effort: degrade to un-embedded chunks.
            logger.warning(
                "Failed to generate embeddings: %s. "
                "Chunks will be stored without embeddings.",
                exc,
            )
            return None

        logger.info("Generated %d embeddings", len(embeddings))
        return embeddings

    def _resolve_embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is not None:
            return self._embedding_provider

        from ...infrastructure.openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider()

    # ------------------------------------------------------------------ #
    # Persistence (inside the transaction)
    # ------------------------------------------------------------------ #

    def _ensure_not_duplicate(self, draft: ChapterDraft) -> None:
        lookup_title = draft.infobox_title or draft.title

        query = self._db.query(Chapter).filter(Chapter.title == lookup_title)
        if draft.game is not None:
            query = query.filter(Chapter.game == draft.game)

        if query.first() is not None:
            raise DuplicateChapterError(
                f"Chapter '{lookup_title}' for game '{draft.game}' already exists",
                chapter_title=lookup_title,
                game=draft.game,
            )

    def _find_by_pageid(self, pageid: int) -> Chapter | None:
        return self._db.query(Chapter).filter(Chapter.pageid == pageid).first()

    def _persist_new(self, draft: ChapterDraft) -> Chapter:
        chapter = _to_chapter(draft)
        for chunk in _to_chunks(draft):
            chunk.chapter = chapter

        return self._commit(
            chapter,
            f"Ingested chapter: {draft.title} with {len(draft.chunks)} chunks",
        )

    def _persist_replace(self, existing: Chapter, draft: ChapterDraft) -> Chapter:
        # Replacing through the relationship lets the delete-orphan cascade remove
        # the old chunks in the same transaction as the new inserts. Flushing
        # after the clear sends the deletes first, so the (chapter, kind, index)
        # unique constraint does not collide with the replacements.
        existing.chunks.clear()
        self._db.flush()
        _apply_draft(existing, draft)
        existing.chunks.extend(_to_chunks(draft))

        return self._commit(
            existing,
            f"Reingested chapter: {draft.title} with {len(draft.chunks)} chunks",
        )

    def _commit(self, chapter: Chapter, message: str) -> Chapter:
        try:
            self._db.add(chapter)
            self._db.commit()
            self._db.refresh(chapter)
        except Exception:
            self._db.rollback()
            raise

        logger.info(message)
        return chapter


def _to_chapter(draft: ChapterDraft) -> Chapter:
    return Chapter(
        pageid=draft.pageid,
        title=draft.title,
        infobox_title=draft.infobox_title,
        game=draft.game,
        objective=draft.objective,
        units_allowed=draft.units_allowed,
        units_gained=draft.units_gained,
        boss=draft.boss,
        source_url=draft.source_url,
        raw_infobox=draft.raw_infobox,
    )


def _to_chunks(draft: ChapterDraft) -> list[ChapterChunk]:
    return [
        ChapterChunk(
            section_title=chunk.section_title,
            kind=chunk.kind,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            embedding=chunk.embedding,
        )
        for chunk in draft.chunks
    ]


def _apply_draft(chapter: Chapter, draft: ChapterDraft) -> None:
    chapter.title = draft.title
    chapter.infobox_title = draft.infobox_title
    chapter.game = draft.game
    chapter.objective = draft.objective
    chapter.units_allowed = draft.units_allowed
    chapter.units_gained = draft.units_gained
    chapter.boss = draft.boss
    chapter.raw_infobox = draft.raw_infobox
    chapter.source_url = draft.source_url
