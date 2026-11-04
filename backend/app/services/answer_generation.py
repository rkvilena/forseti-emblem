"""Answer generation component of the RAG pipeline.

Wraps the ``AnswerProvider`` port so the chat use cases depend on a single
generation seam instead of the OpenAI SDK. Choosing the default system prompt is
an application decision, so it lives here rather than in the provider adapter.
"""

from __future__ import annotations

from ..application.ports.llm import AnswerProvider
from ..application.ports.models import GeneratedAnswer


# Default system prompt for Fire Emblem RAG
FIRE_EMBLEM_SYSTEM_PROMPT = """You are an expert assistant for Fire Emblem games.
You have access to detailed information about game chapters, including objectives,
available units, bosses, and strategies.

When answering questions:
1. Use the provided context to give accurate, specific answers.
2. If the context doesn't contain enough information, say so.
3. Reference specific chapter names and game titles when relevant.
4. Be helpful and concise in your responses.

Formatting rules:
- Always respond in GitHub-flavored Markdown.
- Use headings, bullet lists, and numbered steps when they improve clarity.
- Use fenced code blocks for code examples.

If you don't know something or the context doesn't provide the answer,
be honest about it rather than making up information."""


class AnswerGenerator:
    """Generate an answer from a question and (optional) prompt context."""

    def __init__(self, provider: AnswerProvider | None = None) -> None:
        if provider is None:
            from ..infrastructure.openai import OpenAIAnswerProvider

            provider = OpenAIAnswerProvider()
        self._provider = provider

    def generate(
        self,
        *,
        question: str,
        context: str | None,
        temperature: float,
        system_prompt: str | None = None,
    ) -> GeneratedAnswer:
        return self._provider.answer(
            question=question,
            context=context,
            system_prompt=system_prompt or FIRE_EMBLEM_SYSTEM_PROMPT,
            temperature=temperature,
        )


def generate_answer(
    *,
    question: str,
    context: str | None,
    temperature: float,
    system_prompt: str | None = None,
) -> GeneratedAnswer:
    """Generate an answer for ``question``, optionally grounded in ``context``."""

    return AnswerGenerator().generate(
        question=question,
        context=context,
        temperature=temperature,
        system_prompt=system_prompt,
    )
