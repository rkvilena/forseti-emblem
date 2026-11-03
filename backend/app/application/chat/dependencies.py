"""FastAPI dependency providers for the chat use cases.

Kept separate from ``service.py`` so the use cases themselves stay free of the
web framework; only this wiring module knows about FastAPI's ``Depends``.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ...db import get_db
from .service import PlainChatService, RagChatService


def get_plain_chat_service() -> PlainChatService:
    """Provide a configured plain chat use case."""

    return PlainChatService()


def get_rag_chat_service(db: Session = Depends(get_db)) -> RagChatService:
    """Provide a retrieval-augmented chat use case bound to a DB session."""

    return RagChatService(db)
