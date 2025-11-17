from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 환경
    app_env: str = "local"
    log_level: str = "INFO"

    # DB
    database_url: str

    # LLM (Judge 용)
    llm_api_base_url: str | None = None
    llm_api_key: str
    openai_model_judge: str = "gpt-5-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
