"""Application-facing command types for the chat flows.

These immutable value objects are the explicit *input* contract of the chat
application layer. They intentionally live outside ``app.schemas`` so the
application layer never depends on the HTTP boundary: routes translate
``schemas.chat`` requests into commands, and translate results back into
response schemas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlainChatCommand:
    """Input for the plain (non-retrieval) chat flow."""

    message: str
    system_prompt: str | None
    context: str | None
    temperature: float


@dataclass(frozen=True)
class RagChatCommand:
    """Input for the retrieval-augmented (RAG) chat flow."""

    message: str
    top_k: int
    temperature: float
    system_prompt: str | None
