"""MediaWiki-backed implementation of the ``WikiClient`` port."""

from __future__ import annotations

from typing import Any

from ...mediawiki_client import MediaWikiClient


class MediaWikiWikiClient:
    """Adapt ``MediaWikiClient`` to the application-facing wiki port."""

    def __init__(self, client: MediaWikiClient | None = None) -> None:
        self._client = client or MediaWikiClient()

    def fetch_page_wikitext(self, title: str) -> dict[str, Any]:
        return self._client.fetch_page_wikitext(title)

    def fetch_page_html(self, title: str) -> dict[str, Any]:
        return self._client.fetch_page_html(title)

    def fetch_category_members(
        self, category_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._client.fetch_category_members(category_name, limit)

    def fetch_pages_in_category(
        self, category_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self._client.fetch_pages_in_category(category_name, limit)
