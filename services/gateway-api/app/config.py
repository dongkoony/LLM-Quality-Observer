from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"

    database_url: str
    openai_model_main: str = "gpt-5-mini"

    llm_api_base_url: str | None = None
    llm_api_key: str | None = None

    # Fallback models (v0.7.0 Phase 4)
    fallback_models: list[str] = ["gpt-4o-mini", "claude-haiku-4"]
    llm_timeout_seconds: int = 30

    log_level: str = "INFO"

    # JWT Authentication (v0.8.0)
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # Authentication settings (v0.8.0)
    enable_authentication: bool = False
    require_authentication: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
