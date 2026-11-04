"""Port for generating an answer from a question and optional context."""

from __future__ import annotations

from typing import Protocol

from .models import GeneratedAnswer


class AnswerProvider(Protocol):
    """Generate an answer for ``question``, optionally grounded in ``context``."""

    def answer(
        self,
        *,
        question: str,
        context: str | None,
        system_prompt: str,
        temperature: float,
    ) -> GeneratedAnswer:
        """Return the generated answer, its model name, and token usage."""

        ...
