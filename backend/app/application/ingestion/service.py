"""Chapter ingestion use case.

One operation, one transaction boundary. Fetching/parsing and embedding happen
outside the transaction; the service owns duplicate detection, the
insert-or-replace decision, and the single commit/rollback boundary. Both
``ingest`` and ``reingest`` share the same draft building, enrichment, and
persistence code, so a chapter can never be created one way and updated another.

Persistence mechanics live behind ``ChapterRepository``; this service decides
*when* to look up, save, or replace and what those operations mean.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from sqlalchemy.orm import Session

from ...chapter_ingest import build_chapter_records_from_wikitext
from ...domain.embedding_status import (
    EMBEDDING_STATUS_PENDING,
    EMBEDDING_STATUS_SEARCHABLE,
)
from ...domain.exceptions import (
    ApplicationError,
    ChapterNotFoundError,
    DuplicateChapterError,
    EmbeddingError,
)
from ...infrastructure.persistence.repository import ChapterRepository
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
        self._repository = ChapterRepository(db)
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
        return self._repository.save_new_chapter(draft)

    def reingest(
        self,
        *,
        pageid: int,
        title: str,
        chapter_data: dict[str, Any],
        generate_embeddings: bool = True,
    ) -> Chapter:
        """Replace an existing chapter's metadata and chunks, or insert it."""

        existing = self._repository.find_by_page_id(pageid)
        if existing is None:
            return self.ingest(
                pageid=pageid,
                title=title,
                chapter_data=chapter_data,
                generate_embeddings=generate_embeddings,
            )

        draft = build_chapter_records_from_wikitext(pageid, title, chapter_data)
        draft = self._enrich_draft(draft, generate_embeddings)
        return self._repository.replace_chapter_with_draft(existing.id, draft)

    def retry_embeddings(self, chapter_id: int) -> Chapter:
        """Generate embeddings for a stored chapter's missing chunks.

        Only chunks without an embedding are sent to the provider, so a chapter
        that failed or skipped embedding during ingestion can become searchable
        without being re-fetched or re-parsed. On provider failure the exception
        propagates and nothing is written, leaving the chapter ``pending``.
        """

        chapter = self._repository.find_by_id(chapter_id)
        if chapter is None:
            raise ChapterNotFoundError(f"Chapter {chapter_id} was not found")

        if not chapter.chunks:
            # Nothing to embed; an empty chapter stays pending.
            return chapter

        missing = [chunk for chunk in chapter.chunks if chunk.embedding is None]
        if not missing:
            if chapter.embedding_status != EMBEDDING_STATUS_SEARCHABLE:
                return self._repository.save_embeddings(
                    chapter,
                    {},
                    status=EMBEDDING_STATUS_SEARCHABLE,
                )
            return chapter

        embeddings = self._embed_batch_or_raise(missing)
        mapping = {
            chunk.id: embedding
            for chunk, embedding in zip(missing, embeddings)
            if chunk.id is not None
        }
        status = (
            EMBEDDING_STATUS_SEARCHABLE
            if self._all_embedded(chapter.chunks, mapping)
            else EMBEDDING_STATUS_PENDING
        )
        return self._repository.save_embeddings(chapter, mapping, status=status)

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

        chunks = [
            replace(chunk, embedding=embedding)
            for chunk, embedding in zip(draft.chunks, embeddings)
        ]
        status = (
            EMBEDDING_STATUS_SEARCHABLE
            if all(chunk.embedding is not None for chunk in chunks)
            else EMBEDDING_STATUS_PENDING
        )
        return replace(draft, chunks=chunks, embedding_status=status)

    @staticmethod
    def _all_embedded(
        chunks: list[ChapterChunk],
        newly_embedded: dict[int, list[float]],
    ) -> bool:
        """True when every chunk has an embedding (existing or freshly set)."""

        return all(
            chunk.embedding is not None or chunk.id in newly_embedded
            for chunk in chunks
        )

    def _embed_batch_or_raise(
        self,
        chunks: list[ChapterChunk],
    ) -> list[list[float]]:
        """Embed ``chunks`` via the provider, translating failures.

        Unlike the best-effort ingestion path, a retry must not silently succeed
        with missing embeddings, so provider errors propagate as application
        exceptions (``EmbeddingError``/``ConfigurationError``).
        """

        provider = self._resolve_embedding_provider()
        texts = [chunk.text for chunk in chunks]
        logger.info("Retrying embeddings for %d chunks...", len(chunks))
        try:
            embeddings = provider.embed_batch(texts)
        except ApplicationError:
            raise
        except Exception as exc:
            raise EmbeddingError("Embedding provider request failed") from exc

        logger.info("Generated %d embeddings", len(embeddings))
        return embeddings

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
    # Duplicate policy (the repository owns the lookup; this decides meaning)
    # ------------------------------------------------------------------ #

    def _ensure_not_duplicate(self, draft: ChapterDraft) -> None:
        lookup_title = draft.infobox_title or draft.title

        existing = self._repository.find_by_title_and_game(
            lookup_title,
            draft.game,
        )
        if existing is not None:
            raise DuplicateChapterError(
                f"Chapter '{lookup_title}' for game '{draft.game}' already exists",
                chapter_title=lookup_title,
                game=draft.game,
            )
