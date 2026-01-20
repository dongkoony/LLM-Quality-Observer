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

    # Email Notification Settings
    smtp_host: str | None = None  # SMTP 서버 주소
    smtp_port: int = 587  # SMTP 포트 (기본 587 - TLS)
    smtp_username: str | None = None  # SMTP 사용자명
    smtp_password: str | None = None  # SMTP 비밀번호
    smtp_from_email: str | None = None  # 발신자 이메일
    smtp_to_emails: str | None = None  # 수신자 이메일들 (쉼표로 구분)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
