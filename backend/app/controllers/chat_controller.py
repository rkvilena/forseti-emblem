from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..openai_service import FIRE_EMBLEM_SYSTEM_PROMPT, chat_completion
from ..rag_service import build_context_from_chunks, retrieve_similar_chunks


def chat_plain(
    message: str,
    system_prompt: str | None,
    context: str | None,
    temperature: float,
) -> dict[str, Any]:
    result, usage = chat_completion(
        system_prompt=system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
        user_message=message,
        context=context,
        temperature=temperature,
    )

    return {
        "response": result,
        "model": settings.openai_chat_model,
        "usage": usage,
    }


def chat_rag(
    db: Session,
    message: str,
    top_k: int,
    temperature: float,
    system_prompt: str | None,
) -> dict[str, Any]:
    chunks = retrieve_similar_chunks(db=db, query=message, top_k=top_k)

    if not chunks:
        return {
            "response": "Not found in provided context.",
            "model": settings.openai_chat_model,
            "usage": None,
        }

    context = build_context_from_chunks(chunks)

    result, usage = chat_completion(
        system_prompt=system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
        user_message=message,
        context=context,
        temperature=temperature,
    )

    sources = []
    seen_chapter_ids = set()

    for chunk in chunks:
        chapter = getattr(chunk, "chapter", None)
        if chapter is None:
            continue

        chapter_id = getattr(chapter, "id", None)
        if chapter_id is None or chapter_id in seen_chapter_ids:
            continue

        seen_chapter_ids.add(chapter_id)

        sources.append(
            {
                "title": getattr(chapter, "title", ""),
                "infobox_title": getattr(chapter, "infobox_title", None),
                "game": getattr(chapter, "game", None),
                "pageid": getattr(chapter, "pageid", 0),
                "source_url": getattr(chapter, "source_url", None),
            }
        )

    message_lower = message.lower()

    filtered_sources = []
    for source in sources:
        match = False
        for key in ("infobox_title", "title"):
            value = source.get(key)
            if isinstance(value, str) and value and value.lower() in message_lower:
                match = True
                break

        if not match:
            game = source.get("game")
            if isinstance(game, str) and game:
                cleaned_game = game.strip("[]")
                if cleaned_game.lower() in message_lower:
                    match = True

        if match:
            filtered_sources.append(source)

    sources_to_return = filtered_sources

    return {
        "response": result,
        "model": settings.openai_chat_model,
        "usage": usage,
        "sources": sources_to_return or None,
    }
