"""OpenAI-backed implementation of the ``EmbeddingProvider`` port."""

from __future__ import annotations

from ...openai_service import create_embedding, create_embeddings_batch


class OpenAIEmbeddingProvider:
    """Adapt the flat ``openai_service`` helpers to the embedding port."""

    def embed(self, text: str) -> list[float]:
        return create_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return create_embeddings_batch(texts)
