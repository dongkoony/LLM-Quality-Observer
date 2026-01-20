# Release Notes - v0.4.0

**Release Date**: 2025
**Status**: Automation & DevOps Release

---

## Overview

LLM-Quality-Observer v0.4.0 introduces automated evaluation scheduling and a multi-channel notification system, transforming the platform from a manual evaluation tool into a fully automated monitoring solution. This release also establishes a CI/CD pipeline with automated testing and code quality enforcement.

---

## 🎯 What's New

### Automated Evaluation Scheduler (NEW)
- **APScheduler Integration**: Continuous background evaluation without manual triggers
- **Configurable Intervals**: Set evaluation frequency (minutes, hours, days)
- **Batch Processing**: Efficient evaluation of pending logs in configurable batch sizes
- **Auto-Start**: Scheduler starts automatically with the Evaluator service
- **Health Monitoring**: Track scheduler status and execution history
- **Graceful Shutdown**: Proper cleanup on service stop

### Multi-Channel Notification System (NEW)
- **Slack Integration**: Send alerts to Slack channels via webhooks
- **Discord Integration**: Post notifications to Discord servers
- **Low-Quality Alerts**: Automatic notifications when scores fall below threshold
- **Batch Summaries**: Periodic summaries of evaluation results
- **Configurable Thresholds**: Set custom score thresholds for alerts
- **Rich Formatting**: Color-coded messages with detailed metrics

### CI/CD Pipeline (NEW)
- **GitHub Actions Workflow**: Automated build, lint, and test on every commit
- **Multi-Service Testing**: Parallel testing of gateway-api, evaluator, and dashboard
- **Code Quality Checks**: Flake8 linting for Python code style enforcement
- **Health Check Tests**: Automated service health verification
- **Build Validation**: Ensure all services build successfully
- **PR Checks**: Required status checks before merge

### Batch Evaluation Optimization (NEW)
- **Efficient Queries**: Optimized database queries for pending logs
- **Configurable Batch Size**: Process logs in customizable batches
- **Progress Tracking**: Monitor evaluation progress in real-time
- **Error Recovery**: Continue processing even if individual evaluations fail
- **Utility Functions**: Helper functions for log management

---

## 🏗️ Architecture Updates

```
                    ┌─────────────┐
                    │   Scheduler │ (APScheduler)
                    │   (cron)    │
                    └──────┬──────┘
                           │
                           ↓
Client/Browser → Dashboard (8501) → Gateway API (18000) → OpenAI GPT
                           ↓              ↓
                      PostgreSQL (5432)
                           ↑
                      Evaluator (18001) → OpenAI Judge
                           ↓
                    ┌──────┴──────┐
                    │             │
                ┌───▼──┐     ┌───▼────┐
                │Slack │     │Discord │
                └──────┘     └────────┘
```

---

## 🆕 New Features in Detail

### APScheduler Implementation

**Automatic Scheduling**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Schedule evaluation every 60 minutes
scheduler.add_job(
    run_batch_evaluation,
    'interval',
    minutes=60,
    id='batch_evaluation',
    max_instances=1
)

scheduler.start()
```

**Configuration Options**:
- `ENABLE_AUTO_EVALUATION`: Enable/disable automatic evaluation
- `EVALUATION_INTERVAL_MINUTES`: Time between evaluation runs
- `EVALUATION_BATCH_SIZE`: Number of logs per batch
- `EVALUATION_JUDGE_TYPE`: Default judge type (rule/llm)

**Scheduler Status API**:
```bash
# Get scheduler information
curl http://localhost:18001/scheduler/status

