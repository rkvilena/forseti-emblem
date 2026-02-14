from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..controllers import chat_controller
from ..security.turnstile import verify_turnstile_token
from ..schemas.chat import ChatRequest, ChatResponse, RagChatRequest
from ..rate_limit import (
    enforce_ip_rate_limit,
    enforce_session_quota,
    enforce_session_cooldown,
)


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request, response: Response) -> Any:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    if len(req.message) > settings.request_max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"message must be at most {settings.request_max_chars} characters",
        )

    client_ip = request.client.host if request.client else None
    enforce_ip_rate_limit(client_ip, scope="chat")
    enforce_session_quota(request, response, scope="chat")
    enforce_session_cooldown(request, response, scope="chat")

    if settings.turnstile_enabled:
        if not req.turnstile_token:
            raise HTTPException(status_code=400, detail="turnstile token is required")

        ok, error = verify_turnstile_token(
            token=req.turnstile_token,
            remote_ip=request.client.host if request.client else None,
        )
        if not ok:
            status_code = (
                500 if error == "turnstile_secret_key is not configured" else 403
            )
            raise HTTPException(
                status_code=status_code,
                detail=error or "Turnstile verification failed",
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
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    if len(req.message) > settings.request_max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"message must be at most {settings.request_max_chars} characters",
        )

    if req.top_k > settings.rag_top_k_max:
        req.top_k = settings.rag_top_k_max

    client_ip = request.client.host if request.client else None
    enforce_ip_rate_limit(client_ip, scope="chat_rag")
    enforce_session_quota(request, response, scope="chat_rag")
    enforce_session_cooldown(request, response, scope="chat_rag")

    if settings.turnstile_enabled:
        if not req.turnstile_token:
            raise HTTPException(status_code=400, detail="turnstile token is required")

        ok, error = verify_turnstile_token(
            token=req.turnstile_token,
            remote_ip=request.client.host if request.client else None,
        )
        if not ok:
            status_code = (
                500 if error == "turnstile_secret_key is not configured" else 403
            )
            raise HTTPException(
                status_code=status_code,
                detail=error or "Turnstile verification failed",
            )

    try:
        result = chat_controller.chat_rag(
            db=db,
            message=req.message,
            top_k=req.top_k,
            temperature=req.temperature,
            system_prompt=req.system_prompt,
        )
    except ValueError as e:
        # Typically: OPENAI_API_KEY not set
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG chat failed: {e}")

    return ChatResponse(**result)
