# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM-Quality-Observer is a microservices-based MLOps platform for monitoring and evaluating LLM response quality. The system logs LLM interactions, evaluates them using rule-based and LLM-as-a-judge approaches, and provides dashboards for visualization and monitoring.

Current status: v0.5.0 with Gateway API + Evaluator + Dashboard + Prometheus + Grafana operational.

## Architecture

Full-stack microservices architecture with monitoring:

```
Client → Gateway API → Postgres ← Evaluator Service
            ↓             ↓            ↓
         Dashboard    Prometheus → Grafana
```

- **Gateway API** (port 18000): FastAPI service that receives chat requests, calls OpenAI GPT-5 mini, logs to database, exposes Prometheus metrics
- **Evaluator Service** (port 18001): Batch evaluation service that scores LLM outputs using rule-based and LLM-as-a-judge methods, sends notifications (Slack/Discord/Email), exposes Prometheus metrics
- **Dashboard Service** (port 8501): Streamlit UI for visualizing quality metrics, latency distributions, and error rates
- **Postgres** (port 5432): PostgreSQL 16 database with `llm_logs` and `llm_evaluations` tables
- **Prometheus** (port 9090): Metrics collection and time-series database
- **Grafana** (port 3000): Monitoring dashboards and visualization platform

## Common Commands

### Local Development (Docker)

```bash
# Start all services
cd infra/docker
docker compose -f docker-compose.local.yml up --build

# Start specific service
docker compose -f docker-compose.local.yml up gateway-api --build

# Stop all services
docker compose -f docker-compose.local.yml down

# View logs
docker compose -f docker-compose.local.yml logs -f gateway-api
docker compose -f docker-compose.local.yml logs -f evaluator
```

### Database Operations

```bash
# Connect to Postgres
docker exec -it llm-postgres psql -U llm_user -d llm_quality

# View recent logs
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "SELECT id, created_at, user_id, LEFT(prompt, 50) AS prompt_snippet, model_version, latency_ms, status FROM llm_logs ORDER BY id DESC LIMIT 10;"

# View evaluations
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "SELECT id, log_id, score_overall, score_instruction_following, score_truthfulness, judge_model FROM llm_evaluations ORDER BY id DESC LIMIT 10;"
```

### Testing Services

```bash
# Test Gateway API health
curl http://localhost:18000/health

# Test Gateway API chat endpoint
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user", "model_version": null}'

# Test Evaluator health
curl http://localhost:18001/health

# Trigger evaluation batch
curl -X POST "http://localhost:18001/evaluate-once?limit=5"

# View Dashboard
# Open browser to http://localhost:8501

# View Prometheus metrics (Gateway)
curl http://localhost:18000/metrics

# View Prometheus metrics (Evaluator)
curl http://localhost:18001/metrics

# View Prometheus UI
# Open browser to http://localhost:9090

# View Grafana Dashboard
# Open browser to http://localhost:3000 (admin/admin)
```

### Dependency Management

Each service uses `uv` for dependency management:

```bash
# Install dependencies for a service
cd services/gateway-api
uv sync

# Add a new dependency
cd services/gateway-api
uv add <package-name>

# Update dependencies
uv sync --upgrade
```

## Key Technical Details

### Gateway API Service (services/gateway-api)

**Entry point**: `app/main.py`
- `/health`: Health check endpoint
- `/chat`: Main LLM endpoint that accepts ChatRequest and returns ChatResponse
- `/metrics`: Prometheus metrics endpoint

**LLM Client** (`app/llm_client.py`):
- Uses OpenAI Python SDK's `client.responses.create()` API (not the standard chat completions API)
- Model resolution: Falls back to `OPENAI_MODEL_MAIN` env var if no model specified
- Returns tuple of `(response_text, latency_ms)`
- Timing measured using `time.perf_counter()`

**Database** (`app/db.py`, `app/models.py`):
- SQLAlchemy ORM with `LLMLog` model
- Tables auto-created on startup via `Base.metadata.create_all(bind=engine)`
- Fields: id, created_at, user_id, prompt, response, model_version, latency_ms, status

**Configuration** (`app/config.py`):
- Pydantic Settings loading from environment variables
- Required: `DATABASE_URL`, `OPENAI_MODEL_MAIN`, `LLM_API_KEY`
- Optional: `LLM_API_BASE_URL`, `LOG_LEVEL`, `APP_ENV`

