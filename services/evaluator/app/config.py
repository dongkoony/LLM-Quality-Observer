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

    # Batch Evaluation Scheduler
    enable_auto_evaluation: bool = True  # 자동 평가 활성화 여부
    evaluation_interval_minutes: int = 60  # 평가 주기 (분 단위, 기본 1시간)
    evaluation_batch_size: int = 10  # 한 번에 평가할 로그 개수
    evaluation_judge_type: str = "rule"  # 자동 평가 시 사용할 judge 타입 ('rule' or 'llm')

    # Notification Settings
    slack_webhook_url: str | None = None  # Slack 웹훅 URL
    discord_webhook_url: str | None = None  # Discord 웹훅 URL
    notification_score_threshold: int = 3  # 알림 보낼 점수 임계값 (이하일 때 알림)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
