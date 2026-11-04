"""Application exception hierarchy (Phase 8).

Application, service, and infrastructure code raise these instead of FastAPI
``HTTPException`` so nothing below the API layer depends on the web framework.
A single set of handlers (``app.api.exception_handlers``) translates each type
into exactly one HTTP status code at the outer boundary.

Every concrete exception is a direct subclass of :class:`ApplicationError` so its
HTTP mapping is explicit and unambiguous (one handler, one code).
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application-level errors."""


class ConfigurationError(ApplicationError):
    """The service is missing required configuration (e.g. a provider key)."""


class ProviderUnavailableError(ApplicationError):
    """An external provider (e.g. OpenAI chat) could not service the request."""


class EmbeddingError(ApplicationError):
    """Embeddings could not be produced for a request."""


class RetrievalError(ApplicationError):
    """Chapter retrieval (similarity search / persistence) failed."""


class DuplicateChapterError(ApplicationError):
    """Raised when an equivalent chapter already exists in the database."""

    def __init__(
        self,
        message: str,
        chapter_title: str | None = None,
        game: str | None = None,
    ) -> None:
        super().__init__(message)
        self.chapter_title = chapter_title
        self.game = game


class ChapterNotFoundError(ApplicationError):
    """Raised when a requested chapter does not exist."""

    def __init__(
        self,
        message: str,
        *,
        title: str | None = None,
        pageid: int | None = None,
    ) -> None:
        super().__init__(message)
        self.title = title
        self.pageid = pageid


class InvalidChatRequest(ApplicationError):
    """Raised when a chat request is invalid at the application level."""
