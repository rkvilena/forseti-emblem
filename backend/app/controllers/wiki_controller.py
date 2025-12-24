from typing import Dict

from ..mediawiki_client import MediaWikiClient
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
