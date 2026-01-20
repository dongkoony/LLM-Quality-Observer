from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from db import get_db, settings
from models import LLMLog, LLMEvaluation
from schemas import (
    SummaryMetricsResponse,
    ModelBreakdownResponse,
    ModelMetricsItem,
)

# FastAPI 앱 생성
app = FastAPI(
    title="LLM Quality Observer - Dashboard Service",
    description="LLM 로그 및 평가 결과를 집계하여 모니터링 지표를 제공하는 대시보드 서비스",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트.
    서비스가 정상 작동하는지 확인용.
    """
    return {
        "status": "ok",
        "env": settings.app_env,
    }


@app.get("/metrics/summary", response_model=SummaryMetricsResponse)
def get_summary_metrics(db: Session = Depends(get_db)):
    """
    전체 시스템의 요약 메트릭을 반환하는 엔드포인트.

    집계 항목:
    - total_logs: 전체 LLM 로그 개수
    - evaluated_logs: 평가 완료된 로그 개수
    - pending_logs: 평가 대기 중인 로그 개수
    - avg_latency_ms: 평균 응답 지연시간
    - avg_score: 평균 평가 점수
    - flagged_ratio: 플래그된 응답 비율

    Args:
        db: SQLAlchemy 세션

    Returns:
        SummaryMetricsResponse: 요약 메트릭
    """
    # 1. 전체 로그 개수
    total_logs = db.query(func.count(LLMLog.id)).scalar() or 0

    # 2. 평가 완료된 로그 개수 (중복 제거)
    evaluated_logs = db.query(func.count(func.distinct(LLMEvaluation.log_id))).scalar() or 0

    # 3. 대기 중인 로그 개수
    pending_logs = total_logs - evaluated_logs

    # 4. 평균 지연시간 (ms)
    avg_latency_ms = db.query(func.avg(LLMLog.latency_ms)).scalar()
    if avg_latency_ms is not None:
        avg_latency_ms = round(float(avg_latency_ms), 2)

    # 5. 평균 평가 점수
    avg_score = None
    if evaluated_logs > 0:
        avg_score = db.query(func.avg(LLMEvaluation.overall_score)).scalar()
        if avg_score is not None:
            avg_score = round(float(avg_score), 2)

    # 6. 플래그된 응답 비율
    flagged_ratio = None
    if evaluated_logs > 0:
        flagged_count = db.query(func.count(LLMEvaluation.id)).filter(
            LLMEvaluation.is_flagged == True
        ).scalar() or 0
        flagged_ratio = round(flagged_count / evaluated_logs, 4)

    return SummaryMetricsResponse(
        total_logs=total_logs,
        evaluated_logs=evaluated_logs,
        pending_logs=pending_logs,
        avg_latency_ms=avg_latency_ms,
        avg_score=avg_score,
        flagged_ratio=flagged_ratio,
    )


@app.get("/metrics/by_model", response_model=ModelBreakdownResponse)
def get_metrics_by_model(db: Session = Depends(get_db)):
    """
    모델별 메트릭을 집계하여 반환하는 엔드포인트.

    각 model_version별로:
    - total_logs: 해당 모델의 전체 로그 개수
    - avg_latency_ms: 평균 응답 지연시간
    - avg_score: 평균 평가 점수 (평가된 로그만)

    Args:
        db: SQLAlchemy 세션

    Returns:
        ModelBreakdownResponse: 모델별 메트릭 리스트
    """
    # model_version별로 그룹화하여 집계
    query = (
        db.query(
            LLMLog.model_version,
            func.count(LLMLog.id).label("total_logs"),
            func.avg(LLMLog.latency_ms).label("avg_latency_ms"),
        )
        .filter(LLMLog.model_version.isnot(None))  # NULL 제외
        .group_by(LLMLog.model_version)
        .order_by(func.count(LLMLog.id).desc())  # 로그 개수 많은 순
    )

    results = query.all()

    model_metrics = []
    for row in results:
        model_version = row.model_version
        total_logs = row.total_logs
        avg_latency_ms = round(float(row.avg_latency_ms), 2) if row.avg_latency_ms else None

        # 해당 모델의 평균 평가 점수 계산
        avg_score_query = (
            db.query(func.avg(LLMEvaluation.overall_score))
            .join(LLMLog, LLMEvaluation.log_id == LLMLog.id)
            .filter(LLMLog.model_version == model_version)
        )
        avg_score = avg_score_query.scalar()
        avg_score = round(float(avg_score), 2) if avg_score is not None else None

        model_metrics.append(
            ModelMetricsItem(
                model_version=model_version,
                total_logs=total_logs,
                avg_latency_ms=avg_latency_ms,
                avg_score=avg_score,
            )
        )

    return ModelBreakdownResponse(models=model_metrics)
