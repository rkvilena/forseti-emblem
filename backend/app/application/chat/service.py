"""Chat application services (use cases).

Each service owns one complete business operation -- answering a plain chat
question or answering a retrieval-augmented question -- including the ordering
of retrieval, context construction, answer generation, and result assembly.

The services read in business terms and import no FastAPI HTTP types
(``Request``/``Response``/``HTTPException``); translating failures into HTTP
responses is the route's job. For this phase the services still depend on the
flat ``rag_service``/``openai_service`` helpers; provider ports and repositories
arrive in later phases.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ...config import settings
from ...openai_service import FIRE_EMBLEM_SYSTEM_PROMPT, chat_completion
from ...rag_service import build_context_from_chunks, retrieve_similar_chunks
from .commands import PlainChatCommand, RagChatCommand
from .results import ChatResult, SourceReference, Usage


def _to_usage(raw: dict[str, int] | None) -> Usage | None:
    """Convert the provider usage mapping into the typed application ``Usage``."""

    if raw is None:
        return None

    return Usage(
        prompt_tokens=raw.get("prompt_tokens"),
        completion_tokens=raw.get("completion_tokens"),
        total_tokens=raw.get("total_tokens"),
    )


class PlainChatService:
    """Use case: answer a chat question without retrieval."""

    def execute(self, command: PlainChatCommand) -> ChatResult:
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


class RagChatService:
    """Use case: answer a chat question augmented with retrieved chunks."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, command: RagChatCommand) -> ChatResult:
        chunks = retrieve_similar_chunks(
            db=self._db, query=command.message, top_k=command.top_k
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
