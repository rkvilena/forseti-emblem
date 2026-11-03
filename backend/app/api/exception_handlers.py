"""Centralized exception translation (Phase 8).

Application, service, and infrastructure code raise the exceptions defined in
``app.domain.exceptions``. This module is the single boundary that turns them into
HTTP responses, so the layers below the API never construct HTTP errors and each
exception maps to exactly one status code.

The observable mappings preserved from the pre-refactor behavior:

- ``DuplicateChapterError`` -> 409 with the ``{message, chapter_title, game}`` body
  (unchanged from ``wiki_controller``).
- Message empty / too long, Turnstile, and rate-limit responses still come from
  the admission policy and ``rate_limit`` as ``HTTPException`` (unchanged).
- OpenAI/provider failures no longer echo provider strings; they become a generic
  ``ProviderUnavailableError`` (503) / ``EmbeddingError`` (503) body.
"""

from __future__ import annotations

import logging
import uuid
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain.exceptions import (
    ChapterNotFoundError,
    ConfigurationError,
    DuplicateChapterError,
    EmbeddingError,
    InvalidChatRequest,
    ProviderUnavailableError,
    RetrievalError,
)


logger = logging.getLogger(__name__)


def _error_response(status_code: int, detail: object) -> JSONResponse:
    """Build a JSON error response in FastAPI's ``{"detail": ...}`` shape."""

    return JSONResponse(status_code=status_code, content={"detail": detail})


def handle_invalid_chat_request(request: Request, exc: Exception) -> JSONResponse:
    """``InvalidChatRequest`` -> 400."""

    return _error_response(400, str(exc) or "invalid chat request")


def handle_duplicate_chapter(request: Request, exc: Exception) -> JSONResponse:
    """``DuplicateChapterError`` -> 409 with the structured duplicate detail."""

    duplicate = cast(DuplicateChapterError, exc)
    return _error_response(
        409,
        {
            "message": str(duplicate),
            "chapter_title": duplicate.chapter_title,
            "game": duplicate.game,
        },
    )


def handle_chapter_not_found(request: Request, exc: Exception) -> JSONResponse:
    """``ChapterNotFoundError`` -> 404."""

    return _error_response(404, str(exc) or "chapter not found")


def handle_provider_unavailable(request: Request, exc: Exception) -> JSONResponse:
    """``ProviderUnavailableError`` -> 503 (no provider internals leak)."""

    logger.error("Answer provider unavailable: %s", exc)
    return _error_response(503, "The service is temporarily unavailable.")


def handle_embedding_error(request: Request, exc: Exception) -> JSONResponse:
    """``EmbeddingError`` -> 503 (no provider internals leak)."""

    logger.error("Embedding provider failed: %s", exc)
    return _error_response(503, "The service is temporarily unavailable.")


def handle_retrieval_error(request: Request, exc: Exception) -> JSONResponse:
    """``RetrievalError`` -> 500 (generic; details stay server-side)."""

    logger.error("Retrieval failed: %s", exc)
    return _error_response(500, "Unable to retrieve information right now.")


def handle_configuration_error(request: Request, exc: Exception) -> JSONResponse:
    """``ConfigurationError`` -> 500 (generic; no secrets/config leak)."""

    logger.error("Configuration error: %s", exc)
    return _error_response(500, "The service is not configured correctly.")


def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    """Unexpected ``Exception`` -> 500 with a generic body and a request id."""

    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    logger.exception("Unhandled error (request_id=%s)", request_id)

    response = _error_response(
        500, "An unexpected error occurred. Please try again later."
    )
    response.headers["X-Request-ID"] = request_id
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register one handler per application exception plus a generic 500."""

    app.add_exception_handler(InvalidChatRequest, handle_invalid_chat_request)
    app.add_exception_handler(DuplicateChapterError, handle_duplicate_chapter)
    app.add_exception_handler(ChapterNotFoundError, handle_chapter_not_found)
    app.add_exception_handler(ProviderUnavailableError, handle_provider_unavailable)
    app.add_exception_handler(EmbeddingError, handle_embedding_error)
    app.add_exception_handler(RetrievalError, handle_retrieval_error)
    app.add_exception_handler(ConfigurationError, handle_configuration_error)
    app.add_exception_handler(Exception, handle_unexpected)