**Metrics** (`app/metrics.py`):
- Prometheus client integration for observability
- HTTP request metrics: rate, latency (p50/p95/p99), status codes
- LLM request metrics: call rate, latency by model, success/error tracking
- Database metrics: query rate, latency by operation and table
- Middleware automatically captures HTTP request metrics

### Evaluator Service (services/evaluator)

**Entry point**: `app/main.py`
- `/health`: Health check endpoint
- `/evaluate-once`: Batch evaluation endpoint (processes up to N unevaluated logs)
- `/metrics`: Prometheus metrics endpoint

**Evaluation Logic**:
- `app/rules.py`: Rule-based evaluation (length checks, keyword detection)
- `app/llm_judge.py`: LLM-as-a-judge evaluation using GPT-4 or similar
- Combines scores from both approaches
- Creates `LLMEvaluation` records with scores and comments

**Scheduler** (`app/scheduler.py`):
- APScheduler for automated batch evaluation
- Configurable interval (default: 60 minutes)
- Processes pending logs in batches
- Records metrics for each evaluation run

**Notifications** (`app/notifier.py`):
- Multi-channel notification system: Slack, Discord, Email
- Low-quality alerts when score falls below threshold
- Batch evaluation summaries
- SMTP integration for email (via aiosmtplib)

**Database** (`app/models.py`):
- Reuses `LLMLog` model from shared schema
- New `LLMEvaluation` model: log_id (FK), score_overall, score_instruction_following, score_truthfulness, comments, judge_model, raw_judge_response

**Configuration** (`app/config.py`):
- Uses same `DATABASE_URL` as gateway
- LLM Judge: `OPENAI_MODEL_JUDGE` for the judge model
- Scheduler: `ENABLE_AUTO_EVALUATION`, `EVALUATION_INTERVAL_MINUTES`, `EVALUATION_BATCH_SIZE`, `EVALUATION_JUDGE_TYPE`
- Notifications: `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`, `NOTIFICATION_SCORE_THRESHOLD`
- Email: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_TO_EMAILS`

**Metrics** (`app/metrics.py`):
- Evaluation metrics: rate, duration, score distribution
- Batch evaluation metrics: runs, logs processed
- Notification metrics: sent count by channel and status
- Scheduler metrics: run count, pending logs gauge
- LLM judge metrics: request rate and latency

### Dashboard Service (services/dashboard)

**Entry point**: `app/main.py`
- Streamlit application
- Connects to same Postgres database
- Visualizes metrics from `llm_logs` and `llm_evaluations` tables

**Pages/Views**:
- Overview: Summary statistics, recent requests
- Quality Metrics: Score distributions, trends over time
- Latency Analysis: p50/p95/p99 latencies by model
- Model Comparison: Side-by-side model performance

### Prometheus (Monitoring)

**Configuration**: `infra/prometheus/prometheus.yml`
- Metrics collection from Gateway API and Evaluator services
- Scrape interval: 15 seconds
- Targets: gateway-api:8000, evaluator:8000
- Web UI accessible at http://localhost:9090

**Scrape Targets**:
- `gateway-api`: Collects HTTP, LLM, and database metrics
- `evaluator`: Collects evaluation, notification, and scheduler metrics
- `prometheus`: Self-monitoring

### Grafana (Visualization)

**Configuration**: `infra/grafana/provisioning/`
- Auto-provisioned Prometheus datasource
- Pre-configured LLM Quality Observer dashboard
- Dashboard JSON: `infra/grafana/dashboards/llm-quality-observer.json`
- Web UI accessible at http://localhost:3000 (admin/admin)

**Dashboard Panels** (14 panels total):
- Overview stats: request rate, evaluation rate, pending logs, notification rate
- HTTP performance: request distribution, latency percentiles
- LLM metrics: requests by model, latency analysis
- Quality scores: score distribution by judge type
- Notifications: delivery rates, alert tracking
- System health: scheduler runs, batch processing

### Environment Configuration

Environment variables are managed through `.env.local` file in `configs/env/`:

```env
APP_ENV=local
LOG_LEVEL=DEBUG
OPENAI_MODEL_MAIN=gpt-5-mini
OPENAI_MODEL_JUDGE=gpt-4o-mini
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality

