"""
Configuration Management

Centralized environment variable loading and validation.
"""

from __future__ import annotations
import os
from typing import Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration from environment variables"""

    # ===== TEMPORAL =====
    TEMPORAL_ADDRESS: str = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "default")
    TEMPORAL_API_KEY: Optional[str] = os.getenv("TEMPORAL_API_KEY")
    TEMPORAL_TASK_QUEUE: str = os.getenv("TEMPORAL_TASK_QUEUE", "quest-company-queue")

    @staticmethod
    def _parse_cloudinary_url() -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse CLOUDINARY_URL into components.
        Format: cloudinary://api_key:api_secret@cloud_name

        Returns:
            Tuple of (cloud_name, api_key, api_secret)
        """
        cloudinary_url = os.getenv("CLOUDINARY_URL")
        if not cloudinary_url:
            return (None, None, None)

        try:
            # Remove cloudinary:// prefix
            if cloudinary_url.startswith("cloudinary://"):
                cloudinary_url = cloudinary_url[13:]

            # Parse: api_key:api_secret@cloud_name
            if "@" in cloudinary_url:
                auth, cloud_name = cloudinary_url.split("@", 1)
                if ":" in auth:
                    api_key, api_secret = auth.split(":", 1)
                    return (cloud_name, api_key, api_secret)
        except Exception:
            pass

        return (None, None, None)

    # ===== DATABASE =====
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ===== AI SERVICES =====
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # ===== SEARCH & RESEARCH =====
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")
    EXA_API_KEY: Optional[str] = os.getenv("EXA_API_KEY")
    LINKUP_API_KEY: Optional[str] = os.getenv("LINKUP_API_KEY")
    FIRECRAWL_API_KEY: Optional[str] = os.getenv("FIRECRAWL_API_KEY")
    CRAWL4AI_SERVICE_URL: Optional[str] = os.getenv("CRAWL4AI_SERVICE_URL")

    # ===== IMAGE SERVICES =====
    REPLICATE_API_TOKEN: Optional[str] = os.getenv("REPLICATE_API_TOKEN")
    CLOUDINARY_URL: Optional[str] = os.getenv("CLOUDINARY_URL")

    # Cloudinary components (can be set individually or parsed from CLOUDINARY_URL)
    _cloudinary_parsed = _parse_cloudinary_url.__func__()
    CLOUDINARY_CLOUD_NAME: Optional[str] = (
        os.getenv("CLOUDINARY_CLOUD_NAME") or _cloudinary_parsed[0]
    )
    CLOUDINARY_API_KEY: Optional[str] = (
        os.getenv("CLOUDINARY_API_KEY") or _cloudinary_parsed[1]
    )
    CLOUDINARY_API_SECRET: Optional[str] = (
        os.getenv("CLOUDINARY_API_SECRET") or _cloudinary_parsed[2]
    )

    FLUX_API_KEY: Optional[str] = os.getenv("FLUX_API_KEY")  # Black Forest Labs direct API

    # ===== KNOWLEDGE GRAPH =====
    ZEP_API_KEY: Optional[str] = os.getenv("ZEP_API_KEY")

    # ===== FASTAPI =====
    API_KEY: str = os.getenv("API_KEY", "change-this-secret-key")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # ===== APPLICATION SETTINGS =====
    DEFAULT_APP: str = os.getenv("DEFAULT_APP", "relocation")
    AUTO_PUBLISH: bool = os.getenv("AUTO_PUBLISH", "true").lower() == "true"

    # Research settings
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    MAX_RESEARCH_ATTEMPTS: int = int(os.getenv("MAX_RESEARCH_ATTEMPTS", "2"))

    # Image settings
    GENERATE_FEATURED_IMAGES: bool = os.getenv("GENERATE_FEATURED_IMAGES", "true").lower() == "true"
    LOGO_SIZE: str = os.getenv("LOGO_SIZE", "400x400")

    # Sequential image settings (Flux Kontext)
    FLUX_MODEL: str = os.getenv("FLUX_MODEL", "kontext-pro")  # or "kontext-max"
    MIN_CONTENT_IMAGES: int = int(os.getenv("MIN_CONTENT_IMAGES", "3"))
    MAX_CONTENT_IMAGES: int = int(os.getenv("MAX_CONTENT_IMAGES", "5"))
    GENERATE_SEQUENTIAL_IMAGES: bool = os.getenv("GENERATE_SEQUENTIAL_IMAGES", "true").lower() == "true"

    # Cost limits
    MAX_COST_PER_COMPANY: float = float(os.getenv("MAX_COST_PER_COMPANY", "0.20"))
    ENABLE_COST_ALERTS: bool = os.getenv("ENABLE_COST_ALERTS", "true").lower() == "true"

    # Playwright settings
    PLAYWRIGHT_BROWSER: str = os.getenv("PLAYWRIGHT_BROWSER", "chromium")
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

    @classmethod
    def validate_required(cls) -> list[str]:
        """
        Validate required environment variables.

        Returns:
            List of missing required variables (empty if all present)
        """
        required = {
            "DATABASE_URL": cls.DATABASE_URL,
            "SERPER_API_KEY": cls.SERPER_API_KEY,
            "EXA_API_KEY": cls.EXA_API_KEY,
            "ZEP_API_KEY": cls.ZEP_API_KEY,
            "REPLICATE_API_TOKEN": cls.REPLICATE_API_TOKEN,
            # CLOUDINARY_URL is optional - only needed for image hosting
            # "CLOUDINARY_URL": cls.CLOUDINARY_URL,
        }

        # At least one AI provider
        has_ai = any([
            cls.GOOGLE_API_KEY,
            cls.OPENAI_API_KEY,
            cls.ANTHROPIC_API_KEY
        ])

        missing = [
            key for key, value in required.items()
            if not value
        ]

        if not has_ai:
            missing.append("GOOGLE_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY")

        return missing

    @classmethod
    def get_ai_model(cls) -> tuple[str, str]:
        """
        Get preferred AI model for Pydantic AI.

        Returns:
            Tuple of (provider, model_name)
        """
        # Anthropic Claude for article generation (Haiku for cost savings)
        if cls.ANTHROPIC_API_KEY:
            return ("anthropic", "claude-3-5-haiku-20241022")
        elif cls.GOOGLE_API_KEY:
            return ("google-gla", "gemini-1.5-flash")
        elif cls.OPENAI_API_KEY:
            return ("openai", "gpt-4o-mini")
        else:
            raise ValueError("No AI API key configured")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT.lower() == "production"

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        """Export config as dictionary (sanitized)"""
        return {
            "temporal_address": cls.TEMPORAL_ADDRESS,
            "temporal_namespace": cls.TEMPORAL_NAMESPACE,
            "task_queue": cls.TEMPORAL_TASK_QUEUE,
            "environment": cls.ENVIRONMENT,
            "default_app": cls.DEFAULT_APP,
            "has_database": bool(cls.DATABASE_URL),
            "has_serper": bool(cls.SERPER_API_KEY),
            "has_exa": bool(cls.EXA_API_KEY),
            "has_zep": bool(cls.ZEP_API_KEY),
            "has_replicate": bool(cls.REPLICATE_API_TOKEN),
            "has_cloudinary": bool(cls.CLOUDINARY_URL),
            "has_ai": bool(cls.GOOGLE_API_KEY or cls.OPENAI_API_KEY or cls.ANTHROPIC_API_KEY),
        }


# Singleton instance
config = Config()
