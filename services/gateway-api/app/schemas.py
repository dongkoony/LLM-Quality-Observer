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
    score_instruction_following: int | None = None
    score_truthfulness: int | None = None
    is_flagged: bool
    label: str
    judge_model: str
    comment: str | None
    raw_judge_response: str | None = None
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


class TimeSeriesDataPoint(BaseModel):
    """시간별 데이터 포인트"""
    date: str  # YYYY-MM-DD 형식
    avg_score: float | None
    avg_latency_ms: float | None
    total_requests: int
    total_evaluated: int


class TimeSeriesResponse(BaseModel):
    """시간별 추이 데이터"""
    data: list[TimeSeriesDataPoint]


# Analytics API Schemas (v0.6.0)

class HourlyTrendDataPoint(BaseModel):
    """시간대별 데이터 포인트 (hourly breakdown)"""
    hour: str  # YYYY-MM-DD HH:00:00 형식
    avg_score: float | None
    avg_latency_ms: float | None
    total_requests: int
    total_evaluated: int
    error_rate: float | None  # 에러율 (%)


class HourlyTrendResponse(BaseModel):
    """시간대별 추이 데이터 (Analytics)"""
    data: list[HourlyTrendDataPoint]
    summary: dict  # 전체 통계 요약


class ModelComparisonDetail(BaseModel):
    """모델 상세 비교 데이터"""
    model_version: str
    total_requests: int
    success_rate: float  # 성공률 (%)
    error_rate: float  # 에러율 (%)
    avg_latency_ms: float | None
    p50_latency_ms: float | None
    p95_latency_ms: float | None
    p99_latency_ms: float | None
    avg_score: float | None
    total_evaluated: int
    low_quality_count: int  # 점수 < 3인 개수
    high_quality_count: int  # 점수 >= 4인 개수


class ModelComparisonResponse(BaseModel):
    """모델 비교 응답"""
    models: list[ModelComparisonDetail]
    best_model_by_latency: str | None
    best_model_by_quality: str | None
    best_model_by_stability: str | None  # 가장 낮은 에러율


class AlertInfo(BaseModel):
    """Alert 정보"""
    alert_name: str
    severity: str
    service: str
    summary: str | None
    description: str | None
    started_at: str
    ended_at: str | None
    duration_seconds: int | None
    status: str  # firing, resolved


class AlertHistoryResponse(BaseModel):
    """Alert 이력 응답"""
    alerts: list[AlertInfo]
    total: int
    page: int
    page_size: int
    total_pages: int