# Batch Evaluation Scheduler (v0.4.0+)
ENABLE_AUTO_EVALUATION=true
EVALUATION_INTERVAL_MINUTES=60
EVALUATION_BATCH_SIZE=10
EVALUATION_JUDGE_TYPE=rule

# Notification Settings (v0.4.0+)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
NOTIFICATION_SCORE_THRESHOLD=3

# Email Notification Settings (v0.5.0+)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

**Important**: `.env.local` is gitignored. Each developer must create their own from the template.

### Docker Configuration

All services use similar Dockerfile pattern:
1. Python 3.12-slim base image
2. Install system dependencies (build-essential, libpq-dev for psycopg2)
3. Install `uv` package manager
4. Copy `pyproject.toml` and run `uv sync --no-dev`
5. Copy application code
6. Run with `uv run uvicorn` or `uv run streamlit`

Docker Compose (`infra/docker/docker-compose.local.yml`):
- Defines 6 services: postgres, gateway-api, evaluator, dashboard, prometheus, grafana
- Application services depend on postgres
- Prometheus depends on gateway-api and evaluator
- Grafana depends on prometheus
- Application services mount `configs/env/.env.local` as env_file
- Exposed ports:
  - Gateway API: 18000
  - Evaluator: 18001
  - Dashboard: 8501
  - Prometheus: 9090
  - Grafana: 3000
  - Postgres: 5432

## Development Workflow

1. **Adding a new feature to Gateway API**:
   - Modify `services/gateway-api/app/main.py` for new endpoints
   - Update `app/schemas.py` for new request/response models
   - Update `app/models.py` if database schema changes
   - Rebuild: `docker compose -f docker-compose.local.yml up gateway-api --build`

2. **Adding new evaluation criteria**:
   - Update `services/evaluator/app/rules.py` for rule-based checks
   - Update `services/evaluator/app/llm_judge.py` for judge prompt changes
   - Modify `app/models.py` if new score fields needed
   - Rebuild: `docker compose -f docker-compose.local.yml up evaluator --build`

3. **Adding new dashboard visualizations**:
   - Modify `services/dashboard/app/main.py`
   - Use Streamlit components (st.metric, st.line_chart, st.dataframe)
   - Query data from `llm_logs` or `llm_evaluations` tables
   - Rebuild: `docker compose -f docker-compose.local.yml up dashboard --build`

## Important Notes

- **OpenAI API**: Gateway uses `client.responses.create()` not `client.chat.completions.create()`. This is specific to GPT-5 mini's API interface.
- **Model Resolution**: If request doesn't specify model or uses placeholder "string", falls back to `OPENAI_MODEL_MAIN` from env.
- **Database Initialization**: Tables are auto-created on first run via SQLAlchemy's `create_all()`. No manual migration needed for local development.
- **Automated Evaluation** (v0.4.0+): Scheduler runs automatically when `ENABLE_AUTO_EVALUATION=true`. Configure interval with `EVALUATION_INTERVAL_MINUTES`.
- **Notifications** (v0.4.0+): Low-quality alerts sent when score ≤ `NOTIFICATION_SCORE_THRESHOLD`. Supports Slack, Discord, and Email (v0.5.0+).
- **Metrics** (v0.5.0+): All services expose `/metrics` endpoint for Prometheus scraping. Grafana dashboard auto-provisioned at startup.
- **Error Handling**: LLM failures are logged with status="error" but not evaluated. Only status="success" logs are processed by evaluator.

## Service Dependencies

```
gateway-api:
- fastapi, uvicorn
- sqlalchemy, psycopg2-binary
- pydantic, pydantic-settings
- openai
- httpx, python-dotenv
- prometheus-client (v0.5.0+)

evaluator:
- fastapi, uvicorn
- sqlalchemy, psycopg2-binary
- pydantic-settings
- openai
- apscheduler (v0.4.0+)
- httpx (v0.4.0+ for notifications)
- prometheus-client (v0.5.0+)
- aiosmtplib, email-validator (v0.5.0+ for email)

dashboard:
- streamlit
- sqlalchemy, psycopg2-binary
- pandas, plotly (for visualizations)
```

All managed via `uv` and defined in each service's `pyproject.toml`.

**Infrastructure Services** (v0.5.0+):
- **Prometheus**: Official prom/prometheus Docker image
- **Grafana**: Official grafana/grafana Docker image
