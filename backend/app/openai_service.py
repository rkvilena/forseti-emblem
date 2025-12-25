"""
OpenAI service for embeddings and chat completions.

Provides functions to generate embeddings for text chunks
and handle RAG-based question answering.
"""

import logging
from typing import Any

from openai import OpenAI

from .config import settings


logger = logging.getLogger(__name__)

# Initialize OpenAI client (lazy initialization)
_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please set it in your .env file or environment variables."
            )
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def create_embedding(text: str) -> list[float]:
    """
    Create embedding vector for a single text.
    
    Args:
        text: The text to embed
        
    Returns:
        List of floats representing the embedding vector (1536 dimensions for text-embedding-3-small)
    """
    client = get_openai_client()
    
    # Clean and truncate text if needed (max ~8000 tokens for embedding models)
    text = text.strip()
    if not text:
        raise ValueError("Cannot create embedding for empty text")
    
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    
    return response.data[0].embedding


def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Create embeddings for multiple texts in a single API call.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    client = get_openai_client()
    
    # Filter out empty texts
    cleaned_texts = [t.strip() for t in texts if t.strip()]
    if not cleaned_texts:
        return []
    
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=cleaned_texts,
    )
    
    # Sort by index to maintain order
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]


def chat_completion(
    system_prompt: str,
    user_message: str,
    context: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Generate a chat completion with optional RAG context.
    
    Args:
        system_prompt: System message defining assistant behavior
        user_message: User's question or message
        context: Optional context from retrieved documents
        temperature: Sampling temperature (0-2)
        
    Returns:
        Assistant's response text
    """
    client = get_openai_client()
    
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]
    
    if context:
        messages.append({
            "role": "user",
            "content": f"Context information:\n{context}\n\n---\n\nQuestion: {user_message}"
        })
    else:
        messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        temperature=temperature,
    )
    
    return response.choices[0].message.content or ""


# Default system prompt for Fire Emblem RAG
FIRE_EMBLEM_SYSTEM_PROMPT = """You are an expert assistant for Fire Emblem games. 
You have access to detailed information about game chapters, including objectives, 
available units, bosses, and strategies.

When answering questions:
1. Use the provided context to give accurate, specific answers
2. If the context doesn't contain enough information, say so
3. Reference specific chapter names and game titles when relevant
4. Be helpful and concise in your responses

If you don't know something or the context doesn't provide the answer, 
be honest about it rather than making up information."""
