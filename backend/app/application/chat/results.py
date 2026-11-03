"""Application-facing result types for the chat flows.

Named, immutable outputs of the chat application layer. The HTTP layer maps
these to ``app.schemas.chat`` response models; keeping the two separate lets the
internal and public contracts evolve independently.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    """Token usage reported by the model provider."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class SourceReference:
    """A chapter cited as the source of a retrieval-augmented answer."""

    title: str
    infobox_title: str | None
    game: str | None
    pageid: int
    source_url: str | None


@dataclass(frozen=True)
class ChatResult:
    """The outcome of answering a chat question."""

    response: str
    model: str
    usage: Usage | None = None
    sources: list[SourceReference] | None = None
