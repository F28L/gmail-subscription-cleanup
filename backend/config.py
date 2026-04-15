from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/auth/callback"
    database_url: str = "sqlite+aiosqlite:///./subscriptions.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
