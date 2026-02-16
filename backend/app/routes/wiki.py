from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..controllers import wiki_controller
from ..db import get_db
from ..schemas.wiki import (
    ChapterListResponse,
    WikiCategoryPagesResponse,
    WikiIngestResponse,
    WikiPageHtmlResponse,
    WikiPageWikitextResponse,
)


router = APIRouter(tags=["chapters"])


@router.get("/wiki/category/{category_name}", response_model=WikiCategoryPagesResponse)
def get_category_pages(
    category_name: str,
    limit: int = Query(10, ge=1, le=100),
    include_html: bool = Query(False),
    as_markdown: bool = Query(False),
    raw: bool = Query(False),
) -> dict:
    return wiki_controller.get_category_pages(
        category_name=category_name,
        limit=limit,
        include_html=include_html,
        as_markdown=as_markdown,
        raw=raw,
    )


@router.get("/wiki/page/{title}", response_model=WikiPageHtmlResponse)
def get_single_page(
    title: str,
    include_html: bool = Query(False),
    raw: bool = Query(False),
) -> dict:
    return wiki_controller.get_single_page_html(
        title=title,
        include_html=include_html,
        raw=raw,
    )


@router.get("/wiki/page/{title}/wikitext", response_model=WikiPageWikitextResponse)
def get_page_wikitext(
    title: str,
    raw: bool = Query(False),
) -> dict:
    return wiki_controller.get_single_page_wikitext(
        title=title,
        raw=raw,
    )


@router.post("/wiki/page/{title}/ingest", response_model=WikiIngestResponse)
def ingest_chapter(
    title: str,
    generate_embeddings: bool = Query(
        True, description="Generate OpenAI embeddings for chunks"
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Fetch a chapter from MediaWiki, parse it, and store in the database.

    This endpoint:
    1. Fetches the wikitext for the given page title
    2. Parses the wikitext to extract chapter information
    3. Stores the chapter and its chunks in the database
    4. Optionally generates OpenAI embeddings for each chunk

    Args:
        title: The MediaWiki page title (e.g., "Prologue (Blazing Blade)")
        generate_embeddings: Whether to generate embeddings (requires OPENAI_API_KEY)

    Returns:
        Ingestion result with chapter_id and chunks_count
    """
    return wiki_controller.ingest_chapter_from_wikitext(
        db=db,
        title=title,
        generate_embeddings=generate_embeddings,
    )


@router.post("/wiki/page/{title}/reingest", response_model=WikiIngestResponse)
def reingest_chapter(
    title: str,
    generate_embeddings: bool = Query(
        True, description="Generate OpenAI embeddings for chunks"
    ),
    db: Session = Depends(get_db),
) -> dict:
    return wiki_controller.reingest_chapter_from_wikitext(
        db=db,
        title=title,
        generate_embeddings=generate_embeddings,
    )


@router.get("/chapters", response_model=ChapterListResponse)
def list_documented_chapters(db: Session = Depends(get_db)) -> ChapterListResponse:
    """Return all documented chapters grouped by game."""

    data = wiki_controller.list_documented_chapters(db=db)
    return ChapterListResponse.model_validate(data)
