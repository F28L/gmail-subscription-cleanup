from pydantic_settings import BaseSettings


class StreamlitConfig(BaseSettings):
    api_base_url: str = "http://localhost:8500"

    class Config:
        extra = "ignore"


def get_api_base_url() -> str:
    try:
        config = StreamlitConfig()
        return config.api_base_url
    except Exception:
        return "http://localhost:8000"
