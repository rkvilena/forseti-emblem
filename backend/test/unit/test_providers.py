"""Unit tests for the external provider adapters and the in-memory fakes (5).

Adapters are thin wrappers over an external system, so each test asserts only
that the adapter delegates/translates correctly -- no network is used.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.application.ports.embeddings import EmbeddingProvider
from app.application.ports.llm import AnswerProvider
from app.application.ports.models import GeneratedAnswer, Usage
from app.application.ports.rate_limit import RateLimitStore
from app.config import settings
from app.infrastructure.mediawiki import wiki_client as wiki_client_module
from app.infrastructure.openai import (
    answer_provider as answer_provider_module,
)
from app.infrastructure.openai import (
    embedding_provider as embedding_provider_module,
)
from app.infrastructure.redis.rate_limit_store import (
    RateLimitStoreError,
    RedisRateLimitStore,
)

from fakes import FakeAnswerProvider, FakeEmbeddingProvider, FakeRateLimitStore


# --------------------------------------------------------------------------- #
# OpenAI adapters
# --------------------------------------------------------------------------- #


def test_openai_embedding_provider_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    single: list[str] = []
    batch: list[list[str]] = []

    monkeypatch.setattr(
        embedding_provider_module,
        "create_embedding",
        lambda text: single.append(text) or [0.5],
    )
    monkeypatch.setattr(
        embedding_provider_module,
        "create_embeddings_batch",
        lambda texts: batch.append(list(texts)) or [[0.1], [0.2]],
    )

    provider = embedding_provider_module.OpenAIEmbeddingProvider()

    assert provider.embed("a") == [0.5]
    assert provider.embed_batch(["a", "b"]) == [[0.1], [0.2]]
    assert single == ["a"]
    assert batch == [["a", "b"]]


def test_openai_answer_provider_maps_generated_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_completion(**kwargs: Any) -> tuple[str, dict[str, int] | None]:
        captured.update(kwargs)
        return (
            "the answer",
            {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        )

    monkeypatch.setattr(answer_provider_module, "chat_completion", _fake_completion)

    answer = answer_provider_module.OpenAIAnswerProvider().answer(
        question="Q",
        context="CTX",
        system_prompt="SYS",
        temperature=0.2,
    )

    assert answer == GeneratedAnswer(
        text="the answer",
        model=settings.openai_chat_model,
        usage=Usage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
    )
    assert captured == {
        "system_prompt": "SYS",
        "user_message": "Q",
        "context": "CTX",
        "temperature": 0.2,
    }


def test_openai_answer_provider_maps_missing_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        answer_provider_module, "chat_completion", lambda **_: ("answer", None)
    )

    answer = answer_provider_module.OpenAIAnswerProvider().answer(
        question="Q",
        context=None,
        system_prompt="SYS",
        temperature=0.2,
    )

    assert answer.usage is None


# --------------------------------------------------------------------------- #
# Redis rate-limit store adapter
# --------------------------------------------------------------------------- #


class _FakeRedis:
    """Minimal Redis stand-in exposing the raw operations the store uses."""

    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expires: list[tuple[str, int]] = []
        self.blobs: dict[str, bytes] = {}

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, ttl: int) -> bool:
        self.expires.append((key, ttl))
        return True

    def get(self, key: str) -> bytes | None:
        return self.blobs.get(key)

    def setex(self, key: str, ttl: int, value: bytes) -> None:
        self.blobs[key] = value


def test_redis_rate_limit_store_owns_key_generation() -> None:
    store = RedisRateLimitStore(_FakeRedis())

    assert store.ip_keys("chat", "1.2.3.4") == (
        "rate:chat:s:1.2.3.4",
        "rate:chat:l:1.2.3.4",
    )
    assert store.session_quota_key("chat", "sid") == "session:chat:sid"
    assert store.cooldown_keys("chat", "sid") == (
        "cooldown:chat:c:sid",
        "cooldown:chat:b:sid",
    )


def test_redis_rate_limit_store_operations() -> None:
    client = _FakeRedis()
    store = RedisRateLimitStore(client)

    assert store.incr("k") == 1
    assert store.incr("k") == 2
    store.expire("k", 60)
    store.setex("block", 30, b"1")

    assert store.get("block") == b"1"
    assert client.expires == [("k", 60)]


def test_redis_rate_limit_store_translates_errors() -> None:
    class _Broken:
        def incr(self, key: str) -> int:
            raise RuntimeError("boom")

    store = RedisRateLimitStore(_Broken())

    with pytest.raises(RateLimitStoreError):
        store.incr("k")


# --------------------------------------------------------------------------- #
# MediaWiki adapter
# --------------------------------------------------------------------------- #


class _FakeMediaWiki:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def fetch_page_wikitext(self, title: str) -> dict[str, Any]:
        self.calls.append(("wikitext", title))
        return {"title": title, "wikitext": "wt", "pageid": 1}

    def fetch_page_html(self, title: str) -> dict[str, Any]:
        self.calls.append(("html", title))
        return {"title": title, "html": "<p/>", "pageid": 1}

    def fetch_category_members(
        self, category_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        self.calls.append(("members", (category_name, limit)))
        return [{"title": "A"}]

    def fetch_pages_in_category(
        self, category_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        self.calls.append(("pages", (category_name, limit)))
        return [{"title": "A", "html": "<p/>"}]


def test_mediawiki_wiki_client_delegates() -> None:
    inner = _FakeMediaWiki()
    client = wiki_client_module.MediaWikiWikiClient(inner)  # type: ignore[arg-type]

    assert client.fetch_page_wikitext("T")["wikitext"] == "wt"
    assert client.fetch_page_html("T")["html"] == "<p/>"
    assert client.fetch_category_members("C", 5) == [{"title": "A"}]
    assert client.fetch_pages_in_category("C", 2) == [{"title": "A", "html": "<p/>"}]
    assert inner.calls == [
        ("wikitext", "T"),
        ("html", "T"),
        ("members", ("C", 5)),
        ("pages", ("C", 2)),
    ]


# --------------------------------------------------------------------------- #
# Fakes conform to the port shapes
# --------------------------------------------------------------------------- #


def test_fakes_satisfy_port_shapes() -> None:
    embedding: EmbeddingProvider = FakeEmbeddingProvider()
    answer: AnswerProvider = FakeAnswerProvider()
    store: RateLimitStore = FakeRateLimitStore()

    assert embedding.embed("x")
    assert answer.answer(
        question="q", context=None, system_prompt="s", temperature=0.1
    )
    assert store.incr("k") == 1
    assert store.get("k") is None
