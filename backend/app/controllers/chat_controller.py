"""Chat orchestration.

Builds the answer for a chat command and returns a typed
:class:`~app.application.chat.results.ChatResult`. The HTTP concerns (request
binding, response mapping, status codes) live in ``app.routes.chat``; this
module knows nothing about FastAPI or ``app.schemas``.
"""

from sqlalchemy.orm import Session

from ..application.chat.commands import PlainChatCommand, RagChatCommand
from ..application.chat.results import ChatResult, SourceReference, Usage
from ..config import settings
from ..openai_service import FIRE_EMBLEM_SYSTEM_PROMPT, chat_completion
from ..rag_service import build_context_from_chunks, retrieve_similar_chunks


def _to_usage(raw: dict[str, int] | None) -> Usage | None:
    """Convert the provider usage mapping into the typed application ``Usage``."""

    if raw is None:
        return None

    return Usage(
        prompt_tokens=raw.get("prompt_tokens"),
        completion_tokens=raw.get("completion_tokens"),
        total_tokens=raw.get("total_tokens"),
    )


def chat_plain(command: PlainChatCommand) -> ChatResult:
    result, usage = chat_completion(
        system_prompt=command.system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
        user_message=command.message,
        context=command.context,
        temperature=command.temperature,
    )

    return ChatResult(
        response=result,
        model=settings.openai_chat_model,
        usage=_to_usage(usage),
    )


def chat_rag(db: Session, command: RagChatCommand) -> ChatResult:
    chunks = retrieve_similar_chunks(
        db=db, query=command.message, top_k=command.top_k
    )

    if not chunks:
        return ChatResult(
            response="Not found in provided context.",
            model=settings.openai_chat_model,
            usage=None,
        )

    context = build_context_from_chunks(chunks)

    result, usage = chat_completion(
        system_prompt=command.system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
        user_message=command.message,
        context=context,
        temperature=command.temperature,
    )

    sources: list[SourceReference] = []
    seen_chapter_ids: set[int] = set()

    for chunk in chunks:
        chapter = getattr(chunk, "chapter", None)
        if chapter is None:
            continue

        chapter_id = getattr(chapter, "id", None)
        if chapter_id is None or chapter_id in seen_chapter_ids:
            continue

        seen_chapter_ids.add(chapter_id)

        sources.append(
            SourceReference(
                title=getattr(chapter, "title", ""),
                infobox_title=getattr(chapter, "infobox_title", None),
                game=getattr(chapter, "game", None),
                pageid=getattr(chapter, "pageid", 0),
                source_url=getattr(chapter, "source_url", None),
            )
        )

    message_lower = command.message.lower()

    filtered_sources: list[SourceReference] = []
    for source in sources:
        match = False
        for value in (source.infobox_title, source.title):
            if isinstance(value, str) and value and value.lower() in message_lower:
                match = True
                break

        if not match:
            if isinstance(source.game, str) and source.game:
                cleaned_game = source.game.strip("[]")
                if cleaned_game.lower() in message_lower:
                    match = True

        if match:
            filtered_sources.append(source)

    return ChatResult(
        response=result,
        model=settings.openai_chat_model,
        usage=_to_usage(usage),
        sources=filtered_sources or None,
    )
