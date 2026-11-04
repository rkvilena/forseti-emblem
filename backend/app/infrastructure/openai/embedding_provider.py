"""OpenAI-backed implementation of the ``EmbeddingProvider`` port.

Translates SDK/transport failures into the application exception vocabulary
(``ConfigurationError`` for missing setup, ``EmbeddingError`` for provider
failures) so callers never see raw provider errors.
"""

from __future__ import annotations

from ...domain.exceptions import ConfigurationError, EmbeddingError
from ...openai_service import create_embedding, create_embeddings_batch


class OpenAIEmbeddingProvider:
    """Adapt the flat ``openai_service`` helpers to the embedding port."""

    def embed(self, text: str) -> list[float]:
        try:
            return create_embedding(text)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        except Exception as exc:
            raise EmbeddingError("Embedding provider request failed") from exc

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            return create_embeddings_batch(texts)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        except Exception as exc:
            raise EmbeddingError("Embedding provider request failed") from exc
