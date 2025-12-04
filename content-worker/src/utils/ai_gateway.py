"""
AI Gateway Utility

Provides unified access to AI models via Pydantic AI Gateway or direct providers.
Gateway uses OpenAI-compatible proxy for unified access.

Usage:
    from src.utils.ai_gateway import get_completion, get_completion_async

    # Sync
    response = get_completion("What is 2+2?", model="gpt-4o-mini")

    # Async
    response = await get_completion_async("What is 2+2?", model="gpt-4o-mini")
"""

import os
import openai
from typing import Optional, List, Dict, Any

from src.utils.config import config


# Gateway configuration
GATEWAY_BASE_URL = "https://gateway.pydantic.dev/proxy/chat/"

# Model aliases for convenience
MODEL_ALIASES = {
    # Fast models (for quick tasks)
    "fast": "gpt-4o-mini",
    "quick": "gpt-4o-mini",

    # Quality models (for complex tasks)
    "quality": "gpt-4o",
    "smart": "gpt-4o",

    # Specific models
    "gpt4": "gpt-4o",
    "gpt4-mini": "gpt-4o-mini",
    "claude": "claude-sonnet-4-5",
    "claude-haiku": "claude-3-5-haiku-latest",
    "claude-sonnet": "claude-sonnet-4-5",
}


def get_gateway_client() -> Optional[openai.Client]:
    """
    Get OpenAI client configured for Pydantic AI Gateway.

    Returns None if gateway key is not configured.
    """
    gateway_key = os.environ.get("PYDANTIC_AI_GATEWAY_API_KEY") or getattr(
        config, "PYDANTIC_AI_GATEWAY_API_KEY", None
    )

    if not gateway_key:
        return None

    return openai.Client(
        base_url=GATEWAY_BASE_URL,
        api_key=gateway_key,
    )


def get_async_gateway_client() -> Optional[openai.AsyncClient]:
    """
    Get async OpenAI client configured for Pydantic AI Gateway.

    Returns None if gateway key is not configured.
    """
    gateway_key = os.environ.get("PYDANTIC_AI_GATEWAY_API_KEY") or getattr(
        config, "PYDANTIC_AI_GATEWAY_API_KEY", None
    )

    if not gateway_key:
        return None

    return openai.AsyncClient(
        base_url=GATEWAY_BASE_URL,
        api_key=gateway_key,
    )


def resolve_model(model: str) -> str:
    """Resolve model alias to actual model name."""
    return MODEL_ALIASES.get(model, model)


def get_completion(
    prompt: str,
    model: str = "gpt-4o-mini",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Get a completion from AI via Gateway or direct provider.

    Args:
        prompt: User prompt
        model: Model name or alias (fast, quality, gpt4, claude, etc.)
        system_prompt: Optional system prompt
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text response
    """
    model = resolve_model(model)

    # Try Gateway first
    client = get_gateway_client()
    if client:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # Fallback to direct Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or getattr(
        config, "ANTHROPIC_API_KEY", None
    )
    if anthropic_key:
        import anthropic

        client = anthropic.Anthropic(api_key=anthropic_key)

        # Map model to Anthropic equivalent
        if "gpt" in model.lower():
            anthropic_model = "claude-3-5-haiku-latest"
        elif "claude" in model.lower():
            anthropic_model = model.replace("claude-", "claude-")
        else:
            anthropic_model = "claude-3-5-haiku-latest"

        response = client.messages.create(
            model=anthropic_model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    raise ValueError("No AI API key configured (need PYDANTIC_AI_GATEWAY_API_KEY or ANTHROPIC_API_KEY)")


async def get_completion_async(
    prompt: str,
    model: str = "gpt-4o-mini",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Get a completion from AI via Gateway or direct provider (async).

    Args:
        prompt: User prompt
        model: Model name or alias (fast, quality, gpt4, claude, etc.)
        system_prompt: Optional system prompt
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text response
    """
    model = resolve_model(model)

    # Try Gateway first
    client = get_async_gateway_client()
    if client:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # Fallback to direct Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or getattr(
        config, "ANTHROPIC_API_KEY", None
    )
    if anthropic_key:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=anthropic_key)

        # Map model to Anthropic equivalent
        if "gpt" in model.lower():
            anthropic_model = "claude-3-5-haiku-latest"
        elif "claude" in model.lower():
            anthropic_model = model
        else:
            anthropic_model = "claude-3-5-haiku-latest"

        response = await client.messages.create(
            model=anthropic_model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    raise ValueError("No AI API key configured (need PYDANTIC_AI_GATEWAY_API_KEY or ANTHROPIC_API_KEY)")


def is_gateway_available() -> bool:
    """Check if Gateway is configured."""
    gateway_key = os.environ.get("PYDANTIC_AI_GATEWAY_API_KEY") or getattr(
        config, "PYDANTIC_AI_GATEWAY_API_KEY", None
    )
    return bool(gateway_key)
