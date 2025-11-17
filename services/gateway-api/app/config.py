from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"

    database_url: str
    openai_model_main: str = "gpt-5-mini"
    
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
