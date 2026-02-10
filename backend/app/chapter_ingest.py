"""
Chapter ingestion module.

Functions to build database records from parsed wikitext data
and handle the full ingestion pipeline including embeddings.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from .models import Chapter, ChapterChunk
from .openai_service import create_embeddings_batch


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
) -> tuple[Chapter, list[ChapterChunk]]:
    """
    Build Chapter and ChapterChunk records from parsed wikitext data.

    Args:
        pageid: MediaWiki page ID
        title: Page title
        chapter_data: Parsed chapter data from parse_chapter_wikitext()

    Returns:
        Tuple of (Chapter record, list of ChapterChunk records)
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

    # Create Chapter record
    chapter_row = Chapter(
        pageid=pageid,
        title=title,
        infobox_title=infobox_title,
        game=game,
        objective=objective,
        units_allowed=units_allowed,
        units_gained=units_gained,
        boss=boss,
        raw_infobox=infobox,
    )

    chunks: list[ChapterChunk] = []
    chunk_index = 0

    # Add summary as first chunk if available
    summary = chapter_data.get("summary")
    if summary:
        chunks.append(
            ChapterChunk(
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
            ChapterChunk(
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
                ChapterChunk(
                    section_title=section_title,
                    kind="section",
                    chunk_index=chunk_index,
                    text=line,
                )
            )
            chunk_index += 1

    return chapter_row, chunks


def ingest_chapter_to_db(
    db: Session,
    pageid: int,
    title: str,
    chapter_data: dict[str, Any],
    generate_embeddings: bool = True,
) -> Chapter:
    """
    Ingest a chapter into the database.

    Creates or updates the Chapter and its ChapterChunks.
    Optionally generates embeddings for each chunk.

    Args:
        db: Database session
        pageid: MediaWiki page ID
        title: Page title
        chapter_data: Parsed chapter data
        generate_embeddings: Whether to generate OpenAI embeddings

    Returns:
        The created Chapter record
    """
    # Build records from parsed chapter data
    chapter_row, chunks = build_chapter_records_from_wikitext(
        pageid, title, chapter_data
    )

    # Prevent duplicate chapters based on parsed chapter title and game
    lookup_title = chapter_row.infobox_title or chapter_row.title

    query = db.query(Chapter).filter(Chapter.title == lookup_title)
    if chapter_row.game is not None:
        query = query.filter(Chapter.game == chapter_row.game)

    existing = query.first()
    if existing is not None:
        raise DuplicateChapterError(
            f"Chapter '{lookup_title}' for game '{chapter_row.game}' already exists",
            chapter_title=lookup_title,
            game=chapter_row.game,
        )

    # Generate embeddings if requested
    if generate_embeddings and chunks:
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        try:
            texts = [chunk.text for chunk in chunks]
            embeddings = create_embeddings_batch(texts)
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            logger.info(f"Generated {len(embeddings)} embeddings")
        except Exception as e:
            logger.warning(
                f"Failed to generate embeddings: {e}. Chunks will be stored without embeddings."
            )

    # Associate chunks with chapter
    for chunk in chunks:
        chunk.chapter = chapter_row

    # Add to database
    db.add(chapter_row)
    db.commit()
    db.refresh(chapter_row)

    logger.info(f"Ingested chapter: {title} with {len(chunks)} chunks")
    return chapter_row


# Keep old function for backward compatibility
def build_chapter_records(
    pageid: int,
    title: str,
    chapter: dict[str, Any],
) -> tuple[Chapter, list[ChapterChunk]]:
    """
    Legacy function - use build_chapter_records_from_wikitext instead.

    Kept for backward compatibility with HTML-parsed data.
    """
    return build_chapter_records_from_wikitext(pageid, title, chapter)
