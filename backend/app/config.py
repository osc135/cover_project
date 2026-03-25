from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cover:cover@localhost:5432/cover"
    google_maps_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_chat_model: str = "gpt-4o"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
