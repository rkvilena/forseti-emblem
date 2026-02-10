from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WikiCategoryPageItem(BaseModel):
    """A single page entry returned from a category listing.

    Supports both `raw=true` (fields from MediaWiki client) and the parsed form.
    """

    model_config = ConfigDict(extra="allow")

    pageid: int | None = None
    title: str | None = None

    html: str | None = None
    chapter: Any | None = None

    tables_json: Any | None = Field(
        default=None, description="Extracted tables as JSON"
    )
    tables_markdown: str | None = Field(
        default=None, description="Extracted tables as Markdown"
    )


class WikiCategoryPagesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    category: str
    count: int
    pages: list[WikiCategoryPageItem]


class WikiPageHtmlResponse(BaseModel):
    """Response for `/wiki/page/{title}`.

    - `raw=true`: likely returns `pageid`, `title`, `html` (and possibly other fields)
    - otherwise: returns `pageid`, `title`, `chapter`, and optional `html` when `include_html=true`
    """

    model_config = ConfigDict(extra="allow")

    pageid: int | None = None
    title: str | None = None

    html: str | None = None
    chapter: Any | None = None


class WikiPageWikitextResponse(BaseModel):
    """Response for `/wiki/page/{title}/wikitext`.

    - `raw=true`: likely returns `pageid`, `title`, `wikitext` (and possibly other fields)
    - otherwise: returns `pageid`, `title`, `chapter`
    """

    model_config = ConfigDict(extra="allow")

    pageid: int | None = None
    title: str | None = None

    wikitext: str | None = None
    chapter: Any | None = None


class WikiIngestResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    pageid: int
    title: str
    chapter_id: int
    chunks_count: int
    chapter_data: Any


class ChapterSummary(BaseModel):
    """Lightweight representation of a stored chapter.

    Used for listing documented chapters grouped by game.
    """

    id: int
    title: str
    infobox_title: str | None = None
    game: str | None = None


class GameChaptersGroup(BaseModel):
    """Grouping of chapters for a single game (or unknown game)."""

    game: str | None = None
    chapters: list[ChapterSummary]


class ChapterListResponse(BaseModel):
    """Response model for documented chapters grouped by game."""

    total_chapters: int
    games: list[GameChaptersGroup]
