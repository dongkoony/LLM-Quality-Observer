from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

Base = declarative_base()


@lru_cache
def get_engine():
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to initialize the database engine.")

    return create_engine(settings.database_url, future=True)


@lru_cache
def get_session_factory():
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=get_engine(),
        future=True,
    )


def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
