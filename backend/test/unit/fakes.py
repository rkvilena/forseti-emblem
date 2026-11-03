"""In-memory fakes for the application ports (test support, not production).

These let the chat, retrieval, and ingestion flows run with no network and no
Redis, by implementing the ``EmbeddingProvider``, ``AnswerProvider``, and
``RateLimitStore`` ports in memory.
"""

from __future__ import annotations

from typing import Any

from app.application.ports.models import GeneratedAnswer, Usage


class FakeEmbeddingProvider:
    """Deterministic in-memory ``EmbeddingProvider`` that records its inputs."""

    def __init__(
        self,
        vector: list[float] | None = None,
        batch: list[list[float]] | None = None,
    ) -> None:
        self.vector = vector if vector is not None else [0.1, 0.2, 0.3]
        self.batch = batch
        self.embedded: list[str] = []
        self.embedded_batches: list[list[str]] = []

    def embed(self, text: str) -> list[float]:
        self.embedded.append(text)
        return self.vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.embedded_batches.append(list(texts))
        if self.batch is not None:
            return self.batch
        return [self.vector for _ in texts]


class FakeAnswerProvider:
    """In-memory ``AnswerProvider`` that returns a canned answer."""

    def __init__(
        self,
        text: str = "answer",
        model: str = "fake-model",
        usage: Usage | None = None,
    ) -> None:
        self.text = text
        self.model = model
        self.usage = usage
        self.calls: list[dict[str, Any]] = []

    def answer(
        self,
        *,
        question: str,
        context: str | None,
        system_prompt: str,
        temperature: float,
    ) -> GeneratedAnswer:
        self.calls.append(
            {
                "question": question,
                "context": context,
                "system_prompt": system_prompt,
                "temperature": temperature,
            }
        )
        return GeneratedAnswer(text=self.text, model=self.model, usage=self.usage)


class FakeRetriever:
    """In-memory stand-in for the retrieval component."""

    def __init__(self, chunks: list[Any] | None = None) -> None:
        self.chunks = chunks if chunks is not None else []
        self.calls: list[dict[str, Any]] = []

    def retrieve(
        self,
        db: Any,
        query: str,
        options: Any,
    ) -> list[Any]:
        self.calls.append({"db": db, "query": query, "options": options})
        return self.chunks


class FakeRateLimitStore:
    """In-memory implementation of the ``RateLimitStore`` port."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.blocks: dict[str, bytes] = {}

    def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, ttl: int) -> None:
        return None

    def get(self, key: str) -> bytes | None:
        return self.blocks.get(key)

    def setex(self, key: str, ttl: int, value: bytes) -> None:
        self.blocks[key] = value

    def ip_keys(self, scope: str, ip: str) -> tuple[str, str]:
        return f"rate:{scope}:s:{ip}", f"rate:{scope}:l:{ip}"

    def session_quota_key(self, scope: str, session_id: str) -> str:
        return f"session:{scope}:{session_id}"

    def cooldown_keys(self, scope: str, session_id: str) -> tuple[str, str]:
        return (
            f"cooldown:{scope}:c:{session_id}",
            f"cooldown:{scope}:b:{session_id}",
        )
