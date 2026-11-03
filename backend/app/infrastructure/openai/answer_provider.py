"""OpenAI-backed implementation of the ``AnswerProvider`` port.

Converts the SDK-shaped ``(text, usage_dict)`` returned by
``openai_service.chat_completion`` into the application ``GeneratedAnswer`` type,
and translates SDK/transport failures into ``ConfigurationError`` (missing setup)
or ``ProviderUnavailableError`` (provider failure).
"""

from __future__ import annotations

from ...application.ports.models import GeneratedAnswer, Usage
from ...config import settings
from ...domain.exceptions import ConfigurationError, ProviderUnavailableError
from ...openai_service import chat_completion


def _to_usage(raw: dict[str, int] | None) -> Usage | None:
    """Convert the provider usage mapping into the typed application ``Usage``."""

    if raw is None:
        return None

    return Usage(
        prompt_tokens=raw.get("prompt_tokens"),
        completion_tokens=raw.get("completion_tokens"),
        total_tokens=raw.get("total_tokens"),
    )


class OpenAIAnswerProvider:
    """Adapt ``openai_service.chat_completion`` to the answer port."""

    def answer(
        self,
        *,
        question: str,
        context: str | None,
        system_prompt: str,
        temperature: float,
    ) -> GeneratedAnswer:
        try:
            text, usage = chat_completion(
                system_prompt=system_prompt,
                user_message=question,
                context=context,
                temperature=temperature,
            )
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        except Exception as exc:
            raise ProviderUnavailableError("Answer provider request failed") from exc

        return GeneratedAnswer(
            text=text,
            model=settings.openai_chat_model,
            usage=_to_usage(usage),
        )
