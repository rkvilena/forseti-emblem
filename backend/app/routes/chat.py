from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..controllers import chat_controller
from ..schemas.chat import ChatRequest, ChatResponse, RagChatRequest


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> Any:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

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
def chat_rag(req: RagChatRequest, db: Session = Depends(get_db)) -> Any:
    """RAG chat: embeds the question, retrieves similar DB chunks, and asks OpenAI with that context."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

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
