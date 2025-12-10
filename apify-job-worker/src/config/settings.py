"""Configuration management for LinkedIn Apify Scraper Worker."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Temporal Configuration
    temporal_host: str = "europe-west3.gcp.api.temporal.io:7233"
    temporal_namespace: str = "job-workflows.zivkb"
    temporal_task_queue: str = "apify-linkedin-queue"
    temporal_api_key: str = ""
    temporal_tls: bool = True

    # Database
    database_url: str = ""

    # Apify
    apify_api_key: str = ""
    apify_task_id: str = "BHzefUZlZRKWxkTck"  # Numeric task ID (works with Apify API)
    apify_base_url: str = "https://api.apify.com/v2"

    # AI APIs
    google_api_key: str = ""
    gemini_api_key: str = ""  # For Pydantic AI
    openai_api_key: str = ""

    # ZEP Knowledge Graph
    zep_account_id: str = ""
    zep_api_key: str = ""
    zep_base_url: str = "https://api.getzep.com"
    zep_graph_id: str = "jobs-tech"

    # Pydantic AI Gateway & Logfire
    pydantic_gateway_api_key: str = ""
    pydantic_logifire_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
