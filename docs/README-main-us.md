# LLM-Quality-Observer

[🇰🇷 KR](../README.md) | [🇺🇸 EN](README-main-us.md)

---

## Overview

**LLM-Quality-Observer** is an MLOps platform for **monitoring and evaluating** the quality of Large Language Model (LLM) responses.
Built on a microservices architecture, it logs LLM interactions, automatically evaluates quality, and provides real-time monitoring dashboards.

### Key Features

- ✅ **Gateway API**: LLM request processing and automatic logging
- ✅ **Automated Evaluation**: Dual evaluation system (rule-based + LLM-as-a-Judge)
- ✅ **Scheduler**: Automated batch evaluation (APScheduler)
- ✅ **Multi-Channel Notifications**: Slack, Discord, Email integration
- ✅ **Monitoring**: Prometheus metrics collection + Grafana dashboards
- ✅ **Advanced Alerting**: Alertmanager integration (42 production Alert Rules)
- ✅ **Advanced Analytics**: Hourly quality trends + model performance comparison API
- ✅ **Web Dashboard**: Next.js-based real-time quality visualization
- ✅ **Multi-Language Support**: English, Korean, Japanese, Chinese
- ✅ **CI/CD**: GitHub Actions automation pipeline

> **Current Version: v0.6.0** — Alertmanager, Alert Rules, Advanced Analytics API added

---

## 📊 Architecture

```mermaid
flowchart TB
    subgraph "Client"
        ClientApp[Client/Browser]
    end

    subgraph "Frontend"
        WebDashboard["Next.js Dashboard<br/>:3000"]
        Grafana["Grafana<br/>:3001"]
    end

    subgraph "Backend Services"
        Gateway["Gateway API<br/>:18000"]
        Evaluator["Evaluator<br/>:18001"]
        Dashboard["Streamlit Dashboard<br/>:18002"]
    end

    subgraph "Database"
        Postgres["PostgreSQL<br/>:5432"]
    end

    subgraph "Monitoring & Alerting"
        Prometheus["Prometheus<br/>:9090"]
        Alertmanager["Alertmanager<br/>:9093"]
    end

    subgraph "External Services"
        OpenAI_Main["OpenAI GPT<br/>(Main Model)"]
        OpenAI_Judge["OpenAI GPT<br/>(Judge Model)"]
    end

    subgraph "Notification Channels"
        Slack["Slack"]
        Discord["Discord"]
        Email["Email<br/>(SMTP)"]
    end

    %% Client connections
    ClientApp --> WebDashboard
    ClientApp --> Gateway

    %% Gateway connections
    Gateway --> OpenAI_Main
    Gateway --> Postgres
    Gateway -.metrics.-> Prometheus

    %% Evaluator connections
    Postgres --> Evaluator
    Evaluator --> OpenAI_Judge
    Evaluator --> Slack
    Evaluator --> Discord
    Evaluator --> Email
    Evaluator -.metrics.-> Prometheus

    %% Dashboard connections
    Postgres --> Dashboard

    %% Monitoring connections
    Prometheus --> Grafana
    Prometheus --> Alertmanager
    Alertmanager --> Slack
    Alertmanager --> Discord
    Alertmanager --> Email

    style Gateway fill:#4CAF50
    style Evaluator fill:#2196F3
    style Postgres fill:#FF9800
    style Prometheus fill:#E91E63
    style Alertmanager fill:#F44336
    style Grafana fill:#9C27B0
    style OpenAI_Main fill:#00BCD4
    style OpenAI_Judge fill:#00BCD4
```

### Service Components

| Service | Port | Description |
|---------|------|-------------|
| **Gateway API** | 18000 | LLM request processing and logging (FastAPI) |
| **Evaluator** | 18001 | Automated evaluation and notifications (FastAPI) |
| **Dashboard** | 18002 | Streamlit dashboard (legacy) |
| **Web Dashboard** | 3000 | Next.js web dashboard |
| **PostgreSQL** | 5432 | Log and evaluation result storage |
| **Prometheus** | 9090 | Metrics collection and Alert Rules |
| **Alertmanager** | 9093 | Alert routing and grouping |
| **Grafana** | 3001 | Monitoring dashboards (3 dashboards) |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- (Optional) Slack/Discord Webhook URL
- (Optional) Gmail SMTP account

