"""
API Key Authentication

Simple API key validation for protecting endpoints.
"""

import os
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Get expected API key from environment
    expected_api_key = os.getenv("API_KEY")

    if not expected_api_key:
        # No API key configured - allow all requests (dev mode)
        # WARNING: Don't use this in production!
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Include X-API-Key header.",
        )

    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key
