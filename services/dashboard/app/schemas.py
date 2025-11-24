from typing import List, Optional
from pydantic import BaseModel, Field


class SummaryMetricsResponse(BaseModel):
    """
    전체 시스템의 요약 메트릭 응답 스키마.
    """
    total_logs: int = Field(..., description="전체 LLM 로그 개수")
    evaluated_logs: int = Field(..., description="평가 완료된 로그 개수")
    pending_logs: int = Field(..., description="평가 대기 중인 로그 개수")
    avg_latency_ms: Optional[float] = Field(None, description="평균 응답 지연시간 (ms)")
    avg_score: Optional[float] = Field(None, description="평균 평가 점수 (1~5)")
    flagged_ratio: Optional[float] = Field(None, description="플래그된 응답 비율 (0~1)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_logs": 123,
                "evaluated_logs": 80,
                "pending_logs": 43,
                "avg_latency_ms": 1820.5,
                "avg_score": 4.3,
                "flagged_ratio": 0.05
            }
        }


class ModelMetricsItem(BaseModel):
    """
    모델별 메트릭 항목 스키마.
    """
    model_version: str = Field(..., description="모델 버전")
    total_logs: int = Field(..., description="해당 모델의 전체 로그 개수")
    avg_latency_ms: Optional[float] = Field(None, description="평균 응답 지연시간 (ms)")
    avg_score: Optional[float] = Field(None, description="평균 평가 점수 (1~5)")

    class Config:
        json_schema_extra = {
            "example": {
                "model_version": "gpt-5-mini",
                "total_logs": 100,
                "avg_latency_ms": 1700.2,
                "avg_score": 4.4
            }
        }


class ModelBreakdownResponse(BaseModel):
    """
    모델별 메트릭 집계 응답 스키마.
    """
    models: List[ModelMetricsItem] = Field(..., description="모델별 메트릭 리스트")

    class Config:
        json_schema_extra = {
            "example": {
                "models": [
                    {
                        "model_version": "gpt-5-mini",
                        "total_logs": 100,
                        "avg_latency_ms": 1700.2,
                        "avg_score": 4.4
                    }
                ]
            }
        }
