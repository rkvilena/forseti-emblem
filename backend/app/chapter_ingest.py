"""
Chapter record building.

Pure transforms that turn parsed wikitext into draft value objects
(``ChapterDraft``/``ChunkDraft``). They perform no database queries, no OpenAI
calls, and no commits; persistence and transaction handling live in the
ingestion use case (``app.application.ingestion.service``).
"""

import logging
from typing import Any

from .application.ingestion.models import ChapterDraft, ChunkDraft


logger = logging.getLogger(__name__)


class DuplicateChapterError(Exception):
    """Raised when an equivalent chapter already exists in the database."""

    def __init__(self, message: str, chapter_title: str | None, game: str | None):
        super().__init__(message)
        self.chapter_title = chapter_title
        self.game = game


def build_chapter_records_from_wikitext(
    pageid: int,
    title: str,
    chapter_data: dict[str, Any],
) -> ChapterDraft:
    """
    Build a ChapterDraft from parsed wikitext data.

    Pure transform: no database access, no OpenAI calls, no commit.

    Args:
        pageid: MediaWiki page ID
        title: Page title
        chapter_data: Parsed chapter data from parse_chapter_wikitext()

    Returns:
        A ChapterDraft describing the chapter and its chunks
    """
    infobox = chapter_data.get("infobox") or {}
    infobox_title = infobox.get("title")
    fields = infobox.get("fields") or []

    # Build field map for easy access
    field_map: dict[str, str] = {}
    for field in fields:
        label = field.get("label")
        value = field.get("value")
        if not label or value is None:
            continue
        field_map[label] = value

    # Extract known fields
    game = field_map.get("Game")
    objective = field_map.get("Objective")

    # Parse units allowed (may be a string like "12 units")
    units_allowed_value = field_map.get("Units Allowed")
    units_allowed = None
    if isinstance(units_allowed_value, str):
        try:
            units_allowed = int(units_allowed_value.split()[0])
        except (ValueError, IndexError):
            units_allowed = None
    elif isinstance(units_allowed_value, int):
        units_allowed = units_allowed_value

    units_gained = field_map.get("Units Gained") or field_map.get("units gained")
    boss = field_map.get("Boss") or field_map.get("boss name")

    url_title = title.replace(" ", "_")
    source_url = f"https://fireemblem.fandom.com/wiki/{url_title}"

    chunks: list[ChunkDraft] = []
    chunk_index = 0

    # Add summary as first chunk if available
    summary = chapter_data.get("summary")
    if summary:
        chunks.append(
            ChunkDraft(
                section_title=None,
                kind="summary",
                chunk_index=chunk_index,
                text=summary,
            )
        )
        chunk_index += 1

    # Create chunks from infobox fields
    for key, value in field_map.items():
        text = f"{key}: {value}"
        chunks.append(
            ChunkDraft(
                section_title=None,
                kind="infobox",
                chunk_index=chunk_index,
                text=text,
            )
        )
        chunk_index += 1

    # Create chunks from sections
    sections = chapter_data.get("sections") or []
    for section in sections:
        section_title = section.get("title")
        lines = section.get("content") or []
        if not lines:
            continue
        for line in lines:
            chunks.append(
                ChunkDraft(
                    section_title=section_title,
                    kind="section",
                    chunk_index=chunk_index,
                    text=line,
                )
            )
            chunk_index += 1

    return ChapterDraft(
        pageid=pageid,
        title=title,
        infobox_title=infobox_title,
        game=game,
        objective=objective,
        units_allowed=units_allowed,
        units_gained=units_gained,
        boss=boss,
        source_url=source_url,
        raw_infobox=infobox,
        chunks=chunks,
    )


# Kept for backward compatibility; returns a ChapterDraft like the function above.
def build_chapter_records(
    pageid: int,
    title: str,
    chapter: dict[str, Any],
) -> ChapterDraft:
    """
    Legacy function - use build_chapter_records_from_wikitext instead.

    Kept for backward compatibility with HTML-parsed data.
    """
    return build_chapter_records_from_wikitext(pageid, title, chapter)
