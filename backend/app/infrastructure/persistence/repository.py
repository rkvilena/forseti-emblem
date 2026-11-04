"""SQLAlchemy repositories for the chapter aggregate (Phase 7).

A chapter and its chunks are one aggregate: they are read, written, and replaced
together, so a single aggregate-oriented repository owns their persistence. This
module is the only place that builds SQLAlchemy queries for chapters/chunks,
which keeps ORM mechanics out of the use cases and pipeline components.

The repository exposes domain-meaningful operations only. There is deliberately
no ``get_all`` / ``save_anything`` / ``query``; each method names the domain
operation it performs. The SQLAlchemy ``Session`` is injected by the caller
rather than created here, so the caller keeps ownership of the connection.

Decision (Phase 7, step 3): ``list_documented_chapters`` returns the ordered ORM
rows; the grouping by game and the ``_normalize_game_name`` presentation logic
stay in ``wiki_controller``. The repository only shapes the query.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, selectinload

from ...models import Chapter, ChapterChunk

if TYPE_CHECKING:
    from ...application.ingestion.models import ChapterDraft
    from ...services.retrieval import RetrievalOptions


logger = logging.getLogger(__name__)


class ChapterRepository:
    """Persistence and retrieval operations for the chapter aggregate."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    def find_by_page_id(self, pageid: int) -> Chapter | None:
        """Return the chapter with this MediaWiki page id, if any."""

        return self._db.query(Chapter).filter(Chapter.pageid == pageid).first()

    def find_by_id(self, chapter_id: int) -> Chapter | None:
        """Return the chapter with this primary key, if any."""

        return self._db.get(Chapter, chapter_id)

    def find_by_title_and_game(
        self,
        title: str,
        game: str | None,
    ) -> Chapter | None:
        """Return a chapter matching ``title`` (and ``game`` when given).

        When ``game`` is ``None`` the match is by title only, preserving the
        duplicate-detection semantics of the ingestion use case.
        """

        query = self._db.query(Chapter).filter(Chapter.title == title)
        if game is not None:
            query = query.filter(Chapter.game == game)
        return query.first()

    def list_documented_chapters(self) -> list[Chapter]:
        """Return every chapter, ordered by game (unknown last) then id."""

        return (
            self._db.query(Chapter)
            .order_by(Chapter.game.is_(None), Chapter.game, Chapter.id)
            .all()
        )

    def retrieve_similar_chunks(
        self,
        embedding: list[float],
        options: RetrievalOptions,
    ) -> list[ChapterChunk]:
        """Return the chunks closest to ``embedding`` by cosine distance.

        ``cosine_distance()`` is provided by pgvector's SQLAlchemy integration; a
        lower distance means more similar. Only chunks that actually carry an
        embedding are eligible, and each chunk's chapter is eager-loaded so the
        caller can read it without a follow-up query.
        """

        return (
            self._db.query(ChapterChunk)
            .options(selectinload(ChapterChunk.chapter))
            .filter(ChapterChunk.embedding.isnot(None))
            .order_by(ChapterChunk.embedding.cosine_distance(embedding))
            .limit(options.top_k)
            .all()
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def save_new_chapter(self, draft: ChapterDraft) -> Chapter:
        """Insert a new chapter and its chunks in one transaction."""

        chapter = _to_chapter(draft)
        for chunk in _to_chunks(draft):
            chunk.chapter = chapter

        return self._commit(
            chapter,
            f"Ingested chapter: {draft.title} with {len(draft.chunks)} chunks",
        )

    def replace_chapter_with_draft(
        self,
        existing_id: int,
        draft: ChapterDraft,
    ) -> Chapter:
        """Replace an existing chapter's fields and chunks in one transaction."""

        chapter = self._db.get(Chapter, existing_id)
        if chapter is None:
            raise LookupError(f"Chapter {existing_id} no longer exists")

        # Replacing through the relationship lets the delete-orphan cascade
        # remove the old chunks in the same transaction as the new inserts.
        # Flushing after the clear sends the deletes first, so the
        # (chapter, kind, index) unique constraint does not collide with the
        # replacements.
        chapter.chunks.clear()
        self._db.flush()
        _apply_draft(chapter, draft)
        chapter.chunks.extend(_to_chunks(draft))

        return self._commit(
            chapter,
            f"Reingested chapter: {draft.title} with {len(draft.chunks)} chunks",
        )

    def save_embeddings(
        self,
        chapter: Chapter,
        embeddings_by_chunk_id: dict[int, list[float]],
        *,
        status: str,
    ) -> Chapter:
        """Persist newly generated embeddings for a chapter and set its status.

        Only chunks present in ``embeddings_by_chunk_id`` are updated, so a retry
        that fills in missing embeddings never rewrites vectors that already
        exist. The caller decides the resulting ``status`` (business meaning);
        this method owns only the write and the commit/rollback boundary.
        """

        for chunk in chapter.chunks:
            embedding = embeddings_by_chunk_id.get(chunk.id)
            if embedding is not None:
                chunk.embedding = embedding
        chapter.embedding_status = status

        return self._commit(
            chapter,
            f"Updated embeddings for chapter {chapter.id} (status={status})",
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
        embedding_status=draft.embedding_status,
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
    chapter.embedding_status = draft.embedding_status
