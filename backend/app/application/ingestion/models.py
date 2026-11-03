"""Draft value objects produced by chapter record building.

A *draft* is the pure, framework-free description of a chapter and its chunks.
Building a draft has no database or network side effects: the parsed wikitext is
translated into plain data, embeddings are attached later, and only the ingestion
use case turns a draft into persisted ORM rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChunkDraft:
    """One chunk of a chapter before it is persisted."""

    text: str
    kind: str
    section_title: str | None
    chunk_index: int
    embedding: list[float] | None = None


@dataclass(frozen=True)
class ChapterDraft:
    """A chapter and its chunks before they are persisted."""

    pageid: int
    title: str
    infobox_title: str | None
    game: str | None
    objective: str | None
    units_allowed: int | None
    units_gained: str | None
    boss: str | None
    source_url: str | None
    raw_infobox: dict[str, Any]
    chunks: list[ChunkDraft]