### Installation

1. **Clone repository**
```bash
git clone https://github.com/dongkoony/LLM-Quality-Observer.git
cd LLM-Quality-Observer
```

2. **Configure environment variables**
```bash
cp configs/env/.env.local.example configs/env/.env.local
# Edit .env.local to set API keys
```

3. **Start services**
```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

4. **Verify services**
```bash
# Gateway API
curl http://localhost:18000/health

# Evaluator
curl http://localhost:18001/health

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3001  # admin/admin
```

---

## 📖 Usage Guide

### 1. Send LLM Request

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "user_id": "test-user",
    "model_version": "gpt-5-mini"
  }'
```

**Response example:**
```json
{
  "id": 1,
  "prompt": "Explain quantum computing...",
  "response": "Quantum computing is...",
  "model_version": "gpt-5-mini",
  "latency_ms": 1234,
  "status": "success"
}
```

### 2. Run Evaluation

**Manual evaluation:**
```bash
# Rule-based evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=rule"

# LLM-as-a-Judge evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=llm"
```

**Automatic evaluation:** Scheduler runs automatically at configured intervals (default: 60 minutes)

### 3. Check Dashboards

**Grafana Dashboard:**
1. Navigate to http://localhost:3001
2. Login with admin/admin
3. Go to Dashboards → LLM Quality Observer

**Included metrics:**
- HTTP request rate and latency
- LLM performance by model
- Evaluation score distribution
- Notification delivery status
- Scheduler execution state

### 4. Query Database

```bash
# Connect to PostgreSQL
docker exec -it llm-postgres psql -U llm_user -d llm_quality

# View recent logs
SELECT id, created_at, user_id,
       LEFT(prompt, 50) AS prompt,
       model_version, latency_ms, status
FROM llm_logs
ORDER BY id DESC
LIMIT 10;

# View evaluation results
SELECT l.id, l.prompt,
       e.score_overall, e.score_instruction_following, e.score_truthfulness,
       e.judge_type, e.comments
FROM llm_logs l
JOIN llm_evaluations e ON l.id = e.log_id
ORDER BY e.created_at DESC
LIMIT 10;
```

---

## 🔧 Feature Details

### Gateway API (v0.1.0+)

**Endpoints:**
- `GET /health` - Health check
- `POST /chat` - LLM request processing
- `GET /docs` - Swagger UI
- `GET /metrics` - Prometheus metrics

**Features:**
- OpenAI GPT model calls
- Automatic logging (prompt, response, latency, status)
- Model version tracking
- Prometheus metrics export

### Evaluator Service (v0.2.0+)

**Evaluation Methods:**

1. **Rule-Based Evaluation** (fast, cheap):
   - Response length validation
   - Keyword verification
   - Format compliance checks

2. **LLM-as-a-Judge** (v0.3.0+, accurate, costs money):
   - GPT-4 based quality evaluation
   - Multi-dimensional scoring (overall, instruction following, truthfulness)
   - Detailed evaluation comments

**Automated Scheduler** (v0.4.0+):
- Periodic evaluation via APScheduler
- Configurable interval and batch size
- Automatic start/stop

**Notification System** (v0.4.0+, v0.5.0):
- **Slack**: Webhook integration
- **Discord**: Webhook integration
- **Email** (v0.5.0): SMTP (Gmail, etc.)
- Immediate low-quality alerts
- Batch evaluation summaries

### Monitoring (v0.5.0)

