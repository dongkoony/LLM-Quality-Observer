from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db import Base


class LLMLog(Base):
    """
    gateway-api에서 생성하는 llm_logs 테이블.
    Evaluator는 이 테이블을 읽기만 함.
    """
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

    # 1:N 관계 (한 로그에 여러 평가가 있을 수 있음)
    evaluations = relationship(
        "LLMEvaluation",
        back_populates="log",
        cascade="all, delete-orphan",
    )


class LLMEvaluation(Base):
    """
    LLM 응답에 대한 평가 결과를 저장하는 테이블.
    룰 기반 또는 LLM-as-a-judge 방식으로 평가한 결과를 기록.
    """
    __tablename__ = "llm_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 어떤 로그에 대한 평가인지
    log_id = Column(Integer, ForeignKey("llm_logs.id"), nullable=False, index=True)

    # 평가 점수 (1~5 스케일)
    overall_score = Column(Integer, nullable=False)

    # 문제가 있는 응답인지 (예: 에러 메시지, 너무 짧음 등)
    is_flagged = Column(Boolean, nullable=False, default=False)

    # 평가 라벨 (예: "ok", "too_short", "error_like" 등)
    label = Column(String(64), nullable=False)

    # 어떤 judge 모델/룰로 평가했는지 (예: "rule-basic-v1", "gpt-5-mini")
    judge_model = Column(String(128), nullable=False, default="rule-basic-v1")

    # 평가 근거 또는 코멘트
    comment = Column(Text, nullable=True)

    # N:1 관계 (여러 평가가 한 로그를 참조)
    log = relationship("LLMLog", back_populates="evaluations")
