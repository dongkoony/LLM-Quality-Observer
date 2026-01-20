"""
유틸리티 함수 모듈.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import LLMLog, LLMEvaluation


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
