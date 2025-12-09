from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Temporal
    temporal_host: str = "europe-west3.gcp.api.temporal.io:7233"
    temporal_namespace: str = "quickstart-quest.zivkb"
    temporal_task_queue: str = "fractional-jobs-queue"
    temporal_api_key: str = ""
    temporal_tls: bool = True

    # Database
    database_url: str = ""

    # Zep
    zep_api_key: str = ""

    # Crawl4AI service (your existing scraper)
    crawl4ai_url: str = "http://localhost:8000"

    # OpenAI for skill extraction
    openai_api_key: str = ""

    # Gemini for fast/cheap classification
    google_api_key: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