**Prometheus Metrics:**
- `llm_gateway_http_requests_total` - HTTP request count
- `llm_gateway_http_request_duration_seconds` - Request latency
- `llm_gateway_llm_requests_total` - LLM call count
- `llm_evaluator_evaluations_total` - Evaluation count
- `llm_evaluator_evaluation_scores` - Score distribution
- `llm_evaluator_notifications_sent_total` - Notification count
- `llm_evaluator_pending_logs` - Pending log count

**Grafana Dashboard:**
- 14 visualization panels
- Real-time performance monitoring
- Quality trend analysis
- Notification status tracking

---

## ⚙️ Configuration

### Environment Variables

```bash
# Application
APP_ENV=local
LOG_LEVEL=DEBUG

# LLM Models
OPENAI_MODEL_MAIN=gpt-5-mini          # Model for Gateway
OPENAI_MODEL_JUDGE=gpt-4o-mini        # Model for evaluation
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality

# Batch Evaluation Scheduler (v0.4.0+)
ENABLE_AUTO_EVALUATION=true           # Enable automatic evaluation
EVALUATION_INTERVAL_MINUTES=60        # Evaluation interval (minutes)
EVALUATION_BATCH_SIZE=10              # Batch size
EVALUATION_JUDGE_TYPE=rule            # Default evaluation method (rule/llm)

# Notification Settings (v0.4.0+)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
NOTIFICATION_SCORE_THRESHOLD=3        # Alert threshold (≤ 3)

# Email Notifications (v0.5.0+)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

---

## 🏗️ Project Structure

```
LLM-Quality-Observer/
├── services/
│   ├── gateway-api/           # Gateway API service
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app
│   │   │   ├── config.py      # Configuration
│   │   │   ├── llm_client.py  # OpenAI client
│   │   │   ├── db.py          # Database
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   ├── schemas.py     # Pydantic schemas
│   │   │   └── metrics.py     # Prometheus metrics
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── evaluator/             # Evaluator service
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app
│   │   │   ├── rules.py       # Rule-based evaluation
│   │   │   ├── llm_judge.py   # LLM-as-a-Judge
│   │   │   ├── scheduler.py   # APScheduler
│   │   │   ├── notifier.py    # Notification system
│   │   │   ├── metrics.py     # Prometheus metrics
│   │   │   └── utils.py       # Utilities
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── dashboard/             # Streamlit dashboard
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── web/                   # Next.js web dashboard
│       └── dashboard/
│           ├── app/
│           ├── components/
│           ├── locales/       # Multi-language support
│           └── lib/
│
├── infra/
│   ├── docker/
│   │   └── docker-compose.local.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       ├── dashboards/
│       └── DASHBOARD_GUIDE-us.md
│
├── configs/
│   └── env/
│       ├── .env.local.example
│       └── .env.local          # gitignored
│
├── docs/
│   ├── release_notes/         # Release notes
│   │   ├── RELEASE_NOTES_v0.1.0.md
│   │   ├── RELEASE_NOTES_v0.2.0.md
│   │   ├── RELEASE_NOTES_v0.3.0.md
│   │   ├── RELEASE_NOTES_v0.4.0.md
│   │   └── RELEASE_NOTES_v0.5.0.md
│   ├── RELEASE_NOTES_v0.5.0_ko.md
│   ├── METRICS.md
│   ├── EMAIL_SETUP.md
│   └── README-main-us.md
│
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
│
├── .flake8                    # Flake8 configuration
└── README.md
```

---

## 🧪 Testing

### Health Check Tests

```bash
# Check all services
curl http://localhost:18000/health  # Gateway API
curl http://localhost:18001/health  # Evaluator
curl http://localhost:9090/-/healthy # Prometheus
curl http://localhost:3001/api/health # Grafana
```

### Integration Tests

```bash
# 1. Send LLM request
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "user_id": "test"}'

# 2. Run evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=1"

# 3. Check metrics
curl http://localhost:18000/metrics | grep llm_gateway
curl http://localhost:18001/metrics | grep llm_evaluator

