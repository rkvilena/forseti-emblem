"""Shared request-admission policy for the chat endpoints.

Centralizes the checks that decide whether a chat request may run: message
validation, cost-control clamps, IP/session rate limits, and Turnstile
verification. Both ``POST /chat`` and ``POST /chat/rag`` funnel through
:func:`admit_chat_request` so the policy exists in exactly one place and the
route stays a thin HTTP adapter.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Callable, Protocol

from fastapi import HTTPException, Request, Response

from ..config import settings
from ..rate_limit import (
    enforce_ip_rate_limit,
    enforce_session_cooldown,
    enforce_session_quota,
)


class TurnstileVerifier(Protocol):
    """Callable verifying a Turnstile token, returning ``(ok, error)``."""

    def __call__(
        self, token: str, remote_ip: str | None
    ) -> tuple[bool, str | None]: ...


@dataclass(frozen=True)
class RequestContext:
    """Narrow view of an inbound request used by the admission policy.

    Only the client IP and session-cookie access are exposed; policy internals
    never touch the raw FastAPI ``Request``/``Response``.
    """

    client_ip: str | None
    _read_session_cookie: Callable[[], str | None]
    _write_session_cookie: Callable[[str], None]

    @classmethod
    def from_request(cls, request: Request, response: Response) -> "RequestContext":
        """Build a context that reads/writes the anonymous session cookie."""

        def read_session_cookie() -> str | None:
            return request.cookies.get(settings.session_cookie_name)

        def write_session_cookie(session_id: str) -> None:
            max_age = max(1, int(settings.session_cookie_ttl_seconds))
            response.set_cookie(
                key=settings.session_cookie_name,
                value=session_id,
                max_age=max_age,
                httponly=True,
                secure=bool(settings.is_production),
                samesite="lax",
                path="/",
            )

        client_ip = request.client.host if request.client else None
        return cls(
            client_ip=client_ip,
            _read_session_cookie=read_session_cookie,
            _write_session_cookie=write_session_cookie,
        )

    def get_or_create_session_id(self) -> str:
        """Return the existing session id, creating/persisting one if absent.

        The cookie is written at most once so the same id is reused by every
        consumer of the request (session quota and cooldown).
        """
        session_id = self._read_session_cookie()
        if session_id:
            return session_id

        session_id = secrets.token_urlsafe(18)
        self._write_session_cookie(session_id)
        return session_id


def admit_chat_request(
    context: RequestContext,
    *,
    scope: str,
    message: str,
    turnstile_token: str | None,
    verify_turnstile: TurnstileVerifier,
    top_k: int | None = None,
) -> int | None:
    """Run the shared admission policy for a chat request.

    Performs, in order: empty-message check, max-length check, ``top_k`` clamp
    (RAG only), IP rate limit, session quota, session cooldown, and Turnstile
    verification when enabled. Returns the effective ``top_k`` (``None`` for
    plain chat). Raises ``HTTPException`` with the exact status codes and detail
    strings the routes returned before this refactor.
    """
    if not message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    if len(message) > settings.request_max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"message must be at most {settings.request_max_chars} characters",
        )

    if top_k is not None and top_k > settings.rag_top_k_max:
        top_k = settings.rag_top_k_max

    enforce_ip_rate_limit(context.client_ip, scope=scope)

    session_id = context.get_or_create_session_id()
    enforce_session_quota(session_id, scope=scope)
    enforce_session_cooldown(session_id, scope=scope)

    if settings.turnstile_enabled:
        if not turnstile_token:
            raise HTTPException(status_code=400, detail="turnstile token is required")

        ok, error = verify_turnstile(token=turnstile_token, remote_ip=context.client_ip)
        if not ok:
            status_code = (
                500 if error == "turnstile_secret_key is not configured" else 403
            )
            raise HTTPException(
                status_code=status_code,
                detail=error or "Turnstile verification failed",
            )

    return top_k
