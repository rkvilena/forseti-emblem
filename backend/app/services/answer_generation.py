"""Answer generation component of the RAG pipeline.

Wraps the existing OpenAI chat completion call so the chat use cases depend on a
single generation seam. This phase keeps it a thin wrapper around
``openai_service.chat_completion``; Phase 5 replaces the SDK-facing call with an
``AnswerProvider`` port.
"""

from __future__ import annotations

from ..openai_service import FIRE_EMBLEM_SYSTEM_PROMPT, chat_completion


def generate_answer(
    *,
    question: str,
    context: str | None,
    temperature: float,
    system_prompt: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Generate an answer for ``question``, optionally grounded in ``context``."""

    return chat_completion(
        system_prompt=system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
        user_message=question,
        context=context,
        temperature=temperature,
    )


class AnswerGenerator:
    """Generate an answer from a question and (optional) prompt context."""

    def generate(
        self,
        *,
        question: str,
        context: str | None,
        temperature: float,
        system_prompt: str | None = None,
    ) -> tuple[str, dict[str, int] | None]:
        return generate_answer(
            question=question,
            context=context,
            temperature=temperature,
            system_prompt=system_prompt,
        )
