from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    user_id: str | None = None
    model_version: str | None = None


class ChatResponse(BaseModel):
    response: str
    model_version: str | None = None
    latency_ms: float | None = None


class LLMLogRead(BaseModel):
    id: int
    created_at: datetime
    user_id: str | None
    prompt: str
    response: str
    model_version: str | None
    latency_ms: float | None
    status: str

    class Config:
        from_attributes = True


# Dashboard API Schemas

class DashboardSummary(BaseModel):
    """대시보드 Overview 페이지용 전체 통계"""
    total_logs: int
    total_evaluated: int
    avg_latency_ms: float | None
    avg_score: float | None


class LogListItem(BaseModel):
    """로그 목록용 간략한 로그 정보"""
    id: int
    created_at: datetime
    user_id: str | None
    prompt: str
    response: str
    model_version: str | None
    latency_ms: float | None
    status: str

    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    """로그 목록 응답 (페이지네이션 포함)"""
    logs: list[LogListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class EvaluationRead(BaseModel):
    """평가 결과 읽기용 스키마"""
    id: int
    created_at: datetime
    log_id: int
    overall_score: int
    is_flagged: bool
    label: str
    judge_model: str
    comment: str | None
    # 로그 정보도 함께 포함
    log_prompt: str | None = None
    log_response: str | None = None
    log_model_version: str | None = None

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """평가 목록 응답 (페이지네이션 포함)"""
    evaluations: list[EvaluationRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class ModelStats(BaseModel):
    """모델별 통계"""
    model_version: str
    total_requests: int
    avg_latency_ms: float | None
    avg_score: float | None
    total_evaluated: int


class ModelStatsResponse(BaseModel):
    """모델 통계 목록"""
    models: list[ModelStats]
