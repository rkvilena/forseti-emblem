"""FastAPI dependency providers for the chat use cases and their adapters.

Kept separate from ``service.py`` so the use cases themselves stay free of the
web framework; only this wiring module knows about FastAPI's ``Depends``. It is
the composition root for chat: it maps application *ports* to their production
adapters, and tests can substitute fakes via ``app.dependency_overrides``.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ...db import get_db
from ...infrastructure.openai import OpenAIAnswerProvider, OpenAIEmbeddingProvider
from ...services.answer_generation import AnswerGenerator
from ...services.retrieval import Retriever
from ..ports.embeddings import EmbeddingProvider
from ..ports.llm import AnswerProvider
from .service import PlainChatService, RagChatService


def get_embedding_provider() -> EmbeddingProvider:
    """Provide the production embeddings adapter."""

    return OpenAIEmbeddingProvider()


def get_answer_provider() -> AnswerProvider:
    """Provide the production answer-generation adapter."""

    return OpenAIAnswerProvider()


def get_plain_chat_service(
    answer_provider: AnswerProvider = Depends(get_answer_provider),
) -> PlainChatService:
    """Provide a configured plain chat use case."""

    return PlainChatService(answer_generator=AnswerGenerator(answer_provider))


def get_rag_chat_service(
    db: Session = Depends(get_db),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    answer_provider: AnswerProvider = Depends(get_answer_provider),
) -> RagChatService:
    """Provide a retrieval-augmented chat use case bound to a DB session."""

    return RagChatService(
        db,
        retriever=Retriever(embedding_provider),
        answer_generator=AnswerGenerator(answer_provider),
    )
