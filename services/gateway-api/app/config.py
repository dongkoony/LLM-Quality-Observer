from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"

    database_url: str | None = None
    openai_model_main: str = "gpt-5-mini"

    llm_api_base_url: str | None = None
    llm_api_key: str | None = None

    # Fallback models (v0.7.0 Phase 4)
    fallback_models: list[str] = ["gpt-4o-mini", "claude-haiku-4"]
    llm_timeout_seconds: int = 30

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
