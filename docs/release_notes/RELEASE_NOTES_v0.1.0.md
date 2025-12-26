# Release Notes - v0.1.0

**Release Date**: 2025 (Initial Release)
**Status**: Foundation Release

---

## Overview

LLM-Quality-Observer v0.1.0 marks the initial release of the project, establishing the foundational architecture for monitoring and evaluating LLM response quality. This version implements the core microservices architecture with Gateway API and Evaluator services.

---

## 🎯 Key Features

### Gateway API Service
- **LLM Request Handling**: FastAPI-based service that receives chat requests and forwards them to OpenAI GPT models
- **Database Logging**: Automatic logging of all LLM interactions to PostgreSQL
- **RESTful API**:
  - `POST /chat`: Accept user prompts and return LLM responses
  - `GET /health`: Health check endpoint
- **OpenAI Integration**: Direct integration with OpenAI API for GPT model access
- **Request/Response Tracking**: Records prompt, response, model version, latency, and status for every interaction

### Evaluator Service
- **Evaluation Framework**: Service dedicated to evaluating logged LLM responses
- **Database Integration**: Reads logs from PostgreSQL and stores evaluation results
- **Basic Evaluation Logic**: Initial evaluation implementation
- **RESTful API**:
  - `GET /health`: Health check endpoint
  - `POST /evaluate-once`: Manual evaluation trigger endpoint

### Infrastructure
- **PostgreSQL Database**: Centralized data storage for logs and evaluations
  - `llm_logs` table: Stores all LLM interactions
  - `llm_evaluations` table: Stores evaluation results
- **Docker Compose**: Complete local development environment
- **Microservices Architecture**: Separation of concerns between gateway and evaluation

---

## 🏗️ Architecture

```
Client → Gateway API (port 18000) → OpenAI GPT
              ↓
         PostgreSQL (port 5432)
              ↑
         Evaluator (port 18001)
```

---

## 📦 Technology Stack

### Gateway API
- **Framework**: FastAPI
- **Server**: Uvicorn
- **ORM**: SQLAlchemy
- **Database Driver**: psycopg2-binary
- **LLM Client**: OpenAI Python SDK
- **Configuration**: pydantic-settings
- **Package Manager**: uv

### Evaluator
- **Framework**: FastAPI
- **Server**: Uvicorn
- **ORM**: SQLAlchemy
- **Database Driver**: psycopg2-binary
- **LLM Client**: OpenAI Python SDK (for future judge capability)
- **Package Manager**: uv

### Infrastructure
- **Database**: PostgreSQL 16
- **Containerization**: Docker, Docker Compose
- **Python Version**: 3.12

---

## 🗄️ Database Schema

### llm_logs Table
```sql
CREATE TABLE llm_logs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR,
    prompt TEXT,
    response TEXT,
    model_version VARCHAR,
    latency_ms INTEGER,
    status VARCHAR
);
```

### llm_evaluations Table
```sql
CREATE TABLE llm_evaluations (
    id SERIAL PRIMARY KEY,
    log_id INTEGER REFERENCES llm_logs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score_overall FLOAT,
    comments TEXT,
    judge_model VARCHAR
);
```

---

## 📖 API Documentation

### Gateway API (port 18000)

#### POST /chat
**Description**: Submit a prompt and receive LLM response

**Request**:
```json
{
  "prompt": "What is Python?",
  "user_id": "user123",
  "model_version": "gpt-3.5-turbo"
}
```

**Response**:
```json
{
  "id": 1,
  "prompt": "What is Python?",
  "response": "Python is a high-level programming language...",
  "model_version": "gpt-3.5-turbo",
  "latency_ms": 1234,
  "status": "success"
}
```

#### GET /health
**Description**: Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

### Evaluator (port 18001)

#### POST /evaluate-once
**Description**: Trigger manual evaluation of pending logs

**Query Parameters**:
- `limit` (optional): Number of logs to evaluate

**Response**:
```json
{
  "message": "Evaluation completed",
  "evaluated_count": 5
}
```

#### GET /health
**Description**: Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

