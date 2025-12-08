from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db import Base


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

    # 1:N 관계 (한 로그에 여러 평가가 있을 수 있음)
    evaluations = relationship(
        "LLMEvaluation",
        back_populates="log",
        cascade="all, delete-orphan",
    )


class LLMEvaluation(Base):
    """
    LLM 응답에 대한 평가 결과를 저장하는 테이블.
    Evaluator 서비스에서 생성하고, Gateway API에서는 읽기만 함.
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

    # LLM-as-a-Judge 세부 점수 (옵션널)
    score_instruction_following = Column(Integer, nullable=True)
    score_truthfulness = Column(Integer, nullable=True)

    # 문제가 있는 응답인지
    is_flagged = Column(Boolean, nullable=False, default=False)

    # 평가 라벨
    label = Column(String(64), nullable=False)

    # 어떤 judge 모델/룰로 평가했는지 (예: "rule-basic-v1", "gpt-4o-mini" 등)
    judge_model = Column(String(128), nullable=False, default="rule-basic-v1")

    # 평가 근거 또는 코멘트
    comment = Column(Text, nullable=True)

    # LLM judge의 원본 응답 (디버깅용, 옵션널)
    raw_judge_response = Column(Text, nullable=True)

    # N:1 관계 (여러 평가가 한 로그를 참조)
    log = relationship("LLMLog", back_populates="evaluations")
