# LLM Quality Observer - Project Overview

> **AI Agent Guide**: This document provides comprehensive project information for AI coding assistants (Claude Code, OpenAI Codex, etc.)

---

## 📌 Project Identity

**Name:** LLM Quality Observer
**Version:** v0.6.0
**Type:** MLOps Platform for LLM Quality Monitoring
**Architecture:** Microservices (FastAPI, Next.js, Docker)
**Status:** Production-Ready

---

## 🎯 Project Purpose

LLM Quality Observer는 대형 언어 모델(LLM)의 응답 품질을 **자동으로 모니터링하고 평가**하는 프로덕션급 MLOps 플랫폼입니다.

### 핵심 가치

1. **자동화**: LLM 요청/응답 자동 로깅, 품질 자동 평가
2. **실시간 모니터링**: Prometheus + Grafana 기반 실시간 메트릭
3. **프로액티브 알림**: 42개 Alert Rules로 품질 저하 사전 감지
4. **데이터 기반 의사결정**: 고급 분석 API로 모델 성능 비교

### 주요 사용 사례

- LLM 기반 서비스의 품질 관리
- 여러 LLM 모델 성능 비교 및 선택
- 프롬프트 엔지니어링 효과 측정
- 품질 저하 시 즉각 대응 (알림)
- 비용 대비 성능 최적화

---

## 🏗️ System Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
├─────────────┬───────────────┬───────────────────┤
│ Gateway API │  Evaluator    │  Next.js Dashboard│
│   :18000    │    :18001     │      :3000        │
└──────┬──────┴───────┬───────┴───────────────────┘
       │              │
       v              v
┌─────────────────────────────────────────────────┐
│              Data Layer                          │
│           PostgreSQL :5432                       │
└─────────────────────────────────────────────────┘
       ^              ^
       │              │
┌──────┴──────────────┴───────────────────────────┐
│         Monitoring & Alerting Layer             │
├─────────────┬──────────────┬────────────────────┤
│ Prometheus  │ Alertmanager │    Grafana         │
│   :9090     │    :9093     │     :3001          │
└─────────────┴──────────────┴────────────────────┘
```

### 서비스 구성 (7개)

| Service | Port | Tech Stack | Purpose |
|---------|------|------------|---------|
| **Gateway API** | 18000 | FastAPI, Python 3.12 | LLM 요청 처리 및 로깅 |
| **Evaluator** | 18001 | FastAPI, Python 3.12 | 자동 평가 및 알림 |
| **Dashboard** | 18002 | Streamlit | 레거시 대시보드 |
| **Web Dashboard** | 3000 | Next.js, TypeScript | 현대적 웹 UI |
| **PostgreSQL** | 5432 | PostgreSQL 16 | 데이터 저장 |
| **Prometheus** | 9090 | Prometheus | 메트릭 수집, Alert Rules |
| **Alertmanager** | 9093 | Alertmanager | Alert 라우팅 |
| **Grafana** | 3001 | Grafana | 모니터링 대시보드 |

---

## 📊 Data Flow

### 1. Request Flow (요청 흐름)

```
Client Request
    ↓
Gateway API (/chat)
    ↓
OpenAI API (GPT-5 mini or GPT-4)
    ↓
Gateway API (저장)
    ↓
PostgreSQL (llm_logs)
    ↓
Prometheus Metrics
```

### 2. Evaluation Flow (평가 흐름)

```
Scheduler (매 60분)
    ↓
Evaluator Service
    ↓
PostgreSQL (llm_logs 읽기)
    ↓
Rule-based Evaluation + LLM-as-a-Judge
    ↓
PostgreSQL (llm_evaluations 저장)
    ↓
Notification (Slack/Discord/Email)
    ↓
Prometheus Metrics
```

### 3. Alert Flow (알림 흐름)

```
Services (Gateway, Evaluator)
    ↓
Prometheus (metrics 수집)
    ↓
Alert Rules 평가 (42 rules)
    ↓
Alertmanager (routing)
    ↓
