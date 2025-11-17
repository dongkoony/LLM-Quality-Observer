# LLM-Quality-Observer

[🇰🇷 KR](../README.md) | [🇺🇸 EN](docs/README-main-us.md)

---

LLM-Quality-Observer is a small MLOps playground project for **monitoring and evaluating LLM responses**.  
It is designed as a portfolio-ready system that shows how to:

- Expose an LLM-backed chat API
- Log prompts, responses, and latency into a database
- (Planned) Run batch evaluation jobs on logged data
- (Planned) Visualize quality metrics on a dashboard

> Status: **v1 — Gateway API + logging to Postgres is working**

---

## Architecture Overview

Current v1 architecture:

```mermaid
flowchart TD
    C["Client (Swagger UI / HTTP)"]
    G["Gateway API (FastAPI)"]
    DB["Postgres (table: llm_logs)"]
    E["Evaluator Service (future)"]
    D["Dashboard Service (future)"]

    C --> G
    G -->|LLM call + latency + logging| DB
    DB --> E
    DB --> D
```

---

## Tech Stack

* **Language**: Python 3.12
* **LLM Provider**: OpenAI GPT-5 mini (via `responses` API)
* **Web Framework**: FastAPI
* **Database**: PostgreSQL 16
* **ORM**: SQLAlchemy
* **Config & Settings**: Pydantic Settings
* **Dependency Management**: [`uv`](https://github.com/astral-sh/uv)
* **Container / Orchestration**: Docker, Docker Compose

---

## Project Structure

High-level directory layout:

```text
LLM-Quality-Observer/
├── services/
│   ├── gateway-api/
│   │   ├── app/
│   │   │   ├── app/
│   │   │   │   ├── main.py
│   │   │   │   ├── config.py
│   │   │   │   ├── llm_client.py
│   │   │   │   ├── db.py
│   │   │   │   ├── models.py
│   │   │   │   ├── schemas.py
│   │   │   └── pyproject.toml
│   │   └── Dockerfile
│   ├── evaluator/
│   │   ├── app/
│   │   │   └── pyproject.toml
│   │   └── Dockerfile
│   └── dashboard/
│       ├── app/
│       │   └── pyproject.toml
│       └── Dockerfile
├── infra/
│   └── docker/
│       └── docker-compose.local.yml
├── configs/
│   └── env/
│       └── .env.local        # local env file (not committed)
└── README.md
```

### services/gateway-api

FastAPI-based gateway that:

* exposes `/health`, `/chat` endpoints
* calls OpenAI GPT-5 mini
* logs interactions to Postgres

Files:

* `app/app/main.py`

  * FastAPI application entrypoint
  * `/health` and `/chat` endpoints
  * Creates DB tables on startup (simple version)
  * Persists `LLMLog` rows and returns `ChatResponse`

* `app/app/config.py`

  * Pydantic `Settings` class
  * Reads environment variables:

    * `APP_ENV`
    * `DATABASE_URL`
    * `OPENAI_MODEL_MAIN`
    * `LLM_API_BASE_URL`
    * `LLM_API_KEY`
    * `LOG_LEVEL`

* `app/app/llm_client.py`

  * Wraps OpenAI Python client
  * Resolves model version (uses `OPENAI_MODEL_MAIN` by default)
  * Calls `client.responses.create(...)`
  * Returns `(response_text, latency_ms)`

* `app/app/db.py`

  * SQLAlchemy engine & session factory
  * `get_db()` dependency used by FastAPI

* `app/app/models.py`

  * SQLAlchemy ORM model: `LLMLog`
  * Columns:

    * `id`, `created_at`
    * `user_id`, `prompt`, `response`
    * `model_version`
    * `latency_ms`
    * `status`

* `app/app/schemas.py`

  * Pydantic models for request/response:

    * `ChatRequest`
    * `ChatResponse`

* `app/pyproject.toml`

  * Python package metadata / dependencies for the gateway service
  * Used by `uv sync` both locally and inside Docker image.

### services/evaluator (planned)

* Python service for **batch evaluation of logged LLM outputs**
* Will read from Postgres (`llm_logs`), compute metrics, and write evaluation results
* `app/pyproject.toml` is already prepared for future implementation.
* `Dockerfile` builds a Python 3.12 image and installs dependencies via `uv`.

### services/dashboard (planned)

* UI/dashboard service (e.g. Streamlit or FastAPI + frontend)
* Will visualize:

  * latency stats
  * quality scores
  * error rates
* `app/pyproject.toml` prepared for future implementation.
* `Dockerfile` ready for Python 3.12 + `uv` build.

### infra/docker

* `docker-compose.local.yml`

  * Local development stack:

    * `llm-postgres` (Postgres 16)
    * `llm-gateway-api` (FastAPI + OpenAI client)
    * `llm-evaluator` (placeholder)
    * `llm-dashboard` (placeholder)
  * Binds gateway API to `localhost:18000` by default.

### configs/env

* `.env.local`

  * Local configuration used by `docker-compose.local.yml`
  * Mounted as env file for gateway/evaluator/dashboard

Example `.env.local`:

```env
# Application
APP_ENV=local
LOG_LEVEL=DEBUG

# LLM
OPENAI_MODEL_MAIN=gpt-5-mini
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...

# Database (used by gateway-api)
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality
```

---

## Getting Started (Local, Docker)

### Prerequisites

* Docker
* Docker Compose plugin (e.g. `docker compose` command available)
* OpenAI API key with some available credit

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/LLM-Quality-Observer.git
cd LLM-Quality-Observer
```

### 2. Create local env file

```bash
cp configs/env/.env.local configs/env/.env.local.example  # optional backup
# edit configs/env/.env.local with your values
```

Make sure `LLM_API_KEY` and `OPENAI_MODEL_MAIN` are set.

### 3. Run with Docker Compose

```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

Services:

* Gateway API: `http://localhost:18000`
* Postgres: exposed inside Docker network as `postgres:5432`

---

## Using the Gateway API

### Health Check

```bash
curl http://localhost:18000/health
# -> { "status": "ok" }
```

### Interactive API docs (Swagger UI)

Open in browser:

```text
http://localhost:18000/docs
```

You can use `POST /chat` directly from Swagger.

### Chat Example

Request:

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what LLM-Quality-Observer is in one sentence.",
    "user_id": "test-user",
    "model_version": null
  }'