# 4. Verify Grafana dashboard
open http://localhost:3001
```

### Automated Tests

```bash
# Run CI/CD pipeline locally
cd services/gateway-api
pytest tests/

cd ../evaluator
pytest tests/

# Lint check
flake8 services/
```

---

## 📈 Monitoring Guide

### Prometheus Query Examples

```promql
# HTTP request rate
sum(rate(llm_gateway_http_requests_total[5m]))

# LLM latency p95
histogram_quantile(0.95, sum(rate(llm_gateway_llm_request_duration_seconds_bucket[5m])) by (le, model))

# Evaluation score median
histogram_quantile(0.50, sum(rate(llm_evaluator_evaluation_scores_bucket{score_type="overall"}[5m])) by (le))

# Pending logs count
llm_evaluator_pending_logs
```

### Grafana Dashboard Usage

For detailed guide, see [Grafana Dashboard Guide](../infra/grafana/DASHBOARD_GUIDE-us.md)

---

## 📚 Documentation

### Release Notes

- [v0.5.0 (Latest)](./RELEASE_NOTES_v0.5.0.md) - Prometheus, Grafana, Email notifications
- [v0.4.0](./release_notes/RELEASE_NOTES_v0.4.0.md) - Scheduler, Slack/Discord notifications, CI/CD
- [v0.3.0](./release_notes/RELEASE_NOTES_v0.3.0.md) - LLM-as-a-Judge, Multi-language support
- [v0.2.0](./release_notes/RELEASE_NOTES_v0.2.0.md) - Dashboard, CORS, Rule-based evaluation
- [v0.1.0](./release_notes/RELEASE_NOTES_v0.1.0.md) - Initial release (Gateway + Evaluator)

### Technical Documentation

- [Metrics Reference](./METRICS.md) - Prometheus metrics details
- [Email Setup Guide](./EMAIL_SETUP.md) - Gmail SMTP configuration
- [Grafana Dashboard Guide](../infra/grafana/DASHBOARD_GUIDE-us.md) - Dashboard usage

---

## 🛣️ Roadmap

### Completed Features

- ✅ v0.1.0: Gateway API + Evaluator foundation
- ✅ v0.2.0: Web dashboard + Rule-based evaluation
- ✅ v0.3.0: LLM-as-a-Judge + Multi-language support
- ✅ v0.4.0: Automated scheduler + Slack/Discord notifications
- ✅ v0.5.0: Prometheus + Grafana + Email notifications

### Future Plans (v0.6.0+)

- [ ] **Alertmanager Integration**: Advanced alerting rules and routing
- [ ] **Multi-LLM Provider Support**: Anthropic Claude, Google Gemini, etc.
- [ ] **Cost Tracking**: Token usage and cost monitoring
- [ ] **A/B Testing**: Prompt and model comparison
- [ ] **User Feedback**: RLHF-style human evaluation
- [ ] **Kubernetes Deployment**: Helm charts and deployment guides
- [ ] **API Authentication**: JWT-based security
- [ ] **Rate Limiting**: Request limits and quota management

---

## 🔒 Security

### Precautions

- Never commit `.env.local` file (gitignored)
- Store OpenAI API key securely
- Don't expose Slack/Discord webhook URLs
- Use app passwords for SMTP (Gmail)

### Recommendations

- Store environment variables in secret managers for production
- Add authentication to API endpoints (v0.6.0+)
- Use HTTPS/TLS
- Regular dependency updates

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Python code must follow Flake8 style guide
- All PRs must pass CI tests
- Use Conventional Commits format for commit messages
- Add tests for new features

---

## 📄 License

This project is distributed under the MIT License.

---

## 👥 Author

**Dong-hyeon Shin (dongkoony)**
- GitHub: [@dongkoony](https://github.com/dongkoony)
- Email: dhyeon.shin@icloud.com

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/dongkoony/LLM-Quality-Observer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dongkoony/LLM-Quality-Observer/discussions)
- **Email**: dhyeon.shin@icloud.com

---

**⭐ If this project helped you, please give it a star!**
