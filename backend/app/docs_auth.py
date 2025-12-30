"""Swagger/ReDoc protection helpers.

Keeps FastAPI's built-in Swagger UI at /docs, but optionally restricts access.

Supported modes:
- basic: HTTP Basic Auth (browser-managed)
- session: short-lived signed cookie set via /docs-login
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import html
import json
import secrets
import time
from urllib.parse import quote

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from .config import settings

_DOCS_COOKIE_NAME = "docs_session"


def _is_docs_path(path: str) -> bool:
    if path == "/docs" or path.startswith("/docs/"):
        return True
    return path in {"/redoc", "/openapi.json"}


def _sanitize_next(next_url: str | None) -> str:
    if not next_url:
        return "/docs"

    # Only allow relative paths to prevent open redirects.
    if not next_url.startswith("/"):
        return "/docs"
    if next_url.startswith("//"):
        return "/docs"
    if "://" in next_url:
        return "/docs"

    return next_url


def _docs_issue_token(*, secret: str, ttl_seconds: int) -> str:
    exp = int(time.time()) + max(1, int(ttl_seconds))
    payload_bytes = json.dumps(
        {"exp": exp, "nonce": secrets.token_urlsafe(12)},
        separators=(",", ":"),
    ).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload_bytes + b"." + sig).decode("utf-8")


def _verify_token(*, token: str | None, secret: str) -> bool:
    if not token or not secret:
        return False

    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        payload_bytes, sig = raw.rsplit(b".", 1)
    except Exception:
        return False

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not secrets.compare_digest(sig, expected_sig):
        return False

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return False

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return False

    return int(time.time()) <= exp


def _login_html(*, next_url: str, error: str | None) -> str:
    error_title = None
    error_message = None
    if error == "invalid":
        error_title = "Sign-in failed"
        error_message = "Invalid username or password."
    elif error == "not-configured":
        error_title = "Docs login unavailable"
        error_message = "This service is not configured for docs login."

    error_html = ""
    if error_title and error_message:
        error_html = f"""
                <div class=\"alert alert--error\" role=\"alert\" aria-live=\"polite\">
                    <div class=\"alert__title\">{error_title}</div>
                    <div class=\"alert__message\">{error_message}</div>
                </div>
                """

    next_url_attr = html.escape(next_url, quote=True)
    next_url_text = html.escape(next_url)

    return f"""<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Forseti Emblem: Swagger API</title>
        <style>
            :root {{
                color-scheme: light dark;
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 24px;
                background: Canvas;
                color: CanvasText;
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
            }}
            .wrap {{
                min-height: calc(100vh - 48px);
                display: grid;
                place-items: center;
            }}
            .card {{
                width: min(520px, 100%);
                border: 1px solid GrayText;
                border-radius: 5px;
                padding: 20px;
            }}
            .title {{
                margin: 0;
                font-size: 22px;
                line-height: 1.2;
            }}
            .subtitle {{
                margin: 8px 0 0;
                color: GrayText;
                line-height: 1.4;
            }}
            .alert {{
                margin-top: 14px;
                padding: 12px;
                border-radius: 10px;
                border: 1px solid GrayText;
            }}
            .alert--error {{
                border-color: #b00020;
                background: #b00020;
                color: #ffffff;
            }}
            .alert__title {{
                font-weight: 600;
                margin-bottom: 4px;
            }}
            .alert__message {{
                color: GrayText;
            }}
            .alert--error .alert__message {{
                color: #ffffff;
                opacity: 0.95;
            }}
            form {{
                margin-top: 16px;
            }}
            .field {{
                margin-top: 12px;
            }}
            label {{
                display: inline-block;
                margin-bottom: 6px;
                font-weight: 600;
            }}
            input {{
                width: 100%;
                padding: 10px 12px;
                border-radius: 5px;
                border: 1px solid GrayText;
                background: Canvas;
                color: CanvasText;
            }}
            input:focus {{
                outline: 2px solid Highlight;
                outline-offset: 2px;
            }}
            .actions {{
                margin-top: 16px;
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            button {{
                padding: 10px 14px;
                border-radius: 5px;
                border: 1px solid GrayText;
                background: ButtonFace;
                color: ButtonText;
                cursor: pointer;
            }}
            button:hover {{
                filter: contrast(1.05);
            }}
            .hint {{
                margin-top: 14px;
                font-size: 13px;
                color: GrayText;
                line-height: 1.4;
            }}
            .hint code {{
                padding: 2px 6px;
                border-radius: 8px;
                border: 1px solid GrayText;
            }}
        </style>
        <script>
            // Clean query params (like ?error=invalid&next=...) so refresh doesn't retain them.
            (function () {{
                try {{
                    if (window.location.search) {{
                        window.history.replaceState(null, document.title, window.location.pathname);
                    }}
                }} catch (e) {{
                    // no-op
                }}
            }})();
        </script>
    </head>
    <body>
        <div class=\"wrap\">
            <main class=\"card\">
                <h1 class=\"title\">Forseti Emblem: Swagger UI Docs</h1>
                <p class=\"subtitle\">Enter credentials to access Swagger UI.</p>

                {error_html}

                <form method=\"post\" action=\"/docs-login\">
                    <input type=\"hidden\" name=\"next\" value=\"{next_url_attr}\" />

                    <div class=\"field\">
                        <label for=\"username\">Username</label>
                        <input id=\"username\" name=\"username\" autocomplete=\"username\" autofocus />
                    </div>

                    <div class=\"field\">
                        <label for=\"password\">Password</label>
                        <input id=\"password\" name=\"password\" type=\"password\" autocomplete=\"current-password\" />
                    </div>

                    <div class=\"actions\">
                        <button type=\"submit\">Sign in</button>
                    </div>
                </form>

                <div class=\"hint\">
                    You’ll be redirected back to <code>{next_url_text}</code> after signing in.
                </div>
            </main>
        </div>
    </body>
</html>"""


class DocsBasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        *,
        enabled: bool,
        username: str,
        password: str,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.username = username
        self.password = password

    @staticmethod
    def _unauthorized() -> Response:
        return PlainTextResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="api-docs"'},
        )

    def _valid_basic_auth(self, authorization_header: str | None) -> bool:
        if not authorization_header:
            return False
        if not authorization_header.lower().startswith("basic "):
            return False

        token = authorization_header.split(" ", 1)[1].strip()
        try:
            decoded = base64.b64decode(token).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False

        if ":" not in decoded:
            return False

        provided_username, provided_password = decoded.split(":", 1)
        return secrets.compare_digest(provided_username, self.username) and secrets.compare_digest(
            provided_password,
            self.password,
        )

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or not _is_docs_path(request.url.path):
            return await call_next(request)

        if self._valid_basic_auth(request.headers.get("Authorization")):
            return await call_next(request)

        return self._unauthorized()


class DocsSessionAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        *,
        enabled: bool,
        secret: str,
        cookie_name: str = _DOCS_COOKIE_NAME,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.secret = secret
        self.cookie_name = cookie_name

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or not _is_docs_path(request.url.path):
            return await call_next(request)

        if _verify_token(token=request.cookies.get(self.cookie_name), secret=self.secret):
            return await call_next(request)

        next_url = str(request.url.path)
        if request.url.query:
            next_url += f"?{request.url.query}"
        return RedirectResponse(url=f"/docs-login?next={quote(next_url, safe='/:?&=%')}" , status_code=302)


def setup_docs_auth(app: FastAPI, *, logger) -> tuple[bool, str]:
    """Configure docs protection and register routes.

    Returns: (docs_auth_enabled, docs_auth_mode)
    """

    docs_auth_enabled = bool(
        settings.docs_auth_enabled
        or (
            settings.is_production
            and settings.docs_username
            and settings.docs_password
            and (settings.docs_auth_mode in {"basic", "session"})
        )
    )

    if not docs_auth_enabled:
        return False, settings.docs_auth_mode

    if not (settings.docs_username and settings.docs_password):
        logger.warning("Docs auth enabled but DOCS_USERNAME/DOCS_PASSWORD not set; leaving docs unprotected")
        return True, settings.docs_auth_mode

    if settings.docs_auth_mode == "basic":
        app.add_middleware(
            DocsBasicAuthMiddleware,
            enabled=True,
            username=settings.docs_username,
            password=settings.docs_password,
        )
        return True, "basic"

    if settings.docs_auth_mode == "session":
        if not settings.docs_session_secret:
            logger.warning("Docs auth mode=session but DOCS_SESSION_SECRET not set; leaving docs unprotected")
        else:
            app.add_middleware(
                DocsSessionAuthMiddleware,
                enabled=True,
                secret=settings.docs_session_secret,
            )

        # Register login/logout endpoints even if misconfigured; helps debugging.
        def docs_login_form(next: str = "/docs", error: str | None = None) -> HTMLResponse:
            safe_next = _sanitize_next(next)
            return HTMLResponse(content=_login_html(next_url=safe_next, error=error))

        async def docs_login_submit(request: Request) -> Response:
            form = await request.form()
            username = str(form.get("username", ""))
            password = str(form.get("password", ""))
            next_url = _sanitize_next(str(form.get("next", "/docs")))

            if not (settings.docs_username and settings.docs_password and settings.docs_session_secret):
                return RedirectResponse(
                    url=f"/docs-login?error=not-configured&next={quote(next_url, safe='/:?&=%')}",
                    status_code=303,
                )

            if not (
                secrets.compare_digest(username, settings.docs_username)
                and secrets.compare_digest(password, settings.docs_password)
            ):
                # PRG pattern: redirect back to GET so refresh works.
                return RedirectResponse(
                    url=f"/docs-login?error=invalid&next={quote(next_url, safe='/:?&=%')}",
                    status_code=303,
                )

            token = _docs_issue_token(
                secret=settings.docs_session_secret,
                ttl_seconds=settings.docs_session_ttl_seconds,
            )
            response = RedirectResponse(url=next_url or "/docs", status_code=303)
            response.set_cookie(
                key=_DOCS_COOKIE_NAME,
                value=token,
                max_age=max(1, int(settings.docs_session_ttl_seconds)),
                httponly=True,
                secure=bool(settings.is_production),
                samesite="lax",
                path="/",
            )
            return response

        def docs_logout() -> Response:
            response = RedirectResponse(url="/docs-login", status_code=303)
            response.delete_cookie(_DOCS_COOKIE_NAME, path="/")
            return response

        app.add_api_route("/docs-login", docs_login_form, methods=["GET"], include_in_schema=False)
        app.add_api_route("/docs-login", docs_login_submit, methods=["POST"], include_in_schema=False)
        app.add_api_route("/docs-logout", docs_logout, methods=["POST"], include_in_schema=False)

        return True, "session"

    # Unknown mode => leave unprotected, but report enabled.
    logger.warning(f"Unknown DOCS_AUTH_MODE={settings.docs_auth_mode}; leaving docs unprotected")
    return True, settings.docs_auth_mode
