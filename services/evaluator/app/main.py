from typing import List

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import LLMLog, LLMEvaluation
from .llm_judge import run_judge
from .config import settings

app = FastAPI(title="LLM Quality Observer - Evaluator Service")

# 최초 실행 시 테이블 생성 (llm_evaluations)
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env}


def get_pending_logs(db: Session, limit: int = 5) -> List[LLMLog]:
    """
    아직 평가되지 않은 llm_logs 를 가져온다.
    조건:
    - status = 'success'
    - llm_evaluations 에 해당 log_id 가 없음
    """
    stmt = (
        select(LLMLog)
        .outerjoin(LLMEvaluation, LLMEvaluation.log_id == LLMLog.id)
        .where(LLMEvaluation.id.is_(None))
        .where(LLMLog.status == "success")
        .order_by(LLMLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


@app.post("/evaluate-once")
def evaluate_once(limit: int = 5, db: Session = Depends(get_db)):
    """
    한 번 호출할 때마다 최대 N개의 로그를 평가한다.
    - 실제 운영 환경에서는 배치/스케줄러/백그라운드 태스크로 돌릴 수 있음.
    """

    logs = get_pending_logs(db, limit=limit)
    if not logs:
        return {"evaluated": 0, "message": "No pending logs to evaluate."}

    created = 0

    for log in logs:
        eval_result = run_judge(log)

        evaluation = LLMEvaluation(
            log_id=log.id,
            score_overall=eval_result["score_overall"],
            score_instruction_following=eval_result["score_instruction_following"],
            score_truthfulness=eval_result["score_truthfulness"],
            comments=eval_result["comments"],
            judge_model=settings.openai_model_judge,
            raw_judge_response=eval_result["raw_judge_response"],
        )

        db.add(evaluation)
        created += 1

    db.commit()

    return {
        "evaluated": created,
        "judge_model": settings.openai_model_judge,
    }
