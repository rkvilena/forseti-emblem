from typing import Any, Dict, List, Tuple

from .models import Chapter, ChapterChunk


def build_chapter_records(pageid: int, title: str, chapter: Dict[str, Any]) -> Tuple[Chapter, List[ChapterChunk]]:
    infobox = chapter.get("infobox") or {}
    infobox_title = infobox.get("title")
    fields = infobox.get("fields") or []

    field_map = {}
    for field in fields:
        label = field.get("label")
        value = field.get("value")
        if not label or value is None:
            continue
        field_map[label] = value

    game = field_map.get("Game")
    objective = field_map.get("Objective")

    units_allowed_value = field_map.get("Units Allowed")
    units_allowed = None
    if isinstance(units_allowed_value, str):
        try:
            units_allowed = int(units_allowed_value.split()[0])
        except ValueError:
            units_allowed = None
    elif isinstance(units_allowed_value, int):
        units_allowed = units_allowed_value

    units_gained = field_map.get("Units Gained") or field_map.get("units gained")
    boss = field_map.get("Boss") or field_map.get("boss name")

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

    chunks: List[ChapterChunk] = []
    chunk_index = 0

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

    sections = chapter.get("sections") or []
    for section in sections:
        title_value = section.get("title")
        lines = section.get("content") or []
        if not lines:
            continue
        for line in lines:
            text = line
            chunks.append(
                ChapterChunk(
                    section_title=title_value,
                    kind="section",
                    chunk_index=chunk_index,
                    text=text,
                )
            )
            chunk_index += 1

    return chapter_row, chunks