# Response:
{
  "enabled": true,
  "interval_minutes": 60,
  "next_run": "2024-01-01T13:00:00Z",
  "last_run": "2024-01-01T12:00:00Z",
  "total_runs": 42
}
```

### Notification System

**Slack Notifications**:
```json
{
  "text": "🚨 Low Quality Alert",
  "attachments": [{
    "color": "danger",
    "fields": [
      {"title": "Log ID", "value": "123", "short": true},
      {"title": "Score", "value": "2.0/5.0", "short": true},
      {"title": "Model", "value": "gpt-3.5-turbo", "short": true},
      {"title": "Judge", "value": "llm", "short": true}
    ],
    "footer": "LLM Quality Observer"
  }]
}
```

**Discord Notifications**:
```json
{
  "embeds": [{
    "title": "🚨 Low Quality Alert",
    "color": 15158332,
    "fields": [
      {"name": "Log ID", "value": "123", "inline": true},
      {"name": "Score", "value": "2.0/5.0", "inline": true},
      {"name": "Prompt", "value": "User question..."}
    ],
    "footer": {"text": "LLM Quality Observer"}
  }]
}
```

**Notification Types**:

1. **Low-Quality Alerts** (Real-time):
   - Triggered when `score_overall ≤ NOTIFICATION_SCORE_THRESHOLD`
   - Includes log details, prompt snippet, and scores
   - Sent immediately after evaluation

2. **Batch Summaries** (Periodic):
   - Summary of batch evaluation results
   - Statistics: total evaluated, average score, low-quality count
   - Sent after each scheduler run

### CI/CD Workflow

**GitHub Actions Workflow** (`.github/workflows/ci.yml`):
```yaml
name: CI

