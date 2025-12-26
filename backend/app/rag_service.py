"""RAG retrieval helpers.

Given a user query, embed it and retrieve the most similar ChapterChunks
from Postgres + pgvector.
"""

from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session, selectinload

from .models import ChapterChunk
from .openai_service import create_embedding


def retrieve_similar_chunks(
    db: Session,
    query: str,
    top_k: int = 8,
) -> list[ChapterChunk]:
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
        .limit(top_k)
        .all()
    )


def build_context_from_chunks(
    chunks: Iterable[ChapterChunk],
    max_chars: int = 8000,
) -> str:
    parts: list[str] = []
    used = 0

    for chunk in chunks:
        chapter = getattr(chunk, "chapter", None)
        chapter_title = getattr(chapter, "title", None) or "(unknown chapter)"
        section = chunk.section_title or ""

        meta_parts: list[str] = []
        if chapter is not None:
            game = getattr(chapter, "game", None)
            objective = getattr(chapter, "objective", None)
            units_gained = getattr(chapter, "units_gained", None)
            boss = getattr(chapter, "boss", None)
            if game:
                meta_parts.append(f"game={game}")
            if objective:
                meta_parts.append(f"objective={objective}")
            if units_gained:
                meta_parts.append(f"units_gained={units_gained}")
            if boss:
                meta_parts.append(f"boss={boss}")

        meta_line = (" | ".join(meta_parts)).strip()
        header = f"[Chapter: {chapter_title} | kind={chunk.kind} | section={section} | idx={chunk.chunk_index}]"
        if meta_line:
            header = f"{header}\n[Meta: {meta_line}]"

        block = f"{header}\n{chunk.text}".strip()

        # keep a little separator budget
        if used + len(block) + 2 > max_chars:
            break

        parts.append(block)
        used += len(block) + 2

    return "\n\n".join(parts)
