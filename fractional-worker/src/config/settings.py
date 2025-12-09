"""Configuration management for LinkedIn Apify Scraper Worker."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Temporal Configuration
    temporal_host: str = "europe-west3.gcp.api.temporal.io:7233"
    temporal_namespace: str = "quickstart-quest.zivkb"
    temporal_task_queue: str = "apify-linkedin-queue"
    temporal_api_key: str = ""
    temporal_tls: bool = True

    # Database
    database_url: str = ""

    # Apify
    apify_api_key: str = ""
    apify_task_id: str = "infrastructure_quest/rapid-linkedin-jobs-scraper-free-jobs-scraper-task"
    apify_base_url: str = "https://api.apify.com/v2"

    # AI APIs
    google_api_key: str = ""
    openai_api_key: str = ""
    zep_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
