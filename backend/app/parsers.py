from typing import Any, Dict, List

import mwparserfromhell
from bs4 import BeautifulSoup, Tag
import re


def parse_chapter_page(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_="mw-parser-output") or soup

    infobox = {}
    aside = root.find("aside")
    if aside:
        infobox = _parse_infobox(aside)

    sections = _parse_sections(root)

    return {
        "infobox": infobox,
        "sections": sections,
    }


def _parse_infobox(aside: Tag) -> Dict[str, Any]:
    title_tag = aside.find(class_="pi-title") or aside.find("h2") or aside.find("h1")
    title = title_tag.get_text(" ", strip=True) if title_tag else None

    image_tag = aside.find("img")
    image = None
    if image_tag:
        image = {
            "src": image_tag.get("src"),
            "alt": image_tag.get("alt"),
        }

    fields: List[Dict[str, Any]] = []
    for data in aside.select(".pi-data"):
        label_tag = data.select_one(".pi-data-label")
        value_tag = data.select_one(".pi-data-value")

        label = label_tag.get_text(" ", strip=True) if label_tag else None
        value_text = (
            value_tag.get_text(" ", strip=True)
            if value_tag
            else data.get_text(" ", strip=True)
        )

        group_title = None
        group = data.find_parent(class_="pi-group")
        if group:
            header = group.find(class_="pi-header") or group.find(["h2", "h3"])
            if header:
                group_title = header.get_text(" ", strip=True)

        fields.append(
            {
                "label": label,
                "value": value_text,
                "group": group_title,
            }
        )

    return {
        "title": title,
        "image": image,
        "fields": fields,
    }


def _parse_sections(root: Tag) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    current_section: Dict[str, Any] | None = None

    for child in root.children:
        if not isinstance(child, Tag):
            continue

        if child.name in ("h2", "h3", "h4"):
            title = child.get_text(" ", strip=True)
            if not title:
                continue
            current_section = {
                "title": title,
                "content": [],
            }
            sections.append(current_section)
            continue

        if current_section is None:
            continue

        if child.name == "p":
            text = child.get_text(" ", strip=True)
            if text:
                current_section["content"].append(text)
        elif child.name in ("ul", "ol"):
            for li in child.find_all("li", recursive=False):
                li_text = li.get_text(" ", strip=True)
                if li_text:
                    current_section["content"].append(li_text)

    return sections