Receivers (Slack/Discord/Email)
```

---

## 🗄️ Database Schema

### Table: llm_logs

```sql
CREATE TABLE llm_logs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(255),
    prompt TEXT NOT NULL,
    response TEXT,
    model_version VARCHAR(50),
    latency_ms FLOAT,
    status VARCHAR(20)  -- 'success' or 'error'
);
```

### Table: llm_evaluations

```sql
CREATE TABLE llm_evaluations (
    id SERIAL PRIMARY KEY,
    log_id INTEGER REFERENCES llm_logs(id),
    created_at TIMESTAMP DEFAULT NOW(),
    score_overall FLOAT,
    score_instruction_following FLOAT,
    score_truthfulness FLOAT,
    comments TEXT,
    judge_model VARCHAR(50),
    raw_judge_response TEXT
);
```

---

## 🔧 Technology Stack

### Backend Services

- **Language**: Python 3.12
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 16
- **LLM Client**: OpenAI Python SDK
- **Scheduler**: APScheduler
- **Metrics**: prometheus-client
- **Notifications**: httpx (Slack/Discord), aiosmtplib (Email)

### Frontend

- **Framework**: Next.js 14+
- **Language**: TypeScript
- **UI Library**: shadcn/ui, Tailwind CSS
- **State Management**: React Context
- **i18n**: Custom translation system (EN/KO/JA/ZH)

### Infrastructure

- **Containerization**: Docker, Docker Compose
- **Monitoring**: Prometheus, Grafana, Alertmanager
- **Database**: PostgreSQL 16
- **Reverse Proxy**: None (직접 포트 노출)

### Development Tools

- **Package Manager**: uv (Python), npm (Node.js)
- **Code Quality**: ruff (Python linter), ESLint (TypeScript)
- **Version Control**: Git, GitHub
- **CI/CD**: GitHub Actions

---

## 📁 Project Structure

```
LLM-Quality-Observer/
├── agent/                    # AI 에이전트 가이드 (NEW)
│   ├── PROJECT_OVERVIEW.md
│   ├── CODING_STANDARDS.md
│   └── WORKFLOW.md
│
├── services/
│   ├── gateway-api/         # FastAPI - LLM 게이트웨이
│   │   ├── app/
│   │   │   ├── main.py      # 엔트리포인트
│   │   │   ├── config.py    # 환경 변수
│   │   │   ├── models.py    # SQLAlchemy 모델
│   │   │   ├── schemas.py   # Pydantic 스키마
│   │   │   ├── llm_client.py # OpenAI 클라이언트
│   │   │   └── metrics.py   # Prometheus 메트릭
│   │   └── pyproject.toml
│   │
│   ├── evaluator/           # FastAPI - 평가 서비스
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── rules.py     # Rule-based 평가
│   │   │   ├── llm_judge.py # LLM-as-a-Judge
│   │   │   ├── scheduler.py # APScheduler
│   │   │   ├── notifier.py  # 알림 전송
│   │   │   └── metrics.py
│   │   └── pyproject.toml
│   │
│   ├── dashboard/           # Streamlit (레거시)
│   │   └── app/
│   │       └── main.py
│   │
│   └── web/
│       └── dashboard/       # Next.js 웹 대시보드
│           ├── app/         # Next.js 13+ App Router
│           ├── components/
│           ├── lib/
│           └── locales/     # i18n
│
├── infra/
│   ├── docker/
│   │   └── docker-compose.local.yml
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts/          # 42 Alert Rules
│   │       ├── http_alerts.yml
│   │       ├── llm_alerts.yml
│   │       ├── evaluation_alerts.yml
│   │       └── system_alerts.yml
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   └── grafana/
│       ├── dashboards/      # 3개 대시보드
│       │   ├── llm-quality-observer.json
│       │   ├── alert-history.json
│       │   └── advanced-analytics.json
│       └── provisioning/
│
├── configs/
│   └── env/
│       └── .env.local.example
│
├── scripts/
│   └── test-v0.6.0.sh       # 자동화 테스트
│
├── docs/
│   ├── README-main-us.md
│   ├── ROADMAP.md
│   ├── API_GUIDE_v0.6.0.md
│   ├── TESTING_GUIDE_v0.6.0.md
│   └── release_notes/
│       └── RELEASE_NOTES_v0.6.0.md
│
├── CLAUDE.md                # Claude Code 전용 가이드
└── README.md
```

---

## 🚦 Development Status

### ✅ Completed (v0.6.0)

- [x] Gateway API with LLM integration
- [x] Automatic evaluation system (rule-based + LLM judge)
- [x] Automated scheduler (APScheduler)
- [x] Multi-channel notifications (Slack, Discord, Email)
- [x] Prometheus metrics collection
- [x] Grafana dashboards (3개)
- [x] **Alertmanager integration** (NEW in v0.6.0)
- [x] **42 Alert Rules** (NEW in v0.6.0)
- [x] **Advanced Analytics API** (NEW in v0.6.0)
- [x] Next.js web dashboard with i18n
- [x] CI/CD pipeline (GitHub Actions)

### 🚧 In Progress

- [ ] None (v0.6.0 완료)

### 📋 Planned (v0.7.0+)

- [ ] Cost tracking (token usage)
- [ ] Multi-model support enhancements
- [ ] Custom dashboard builder
- [ ] Alert rule management UI
- [ ] SLA tracking

---

## 🔐 Environment Variables

### 필수 환경 변수

```bash
# LLM API
LLM_API_KEY=sk-...                    # OpenAI API Key
OPENAI_MODEL_MAIN=gpt-5-mini          # Main model
OPENAI_MODEL_JUDGE=gpt-4o-mini        # Judge model