---

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-username/LLM-Quality-Observer.git
cd LLM-Quality-Observer
```

2. **Set up environment variables**:
```bash
cp configs/env/.env.local.example configs/env/.env.local
# Edit .env.local and add your OpenAI API key
```

3. **Start services**:
```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

4. **Verify services**:
```bash
# Gateway API
curl http://localhost:18000/health

# Evaluator
curl http://localhost:18001/health
```

### Usage Example

**Send a chat request**:
```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain machine learning in simple terms",
    "user_id": "test-user",
    "model_version": "gpt-3.5-turbo"
  }'
```

**Trigger evaluation**:
```bash
curl -X POST "http://localhost:18001/evaluate-once?limit=10"
```

**Check database**:
```bash
docker exec -it llm-postgres psql -U llm_user -d llm_quality

# View logs
SELECT * FROM llm_logs ORDER BY created_at DESC LIMIT 5;

# View evaluations
SELECT * FROM llm_evaluations ORDER BY created_at DESC LIMIT 5;
```

---

## 📁 Project Structure

```
LLM-Quality-Observer/
├── services/
│   ├── gateway-api/
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI application
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   ├── schemas.py       # Pydantic schemas
│   │   │   ├── config.py        # Configuration
│   │   │   ├── db.py            # Database connection
│   │   │   └── llm_client.py    # OpenAI client
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── evaluator/
│       ├── app/
│       │   ├── main.py          # FastAPI application
│       │   ├── models.py        # SQLAlchemy models
│       │   ├── config.py        # Configuration
│       │   └── db.py            # Database connection
│       ├── Dockerfile
│       └── pyproject.toml
├── infra/
│   └── docker/
│       └── docker-compose.local.yml
├── configs/
│   └── env/
│       └── .env.local.example
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

**Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL_MAIN`: Default LLM model (e.g., gpt-3.5-turbo)

**Optional**:
- `LOG_LEVEL`: Logging level (default: INFO)
- `APP_ENV`: Application environment (default: local)

### Example .env.local
```bash
APP_ENV=local
LOG_LEVEL=INFO
OPENAI_MODEL_MAIN=gpt-3.5-turbo
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality
```

---

## 🧪 Testing

### Manual Testing

**Test Gateway API**:
```bash
# Health check
curl http://localhost:18000/health

# Chat request
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "user_id": "test"}'
```

**Test Evaluator**:
```bash
# Health check
curl http://localhost:18001/health

# Trigger evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=5"
```

---

## 🐛 Known Limitations

- **Manual Evaluation Only**: No automated scheduler for continuous evaluation
- **Basic Evaluation Logic**: Evaluation criteria not yet fully implemented
- **No Dashboard**: No web interface for viewing metrics and logs
- **No Notifications**: No alerting system for quality issues
- **Single Model Support**: Designed for OpenAI models only
- **No Metrics Export**: No Prometheus/Grafana integration

---

## 🛣️ Future Roadmap

- [ ] Implement comprehensive evaluation criteria (rule-based and LLM-as-a-judge)
- [ ] Add web dashboard for visualization
- [ ] Implement automated evaluation scheduler
- [ ] Add notification system (Slack, Discord, Email)
- [ ] Add Prometheus metrics and Grafana dashboards
- [ ] Support multiple LLM providers
- [ ] Add batch processing capabilities

---

## 📝 Technical Notes

### Database Connection Pooling
SQLAlchemy handles connection pooling automatically. Default pool size is 5 connections.

### Error Handling
Failed LLM requests are logged with `status="error"` and stored in the database for analysis.

### OpenAI API Usage
The gateway uses `client.chat.completions.create()` for standard chat completions. Response streaming is not implemented in v0.1.0.

### Docker Networking
All services communicate via Docker Compose default network. Service names (e.g., `postgres`, `gateway-api`) are used as hostnames.

---

## 🤝 Contributing

This is the initial release. Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

[Add your license information here]

---

## 👥 Authors

- Initial work - [Your Name]

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- OpenAI for the LLM API
- PostgreSQL for reliable data storage

---

**Next Release**: v0.2.0 will introduce web dashboard and enhanced evaluation capabilities.
