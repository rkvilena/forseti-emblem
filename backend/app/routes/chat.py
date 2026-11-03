from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..controllers import chat_controller
from ..security.request_admission import RequestContext, admit_chat_request
from ..security.turnstile import verify_turnstile_token
from ..schemas.chat import ChatRequest, ChatResponse, RagChatRequest


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request, response: Response) -> Any:
    context = RequestContext.from_request(request, response)
    admit_chat_request(
        context,
        scope="chat",
        message=req.message,
        turnstile_token=req.turnstile_token,
        verify_turnstile=verify_turnstile_token,
    )

    try:
        result = chat_controller.chat_plain(
            message=req.message,
            system_prompt=req.system_prompt,
            context=req.context,
            temperature=req.temperature,
        )
    except ValueError as e:
        # Typically: OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI request failed: {e}")

    return ChatResponse(**result)


@router.post("/chat/rag", response_model=ChatResponse)
def chat_rag(
    req: RagChatRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Any:
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

    try:
        result = chat_controller.chat_rag(
            db=db,
            message=req.message,
            top_k=req.top_k if admitted_top_k is None else admitted_top_k,
            temperature=req.temperature,
            system_prompt=req.system_prompt,
        )
    except ValueError as e:
        # Typically: OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG chat failed: {e}")

    return ChatResponse(**result)

