from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, select, distinct
import math

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
)
from .llm_client import call_llm
from .config import settings

# 최초 실행 시 테이블 생성 (간단 버전)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Quality Observer - Gateway API")

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
    response_text, latency_ms = call_llm(request.prompt, used_model)

    # DB 로그 저장
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
            "is_flagged": evaluation.is_flagged,
            "label": evaluation.label,
            "judge_model": evaluation.judge_model,
            "comment": evaluation.comment,
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