```

Example response:

```json
{
  "response": "LLM-Quality-Observer is a monitoring and evaluation framework that continuously assesses and tracks the quality of LLM outputs.",
  "model_version": "gpt-5-mini",
  "latency_ms": 4735.19
}
```

Behind the scenes, the request/response pair is also stored in `llm_logs` table in Postgres.

---

## Checking Logged Data (Postgres)

```bash
docker exec -it llm-postgres psql -U llm_user -d llm_quality

SELECT id, created_at, user_id,
       LEFT(prompt, 60)   AS prompt_snippet,
       LEFT(response, 60) AS response_snippet,
       model_version,
       latency_ms,
       status
FROM llm_logs
ORDER BY id DESC
LIMIT 10;
```

---

## Roadmap

Planned enhancements for future versions:

* **Evaluator Service**

  * Batch jobs to score LLM outputs using:

    * heuristics (e.g. length, keyword constraints)
    * LLM-as-a-judge prompts
    * human labels / RLHF-like feedback
  * Persist evaluation results in new tables (e.g. `llm_evaluations`)

* **Dashboard Service**

  * High-level quality metrics:

    * average score per model/version
    * latency distributions
    * error rates and failure patterns
  * Filters by:

    * time range, user, use case, model version

* **Alerting / Notifications**

  * Simple rules:

    * “Alert when average score drops below threshold”
    * “Alert when latency p95 > X ms”
  * Send alerts to Slack / email.

* **Cost Awareness**

  * Track token usage and cost per model/version
  * Combine with quality metrics for cost–quality tradeoff analysis.

---

## License

MIT (or your preferred license)

---

## Notes

This project is intended as a **learning and portfolio project** to demonstrate practical MLOps patterns for LLM applications:

* clean separation of services (gateway / evaluator / dashboard)
* environment-based configuration
* logging & observability for LLM responses
* room to extend into production-style MLOps workflows.
