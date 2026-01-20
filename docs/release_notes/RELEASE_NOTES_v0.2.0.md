# Release Notes - v0.2.0

**Release Date**: 2025
**Status**: Dashboard Release

---

## Overview

LLM-Quality-Observer v0.2.0 introduces a web-based dashboard for visualizing quality metrics and monitoring LLM performance. This release adds a new Dashboard service using Streamlit, enhances the evaluation logic with rule-based criteria, and improves API accessibility with CORS middleware.

---

## 🎯 What's New

### Dashboard Service (NEW)
- **Streamlit Web Interface**: Interactive dashboard for real-time monitoring
- **Quality Metrics Visualization**: View evaluation scores, trends, and distributions
- **Log Exploration**: Browse and filter LLM interaction logs
- **Performance Analytics**: Track latency, success rates, and model performance
- **FastAPI Backend**: Dashboard API endpoints for data retrieval
- **Port**: Accessible at http://localhost:8501

### Enhanced Evaluator Service
- **Rule-Based Evaluation**: Comprehensive rule-based scoring system
  - Response length validation
  - Keyword presence checking
  - Format compliance verification
  - Language quality assessment
- **Structured Evaluation Schema**: Improved evaluation data models
- **Better Error Handling**: Enhanced error tracking and logging

### Improved Gateway API
- **CORS Middleware**: Enable cross-origin requests from web dashboard
- **Dashboard API Endpoints**: New endpoints for serving dashboard data
- **Enhanced Logging**: More detailed request/response logging

---

## 🏗️ Updated Architecture

```
Client/Browser → Dashboard (port 8501)
                      ↓
                 Gateway API (port 18000) → OpenAI GPT
                      ↓
                 PostgreSQL (port 5432)
                      ↑
                 Evaluator (port 18001)
```

---

## 📦 New Technology Stack

### Dashboard Service
- **Framework**: Streamlit
- **Visualization**: Plotly, Pandas
- **ORM**: SQLAlchemy
- **Database Driver**: psycopg2-binary
- **Package Manager**: uv

---

## 🆕 New Features in Detail

### Dashboard Pages

#### Overview Page
- **Summary Statistics**: Total requests, average score, success rate
- **Recent Activity**: Latest LLM interactions
- **Quick Stats**: Key performance indicators

#### Quality Metrics Page
- **Score Distribution**: Histogram of evaluation scores
- **Score Trends**: Time series chart of quality over time
- **Score by Model**: Compare quality across different models

#### Latency Analysis Page
- **Latency Distribution**: p50, p95, p99 percentiles
- **Latency by Model**: Performance comparison
- **Response Time Trends**: Track performance over time

#### Logs Explorer Page
- **Filterable Table**: Search and filter logs
- **Column Selection**: Customize displayed columns
- **Detailed View**: Inspect individual interactions
- **Export Capability**: Download filtered results

### Rule-Based Evaluation Criteria

The evaluator now implements structured evaluation rules:

**Response Length Check**:
- Minimum length requirement
- Maximum length limit
- Optimal range scoring

**Content Quality**:
- Keyword presence validation
- Banned word detection
- Format compliance

**Scoring System**:
- Score range: 1-5
- Weighted criteria
- Automatic pass/fail determination

---

## 📖 New API Endpoints

### Gateway API

#### GET /api/logs
**Description**: Retrieve LLM logs with filtering

**Query Parameters**:
- `limit` (optional): Maximum number of logs to return
- `offset` (optional): Pagination offset
- `user_id` (optional): Filter by user ID
- `model_version` (optional): Filter by model

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "user_id": "user123",
      "prompt": "What is Python?",
      "response": "Python is...",
      "model_version": "gpt-3.5-turbo",
      "latency_ms": 1234,
      "status": "success"
    }
  ],
  "total": 100
}
```

#### GET /api/evaluations
**Description**: Retrieve evaluation results

**Query Parameters**:
- `limit` (optional): Maximum number of evaluations
- `min_score` (optional): Filter by minimum score
- `max_score` (optional): Filter by maximum score

**Response**:
```json
{
  "evaluations": [
    {
      "id": 1,
      "log_id": 1,
      "score_overall": 4.5,
      "comments": "Good response quality",
      "judge_model": "rule-based"
    }
  ],
  "total": 50
}
```

#### GET /api/stats
**Description**: Get summary statistics

**Response**:
```json
{
  "total_requests": 1000,
  "average_score": 4.2,
  "success_rate": 0.98,
  "average_latency_ms": 1500,
  "total_evaluations": 950
}
```

---

## 🔧 Configuration Updates

### New Environment Variables

```bash
# Dashboard Service (optional)
DASHBOARD_TITLE=LLM Quality Observer
DASHBOARD_REFRESH_INTERVAL=30

# CORS Settings (Gateway API)
CORS_ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
```

### Updated docker-compose.local.yml

```yaml
services:
  # ... existing services ...

  dashboard:
    build: ../../services/dashboard
    container_name: llm-dashboard
    depends_on:
      - postgres
    env_file:
      - ../../configs/env/.env.local
    environment:
      DATABASE_URL: postgresql://llm_user:llm_password@postgres:5432/llm_quality
    ports:
      - "8501:8501"
