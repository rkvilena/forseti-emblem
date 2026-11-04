"""Embedding-status vocabulary (Phase 9, item 5).

A chapter is *searchable* only when every one of its chunks carries an
embedding; otherwise it is *pending*. These two values are the persisted,
framework-free business states shared by the ingestion use case, the ORM model,
and the API schemas.
"""

from __future__ import annotations

from typing import Final

#: The chapter exists but one or more chunks lack an embedding, so vector
#: retrieval cannot return it yet. This is the initial state of every chapter
#: and the state embeddings intentionally skipped or failed to produce.
EMBEDDING_STATUS_PENDING: Final = "pending"

#: Every chunk of the chapter carries an embedding, so RAG retrieval can use it.
EMBEDDING_STATUS_SEARCHABLE: Final = "searchable"

#: All valid values, useful for validation and migrations.
EMBEDDING_STATUSES: Final = (EMBEDDING_STATUS_PENDING, EMBEDDING_STATUS_SEARCHABLE)
