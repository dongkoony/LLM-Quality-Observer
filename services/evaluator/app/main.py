from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging

from .db import Base, engine, get_db
from .models import LLMLog, LLMEvaluation
from .rules import basic_rule_evaluate
from .llm_judge import run_judge
from .config import settings
from .scheduler import start_scheduler, stop_scheduler
from .utils import get_pending_logs

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 앱의 수명 주기 관리.
    시작 시 테이블 생성 및 스케줄러 시작, 종료 시 스케줄러 중지.
    """
    # Startup
    logger.info("Starting Evaluator Service...")
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # Shutdown
    logger.info("Stopping Evaluator Service...")
    stop_scheduler()


# FastAPI 앱 생성
app = FastAPI(
    title="LLM Quality Observer - Evaluator Service",
    description="룰 기반 및 LLM-as-a-judge 방식으로 LLM 응답 품질을 평가하는 서비스",
    version="1.0.0",
    lifespan=lifespan,
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
