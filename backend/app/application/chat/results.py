"""Application-facing result types for the chat flows.

Named, immutable outputs of the chat application layer. The HTTP layer maps
these to ``app.schemas.chat`` response models; keeping the two separate lets the
internal and public contracts evolve independently.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ports.models import Usage

__all__ = ["ChatResult", "SourceReference", "Usage"]


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
