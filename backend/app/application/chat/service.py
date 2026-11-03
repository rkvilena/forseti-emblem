"""Chat application services (use cases).

Each service owns one complete business operation -- answering a plain chat
question or answering a retrieval-augmented question. The RAG service is a
composition of named pipeline components (``app.services``): retrieval, context
building, answer generation, and source selection. Each step has a single reason
to change and is independently testable.

The services read in business terms and import no FastAPI HTTP types
(``Request``/``Response``/``HTTPException``); translating failures into HTTP
responses is the route's job. For this phase the services still depend on the
flat ``openai_service`` helper behind the answer generator; provider ports and
repositories arrive in later phases.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ...config import settings
from ...services.answer_generation import AnswerGenerator
from ...services.context_builder import ContextBuilder
from ...services.retrieval import Retriever, RetrievalOptions
from ...services.source_selector import SourceSelector
from .commands import PlainChatCommand, RagChatCommand
from .results import ChatResult, Usage


def _to_usage(raw: dict[str, int] | None) -> Usage | None:
    """Convert the provider usage mapping into the typed application ``Usage``."""

    if raw is None:
        return None

    return Usage(
        prompt_tokens=raw.get("prompt_tokens"),
        completion_tokens=raw.get("completion_tokens"),
        total_tokens=raw.get("total_tokens"),
    )


class PlainChatService:
    """Use case: answer a chat question without retrieval."""

    def __init__(self, answer_generator: AnswerGenerator | None = None) -> None:
        self._answer_generator = answer_generator or AnswerGenerator()

    def execute(self, command: PlainChatCommand) -> ChatResult:
        text, usage = self._answer_generator.generate(
            system_prompt=command.system_prompt,
            question=command.message,
            context=command.context,
            temperature=command.temperature,
        )

        return ChatResult(
            response=text,
            model=settings.openai_chat_model,
            usage=_to_usage(usage),
        )


class RagChatService:
    """Use case: answer a chat question augmented with retrieved chunks."""

    def __init__(
        self,
        db: Session,
        retriever: Retriever | None = None,
        context_builder: ContextBuilder | None = None,
        answer_generator: AnswerGenerator | None = None,
        source_selector: SourceSelector | None = None,
    ) -> None:
        self._db = db
        self._retriever = retriever or Retriever()
        self._context_builder = context_builder or ContextBuilder()
        self._answer_generator = answer_generator or AnswerGenerator()
        self._source_selector = source_selector or SourceSelector()

    def execute(self, command: RagChatCommand) -> ChatResult:
        chunks = self._retriever.retrieve(
            db=self._db,
            query=command.message,
            options=RetrievalOptions(top_k=command.top_k),
        )

        if not chunks:
            return ChatResult(
                response="Not found in provided context.",
                model=settings.openai_chat_model,
                usage=None,
            )

        context = self._context_builder.build(chunks)

        text, usage = self._answer_generator.generate(
            system_prompt=command.system_prompt,
            question=command.message,
            context=context,
            temperature=command.temperature,
        )

        sources = self._source_selector.select(
            chunks=chunks,
            question=command.message,
        )

        return ChatResult(
            response=text,
            model=settings.openai_chat_model,
            usage=_to_usage(usage),
            sources=sources or None,
        )

