"""Port for reading pages and category members from an external wiki."""

from __future__ import annotations

from typing import Any, Protocol


class WikiClient(Protocol):
    """Read chapter content from an external wiki."""

    def fetch_page_wikitext(self, title: str) -> dict[str, Any]:
        """Return the wikitext payload for a page title."""

        ...

    def fetch_page_html(self, title: str) -> dict[str, Any]:
        """Return the parsed-HTML payload for a page title."""

        ...

    def fetch_category_members(
        self, category_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return the members of a category."""

        ...

    def fetch_pages_in_category(
        self, category_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return parsed pages for a category."""

        ...