```

---

## 🚀 Getting Started with Dashboard

### Access the Dashboard

1. **Start all services**:
```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

2. **Open browser**:
```
http://localhost:8501
```

3. **Navigate pages**:
- Use sidebar to switch between Overview, Quality Metrics, Latency Analysis, and Logs

### Generate Sample Data

```bash
# Send multiple requests to populate dashboard
for i in {1..20}; do
  curl -X POST "http://localhost:18000/chat" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test prompt $i\", \"user_id\": \"user$i\"}"
done

# Trigger evaluations
curl -X POST "http://localhost:18001/evaluate-once?limit=20"

# Refresh dashboard to see data
```

---

## 📁 Updated Project Structure

```
LLM-Quality-Observer/
├── services/
│   ├── gateway-api/
│   │   └── app/
│   │       └── main.py          # Added CORS and dashboard endpoints
│   ├── evaluator/
│   │   └── app/
│   │       ├── main.py
│   │       ├── rules.py         # NEW: Rule-based evaluation logic
│   │       └── schemas.py       # NEW: Evaluation schemas
│   └── dashboard/               # NEW: Dashboard service
│       ├── app/
│       │   ├── main.py          # Streamlit application
│       │   ├── models.py        # Database models
│       │   ├── config.py        # Configuration
│       │   └── db.py            # Database connection
│       ├── Dockerfile
│       └── pyproject.toml
└── configs/
    └── env/
        └── .env.local.example   # Updated with CORS settings
```

---

## 🔄 Migration from v0.1.0

### Database Schema (No changes)
The database schema remains compatible with v0.1.0. No migration required.

### Configuration Changes
Add CORS settings to your `.env.local`:
```bash
CORS_ALLOWED_ORIGINS=http://localhost:8501
```

### Docker Compose
Update your docker-compose setup:
```bash
cd infra/docker
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up --build
```

---

## 🧪 Testing

### Test Dashboard Access
```bash
# Check dashboard is running
curl http://localhost:8501

# Should return Streamlit HTML
```

### Test CORS Functionality
```bash
# From browser console on http://localhost:8501
fetch('http://localhost:18000/api/stats')
  .then(r => r.json())
  .then(console.log)
```

### Test New API Endpoints
```bash
# Get logs
curl http://localhost:18000/api/logs?limit=10

# Get evaluations
curl http://localhost:18000/api/evaluations

# Get statistics
curl http://localhost:18000/api/stats
```

---

## 🐛 Bug Fixes

- Fixed README documentation links for consistency
- Improved error handling in evaluator service
- Enhanced database connection stability
- Fixed gitignore to properly exclude .env.local files

---

## 💡 Improvements

- **Better Code Organization**: Separated evaluation logic into dedicated modules
- **Configuration Management**: Added .env.local.example template
- **Documentation**: Updated README with dashboard features
- **Error Logging**: More comprehensive error tracking

---

## 🔒 Security Updates

- **CORS Configuration**: Properly configured CORS to only allow dashboard origin
- **Environment Variables**: Sensitive data moved to .env.local (gitignored)

---

## ⚠️ Known Limitations

- **Single Page App**: Dashboard does not support deep linking
- **No Authentication**: Dashboard and APIs are unauthenticated
- **Limited Caching**: Dashboard queries database on every refresh
- **No Real-time Updates**: Manual page refresh required to see new data
- **Rule-Based Only**: LLM-as-a-judge not yet implemented

---

## 🛣️ Roadmap to v0.3.0

- [ ] Implement LLM-as-a-judge evaluation
- [ ] Add multi-language support for dashboard
- [ ] Implement additional evaluation metrics
- [ ] Add real-time dashboard updates
- [ ] Improve dashboard performance with caching

---

## 📝 Technical Notes

### CORS Configuration
The Gateway API now includes CORS middleware to allow requests from the Streamlit dashboard:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rule-Based Evaluation Logic
Evaluations now follow structured rules defined in `services/evaluator/app/rules.py`:

```python
def evaluate_response_length(response: str) -> float:
    """Score based on response length."""
    length = len(response)
    if length < 50:
        return 1.0
    elif length < 200:
        return 3.0
    elif length < 1000:
        return 5.0
    else:
        return 4.0
```

### Streamlit Dashboard
The dashboard uses Streamlit's session state for maintaining filters and selections across reruns.

---

## 📚 Documentation Updates

- Updated README.md with dashboard setup instructions
- Added dashboard usage examples
- Documented new API endpoints
- Updated architecture diagrams

---

## 🙏 Acknowledgments

- Streamlit team for the excellent dashboard framework
- FastAPI for CORS middleware support
- Community feedback on initial v0.1.0 release

---

**Previous Release**: [v0.1.0](./RELEASE_NOTES_v0.1.0.md)
**Next Release**: v0.3.0 will introduce LLM-as-a-judge and multi-language support
