"""Context builder component of the RAG pipeline.

Formats retrieved chunks into a bounded prompt context string. The character
budget behavior is preserved exactly from the previous ``rag_service``
implementation; ``ContextBudget`` leaves room for token-aware budgeting later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..models import ChapterChunk


@dataclass(frozen=True)
class ContextBudget:
    """Bound on the prompt context the builder may emit.

    ``max_chunks`` is threaded through but stays ``None`` (unused) until a later
    phase enables chunk-count budgeting; ``max_chars`` preserves the previous
    8000-character default.
    """

    max_chars: int = 8000
    max_chunks: int | None = None


def build_context_from_chunks(
    chunks: Iterable[ChapterChunk],
    budget: ContextBudget | None = None,
) -> str:
    """Render ``chunks`` into a single bounded context string."""

    if budget is None:
        budget = ContextBudget()

    parts: list[str] = []
    used = 0

    for chunk in chunks:
        chapter = chunk.chapter
        chapter_title = chapter.title or "(unknown chapter)"
        section = chunk.section_title or ""

        meta_parts: list[str] = []
        if chapter.game:
            meta_parts.append(f"game={chapter.game}")
        if chapter.objective:
            meta_parts.append(f"objective={chapter.objective}")
        if chapter.units_gained:
            meta_parts.append(f"units_gained={chapter.units_gained}")
        if chapter.boss:
            meta_parts.append(f"boss={chapter.boss}")

        meta_line = (" | ".join(meta_parts)).strip()
        header = f"[Chapter: {chapter_title} | kind={chunk.kind} | section={section} | idx={chunk.chunk_index}]"
        if meta_line:
            header = f"{header}\n[Meta: {meta_line}]"

        block = f"{header}\n{chunk.text}".strip()

        # keep a little separator budget
        if used + len(block) + 2 > budget.max_chars:
            break

        parts.append(block)
        used += len(block) + 2

    return "\n\n".join(parts)


class ContextBuilder:
    """Build the bounded prompt context from retrieved chunks."""

    def build(
        self,
        chunks: Iterable[ChapterChunk],
        budget: ContextBudget | None = None,
    ) -> str:
        return build_context_from_chunks(chunks, budget=budget)
