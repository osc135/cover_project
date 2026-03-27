from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# .env lives in the project root (one level above backend/)
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cover:cover@localhost:5432/cover"
    google_maps_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_chat_model: str = "gpt-4o"

    class Config:
        env_file = str(ENV_FILE)
        extra = "ignore"

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses the asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
