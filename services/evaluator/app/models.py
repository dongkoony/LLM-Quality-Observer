from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from .db import Base


class LLMLog(Base):
    """
    gateway-api에서 쓰는 llm_logs 테이블과 동일한 구조여야 함.
    여기서는 Evaluator가 읽기만 하면 되므로, 최소 필드만 정의해도 OK.
    """

    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user_id = Column(String(255), nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_version = Column(String(255), nullable=True)

    latency_ms = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)

    evaluations = relationship(
        "LLMEvaluation",
        back_populates="log",
        cascade="all, delete-orphan",
    )


class LLMEvaluation(Base):
    """
    LLM 응답에 대한 품질 평가 결과를 저장하는 테이블.
    """

    __tablename__ = "llm_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    log_id = Column(Integer, ForeignKey("llm_logs.id"), nullable=False, index=True)

    # 점수 (1~5 스케일)
    score_overall = Column(Integer, nullable=False)
    score_instruction_following = Column(Integer, nullable=True)
    score_truthfulness = Column(Integer, nullable=True)

    comments = Column(Text, nullable=True)

    judge_model = Column(String(255), nullable=False)
    raw_judge_response = Column(Text, nullable=True)

    log = relationship("LLMLog", back_populates="evaluations")
