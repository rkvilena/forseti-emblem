from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..application.chat.commands import PlainChatCommand, RagChatCommand
from ..application.chat.results import ChatResult
from ..db import get_db
from ..controllers import chat_controller
from ..security.request_admission import RequestContext, admit_chat_request
from ..security.turnstile import verify_turnstile_token
from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatUsage,
    RagChatRequest,
    SourceReference,
)


router = APIRouter(tags=["chat"])


def _to_chat_response(result: ChatResult) -> ChatResponse:
    """Map the application ``ChatResult`` onto the public HTTP response model."""

    usage: ChatUsage | None = None
    if result.usage is not None:
        usage = ChatUsage(
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            total_tokens=result.usage.total_tokens,
        )

    sources: list[SourceReference] | None = None
    if result.sources is not None:
        sources = [
            SourceReference(
                title=source.title,
                infobox_title=source.infobox_title,
                game=source.game,
                pageid=source.pageid,
                source_url=source.source_url,
            )
            for source in result.sources
        ]

    return ChatResponse(
        response=result.response,
        model=result.model,
        usage=usage,
        sources=sources,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request, response: Response) -> ChatResponse:
    context = RequestContext.from_request(request, response)
    admit_chat_request(
        context,
        scope="chat",
        message=req.message,
        turnstile_token=req.turnstile_token,
        verify_turnstile=verify_turnstile_token,
    )

    command = PlainChatCommand(
        message=req.message,
        system_prompt=req.system_prompt,
        context=req.context,
        temperature=req.temperature,
    )

    try:
        result = chat_controller.chat_plain(command=command)
    except ValueError as e:
        # Typically: OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {e}")

    return _to_chat_response(result)


@router.post("/chat/rag", response_model=ChatResponse)
def chat_rag(
    req: RagChatRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """RAG chat: embeds the question, retrieves similar DB chunks, and asks OpenAI with that context."""
    context = RequestContext.from_request(request, response)
    admitted_top_k = admit_chat_request(
        context,
        scope="chat_rag",
        message=req.message,
        turnstile_token=req.turnstile_token,
        verify_turnstile=verify_turnstile_token,
        top_k=req.top_k,
    )

    command = RagChatCommand(
        message=req.message,
        top_k=req.top_k if admitted_top_k is None else admitted_top_k,
        temperature=req.temperature,
        system_prompt=req.system_prompt,
    )

    try:
        result = chat_controller.chat_rag(db=db, command=command)
    except ValueError as e:
        # Typically: OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG chat failed: {e}")

    return _to_chat_response(result)