def extract_tables_as_json(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    result: List[Dict[str, Any]] = []

    for table in tables:
        headers: List[str] = []
        header_row = table.find("tr")

        if header_row:
            for th in header_row.find_all(["th", "td"]):
                header_text = th.get_text(strip=True)
                headers.append(header_text)

        rows_data: List[Dict[str, Any]] = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue

            row_values: Dict[str, Any] = {}
            for index, cell in enumerate(cells):
                key = headers[index] if index < len(headers) else f"col_{index}"
                row_values[key] = cell.get_text(strip=True)

            rows_data.append(row_values)

        if rows_data:
            caption_tag = table.find("caption")
            caption = caption_tag.get_text(strip=True) if caption_tag else None

            table_data: Dict[str, Any] = {
                "caption": caption,
                "headers": headers,
                "rows": rows_data,
            }
            result.append(table_data)

    return result


def extract_tables_as_markdown(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    markdown_tables: List[str] = []

    for table in tables:
        header_row = table.find("tr")
        headers: List[str] = []

        if header_row:
            for th in header_row.find_all(["th", "td"]):
                header_text = th.get_text(strip=True)
                headers.append(header_text or " ")

        if not headers:
            continue

        header_line = "|" + "|".join(headers) + "|"
        separator_line = "|" + "|".join("---" for _ in headers) + "|"

        body_lines: List[str] = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue
            values: List[str] = []
            for index, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                values.append(text or " ")
            while len(values) < len(headers):
                values.append(" ")
            body_line = "|" + "|".join(values[: len(headers)]) + "|"
            body_lines.append(body_line)

        if body_lines:
            markdown_table = "\n".join([header_line, separator_line, *body_lines])
            markdown_tables.append(markdown_table)

    return markdown_tables


def parse_chapter_wikitext(wikitext: str) -> Dict[str, Any]:
    infobox = _parse_wikitext_infobox(wikitext)
    sections = _parse_wikitext_sections(wikitext)
    return {
        "summary": _parse_wikitext_summary(wikitext),
        "infobox": infobox,
        "sections": sections,
    }


def _extract_chapterinfobox_block(wikitext: str) -> str | None:
    marker = "{{Chapterinfobox"
    start = wikitext.find(marker)
    if start == -1:
        return None
    i = start
    depth = 0
    length = len(wikitext)
    while i < length - 1:
        pair = wikitext[i : i + 2]
        if pair == "{{":
            depth += 1
            i += 2
            continue
        if pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[start:i]
            continue
        i += 1
    return None


def _parse_wikitext_infobox(wikitext: str) -> Dict[str, Any]:
    block = _extract_chapterinfobox_block(wikitext)
    if not block:
        return {}

    text = block.strip()
    if text.startswith("{{"):
        text = text[2:]
    if text.lower().startswith("chapterinfobox".lower()):
        text = text[len("chapterinfobox") :]

    lines = text.splitlines()
    params: Dict[str, str] = {}
    current_name: str | None = None
    current_value_lines: List[str] = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("|"):
            if current_name is not None:
                params[current_name] = "\n".join(current_value_lines).strip()
            body = stripped[1:]
            if "=" in body:
                name, value = body.split("=", 1)
                current_name = name.strip().lower()
                current_value_lines = [value.strip()]
            else:
                current_name = body.strip().lower()
                current_value_lines = []
        else:
            if current_name is not None:
                current_value_lines.append(stripped)

    if current_name is not None:
        params[current_name] = "\n".join(current_value_lines).strip()

    title = params.get("title")

    label_map = {
        "game": "Game",
        "objective": "Objective",
        "number of allowed units": "Units Allowed",
        "units gained": "Units Gained",
        "boss name": "Boss",
    }

    fields: List[Dict[str, Any]] = []
    for raw_name, raw_value in params.items():
        label = label_map.get(raw_name, raw_name.replace("_", " ").strip().title())
        fields.append(
            {
                "label": label,
                "value": raw_value,
                "group": None,
            }
        )

    return {
        "title": title,
        "image": None,
        "fields": fields,
    }


def _strip_templates_from_section(text: str) -> str:
    code = mwparserfromhell.parse(text)
    return code.strip_code().strip()


def _parse_wikitext_sections(wikitext: str) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    heading_re = re.compile(r"^==+\s*(.+?)\s*==+\s*$", re.MULTILINE)
    matches = list(heading_re.finditer(wikitext))
    if not matches:
        return sections

    for index, match in enumerate(matches):
        title = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(wikitext)
        body = wikitext[start:end]

        lines: List[str] = []
        for raw_line in body.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("{{") and stripped.endswith("}}"):
                continue
            cleaned = _strip_templates_from_section(stripped)
            if not cleaned:
                continue
            lines.append(cleaned)

        if lines:
            sections.append(
                {
                    "title": title,
                    "content": lines,
                }
            )

    return sections


def _parse_wikitext_summary(wikitext: str) -> str | None:
    marker = "{{Chapterinfobox"
    start = wikitext.find(marker)
    if start == -1:
        return None

    i = start
    depth = 0
    length = len(wikitext)
    while i < length - 1:
        pair = wikitext[i : i + 2]
        if pair == "{{":
            depth += 1
            i += 2
            continue
        if pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                break
            continue
        i += 1

    end_infobox = i
    if end_infobox >= length:
        return None

    after = wikitext[end_infobox:]
    after = after.lstrip()

    while after.lstrip().startswith("{{"):
        local = after.lstrip()
        idx = after.find("{{")
        if idx == -1:
            break
        j = idx
        d = 0
        n = len(after)
        while j < n - 1:
            p = after[j : j + 2]
            if p == "{{":
                d += 1
                j += 2
                continue
            if p == "}}":
                d -= 1
                j += 2
                if d == 0:
                    break
                continue
            j += 1
        after = after[j:].lstrip()

    heading_match = re.search(r"^==+", after, re.MULTILINE)
    if heading_match:
        segment = after[: heading_match.start()]
    else:
        segment = after

    for line in segment.splitlines():
        if "'''" not in line:
            continue
        cleaned = _strip_templates_from_section(line)
        if cleaned:
            return cleaned

    return None
