"""Source selector component of the RAG pipeline.

Turns retrieved chunks into the public ``SourceReference`` list: one entry per
chapter, deduplicated, and filtered down to the chapters the question actually
mentions (title, infobox title, or game).
"""

from __future__ import annotations

from collections.abc import Iterable

from ..application.chat.results import SourceReference
from ..models import ChapterChunk


def select_sources(
    chunks: Iterable[ChapterChunk],
    question: str,
) -> list[SourceReference]:
    """Collapse chunks into per-chapter references referenced by ``question``."""

    sources: list[SourceReference] = []
    seen_chapter_ids: set[int] = set()

    for chunk in chunks:
        chapter = chunk.chapter
        chapter_id = chapter.id
        if chapter_id in seen_chapter_ids:
            continue

        seen_chapter_ids.add(chapter_id)

        sources.append(
            SourceReference(
                title=chapter.title,
                infobox_title=chapter.infobox_title,
                game=chapter.game,
                pageid=chapter.pageid,
                source_url=chapter.source_url,
            )
        )

    message_lower = question.lower()

    filtered_sources: list[SourceReference] = []
    for source in sources:
        match = False
        for value in (source.infobox_title, source.title):
            if isinstance(value, str) and value and value.lower() in message_lower:
                match = True
                break

        if not match:
            if isinstance(source.game, str) and source.game:
                cleaned_game = source.game.strip("[]")
                if cleaned_game.lower() in message_lower:
                    match = True

        if match:
            filtered_sources.append(source)

    return filtered_sources


class SourceSelector:
    """Select the public source references for a retrieval-augmented answer."""

    def select(
        self,
        chunks: Iterable[ChapterChunk],
        question: str,
    ) -> list[SourceReference]:
        return select_sources(chunks, question)
