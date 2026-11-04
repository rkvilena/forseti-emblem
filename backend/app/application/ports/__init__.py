"""Application-facing ports (interfaces) for external systems.

Ports are ``Protocol`` definitions that express *what* the application needs
from an external system (OpenAI, Redis, MediaWiki) without depending on the SDK
that provides it. Concrete adapters live under ``app.infrastructure``; the chat
use cases and RAG components depend on these ports instead of the SDKs.
"""

from .embeddings import EmbeddingProvider
from .llm import AnswerProvider
from .models import GeneratedAnswer, Usage
from .rate_limit import RateLimitStore
from .wiki import WikiClient

__all__ = [
    "AnswerProvider",
    "EmbeddingProvider",
    "GeneratedAnswer",
    "RateLimitStore",
    "Usage",
    "WikiClient",
]
