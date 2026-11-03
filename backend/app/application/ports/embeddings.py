"""Port for turning text into embedding vectors."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Create embedding vectors for text via an external provider."""

    def embed(self, text: str) -> list[float]:
        """Return the embedding vector for a single piece of text."""

        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for several texts in one call."""

        ...
