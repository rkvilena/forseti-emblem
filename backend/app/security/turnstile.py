from __future__ import annotations

from typing import Any

import requests

from ..config import settings

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_token(
    token: str, remote_ip: str | None
) -> tuple[bool, str | None]:
    if not settings.turnstile_secret_key:
        return False, "turnstile_secret_key is not configured"

    payload: dict[str, Any] = {
        "secret": settings.turnstile_secret_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = requests.post(
            TURNSTILE_VERIFY_URL,
            data=payload,
            timeout=5,
        )
    except requests.RequestException as exc:
        return False, f"Turnstile verification failed: {exc}"

    if response.status_code != 200:
        return (
            False,
            f"Turnstile verification failed with status {response.status_code}",
        )

    data = response.json()
    if not data.get("success"):
        codes = data.get("error-codes") or []
        message = "Turnstile verification failed"
        if codes:
            message = f"{message}: {', '.join(codes)}"
        return False, message

    return True, None
