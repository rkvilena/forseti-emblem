from typing import Any, Dict, List

import requests


class MediaWikiClient:
    def __init__(
        self,
        api_url: str = "https://fireemblem.fandom.com/api.php",
        user_agent: str = "forsetiemblem-rag-backend/0.1",
    ) -> None:
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def fetch_category_members(self, category_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category_name}",
            "cmlimit": min(limit, 500),
        }

        members: List[Dict[str, Any]] = []
        cont: Dict[str, Any] | None = None

        while True:
            if cont:
                params.update(cont)

            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            batch = data.get("query", {}).get("categorymembers", [])
            members.extend(batch)

            if len(members) >= limit:
                return members[:limit]

            cont = data.get("continue")
            if not cont:
                break

        return members

    def fetch_page_html(self, title: str) -> Dict[str, Any]:
        params = {
            "action": "parse",
            "format": "json",
            "page": title,
            "prop": "text",
            "formatversion": "2",
        }

        response = self.session.get(self.api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        parsed = data.get("parse", {})
        html = parsed.get("text", "")

        return {
            "pageid": parsed.get("pageid"),
            "title": parsed.get("title", title),
            "html": html,
        }

    def fetch_page_wikitext(self, title: str) -> Dict[str, Any]:
        params = {
            "action": "parse",
            "format": "json",
            "page": title,
            "prop": "wikitext",
            "formatversion": "2",
        }

        response = self.session.get(self.api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        parsed = data.get("parse", {})
        wikitext = parsed.get("wikitext", "")

        return {
            "pageid": parsed.get("pageid"),
            "title": parsed.get("title", title),
            "wikitext": wikitext,
        }

    def fetch_pages_in_category(self, category_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        members = self.fetch_category_members(category_name=category_name, limit=limit)

        pages: List[Dict[str, Any]] = []
        for member in members:
            title = member.get("title")
            if not title:
                continue
            page = self.fetch_page_html(title=title)
            page["pageid"] = member.get("pageid", page.get("pageid"))
            pages.append(page)

        return pages
