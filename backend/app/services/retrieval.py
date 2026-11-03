"""Retrieval component of the RAG pipeline.

Owns query embedding and the pgvector similarity query, so callers never build
vector SQL directly. ``create_embedding`` stays inside this component so the use
case does not need to know how the query vector is produced.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, selectinload

from ..models import ChapterChunk
from ..openai_service import create_embedding


@dataclass(frozen=True)
class RetrievalOptions:
    """Inputs that shape a similarity search.

    ``similarity_threshold`` and ``chapter_filter`` are threaded through the
    pipeline now but stay ``None`` (unused) until Phase 9 turns them on, so call
    sites will not need reshaping later.
    """

    top_k: int = 8
    similarity_threshold: float | None = None
    chapter_filter: int | None = None


def retrieve_similar_chunks(
    db: Session,
    query: str,
    options: RetrievalOptions,
) -> list[ChapterChunk]:
    """Embed ``query`` and return the most similar chunks from Postgres."""

    query = query.strip()
    if not query:
        return []

    query_embedding = create_embedding(query)

    # cosine_distance() is provided by pgvector's SQLAlchemy integration.
    # Lower distance = more similar.
    return (
        db.query(ChapterChunk)
        .options(selectinload(ChapterChunk.chapter))
        .filter(ChapterChunk.embedding.isnot(None))
        .order_by(ChapterChunk.embedding.cosine_distance(query_embedding))
        .limit(options.top_k)
        .all()
    )


class Retriever:
    """Retrieve the most similar chapter chunks for a query."""

    def retrieve(
        self,
        db: Session,
        query: str,
        options: RetrievalOptions,
    ) -> list[ChapterChunk]:
        return retrieve_similar_chunks(db=db, query=query, options=options)
