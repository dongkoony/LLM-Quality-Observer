from typing import List, Literal
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import Base, engine, get_db
from .models import LLMLog, LLMEvaluation
from .rules import basic_rule_evaluate
from .llm_judge import run_judge
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
    judge_type: Literal["rule", "llm"] = Query("rule", description="평가 방식: 'rule' (룰 기반) 또는 'llm' (LLM-as-a-Judge)"),
    db: Session = Depends(get_db),
):
    """
    아직 평가되지 않은 LLM 로그들을 평가하는 엔드포인트.

    - judge_type='rule': 순수 룰 기반 평가 (OpenAI API 호출 없음)
    - judge_type='llm': LLM-as-a-Judge 평가 (OpenAI API 호출)
    - 이미 평가된 로그는 건너뜀
    - 최대 `limit` 개의 로그를 평가하고 결과를 DB에 저장

    Args:
        limit: 한 번에 평가할 최대 로그 개수 (기본값 10, 최대 100)
        judge_type: 평가 방식 ('rule' 또는 'llm')
        db: SQLAlchemy 세션

    Returns:
        dict: {"evaluated": <평가한 개수>, "judge_model": <사용한 모델>, "judge_type": <평가 방식>}
    """
    # 1. 아직 평가되지 않은 로그 가져오기
    pending_logs = get_pending_logs(db, limit=limit)

    if not pending_logs:
        return {
            "evaluated": 0,
            "judge_type": judge_type,
            "judge_model": "rule-basic-v1" if judge_type == "rule" else settings.openai_model_judge,
        }

    # 2. 각 로그에 대해 평가 수행
    evaluated_count = 0
    judge_model_name = ""

    for log in pending_logs:
        try:
            if judge_type == "rule":
                # 룰 기반 평가
                eval_result = basic_rule_evaluate(log)
                judge_model_name = eval_result.judge_model

                # LLMEvaluation 인스턴스 생성
                evaluation = LLMEvaluation(
                    log_id=eval_result.log_id,
                    overall_score=eval_result.overall_score,
                    is_flagged=eval_result.is_flagged,
                    label=eval_result.label,
                    judge_model=eval_result.judge_model,
                    comment=eval_result.comment,
                )
            else:  # judge_type == "llm"
                # LLM-as-a-Judge 평가
                llm_eval_result = run_judge(log)
                judge_model_name = settings.openai_model_judge

                # LLMEvaluation 인스턴스 생성 (세부 점수 포함)
                evaluation = LLMEvaluation(
                    log_id=log.id,
                    overall_score=llm_eval_result["score_overall"],
                    score_instruction_following=llm_eval_result["score_instruction_following"],
                    score_truthfulness=llm_eval_result["score_truthfulness"],
                    is_flagged=llm_eval_result["score_overall"] < 3,  # 점수 3 미만이면 플래그
                    label="llm-judge",
                    judge_model=judge_model_name,
                    comment=llm_eval_result["comments"],
                    raw_judge_response=llm_eval_result["raw_judge_response"],
                )

            # DB에 추가
            db.add(evaluation)
            evaluated_count += 1

        except HTTPException as e:
            # LLM judge 호출 실패 시 롤백하고 에러 반환
            db.rollback()
            raise e
        except Exception as e:
            # 기타 예외 처리
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

    # 3. 모든 평가 결과 커밋
    db.commit()

    # 4. 결과 반환
    return {
        "evaluated": evaluated_count,
        "judge_type": judge_type,
        "judge_model": judge_model_name,
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
