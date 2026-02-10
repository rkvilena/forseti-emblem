from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..chapter_ingest import DuplicateChapterError, ingest_chapter_to_db
from ..mediawiki_client import MediaWikiClient
from ..models import Chapter
from ..parsers import (
    extract_tables_as_json,
    extract_tables_as_markdown,
    parse_chapter_page,
    parse_chapter_wikitext,
)


client = MediaWikiClient()


def get_category_pages(
    category_name: str,
    limit: int,
    include_html: bool,
    as_markdown: bool,
    raw: bool,
) -> Dict:
    pages = client.fetch_pages_in_category(category_name=category_name, limit=limit)

    if raw:
        return {
            "category": category_name,
            "count": len(pages),
            "pages": pages,
        }

    results = []
    for page in pages:
        html = page["html"]
        chapter = parse_chapter_page(html)
        tables_json = extract_tables_as_json(html)
        tables_markdown = extract_tables_as_markdown(html) if as_markdown else None

        result_page = {
            "pageid": page["pageid"],
            "title": page["title"],
            "chapter": chapter,
            "tables_json": tables_json,
        }

        if tables_markdown is not None:
            result_page["tables_markdown"] = tables_markdown

        if include_html:
            result_page["html"] = html

        results.append(result_page)

    return {
        "category": category_name,
        "count": len(results),
        "pages": results,
    }


def get_single_page_html(
    title: str,
    include_html: bool,
    raw: bool,
) -> Dict:
    page = client.fetch_page_html(title=title)

    if raw:
        return page

    html = page["html"]
    chapter = parse_chapter_page(html)

    result = {
        "pageid": page["pageid"],
        "title": page["title"],
        "chapter": chapter,
    }

    if include_html:
        result["html"] = html

    return result


def get_single_page_wikitext(
    title: str,
    raw: bool,
) -> Dict:
    page = client.fetch_page_wikitext(title=title)

    if raw:
        return page

    wikitext = page["wikitext"]
    chapter = parse_chapter_wikitext(wikitext)

    return {
        "pageid": page["pageid"],
        "title": page["title"],
        "chapter": chapter,
    }


def ingest_chapter_from_wikitext(
    db: Session,
    title: str,
    generate_embeddings: bool = True,
) -> Dict[str, Any]:
    """
    Fetch a chapter from MediaWiki, parse it, and store in the database.

    Args:
        db: Database session
        title: Page title to fetch
        generate_embeddings: Whether to generate OpenAI embeddings

    Returns:
        Dict with ingestion results
    """
    # Fetch wikitext from MediaWiki
    page = client.fetch_page_wikitext(title=title)
    wikitext = page["wikitext"]
    pageid = page["pageid"]

    # Parse the wikitext
    chapter_data = parse_chapter_wikitext(wikitext)

    # Ingest into database
    try:
        chapter = ingest_chapter_to_db(
            db=db,
            pageid=pageid,
            title=page["title"],
            chapter_data=chapter_data,
            generate_embeddings=generate_embeddings,
        )
    except DuplicateChapterError as exc:
        detail: dict[str, Any] = {
            "message": str(exc),
            "chapter_title": exc.chapter_title,
            "game": exc.game,
        }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        ) from exc

    return {
        "status": "success",
        "pageid": pageid,
        "title": page["title"],
        "chapter_id": chapter.id,
        "chunks_count": len(chapter.chunks),
        "chapter_data": chapter_data,
    }


def _normalize_game_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = raw.strip()
    if text.startswith("[[") and text.endswith("]]") and len(text) > 4:
        return text[2:-2].strip()
    return text


def list_documented_chapters(db: Session) -> Dict[str, Any]:
    chapters = (
        db.query(Chapter)
        .order_by(Chapter.game.is_(None), Chapter.game, Chapter.id)
        .all()
    )

    groups: dict[str | None, list[Chapter]] = {}
    for chapter in chapters:
        key = _normalize_game_name(chapter.game)
        groups.setdefault(key, []).append(chapter)

    games: list[Dict[str, Any]] = []
    for game_name, game_chapters in groups.items():
        games.append(
            {
                "game": game_name,
                "chapters": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "infobox_title": c.infobox_title,
                        "game": _normalize_game_name(c.game),
                    }
                    for c in game_chapters
                ],
            }
        )

    return {"total_chapters": len(chapters), "games": games}
