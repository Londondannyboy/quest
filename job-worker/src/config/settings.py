from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Temporal
    temporal_host: str = "job-workflows.zivkb.tmprl.cloud:7233"
    temporal_namespace: str = "job-workflows.zivkb"
    temporal_task_queue: str = "job-scraping-queue"
    temporal_api_key: str = ""

    # Database
    database_url: str = ""

    # Zep
    zep_api_key: str = ""

    # Crawl4AI service (your existing scraper)
    crawl4ai_url: str = "http://localhost:8000"

    # OpenAI for skill extraction
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
