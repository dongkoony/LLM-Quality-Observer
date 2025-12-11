"""
알림 시스템 모듈.
Slack, Discord 웹훅을 통해 평가 결과 알림을 전송합니다.
"""

import logging
from typing import Optional
import httpx

from .config import settings
from .models import LLMLog, LLMEvaluation

logger = logging.getLogger(__name__)


def send_slack_notification(message: str) -> bool:
    """
    Slack 웹훅을 통해 메시지를 전송합니다.

    Args:
        message: 전송할 메시지

    Returns:
        bool: 전송 성공 여부
    """
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook URL이 설정되지 않았습니다.")
        return False

    try:
        payload = {"text": message}
        response = httpx.post(
            settings.slack_webhook_url,
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("Slack 알림 전송 성공")
        return True
    except Exception as e:
        logger.error(f"Slack 알림 전송 실패: {str(e)}")
        return False


def send_discord_notification(message: str) -> bool:
    """
    Discord 웹훅을 통해 메시지를 전송합니다.

    Args:
        message: 전송할 메시지

    Returns:
        bool: 전송 성공 여부
    """
    if not settings.discord_webhook_url:
        logger.debug("Discord webhook URL이 설정되지 않았습니다.")
        return False

    try:
        payload = {"content": message}
        response = httpx.post(
            settings.discord_webhook_url,
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("Discord 알림 전송 성공")
        return True
    except Exception as e:
        logger.error(f"Discord 알림 전송 실패: {str(e)}")
        return False


def send_low_quality_alert(log: LLMLog, evaluation: LLMEvaluation):
    """
    품질 점수가 낮은 평가 결과에 대한 알림을 전송합니다.

    Args:
        log: LLM 로그
        evaluation: 평가 결과
    """
    if evaluation.overall_score >= settings.notification_score_threshold:
        # 임계값 이상이면 알림 안 보냄
        return

    # 메시지 구성
    message = f"""
🚨 **Low Quality Alert**

**Score:** {evaluation.overall_score}/5
**Judge:** {evaluation.judge_model}
**Label:** {evaluation.label}

**Prompt:** {log.prompt[:100]}...
**Response:** {log.response[:100]}...

**Comment:** {evaluation.comment or 'N/A'}

**Log ID:** {log.id}
**Created:** {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

    # Slack과 Discord에 동시 전송
    slack_sent = send_slack_notification(message)
    discord_sent = send_discord_notification(message)

    if slack_sent or discord_sent:
        logger.info(f"Low quality alert sent for log_id={log.id}, score={evaluation.overall_score}")
    else:
        logger.warning(f"Failed to send alert for log_id={log.id}")


def send_batch_evaluation_summary(evaluated_count: int, judge_type: str, judge_model: str):
    """
    배치 평가 완료 요약 알림을 전송합니다.

    Args:
        evaluated_count: 평가한 로그 개수
        judge_type: 평가 방식
        judge_model: 사용한 모델
    """
    if evaluated_count == 0:
        return

    message = f"""
✅ **Batch Evaluation Complete**

**Evaluated:** {evaluated_count} logs
**Judge Type:** {judge_type}
**Judge Model:** {judge_model}
""".strip()

    send_slack_notification(message)
    send_discord_notification(message)
