"""
Universal LLM client compatible with OpenAI, Groq, and Ollama.

Usage:
    from src.ai.llm_client import llm_chat

    answer = llm_chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is 2+2?"},
    ])

Providers are selected via env vars:
    LLM_PROVIDER=openai   LLM_MODEL=gpt-4o-mini     LLM_API_KEY=sk-...
    LLM_PROVIDER=groq     LLM_MODEL=llama-3.3-70b-versatile  LLM_API_KEY=gsk_...  LLM_BASE_URL=https://api.groq.com/openai/v1
    LLM_PROVIDER=ollama   LLM_MODEL=gemma3:27b       LLM_API_KEY=ollama   LLM_BASE_URL=http://localhost:11434/v1
"""
from __future__ import annotations

from openai import OpenAI

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Groq's OpenAI-compatible endpoint
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def _build_client() -> OpenAI:
    """Build an OpenAI-SDK-compatible client for the configured provider."""
    provider = settings.llm_provider.lower()

    if provider == "groq":
        base_url = settings.llm_base_url or _GROQ_BASE_URL
        api_key = settings.llm_api_key
    elif provider == "ollama":
        base_url = settings.llm_base_url or "http://localhost:11434/v1"
        api_key = settings.llm_api_key or "ollama"
    else:
        # "openai" or any custom OpenAI-compatible service
        base_url = settings.llm_base_url or None
        api_key = settings.llm_api_key

    return OpenAI(api_key=api_key, base_url=base_url)


# Module-level client — created once, reused per process.
# Celery workers each have their own process, so this is safe.
_client: OpenAI | None = None


def get_llm_client() -> OpenAI:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def llm_chat(
    messages: list[dict],
    *,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model: str | None = None,
) -> str:
    """
    Send a chat-completion request to the configured LLM.

    Args:
        messages:    List of {"role": ..., "content": ...} dicts.
        temperature: Sampling temperature (0.0 = deterministic).
        max_tokens:  Maximum output tokens.
        model:       Override model name (uses settings.llm_model by default).

    Returns:
        The assistant's text response as a string.

    Raises:
        openai.OpenAIError: On API or network failure.
    """
    client = get_llm_client()
    effective_model = model or settings.llm_model

    logger.debug(
        "llm_chat provider=%s model=%s messages=%d",
        settings.llm_provider,
        effective_model,
        len(messages),
    )

    response = client.chat.completions.create(
        model=effective_model,
        messages=messages,  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,
    )

    message = response.choices[0].message
    content = message.content or ""
    
    # Handle deep-thinking/reasoning content if returned by the provider (e.g. DeepSeek, NVIDIA, OpenAI o1)
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        logger.info("Retrieved reasoning content from %s", effective_model)
        # We log it but usually keep it separate from the final answer in RAG
        # Unless we want to prepend it: content = f"<think>\n{reasoning}\n</think>\n\n{content}"
    
    return content
