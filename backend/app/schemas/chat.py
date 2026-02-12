from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, description="User prompt")
    turnstile_token: str | None = Field(
        default=None,
        min_length=1,
        description="Cloudflare Turnstile token",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt override. Defaults to Fire Emblem assistant prompt.",
    )
    context: str | None = Field(
        default=None,
        description="Optional context string to include (manual RAG context)",
    )
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)


class RagChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, description="User prompt")
    turnstile_token: str | None = Field(
        default=None,
        min_length=1,
        description="Cloudflare Turnstile token",
    )
    top_k: int = Field(
        default=8, ge=1, le=30, description="How many chunks to retrieve"
    )
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt override. Defaults to Fire Emblem assistant prompt.",
    )


class ChatUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    response: str
    model: str
    usage: ChatUsage | None = None