on:
  push:
    branches: [main, feat/*]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install flake8
      - name: Lint with flake8
        run: flake8 services/

  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [gateway-api, evaluator, dashboard]
    steps:
      - uses: actions/checkout@v3
      - name: Build ${{ matrix.service }}
        run: docker build services/${{ matrix.service }}

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker compose -f infra/docker/docker-compose.local.yml up -d
      - name: Run health checks
        run: |
          curl -f http://localhost:18000/health
          curl -f http://localhost:18001/health
```

**Flake8 Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv,venv,build,dist
ignore = E203,W503
```

### Health Check Tests

**Test Suite** (`services/*/tests/test_health.py`):
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_response_time():
    response = client.get("/health")
    assert response.elapsed.total_seconds() < 1.0
```

---

## 📖 New API Endpoints

### Evaluator Service

#### GET /scheduler/status
**Description**: Get scheduler information

**Response**:
```json
{
  "enabled": true,
  "interval_minutes": 60,
  "batch_size": 10,
  "judge_type": "rule",
  "next_run_time": "2024-01-01T13:00:00Z",
  "last_run_time": "2024-01-01T12:00:00Z",
  "total_runs": 42,
  "last_run_stats": {
    "evaluated_count": 10,
    "average_score": 4.2,
    "low_quality_count": 1
  }
}
```

#### POST /scheduler/trigger
**Description**: Manually trigger scheduler (in addition to automatic runs)

**Response**:
```json
{
  "message": "Scheduler triggered",
  "job_id": "batch_evaluation"
}
```

#### GET /notifications/stats
**Description**: Get notification delivery statistics

**Response**:
```json
{
  "total_sent": 150,
  "by_channel": {
    "slack": 80,
    "discord": 70
  },
  "by_type": {
    "low_quality_alert": 30,
    "batch_summary": 120
  },
  "success_rate": 0.98
}
```

---

## 🔧 Configuration Updates

### New Environment Variables

```bash
# Batch Evaluation Scheduler (v0.4.0+)
ENABLE_AUTO_EVALUATION=true           # Enable automatic evaluation
EVALUATION_INTERVAL_MINUTES=60        # Run every 60 minutes
EVALUATION_BATCH_SIZE=10              # Process 10 logs per batch
EVALUATION_JUDGE_TYPE=rule            # Default judge type

# Notification Settings (v0.4.0+)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
NOTIFICATION_SCORE_THRESHOLD=3        # Alert when score ≤ 3
```

### Updated .env.local.example

```bash
# Existing variables...

# Batch Evaluation Scheduler (v0.4.0+)
ENABLE_AUTO_EVALUATION=true
EVALUATION_INTERVAL_MINUTES=60
EVALUATION_BATCH_SIZE=10
EVALUATION_JUDGE_TYPE=rule

# Notification Settings (v0.4.0+)
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
NOTIFICATION_SCORE_THRESHOLD=3
```

---

## 📁 Updated Project Structure

```
LLM-Quality-Observer/
├── .github/
│   └── workflows/
│       └── ci.yml               # NEW: GitHub Actions CI/CD
├── .flake8                      # NEW: Flake8 configuration
├── services/
│   ├── gateway-api/
│   │   └── tests/               # NEW: Health check tests
│   │       ├── __init__.py
│   │       └── test_health.py
│   ├── evaluator/
│   │   ├── app/
│   │   │   ├── scheduler.py     # NEW: APScheduler integration
│   │   │   ├── notifier.py      # NEW: Slack/Discord notifications
│   │   │   └── utils.py         # NEW: Utility functions
│   │   └── tests/               # NEW: Health check tests
│   │       ├── __init__.py
│   │       └── test_health.py
│   └── dashboard/
│       └── tests/
└── docs/
    └── RELEASE_NOTES_v0.4.0.md  # This file
```

---

## 🔄 Migration from v0.3.0

### Database Schema (No changes)
The database schema remains compatible with v0.3.0. No migration required.

### Configuration Updates

1. **Update .env.local with scheduler settings**:
```bash
# Add these new variables
ENABLE_AUTO_EVALUATION=true
EVALUATION_INTERVAL_MINUTES=60
EVALUATION_BATCH_SIZE=10
EVALUATION_JUDGE_TYPE=rule
NOTIFICATION_SCORE_THRESHOLD=3
```

2. **Add notification webhooks** (optional):
```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

3. **Restart Evaluator service**:
```bash
cd infra/docker
docker compose -f docker-compose.local.yml restart evaluator
```

### Verify Scheduler

```bash
# Check scheduler status
curl http://localhost:18001/scheduler/status

# Check logs for scheduler startup
docker logs llm-evaluator | grep -i scheduler
```

---

## 🚀 Setting Up Notifications

### Slack Setup

1. **Create Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create new app → Incoming Webhooks
   - Add to workspace and select channel
   - Copy webhook URL

2. **Configure in .env.local**:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

3. **Test notification**:
```bash
# Trigger evaluation with low threshold to force alert
NOTIFICATION_SCORE_THRESHOLD=5 docker compose -f docker-compose.local.yml restart evaluator

# Send test request and evaluate
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "user_id": "test"}'

curl -X POST "http://localhost:18001/evaluate-once?limit=1"
```

### Discord Setup

1. **Create Discord Webhook**:
   - Open Discord server settings
   - Integrations → Webhooks → New Webhook
   - Select channel and copy URL

2. **Configure in .env.local**:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz
```

3. **Test notification**: Same as Slack test above

---

## 🧪 Testing

### Test Scheduler

```bash
# Check scheduler is running
curl http://localhost:18001/scheduler/status

# Expected response:
{
  "enabled": true,
  "next_run_time": "2024-01-01T13:00:00Z",
  ...
}

# Manually trigger evaluation
curl -X POST "http://localhost:18001/scheduler/trigger"

# Check logs
docker logs llm-evaluator | grep "Batch evaluation"
```

### Test Notifications

```bash
# Generate low-quality response (adjust prompt for poor response)
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "asdf", "user_id": "test"}'

# Evaluate (should trigger notification if score is low)
curl -X POST "http://localhost:18001/evaluate-once?limit=1"

# Check Slack/Discord channel for notification
```

### Run CI Tests Locally

