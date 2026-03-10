"""
알림 시스템 모듈.
Slack, Discord 웹훅 및 이메일을 통해 평가 결과 알림을 전송합니다.
"""

import logging
import asyncio
from typing import Optional
import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import get_settings
from .models import LLMLog, LLMEvaluation
from .metrics import record_notification, record_low_quality_alert

logger = logging.getLogger(__name__)


def send_slack_notification(message: str, notification_type: str = "alert") -> bool:
    """
    Slack 웹훅을 통해 메시지를 전송합니다.

    Args:
        message: 전송할 메시지
        notification_type: 'alert' or 'summary'

    Returns:
        bool: 전송 성공 여부
    """
    settings = get_settings()

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
        record_notification("slack", notification_type, "success")
        logger.info("Slack 알림 전송 성공")
        return True
    except Exception as e:
        record_notification("slack", notification_type, "error")
        logger.error(f"Slack 알림 전송 실패: {str(e)}")
        return False


def send_discord_notification(message: str, notification_type: str = "alert") -> bool:
    """
    Discord 웹훅을 통해 메시지를 전송합니다.

    Args:
        message: 전송할 메시지
        notification_type: 'alert' or 'summary'

    Returns:
        bool: 전송 성공 여부
    """
    settings = get_settings()

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
        record_notification("discord", notification_type, "success")
        logger.info("Discord 알림 전송 성공")
        return True
    except Exception as e:
        record_notification("discord", notification_type, "error")
        logger.error(f"Discord 알림 전송 실패: {str(e)}")
        return False


async def send_email_notification(subject: str, message: str, notification_type: str = "alert", html_content: str = None) -> bool:
    """
    SMTP를 통해 이메일 알림을 전송합니다.

    Args:
        subject: 이메일 제목
        message: 전송할 메시지 (plain text)
        notification_type: 'alert' or 'summary'
        html_content: HTML 콘텐츠 (없으면 자동 생성)

    Returns:
        bool: 전송 성공 여부
    """
    settings = get_settings()

    if not all([
        settings.smtp_host,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_from_email,
        settings.smtp_to_emails,
    ]):
        logger.debug("SMTP 설정이 완전하지 않습니다.")
        return False

    try:
        # 수신자 이메일 리스트 파싱
        to_emails = [email.strip() for email in settings.smtp_to_emails.split(",")]

        # MIME 메시지 생성
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = ", ".join(to_emails)

        # 텍스트 버전
        text_part = MIMEText(message, "plain")

        # HTML 버전 (제공되지 않으면 기본 템플릿 사용)
        if html_content is None:
            html_message = message.replace("\n", "<br>")
            html_content = f"<html><body><pre>{html_message}</pre></body></html>"

        html_part = MIMEText(html_content, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        # SMTP 연결 및 전송 (포트 587은 STARTTLS 사용)
        async with aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
        ) as smtp:
            await smtp.login(settings.smtp_username, settings.smtp_password)
            await smtp.send_message(msg)

        record_notification("email", notification_type, "success")
        logger.info(f"이메일 알림 전송 성공: {to_emails}")
        return True
    except Exception as e:
        record_notification("email", notification_type, "error")
        logger.error(f"이메일 알림 전송 실패: {str(e)}")
        return False


