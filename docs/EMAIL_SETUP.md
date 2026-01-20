# Email Notification Setup Guide

This guide walks you through setting up email notifications for the LLM Quality Observer system.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Gmail Setup](#gmail-setup)
- [Other SMTP Providers](#other-smtp-providers)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Overview

LLM Quality Observer supports email notifications for:
- **Low-quality alerts**: Sent when LLM responses score below the configured threshold
- **Batch evaluation summaries**: Sent after scheduled batch evaluation runs complete

Email notifications are sent via SMTP and support multiple recipients.

---

## Prerequisites

- SMTP server credentials (email provider)
- Sender email address
- Recipient email address(es)
- For Gmail: 2-factor authentication enabled and app password

---

## Gmail Setup

### Step 1: Enable 2-Factor Authentication

1. Go to your [Google Account](https://myaccount.google.com/)
2. Navigate to **Security**
3. Under "Signing in to Google", select **2-Step Verification**
4. Follow the prompts to enable 2FA

### Step 2: Generate App Password

1. In **Security** settings, scroll to **2-Step Verification**
2. At the bottom, select **App passwords**
3. You may need to sign in again
4. Under "Select app", choose **Mail**
5. Under "Select device", choose **Other (Custom name)**
6. Enter "LLM Quality Observer" and click **Generate**
7. Copy the 16-character password (you won't be able to see it again)

### Step 3: Configure Environment Variables

Add these to your `.env.local` file:

```bash
# Email Notification Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App password from Step 2
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

**Note:** Replace spaces in the app password with no spaces when copying to .env file.

---

## Other SMTP Providers

### Microsoft 365 / Outlook

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=your-email@outlook.com
SMTP_TO_EMAILS=recipient@example.com
```

**Note:** If using 2FA, generate an app password in your Microsoft account settings.

### SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=verified-sender@yourdomain.com
SMTP_TO_EMAILS=recipient@example.com
```

**Note:** You must verify your sender email in SendGrid before sending.

### AWS SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=verified-sender@yourdomain.com
SMTP_TO_EMAILS=recipient@example.com
```

**Note:** Generate SMTP credentials in AWS SES console and verify your sender domain.

### Mailgun

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@your-domain.mailgun.org
SMTP_TO_EMAILS=recipient@example.com
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | Yes | None | SMTP server hostname |
| `SMTP_PORT` | No | 587 | SMTP server port (use 587 for TLS) |
| `SMTP_USERNAME` | Yes | None | SMTP authentication username |
| `SMTP_PASSWORD` | Yes | None | SMTP authentication password |
| `SMTP_FROM_EMAIL` | Yes | None | Sender email address |
| `SMTP_TO_EMAILS` | Yes | None | Comma-separated recipient emails |
| `NOTIFICATION_SCORE_THRESHOLD` | No | 3 | Threshold for low-quality alerts (1-5) |

### Multiple Recipients

To send notifications to multiple recipients, separate email addresses with commas:

```bash
SMTP_TO_EMAILS=team-lead@company.com,on-call@company.com,quality-team@company.com
```

### Notification Threshold

The `NOTIFICATION_SCORE_THRESHOLD` determines when low-quality alerts are sent:

```bash
# Send alerts for scores of 3 or below
NOTIFICATION_SCORE_THRESHOLD=3

# Only send alerts for very low scores (2 or below)
NOTIFICATION_SCORE_THRESHOLD=2
```

---

## Testing

### Step 1: Update Configuration

1. Edit your `.env.local` file with SMTP credentials
2. Set `SMTP_TO_EMAILS` to your test email address

### Step 2: Restart Services

```bash
cd infra/docker
docker compose -f docker-compose.local.yml restart evaluator
```

### Step 3: Trigger a Low-Quality Alert

#### Option A: Submit a Low-Quality Request

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "x",
    "user_id": "test-user"
  }'
```

Wait a few seconds, then trigger evaluation:

```bash
curl -X POST "http://localhost:18001/evaluate-once?limit=5"
```

#### Option B: Use Python Test Script

Create `test_email.py`:

```python
import asyncio
import sys
sys.path.append('services/evaluator')

from app.notifier import send_email_notification

async def test():
    result = await send_email_notification(
        subject="🚨 Test Alert - LLM Quality Observer",
        message="""
Test email notification from LLM Quality Observer.

If you're seeing this, your email configuration is working correctly!

Score: 2/5
Judge: rule-based
Status: Low Quality
        """.strip(),
        notification_type="alert"
    )
    print(f"Email sent: {result}")

asyncio.run(test())
```

Run the test:

```bash
cd services/evaluator
uv run python test_email.py
```

### Step 4: Check Logs

```bash
docker compose -f docker-compose.local.yml logs evaluator | grep -i email
```

You should see:
```
이메일 알림 전송 성공: ['recipient@example.com']
```

---

## Troubleshooting

### Error: "SMTP settings not configured"

**Cause:** One or more required SMTP environment variables are missing.

**Solution:**
1. Verify all required variables are set in `.env.local`
2. Restart the evaluator service
3. Check logs: `docker compose logs evaluator`

### Error: "Authentication failed"

**Cause:** Invalid SMTP credentials.

**Solution:**
- **Gmail:** Ensure you're using an app password, not your account password
- **Other providers:** Verify username and password are correct
- Check if 2FA is required and generate an app password

### Error: "Connection timeout"

**Cause:** Cannot reach SMTP server.

**Solution:**
1. Verify `SMTP_HOST` is correct
2. Check `SMTP_PORT` (587 for TLS, 465 for SSL)
3. Ensure firewall allows outbound SMTP connections
4. Try from host machine: `telnet smtp.gmail.com 587`

### Error: "Sender address rejected"

**Cause:** Sender email not verified or doesn't match credentials.

**Solution:**
- **Gmail:** Use the same email as `SMTP_USERNAME`
- **SendGrid/SES:** Verify sender email/domain in provider dashboard
- Check `SMTP_FROM_EMAIL` matches verified sender

### Emails Not Arriving

**Possible causes:**
1. **Spam folder:** Check recipient's spam/junk folder
2. **Rate limiting:** Provider may be rate-limiting sends
3. **Blocked sender:** Recipient's email server may be blocking emails

**Solutions:**
1. Add sender to recipient's contacts/whitelist
2. Check evaluator logs for send confirmation
3. Use a verified domain instead of Gmail
4. Contact email provider support

### SSL/TLS Errors

**Symptoms:** "SSL handshake failed" or similar

**Solution:**
```bash
# Try different port configurations
SMTP_PORT=587  # STARTTLS (recommended)
SMTP_PORT=465  # SSL
SMTP_PORT=25   # Unencrypted (not recommended)
```

---

## Security Best Practices

### 1. Use App Passwords

Never use your main email account password. Always generate app-specific passwords.

**Why:** If compromised, you can revoke the app password without changing your main password.

### 2. Restrict SMTP Credentials

```bash
# .env.local should be gitignored
echo ".env.local" >> .gitignore

# Set proper file permissions
chmod 600 configs/env/.env.local
```

### 3. Use Environment-Specific Credentials

Don't share credentials between environments:

```bash
# Development
SMTP_FROM_EMAIL=dev-alerts@company.com

# Production
SMTP_FROM_EMAIL=prod-alerts@company.com
```

### 4. Limit Recipients

Only send to authorized recipients:

```bash
# Good: Specific team addresses
SMTP_TO_EMAILS=ml-team@company.com,on-call@company.com

# Bad: Personal emails
SMTP_TO_EMAILS=john.personal@gmail.com
```

### 5. Monitor Email Usage

Track email notification metrics:

```promql
# Email notification rate
rate(llm_evaluator_notifications_sent_total{channel="email"}[5m])

# Email failure rate
rate(llm_evaluator_notifications_sent_total{channel="email",status="error"}[5m])
```

### 6. Rotate Credentials Regularly

- Rotate app passwords every 90 days
- Update credentials immediately if compromised
- Document who has access to SMTP credentials

---

## Advanced Configuration

### Custom Email Templates

To customize email format, modify `services/evaluator/app/notifier.py`:

```python
# Current simple format
html_message = message.replace("\n", "<br>")
html_part = MIMEText(f"<html><body><pre>{html_message}</pre></body></html>", "html")

# Custom HTML template
html_template = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ background-color: #ffebee; padding: 20px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #d32f2f; }}
    </style>
</head>
<body>
    <div class="alert">
        <h2>🚨 Low Quality Alert</h2>
        <p class="score">Score: {score}/5</p>
        <p>{message}</p>
    </div>
</body>
</html>
"""
```

### Conditional Email Sending

Only send emails for specific conditions:

```python
# In notifier.py, modify send_low_quality_alert()
def send_low_quality_alert(log: LLMLog, evaluation: LLMEvaluation):
    # Only send email for very low scores
    if evaluation.overall_score <= 2:
        asyncio.run(send_email_notification(subject, message))

    # Always send Slack/Discord
    send_slack_notification(message)
    send_discord_notification(message)
```

### Email Throttling

Prevent email spam by adding rate limiting:

```python
import time
from collections import deque

# Track recent emails
email_timestamps = deque(maxlen=10)

def should_send_email():
    now = time.time()
    # Max 10 emails per hour
    if len(email_timestamps) == 10:
        if now - email_timestamps[0] < 3600:
            return False
    email_timestamps.append(now)
    return True
```

---

## Monitoring

### Key Metrics

Monitor these Prometheus metrics for email health:

```promql
# Email send rate
rate(llm_evaluator_notifications_sent_total{channel="email"}[5m])

# Email success rate
sum(rate(llm_evaluator_notifications_sent_total{channel="email",status="success"}[5m])) /
sum(rate(llm_evaluator_notifications_sent_total{channel="email"}[5m]))

# Recent email failures
increase(llm_evaluator_notifications_sent_total{channel="email",status="error"}[1h])
```

### Grafana Alerts

Create alerts for email delivery issues:

```yaml
- alert: EmailDeliveryFailure
  expr: |
    rate(llm_evaluator_notifications_sent_total{channel="email",status="error"}[5m]) > 0.1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Email notifications failing"
    description: "Email delivery failure rate: {{ $value }}"
```

---

## Support

For issues not covered in this guide:
- Check evaluator service logs: `docker compose logs evaluator`
- Review SMTP provider documentation
- Open GitHub issue with logs and configuration (redact credentials)

---

## Related Documentation

- [Notification Settings](../configs/env/.env.local.example)
- [Metrics Reference](./METRICS.md)
- [Release Notes](./RELEASE_NOTES_v0.5.0.md)