```bash
# Lint check
pip install flake8
flake8 services/

# Build services
docker build services/gateway-api
docker build services/evaluator
docker build services/dashboard

# Run health check tests
cd services/gateway-api
pip install pytest httpx
pytest tests/

cd ../evaluator
pytest tests/
```

---

## 💡 Improvements

- **Automation**: Eliminates need for manual evaluation triggers
- **Proactive Monitoring**: Real-time alerts for quality issues
- **Team Collaboration**: Slack/Discord integration keeps teams informed
- **Code Quality**: Flake8 ensures consistent Python style
- **Reliability**: CI/CD catches issues before deployment
- **Scalability**: Batch processing handles high-volume scenarios
- **Observability**: Scheduler status tracking and notification stats

---

## 🐛 Bug Fixes

- Fixed database connection pool exhaustion during batch processing
- Improved error handling for failed LLM API calls
- Fixed race condition in concurrent evaluation requests
- Enhanced graceful shutdown for scheduler cleanup
- Fixed timezone handling in scheduler timestamps

---

## ⚠️ Known Limitations

- **Scheduler Precision**: Interval-based, not cron-style scheduling
- **Notification Rate Limits**: Slack/Discord have rate limits (respect webhook limits)
- **Single Instance**: Scheduler designed for single evaluator instance
- **No Notification Retry**: Failed notifications are logged but not retried
- **Limited Test Coverage**: Only health checks, no integration tests

---

## 🛣️ Roadmap to v0.5.0

- [ ] Prometheus metrics for monitoring
- [ ] Grafana dashboards for visualization
- [ ] Email notification support (SMTP)
- [ ] Advanced alerting rules
- [ ] Notification retry mechanism
- [ ] Multi-instance scheduler coordination

---

## 📝 Technical Notes

### APScheduler Configuration

The scheduler uses `AsyncIOScheduler` for FastAPI compatibility:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.enable_auto_evaluation:
        scheduler.add_job(
            run_batch_evaluation,
            'interval',
            minutes=settings.evaluation_interval_minutes,
            id='batch_evaluation',
            max_instances=1
        )
        scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Notification Implementation

Uses `httpx` for async webhook calls:

```python
import httpx

async def send_slack_notification(message: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.slack_webhook_url,
            json=message,
            timeout=10.0
        )
        return response.status_code == 200
```

### Batch Processing Logic

```python
from app.utils import get_pending_logs

async def run_batch_evaluation():
    # Get unevaluated logs
    pending_logs = get_pending_logs(
        limit=settings.evaluation_batch_size
    )

    results = []
    for log in pending_logs:
        try:
            evaluation = await evaluate_log(
                log,
                judge_type=settings.evaluation_judge_type
            )
            results.append(evaluation)

            # Send notification if low quality
            if evaluation.score_overall <= settings.notification_score_threshold:
                await send_low_quality_alert(log, evaluation)
        except Exception as e:
            logger.error(f"Evaluation failed for log {log.id}: {e}")
            continue

    # Send batch summary
    await send_batch_summary(results)

    return len(results)
```

---

## 📚 Documentation Updates

- Added scheduler configuration guide
- Documented notification setup for Slack and Discord
- Updated architecture diagrams with automation flow
- Added CI/CD pipeline documentation
- Created troubleshooting guide for common issues

---

## 🔒 Security Considerations

- **Webhook URLs**: Store in environment variables, never commit to git
- **Rate Limiting**: Consider implementing rate limits for notification webhooks
- **Error Messages**: Ensure notifications don't expose sensitive data
- **CI Secrets**: Use GitHub Secrets for sensitive CI/CD variables

---

## 🙏 Acknowledgments

- APScheduler team for robust scheduling framework
- Slack and Discord for webhook APIs
- GitHub Actions for CI/CD platform
- Community feedback on automation needs

---

**Previous Release**: [v0.3.0](./RELEASE_NOTES_v0.3.0.md)
**Next Release**: v0.5.0 will introduce Prometheus/Grafana monitoring and email notifications