def send_low_quality_alert(log: LLMLog, evaluation: LLMEvaluation):
    """
    품질 점수가 낮은 평가 결과에 대한 알림을 전송합니다.

    Args:
        log: LLM 로그
        evaluation: 평가 결과
    """
    settings = get_settings()

    if evaluation.overall_score >= settings.notification_score_threshold:
        # 임계값 이상이면 알림 안 보냄
        return

    # 점수에 따른 색상 결정
    if evaluation.overall_score <= 2:
        score_color = "#dc3545"  # 빨강
        status_badge = "Critical"
    elif evaluation.overall_score <= 3:
        score_color = "#fd7e14"  # 주황
        status_badge = "Warning"
    else:
        score_color = "#ffc107"  # 노랑
        status_badge = "Low Quality"

    # Plain text 메시지 (Slack/Discord용)
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

    # HTML 이메일 템플릿
    html_email = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {score_color} 0%, #c82333 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">
                                🚨 LLM Quality Alert
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 14px; opacity: 0.9;">
                                {status_badge} - Immediate Attention Required
                            </p>
                        </td>
                    </tr>

                    <!-- Score Badge -->
                    <tr>
                        <td style="padding: 30px; text-align: center; background-color: #f8f9fa;">
                            <div style="display: inline-block; background-color: {score_color}; color: #ffffff; padding: 20px 40px; border-radius: 50px; font-size: 48px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                                {evaluation.overall_score}<span style="font-size: 24px; opacity: 0.8;">/5</span>
                            </div>
                            <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 14px;">Quality Score</p>
                        </td>
                    </tr>

                    <!-- Details -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">

                            <!-- Judge Info -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                <tr>
                                    <td style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #6c757d; border-radius: 4px;">
                                        <p style="margin: 0; font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px;">Judge Information</p>
                                        <p style="margin: 5px 0 0 0; font-size: 16px; color: #212529;"><strong>{evaluation.judge_model}</strong></p>
                                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #6c757d;">Label: <span style="color: #212529;">{evaluation.label}</span></p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Prompt -->
                            <div style="margin-bottom: 20px;">
                                <p style="margin: 0 0 8px 0; font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">📝 Prompt</p>
                                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 3px solid #007bff;">
                                    <p style="margin: 0; font-size: 14px; color: #212529; line-height: 1.6;">{log.prompt[:200]}{"..." if len(log.prompt) > 200 else ""}</p>
                                </div>
                            </div>

                            <!-- Response -->
                            <div style="margin-bottom: 20px;">
                                <p style="margin: 0 0 8px 0; font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">💬 Response</p>
                                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 3px solid #28a745;">
                                    <p style="margin: 0; font-size: 14px; color: #212529; line-height: 1.6;">{log.response[:200]}{"..." if len(log.response) > 200 else ""}</p>
                                </div>
                            </div>

                            <!-- Comment -->
                            <div style="margin-bottom: 20px;">
                                <p style="margin: 0 0 8px 0; font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">💡 Analysis</p>
                                <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; border-left: 3px solid #ffc107;">
                                    <p style="margin: 0; font-size: 14px; color: #856404; line-height: 1.6;">{evaluation.comment or 'No additional comments'}</p>
                                </div>
                            </div>

                            <!-- Metadata -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #e9ecef; border-radius: 6px; padding: 15px;">
                                <tr>
                                    <td style="padding: 8px; font-size: 13px; color: #495057;">
                                        <strong>Log ID:</strong> #{log.id}
                                    </td>
                                    <td style="padding: 8px; font-size: 13px; color: #495057; text-align: right;">
                                        <strong>Created:</strong> {log.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; background-color: #f8f9fa; text-align: center; border-top: 1px solid #dee2e6;">
                            <p style="margin: 0; font-size: 12px; color: #6c757d;">
                                This is an automated alert from <strong>LLM Quality Observer</strong>
                            </p>
                            <p style="margin: 8px 0 0 0; font-size: 11px; color: #adb5bd;">
                                Powered by LLM-Ouality-Observer • {log.created_at.strftime('%Y')}
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""".strip()

    # 낮은 품질 경고 메트릭 기록
    judge_type = "llm" if "llm" in evaluation.judge_model or "gpt" in evaluation.judge_model else "rule"
    record_low_quality_alert(judge_type)

    # Slack, Discord, Email에 동시 전송
    slack_sent = send_slack_notification(message, notification_type="alert")
    discord_sent = send_discord_notification(message, notification_type="alert")

    # 이메일 전송 (HTML 템플릿 포함)
    email_sent = False
    try:
        email_subject = f"🚨 LLM Quality Alert - Score: {evaluation.overall_score}/5"
        email_sent = asyncio.run(send_email_notification(
            email_subject,
            message,
            notification_type="alert",
            html_content=html_email
        ))
    except Exception as e:
        logger.error(f"Email notification error: {str(e)}")

    if slack_sent or discord_sent or email_sent:
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

    send_slack_notification(message, notification_type="summary")
    send_discord_notification(message, notification_type="summary")

    # 이메일 전송 (비동기 함수를 동기 컨텍스트에서 실행)
    try:
        email_subject = f"✅ Batch Evaluation Complete - {evaluated_count} logs evaluated"
        asyncio.run(send_email_notification(email_subject, message, notification_type="summary"))
    except Exception as e:
        logger.error(f"Email notification error: {str(e)}")