# Database
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality

# Application
APP_ENV=local
LOG_LEVEL=DEBUG
```

### 선택적 환경 변수

```bash
# Scheduler
ENABLE_AUTO_EVALUATION=true
EVALUATION_INTERVAL_MINUTES=60
EVALUATION_BATCH_SIZE=10
EVALUATION_JUDGE_TYPE=rule           # 'rule' or 'llm' or 'both'

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
NOTIFICATION_SCORE_THRESHOLD=3

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient@example.com
```

---

## 🎯 Key Metrics

### Application Metrics

**Gateway API:**
- `llm_gateway_http_requests_total` - Total HTTP requests
- `llm_gateway_http_request_duration_seconds` - Request latency
- `llm_gateway_llm_request_duration_seconds` - LLM call latency
- `llm_gateway_llm_requests_total{status, model_version}` - LLM requests by status

**Evaluator:**
- `llm_evaluator_evaluations_total{status, judge_type}` - Evaluations count
- `llm_evaluator_evaluation_duration_seconds` - Evaluation processing time
- `llm_evaluator_evaluation_scores` - Score distribution
- `llm_evaluator_pending_logs` - Pending logs count
- `llm_evaluator_notifications_sent_total{channel, status}` - Notifications sent

### Alert Rules Summary

- **HTTP Alerts**: 7 rules (error rates, latency)
- **LLM Alerts**: 8 rules (timeout, latency spikes, failures)
- **Evaluation Alerts**: 12 rules (score drops, backlogs)
- **System Alerts**: 15 rules (service health, database, storage)

---

## 🔗 External Dependencies

### APIs

- **OpenAI API**: GPT-5 mini, GPT-4o-mini
- **Slack API**: Webhook notifications (optional)
- **Discord API**: Webhook notifications (optional)
- **SMTP Server**: Email notifications (optional)

### Services

- **PostgreSQL**: Primary data store
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Alertmanager**: Alert routing

---

## 📖 Documentation Index

### For Users

- [README.md](../README.md) - Project introduction
- [TESTING_GUIDE_v0.6.0.md](../docs/TESTING_GUIDE_v0.6.0.md) - How to test
- [API_GUIDE_v0.6.0.md](../docs/API_GUIDE_v0.6.0.md) - API documentation

### For Developers

- [CODING_STANDARDS.md](./CODING_STANDARDS.md) - Coding conventions
- [WORKFLOW.md](./WORKFLOW.md) - Development workflow
- [ROADMAP.md](../docs/ROADMAP.md) - Future plans

### For DevOps

- [Alertmanager README](../infra/alertmanager/README.md) - Alert setup
- [Alert Rules README](../infra/prometheus/alerts/README.md) - Alert rules
- [Grafana Dashboard Guide](../infra/grafana/NEW_DASHBOARDS_GUIDE.md) - Dashboard usage

---

## ⚠️ Important Notes

### For AI Agents

1. **Always read files before editing**: Use Read tool before Edit/Write
2. **Follow existing patterns**: Maintain consistency with existing code
3. **Test before committing**: Run tests, verify functionality
4. **Document changes**: Update relevant documentation
5. **Never commit secrets**: Check .env files, API keys

### Critical Rules

- ❌ **Never expose API keys** in code or commits
- ❌ **Never delete data** without user confirmation
- ❌ **Never force push** to main branch
- ❌ **Never skip tests** for production code
- ✅ **Always use type hints** in Python
- ✅ **Always validate input** from external sources
- ✅ **Always handle errors** gracefully
- ✅ **Always write tests** for new features

---

## 🎓 Learning Resources

### Understanding the Codebase

1. Start with [CLAUDE.md](../CLAUDE.md) for quick overview
2. Read [CODING_STANDARDS.md](./CODING_STANDARDS.md) for conventions
3. Review service-specific README files
4. Check recent commits for context

### Key Files to Understand

- `services/gateway-api/app/main.py` - Gateway entry point
- `services/evaluator/app/scheduler.py` - Evaluation logic
- `infra/prometheus/alerts/*.yml` - Alert definitions
- `services/web/dashboard/app/layout.tsx` - Next.js layout

---

**Last Updated**: 2026-01-02 (v0.6.0 release)
**Maintained by**: @dongkoony
**AI Agent Compatible**: Claude Code, OpenAI Codex, GitHub Copilot
