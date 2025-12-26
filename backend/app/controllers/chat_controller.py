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

    return {
        "response": result,
        "model": settings.openai_chat_model,
        "usage": usage,
    }
