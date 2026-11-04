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

    * ``max_chars`` – maximum number of characters to emit.  The default of
      12_000 is higher than the historic 8_000 to give a little more headroom
      for broad questions, but still keeps the request bounded.
    * ``max_chunks`` – a defensive upper bound on the number of chunks
      that may be added.  The default of 16 is intentionally larger than the
      current ``RAG_TOP_K_MAX`` of 8 so it does not interfere with Phase 8
      behaviour, but can be overridden in tests.
    * ``reserved_prompt_tokens`` – left unused for now.  It is a future‑proof
      field for token‑aware budgeting; when ``None`` the builder behaves
      character‑based only.
    """

    max_chars: int = 12_000
    max_chunks: int | None = 16
    reserved_prompt_tokens: int | None = None


def build_context_from_chunks(
    chunks: Iterable[ChapterChunk],
    budget: ContextBudget | None = None,
) -> str:
    """Render ``chunks`` into a single bounded context string.

    The algorithm iterates over chunks in retrieval order and builds a
    formatted block for each.  The block is appended as long as it fits
    within ``budget.max_chars`` and the optional ``max_chunks`` limit.

    *If a chunk would overflow* the budget, the builder attempts to
    truncate the **chunk text** (keeping the header intact) so that the
    remaining budget is used.  If the remaining space is insufficient for
    a meaningful fragment (see ``MIN_TEXT_CHARS``), the chunk is skipped
    entirely and construction stops.
    """

    if budget is None:
        budget = ContextBudget()

    # Constants
    SEPARATOR = "\n\n"
    MIN_TEXT_CHARS = 100  # guard against an overly tiny fragment

    parts: list[str] = []
    used = 0
    included_chunks = 0

    for chunk in chunks:
        # Respect optional chunk limit
        if budget.max_chunks is not None and included_chunks >= budget.max_chunks:
            break

        chapter = chunk.chapter
        chapter_title = chapter.title or "(unknown chapter)"
        section = chunk.section_title or ""

        # Build metadata header
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

        # Estimate space needed if we add a separator after this block
        needed = len(block) + (len(SEPARATOR) if parts else 0)

        if used + needed <= budget.max_chars:
            parts.append(block)
            used += needed
            included_chunks += 1
            continue

        # Block does not fit; try truncation of the text portion
        remaining = budget.max_chars - used
        if remaining < len(header) + 1:  # header plus newline
            # Not enough room even for the header – stop
            break

        available_text = remaining - len(header) - 1 
        if available_text < MIN_TEXT_CHARS:
            # Not enough space for a meaningful fragment – stop
            break

        # Truncate chunk text to fit
        truncated_text = chunk.text[:available_text].rstrip()
        marker = "[…chunk truncated…]"
        if len(marker) + 1 > available_text:
            # Reduce marker size; keep it minimal
            marker = "[…]"
            if len(marker) + 1 > available_text:
                break

        truncated_block = f"{header}\n{truncated_text}{marker}"
        parts.append(truncated_block)
        used += len(truncated_block) + (len(SEPARATOR) if len(parts) > 1 else 0)
        included_chunks += 1
        break

    return SEPARATOR.join(parts)


class ContextBuilder:
    """Build the bounded prompt context from retrieved chunks."""

    def build(
        self,
        chunks: Iterable[ChapterChunk],
        budget: ContextBudget | None = None,
    ) -> str:
        return build_context_from_chunks(chunks, budget=budget)
