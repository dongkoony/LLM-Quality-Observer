from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Dashboard 서비스 설정"""
    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# SQLAlchemy 엔진 및 세션 생성
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM Base
Base = declarative_base()


def get_db():
    """
    FastAPI dependency로 사용할 DB 세션 생성 함수.

    Yields:
        Session: SQLAlchemy 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
