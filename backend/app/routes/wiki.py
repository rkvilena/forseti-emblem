from fastapi import APIRouter, Query

from ..controllers import wiki_controller


router = APIRouter()


@router.get("/wiki/category/{category_name}")
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


@router.get("/wiki/page/{title}")
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


@router.get("/wiki/page/{title}/wikitext")
def get_page_wikitext(
    title: str,
    raw: bool = Query(False),
) -> dict:
    return wiki_controller.get_single_page_wikitext(
        title=title,
        raw=raw,
    )
