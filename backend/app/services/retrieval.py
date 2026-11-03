"""Retrieval component of the RAG pipeline.

Owns query embedding (through the ``EmbeddingProvider`` port) and delegates the
pgvector similarity query to the chapter repository, so callers never build
vector SQL directly and the use case does not need to know how the query vector
is produced or how chunks are fetched.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..application.ports.embeddings import EmbeddingProvider
from ..infrastructure.persistence.repository import ChapterRepository
from ..models import ChapterChunk


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


class Retriever:
    """Retrieve the most similar chapter chunks for a query."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        if embedding_provider is None:
            from ..infrastructure.openai import OpenAIEmbeddingProvider

            embedding_provider = OpenAIEmbeddingProvider()
        self._embedding_provider = embedding_provider

    def retrieve(
        self,
        db: Session,
        query: str,
        options: RetrievalOptions,
    ) -> list[ChapterChunk]:
        query = query.strip()
        if not query:
            return []

        query_embedding = self._embedding_provider.embed(query)

        return ChapterRepository(db).retrieve_similar_chunks(
            query_embedding,
            options,
        )


def retrieve_similar_chunks(
    db: Session,
    query: str,
    options: RetrievalOptions,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[ChapterChunk]:
    """Embed ``query`` and return the most similar chunks from Postgres."""

    return Retriever(embedding_provider).retrieve(db=db, query=query, options=options)
