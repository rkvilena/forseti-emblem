"""Application-facing value objects exchanged with external adapters.

These are the small, framework-free types the application layer shares with its
ports. They live here (rather than next to a single use case) so both the
protocols and their concrete implementations can depend on them without knowing
about each other.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    """Token usage reported by an answer provider."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class GeneratedAnswer:
    """The text, model, and usage returned by an answer provider."""

    text: str
    model: str
    usage: Usage | None = None
