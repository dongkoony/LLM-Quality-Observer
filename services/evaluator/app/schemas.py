from typing import Optional
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """
    룰 기반 평가 함수가 반환하는 평가 결과 스키마.
    이 스키마를 기반으로 LLMEvaluation 모델 인스턴스를 생성함.
    """
    log_id: int
    overall_score: int = Field(..., ge=1, le=5, description="1~5 스케일 점수")
    is_flagged: bool = Field(default=False, description="문제가 있는 응답인지 여부")
    label: str = Field(..., description="평가 라벨 (예: ok, too_short, error_like)")
    judge_model: str = Field(default="rule-basic-v1", description="평가에 사용된 모델/룰 버전")
    comment: Optional[str] = Field(default=None, description="평가 근거 또는 코멘트")

    class Config:
        from_attributes = True  # Pydantic v2에서 ORM 모드 활성화
