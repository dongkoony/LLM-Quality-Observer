from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user_id = Column(String(128), nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    model_version = Column(String(64), nullable=True)
    latency_ms = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="success")


class LLMEvalResult(Base):
    __tablename__ = "llm_eval_results"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    log_id = Column(Integer, ForeignKey("llm_logs.id"), nullable=False, index=True)

    rule_score = Column(Float, nullable=False)
    label = Column(String(16), nullable=False)
