from typing import List
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import LLMLog, LLMEvaluation
from .rules import basic_rule_evaluate
from .config import settings

# FastAPI 앱 생성
app = FastAPI(
    title="LLM Quality Observer - Evaluator Service",
    description="룰 기반 및 LLM-as-a-judge 방식으로 LLM 응답 품질을 평가하는 서비스",
    version="1.0.0",
)

# 앱 시작 시 테이블 생성
Base.metadata.create_all(bind=engine)


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


@app.post("/evaluate-once")
def evaluate_once(
    limit: int = Query(10, ge=1, le=100, description="한 번에 평가할 최대 로그 개수"),
    db: Session = Depends(get_db),
):
    """
    아직 평가되지 않은 LLM 로그들을 룰 기반으로 평가하는 엔드포인트.

    - OpenAI API를 호출하지 않음 (순수 룰 기반 평가)
    - 이미 평가된 로그는 건너뜀
    - 최대 `limit` 개의 로그를 평가하고 결과를 DB에 저장

    Args:
        limit: 한 번에 평가할 최대 로그 개수 (기본값 10, 최대 100)
        db: SQLAlchemy 세션

    Returns:
        dict: {"evaluated": <평가한 개수>, "judge_model": "rule-basic-v1"}
    """
    # 1. 아직 평가되지 않은 로그 가져오기
    pending_logs = get_pending_logs(db, limit=limit)

    if not pending_logs:
        return {
            "evaluated": 0,
            "judge_model": "rule-basic-v1",
        }

    # 2. 각 로그에 대해 룰 기반 평가 수행
    evaluated_count = 0

    for log in pending_logs:
        # 룰 기반 평가 함수 호출
        eval_result = basic_rule_evaluate(log)

        # LLMEvaluation 인스턴스 생성
        evaluation = LLMEvaluation(
            log_id=eval_result.log_id,
            overall_score=eval_result.overall_score,
            is_flagged=eval_result.is_flagged,
            label=eval_result.label,
            judge_model=eval_result.judge_model,
            comment=eval_result.comment,
        )

        # DB에 추가
        db.add(evaluation)
        evaluated_count += 1

    # 3. 모든 평가 결과 커밋
    db.commit()

    # 4. 결과 반환
    return {
        "evaluated": evaluated_count,
        "judge_model": "rule-basic-v1",
    }


def get_pending_logs(db: Session, limit: int = 10) -> List[LLMLog]:
    """
    아직 평가되지 않은 LLM 로그들을 가져오는 함수.

    조건:
    - status가 "success"인 로그만 (에러 로그는 제외)
    - llm_evaluations 테이블에 해당 log_id가 없는 로그만
    - created_at 오름차순 정렬 (오래된 것부터)
    - 최대 limit 개까지

    Args:
        db: SQLAlchemy 세션
        limit: 가져올 최대 개수

    Returns:
        List[LLMLog]: 평가 대기 중인 로그 리스트
    """
    # 이미 평가된 log_id 서브쿼리
    evaluated_log_ids_subquery = select(LLMEvaluation.log_id).subquery()

    # 아직 평가되지 않은 로그 조회
    stmt = (
        select(LLMLog)
        .where(LLMLog.status == "success")  # 성공한 로그만
        .where(LLMLog.id.notin_(evaluated_log_ids_subquery))  # 평가 안 된 것만
        .order_by(LLMLog.created_at.asc())  # 오래된 것부터
        .limit(limit)
    )

    result = db.execute(stmt)
    pending_logs = result.scalars().all()

    return list(pending_logs)
