from fastapi import FastAPI, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, select, distinct
import math
import time
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .db import Base, engine, get_db
from .models import LLMLog, LLMEvaluation
from .schemas import (
    ChatRequest,
    ChatResponse,
    DashboardSummary,
    LogListResponse,
    LogListItem,
    EvaluationListResponse,
    EvaluationRead,
    ModelStatsResponse,
    ModelStats,
    TimeSeriesResponse,
    TimeSeriesDataPoint,
    HourlyTrendResponse,
    HourlyTrendDataPoint,
    ModelComparisonResponse,
    ModelComparisonDetail,
    AlertHistoryResponse,
    AlertInfo,
)
from .llm_client import call_llm
from .config import settings
from .metrics import (
    MetricsMiddleware,
    record_llm_request,
    record_db_query,
    record_log_saved,
)

# 최초 실행 시 테이블 생성 (간단 버전)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Quality Observer - Gateway API")

# Prometheus 메트릭 미들웨어 추가
app.add_middleware(MetricsMiddleware)

# CORS 설정 추가 (웹 대시보드에서 API 호출을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def resolve_model_version(request_model: str | None) -> str:
    """
    요청에서 들어온 model_version이 없거나 Swagger 기본값("string")이면
    환경변수로 설정한 기본 모델(openai_model_main)을 사용한다.
    """
    if not request_model or request_model == "string":
        return settings.openai_model_main
    return request_model


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 실제로 사용할 모델 이름 계산
    used_model = resolve_model_version(request.model_version)

    # LLM 호출 (사용할 모델 명을 넘겨줌)
    llm_start = time.time()
    response_text, latency_ms = call_llm(request.prompt, used_model)
    llm_duration = time.time() - llm_start

    # LLM 메트릭 기록
    record_llm_request(
        model=used_model,
        status="success",
        duration_seconds=llm_duration
    )

    # DB 로그 저장
    db_start = time.time()
    log = LLMLog(
        user_id=request.user_id,
        prompt=request.prompt,
        response=response_text,
        model_version=used_model,
        latency_ms=latency_ms,
        status="success",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    db_duration = time.time() - db_start

    # DB 메트릭 기록
    record_db_query(operation="insert", table="llm_logs", duration_seconds=db_duration)
    record_log_saved(status="success")

    # 클라이언트 응답
    return ChatResponse(
        response=response_text,
        model_version=used_model,
        latency_ms=latency_ms,
    )


# ==================== Dashboard API ====================


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    대시보드 Overview 페이지용 전체 통계 조회.
    """
    # 총 로그 수
    total_logs = db.query(func.count(LLMLog.id)).scalar() or 0

    # 평가된 로그 수
    total_evaluated = db.query(func.count(distinct(LLMEvaluation.log_id))).scalar() or 0

    # 평균 지연시간
    avg_latency = db.query(func.avg(LLMLog.latency_ms)).scalar()

    # 평균 점수
    avg_score = db.query(func.avg(LLMEvaluation.overall_score)).scalar()

    return DashboardSummary(
        total_logs=total_logs,
        total_evaluated=total_evaluated,
        avg_latency_ms=avg_latency,
        avg_score=avg_score,
    )


@app.get("/api/dashboard/logs", response_model=LogListResponse)
def get_logs(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 로그 수"),
    db: Session = Depends(get_db),
):
    """
    LLM 로그 목록 조회 (페이지네이션).
    최신 로그부터 내림차순으로 반환.
    """
    # 전체 로그 수
    total = db.query(func.count(LLMLog.id)).scalar() or 0

    # 페이지네이션 계산
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # 로그 조회
    logs = (
        db.query(LLMLog)
        .order_by(LLMLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    log_items = [LogListItem.model_validate(log) for log in logs]

    return LogListResponse(
        logs=log_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get("/api/dashboard/evaluations", response_model=EvaluationListResponse)
def get_evaluations(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 평가 수"),
    db: Session = Depends(get_db),
):
    """
    평가 결과 목록 조회 (페이지네이션).
    최신 평가부터 내림차순으로 반환, 로그 정보도 함께 포함.
    """
    # 전체 평가 수
    total = db.query(func.count(LLMEvaluation.id)).scalar() or 0

    # 페이지네이션 계산
    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # 평가 조회 (JOIN으로 로그 정보도 함께)
    evaluations = (
        db.query(LLMEvaluation)
        .join(LLMLog, LLMEvaluation.log_id == LLMLog.id)
        .order_by(LLMEvaluation.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # 응답 생성 (로그 정보 포함)
    eval_items = []
    for evaluation in evaluations:
        eval_dict = {
            "id": evaluation.id,
            "created_at": evaluation.created_at,
            "log_id": evaluation.log_id,
            "overall_score": evaluation.overall_score,
            "score_instruction_following": evaluation.score_instruction_following,
            "score_truthfulness": evaluation.score_truthfulness,
            "is_flagged": evaluation.is_flagged,
            "label": evaluation.label,
            "judge_model": evaluation.judge_model,
            "comment": evaluation.comment,
            "raw_judge_response": evaluation.raw_judge_response,
            "log_prompt": evaluation.log.prompt if evaluation.log else None,
            "log_response": evaluation.log.response if evaluation.log else None,
            "log_model_version": evaluation.log.model_version if evaluation.log else None,
        }
        eval_items.append(EvaluationRead(**eval_dict))

    return EvaluationListResponse(
        evaluations=eval_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get("/api/dashboard/models/stats", response_model=ModelStatsResponse)
def get_model_stats(db: Session = Depends(get_db)):
    """
    모델별 통계 조회.
    각 모델의 총 요청 수, 평균 지연시간, 평균 점수, 평가된 수를 반환.
    """
    # 모델별로 그룹화해서 통계 계산
    model_stats_query = (
        db.query(
            LLMLog.model_version,
            func.count(LLMLog.id).label("total_requests"),
            func.avg(LLMLog.latency_ms).label("avg_latency_ms"),
        )
        .group_by(LLMLog.model_version)
        .all()
    )

    models = []
    for model_version, total_requests, avg_latency in model_stats_query:
        # 해당 모델의 평가 통계
        eval_stats = (
            db.query(
                func.count(distinct(LLMEvaluation.log_id)).label("total_evaluated"),
                func.avg(LLMEvaluation.overall_score).label("avg_score"),
            )
            .join(LLMLog, LLMEvaluation.log_id == LLMLog.id)
            .filter(LLMLog.model_version == model_version)
            .first()
        )

        total_evaluated = eval_stats.total_evaluated or 0
        avg_score = eval_stats.avg_score

        models.append(
            ModelStats(
                model_version=model_version or "unknown",
                total_requests=total_requests,
                avg_latency_ms=avg_latency,
                avg_score=avg_score,
                total_evaluated=total_evaluated,
            )
        )

    return ModelStatsResponse(models=models)


@app.get("/api/dashboard/timeseries", response_model=TimeSeriesResponse)
def get_timeseries(
    days: int = Query(7, ge=1, le=30, description="조회할 일수 (1-30일)"),
    db: Session = Depends(get_db),
):
    """
    시간별 추이 데이터 조회.
    최근 N일간의 일별 통계를 반환.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import cast, Date

    # 시작 날짜 계산 (N일 전부터)
    start_date = datetime.now() - timedelta(days=days)

    # 날짜별 로그 통계
    log_stats = (
        db.query(
            cast(LLMLog.created_at, Date).label("date"),
            func.count(LLMLog.id).label("total_requests"),
            func.avg(LLMLog.latency_ms).label("avg_latency_ms"),
        )
        .filter(LLMLog.created_at >= start_date)
        .group_by(cast(LLMLog.created_at, Date))
        .order_by(cast(LLMLog.created_at, Date))
        .all()
    )

    # 날짜별 평가 통계
    eval_stats_query = (
        db.query(
            cast(LLMLog.created_at, Date).label("date"),
            func.count(distinct(LLMEvaluation.log_id)).label("total_evaluated"),
            func.avg(LLMEvaluation.overall_score).label("avg_score"),
        )
        .join(LLMEvaluation, LLMLog.id == LLMEvaluation.log_id)
        .filter(LLMLog.created_at >= start_date)
        .group_by(cast(LLMLog.created_at, Date))
        .order_by(cast(LLMLog.created_at, Date))
        .all()
    )

    # 평가 통계를 딕셔너리로 변환
    eval_stats_dict = {
        str(row.date): {
            "total_evaluated": row.total_evaluated or 0,
            "avg_score": row.avg_score,
        }
        for row in eval_stats_query
    }

    # 결과 조합
    data_points = []
    for row in log_stats:
        date_str = str(row.date)
        eval_data = eval_stats_dict.get(date_str, {"total_evaluated": 0, "avg_score": None})

        data_points.append(
            TimeSeriesDataPoint(
                date=date_str,
                avg_score=eval_data["avg_score"],
                avg_latency_ms=row.avg_latency_ms,
                total_requests=row.total_requests,
                total_evaluated=eval_data["total_evaluated"],
            )
        )

    return TimeSeriesResponse(data=data_points)


# ==================== Analytics API (v0.6.0) ====================


@app.get("/analytics/trends", response_model=HourlyTrendResponse)
def get_hourly_trends(
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 (1-168시간, 최대 7일)"),
    db: Session = Depends(get_db),
):
    """
    시간대별 품질 트렌드 분석.
    최근 N시간 동안의 시간별 통계를 반환 (에러율 포함).
    """
    from datetime import datetime, timedelta
    from sqlalchemy import cast, func as sql_func, case

    # 시작 시간 계산
    start_time = datetime.now() - timedelta(hours=hours)

    # 시간별 로그 통계 (PostgreSQL date_trunc 사용)
    log_stats = (
        db.query(
            sql_func.date_trunc('hour', LLMLog.created_at).label("hour"),
            sql_func.count(LLMLog.id).label("total_requests"),
            sql_func.avg(LLMLog.latency_ms).label("avg_latency_ms"),
            sql_func.sum(case((LLMLog.status == 'error', 1), else_=0)).label("error_count"),
        )
        .filter(LLMLog.created_at >= start_time)
        .group_by(sql_func.date_trunc('hour', LLMLog.created_at))
        .order_by(sql_func.date_trunc('hour', LLMLog.created_at))
        .all()
    )

    # 시간별 평가 통계
    eval_stats_query = (
        db.query(
            sql_func.date_trunc('hour', LLMLog.created_at).label("hour"),
            sql_func.count(distinct(LLMEvaluation.log_id)).label("total_evaluated"),
            sql_func.avg(LLMEvaluation.overall_score).label("avg_score"),
        )
        .join(LLMEvaluation, LLMLog.id == LLMEvaluation.log_id)
        .filter(LLMLog.created_at >= start_time)
        .group_by(sql_func.date_trunc('hour', LLMLog.created_at))
        .order_by(sql_func.date_trunc('hour', LLMLog.created_at))
        .all()
    )

    # 평가 통계를 딕셔너리로 변환
    eval_stats_dict = {
        row.hour: {
            "total_evaluated": row.total_evaluated or 0,
            "avg_score": row.avg_score,
        }
        for row in eval_stats_query
    }

    # 결과 조합
    data_points = []
    total_reqs = 0
    total_errors = 0
    total_evals = 0
    sum_scores = 0
    score_count = 0

    for row in log_stats:
        hour_str = row.hour.strftime("%Y-%m-%d %H:00:00")
        eval_data = eval_stats_dict.get(row.hour, {"total_evaluated": 0, "avg_score": None})

        error_rate = (row.error_count / row.total_requests * 100) if row.total_requests > 0 else 0

        data_points.append(
            HourlyTrendDataPoint(
                hour=hour_str,
                avg_score=eval_data["avg_score"],
                avg_latency_ms=row.avg_latency_ms,
                total_requests=row.total_requests,
                total_evaluated=eval_data["total_evaluated"],
                error_rate=error_rate,
            )
        )

        # 전체 통계 집계
        total_reqs += row.total_requests
        total_errors += row.error_count
        total_evals += eval_data["total_evaluated"]
        if eval_data["avg_score"] is not None:
            sum_scores += eval_data["avg_score"] * eval_data["total_evaluated"]
            score_count += eval_data["total_evaluated"]

    # 전체 통계 요약
    summary = {
        "total_requests": total_reqs,
        "total_errors": total_errors,
        "overall_error_rate": (total_errors / total_reqs * 100) if total_reqs > 0 else 0,
        "total_evaluated": total_evals,
        "overall_avg_score": (sum_scores / score_count) if score_count > 0 else None,
        "hours_analyzed": hours,
    }

    return HourlyTrendResponse(data=data_points, summary=summary)


@app.get("/analytics/compare-models", response_model=ModelComparisonResponse)
def compare_models(
    days: int = Query(7, ge=1, le=30, description="비교할 기간 (일)"),
    db: Session = Depends(get_db),
):
    """
    모델 간 상세 성능 비교.
    지정된 기간 동안의 모델별 상세 통계를 반환 (백분위수, 품질 분포 포함).
    """
    from datetime import datetime, timedelta
    from sqlalchemy import case

    start_date = datetime.now() - timedelta(days=days)

    # 모델별 기본 통계
    model_stats_query = (
        db.query(
            LLMLog.model_version,
            func.count(LLMLog.id).label("total_requests"),
            func.sum(case((LLMLog.status == 'success', 1), else_=0)).label("success_count"),
            func.sum(case((LLMLog.status == 'error', 1), else_=0)).label("error_count"),
            func.avg(LLMLog.latency_ms).label("avg_latency_ms"),
        )
        .filter(LLMLog.created_at >= start_date)
        .group_by(LLMLog.model_version)
        .all()
    )

    models = []
    best_latency_model = None
    best_latency_value = float('inf')
    best_quality_model = None
    best_quality_value = 0
    best_stability_model = None
    best_stability_value = 100  # 낮을수록 좋음 (에러율)

    for model_stat in model_stats_query:
        model_version = model_stat.model_version or "unknown"
        total_requests = model_stat.total_requests
        success_count = model_stat.success_count
        error_count = model_stat.error_count
        avg_latency = model_stat.avg_latency_ms

        # 성공률 및 에러율 계산
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        # 백분위수 계산 (p50, p95, p99)
        latencies = (
            db.query(LLMLog.latency_ms)
            .filter(
                LLMLog.model_version == model_stat.model_version,
                LLMLog.created_at >= start_date,
                LLMLog.latency_ms.isnot(None)
            )
            .order_by(LLMLog.latency_ms)
            .all()
        )

        latency_values = [lat[0] for lat in latencies if lat[0] is not None]
        p50_latency = None
        p95_latency = None
        p99_latency = None

        if latency_values:
            import statistics
            p50_latency = statistics.median(latency_values)
            if len(latency_values) >= 20:  # 충분한 데이터가 있을 때만 p95, p99 계산
                p95_latency = statistics.quantiles(latency_values, n=20)[18]  # 95th percentile
                p99_latency = statistics.quantiles(latency_values, n=100)[98]  # 99th percentile

        # 평가 통계
        eval_stats = (
            db.query(
                func.count(distinct(LLMEvaluation.log_id)).label("total_evaluated"),
                func.avg(LLMEvaluation.overall_score).label("avg_score"),
                func.sum(case((LLMEvaluation.overall_score < 3, 1), else_=0)).label("low_quality_count"),
                func.sum(case((LLMEvaluation.overall_score >= 4, 1), else_=0)).label("high_quality_count"),
            )
            .join(LLMLog, LLMEvaluation.log_id == LLMLog.id)
            .filter(
                LLMLog.model_version == model_stat.model_version,
                LLMLog.created_at >= start_date
            )
            .first()
        )

        total_evaluated = eval_stats.total_evaluated or 0
        avg_score = eval_stats.avg_score
        low_quality_count = eval_stats.low_quality_count or 0
        high_quality_count = eval_stats.high_quality_count or 0

        model_detail = ModelComparisonDetail(
            model_version=model_version,
            total_requests=total_requests,
            success_rate=success_rate,
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            avg_score=avg_score,
            total_evaluated=total_evaluated,
            low_quality_count=low_quality_count,
            high_quality_count=high_quality_count,
        )

        models.append(model_detail)

        # Best model 판단
        if p50_latency and p50_latency < best_latency_value:
            best_latency_value = p50_latency
            best_latency_model = model_version

        if avg_score and avg_score > best_quality_value:
            best_quality_value = avg_score
            best_quality_model = model_version

        if error_rate < best_stability_value:
            best_stability_value = error_rate
            best_stability_model = model_version

    return ModelComparisonResponse(
        models=models,
        best_model_by_latency=best_latency_model,
        best_model_by_quality=best_quality_model,
        best_model_by_stability=best_stability_model,
    )


@app.get("/alerts/history", response_model=AlertHistoryResponse)
def get_alert_history(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 Alert 수"),
    severity: str | None = Query(None, description="Severity 필터 (critical, warning, info)"),
    service: str | None = Query(None, description="Service 필터"),
):
    """
    Prometheus Alert 이력 조회.
    Prometheus API를 통해 최근 Alert 이력을 가져옵니다.

    Note: 실제 Alert 이력은 Prometheus/Alertmanager API에서 조회합니다.
    현재는 Mock 데이터를 반환합니다. 실제 구현 시 httpx로 Prometheus API 호출 필요.
    """
    import httpx
    from datetime import datetime, timedelta

    # Prometheus API URL (docker-compose 네트워크 내부)
    prometheus_url = "http://prometheus:9090"

    try:
        # Prometheus에서 활성 Alert 조회
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{prometheus_url}/api/v1/alerts")
            response.raise_for_status()
            data = response.json()

        alerts_data = data.get("data", {}).get("alerts", [])

        # Alert 정보 파싱
        alerts = []
        for alert in alerts_data:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})

            # 필터링
            if severity and labels.get("severity") != severity:
                continue
            if service and labels.get("service") != service:
                continue

            # Alert 정보 생성
            alert_info = AlertInfo(
                alert_name=labels.get("alertname", "Unknown"),
                severity=labels.get("severity", "unknown"),
                service=labels.get("service", "unknown"),
                summary=annotations.get("summary"),
                description=annotations.get("description"),
                started_at=alert.get("activeAt", datetime.now().isoformat()),
                ended_at=None,  # 활성 Alert는 종료 시간 없음
                duration_seconds=None,
                status=alert.get("state", "firing"),
            )
            alerts.append(alert_info)

    except Exception as e:
        # Prometheus 연결 실패 시 빈 리스트 반환
        print(f"Failed to fetch alerts from Prometheus: {e}")
        alerts = []

    # 페이지네이션 적용
    total = len(alerts)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_alerts = alerts[start_idx:end_idx]

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return AlertHistoryResponse(
        alerts=paginated_alerts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
