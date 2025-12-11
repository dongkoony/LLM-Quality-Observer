"""
배치 평가 스케줄러 모듈.
APScheduler를 사용하여 주기적으로 LLM 로그를 자동 평가합니다.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal
from .utils import get_pending_logs
from .models import LLMLog, LLMEvaluation
from .rules import basic_rule_evaluate
from .llm_judge import run_judge
from .notifier import send_low_quality_alert, send_batch_evaluation_summary

logger = logging.getLogger(__name__)

# 글로벌 스케줄러 인스턴스
scheduler: BackgroundScheduler | None = None


def run_batch_evaluation():
    """
    배치 평가 작업을 실행합니다.
    평가되지 않은 로그를 찾아 자동으로 평가하고, 결과를 DB에 저장합니다.
    """
    logger.info("Starting batch evaluation...")

    db: Session = SessionLocal()
    try:
        # 1. 평가 대기 중인 로그 가져오기
        pending_logs = get_pending_logs(
            db,
            limit=settings.evaluation_batch_size
        )

        if not pending_logs:
            logger.info("No pending logs to evaluate")
            return

        logger.info(f"Found {len(pending_logs)} pending logs")

        # 2. 각 로그 평가
        evaluated_count = 0
        judge_type = settings.evaluation_judge_type
        judge_model_name = ""

        for log in pending_logs:
            try:
                if judge_type == "rule":
                    # 룰 기반 평가
                    eval_result = basic_rule_evaluate(log)
                    judge_model_name = eval_result.judge_model

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

                    evaluation = LLMEvaluation(
                        log_id=log.id,
                        overall_score=llm_eval_result["score_overall"],
                        score_instruction_following=llm_eval_result["score_instruction_following"],
                        score_truthfulness=llm_eval_result["score_truthfulness"],
                        is_flagged=llm_eval_result["score_overall"] < 3,
                        label="llm-judge",
                        judge_model=judge_model_name,
                        comment=llm_eval_result["comments"],
                        raw_judge_response=llm_eval_result["raw_judge_response"],
                    )

                # DB에 추가
                db.add(evaluation)
                db.commit()
                evaluated_count += 1

                # 품질 점수가 낮으면 알림 전송
                send_low_quality_alert(log, evaluation)

                logger.info(
                    f"Evaluated log_id={log.id}, score={evaluation.overall_score}, "
                    f"judge={judge_type}"
                )

            except Exception as e:
                logger.error(f"Failed to evaluate log_id={log.id}: {str(e)}")
                db.rollback()
                continue

        # 3. 배치 평가 완료 요약 알림
        if evaluated_count > 0:
            send_batch_evaluation_summary(
                evaluated_count=evaluated_count,
                judge_type=judge_type,
                judge_model=judge_model_name
            )

        logger.info(
            f"Batch evaluation completed: {evaluated_count}/{len(pending_logs)} logs evaluated"
        )

    except Exception as e:
        logger.error(f"Batch evaluation failed: {str(e)}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """
    스케줄러를 시작합니다.
    """
    global scheduler

    if not settings.enable_auto_evaluation:
        logger.info("Auto evaluation is disabled")
        return

    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return

    try:
        scheduler = BackgroundScheduler()

        # 인터벌 트리거 설정 (분 단위)
        trigger = IntervalTrigger(minutes=settings.evaluation_interval_minutes)

        # 작업 추가
        scheduler.add_job(
            func=run_batch_evaluation,
            trigger=trigger,
            id="batch_evaluation",
            name="Batch LLM Evaluation",
            replace_existing=True,
        )

        # 스케줄러 시작
        scheduler.start()

        logger.info(
            f"Scheduler started: running every {settings.evaluation_interval_minutes} minutes, "
            f"judge_type={settings.evaluation_judge_type}, "
            f"batch_size={settings.evaluation_batch_size}"
        )

    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise


def stop_scheduler():
    """
    스케줄러를 중지합니다.
    """
    global scheduler

    if scheduler is None:
        logger.warning("Scheduler is not running")
        return

    try:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
