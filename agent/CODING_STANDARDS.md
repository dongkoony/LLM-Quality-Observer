# Coding Standards & Conventions

> **AI Agent Guide**: 이 문서는 LLM Quality Observer 프로젝트의 코딩 표준을 정의합니다.

---

## 📋 Table of Contents

1. [General Principles](#general-principles)
2. [Python Standards](#python-standards)
3. [TypeScript/Next.js Standards](#typescriptnextjs-standards)
4. [API Design](#api-design)
5. [Database](#database)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Git Conventions](#git-conventions)
9. [Security](#security)

---

## General Principles

### 1. Code Quality

- ✅ **Readability over cleverness**: 명확한 코드 > 짧은 코드
- ✅ **Consistency**: 기존 패턴 유지
- ✅ **Simplicity**: KISS (Keep It Simple, Stupid)
- ✅ **DRY**: Don't Repeat Yourself
- ❌ **Premature optimization**: 필요하기 전까지 최적화하지 않기

### 2. IMPORTANT: Over-Engineering 금지

**절대 하지 말 것:**
- ❌ 요청하지 않은 기능 추가
- ❌ 요청하지 않은 리팩토링
- ❌ 요청하지 않은 "개선"
- ❌ 불필요한 추상화
- ❌ 미래를 위한 과도한 설계
- ❌ 변경하지 않은 코드에 주석/docstring 추가
- ❌ 사용하지 않는 코드에 대한 하위 호환성 유지

**올바른 접근:**
- ✅ 요청된 작업만 정확히 수행
- ✅ 최소한의 변경으로 목적 달성
- ✅ 3줄의 비슷한 코드 < 불필요한 추상화
- ✅ 현재 요구사항에만 집중

**예시:**

```python
# ❌ 나쁜 예 (over-engineering)
# 버그 수정 요청인데 전체 구조를 리팩토링
def process_data(data):
    # 새로운 validation layer 추가
    # 새로운 error handling class 생성
    # 새로운 logging framework 도입
    # ...

# ✅ 좋은 예 (minimal change)
def process_data(data):
    # 요청된 버그만 수정
    if data is None:  # 이 한 줄만 추가
        return None
    return data.process()
```

### 3. Error Handling Philosophy

**내부 코드는 신뢰하라:**
- ❌ 내부 함수 호출에 try-catch 추가하지 않기
- ❌ "혹시 몰라서" 하는 검증 추가하지 않기
- ✅ 시스템 경계(user input, external API)에서만 검증
- ✅ 프레임워크가 보장하는 것은 다시 검증하지 않기

### 4. Backwards Compatibility

- ❌ 사용하지 않는 변수를 `_var`로 rename하지 않기
- ❌ 삭제된 함수를 re-export하지 않기
- ❌ `# removed` 주석 추가하지 않기
- ✅ 사용하지 않으면 완전히 삭제

---

## Python Standards

### File Organization

```python
# services/gateway-api/app/main.py 구조 예시

"""
Module docstring (선택적 - 복잡한 모듈만)
"""

# 1. Standard library imports
import os
from typing import Optional

# 2. Third-party imports
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

# 3. Local imports
from .config import settings
from .models import LLMLog
from .schemas import ChatRequest, ChatResponse
from .db import get_db

# 4. Constants
DEFAULT_MODEL = "gpt-5-mini"

# 5. Application setup
app = FastAPI(title="Gateway API")

# 6. Functions/Classes
async def process_chat(request: ChatRequest) -> ChatResponse:
    """간단한 docstring (1줄로 충분)"""
    # Implementation
    pass

# 7. Routes
@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """엔드포인트 설명"""
    return await process_chat(request)
```

### Type Hints

**필수 사항:**

```python
# ✅ 좋은 예
def calculate_score(
    prompt: str,
    response: str,
    model: str = "gpt-4o-mini"
) -> float:
    """Calculate quality score."""
    return 3.5

# ✅ 좋은 예 - Optional 사용
from typing import Optional

def get_user(user_id: str) -> Optional[dict]:
    """Return user or None."""
    return None

# ❌ 나쁜 예 - 타입 힌트 없음
def calculate_score(prompt, response, model="gpt-4o-mini"):
    return 3.5
```

### Naming Conventions

```python
# 변수, 함수: snake_case
user_id = "test-user"
def get_user_data():
    pass

# 클래스: PascalCase
class LLMEvaluator:
    pass

# 상수: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# Private: _leading_underscore (진짜 private만)
def _internal_helper():
    pass

# 모듈/패키지: lowercase
# services/gateway_api/app/llm_client.py
```

### Pydantic Models (FastAPI)

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Chat request schema."""
    prompt: str = Field(..., min_length=1, description="User prompt")
    user_id: str = Field(..., description="User identifier")
    model_version: Optional[str] = Field(None, description="LLM model to use")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is AI?",
                "user_id": "user-123",
                "model_version": "gpt-5-mini"
            }
        }
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from .db import Base

class LLMLog(Base):
    """LLM request/response log."""
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(255), index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    model_version = Column(String(50))
    latency_ms = Column(Float)
    status = Column(String(20), default="success")
```

### Error Handling

```python
# ✅ 시스템 경계에서만 검증
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # External API call - 여기서 검증 필요
        response = await openai_client.create(...)
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail="LLM service unavailable")

    # 내부 함수는 신뢰
    save_log(db, request, response)  # try-catch 불필요

# ❌ 내부 함수에 불필요한 검증
def save_log(db, request, response):
    # 이미 Pydantic이 검증했으므로 다시 검증 불필요
    if not request:  # ❌ 이런 거 하지 말기
        raise ValueError("Request is required")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels:
logger.debug("Detailed information")      # 개발 중 디버깅
logger.info("General information")        # 일반 정보
logger.warning("Warning message")         # 주의 필요
logger.error("Error occurred")            # 에러 (복구 가능)
logger.critical("Critical failure")       # 치명적 에러

# ✅ 좋은 로깅
logger.info(f"Processing chat for user {user_id}")
logger.error(f"Failed to call LLM: {error_msg}")

# ❌ 나쁜 로깅
print("Debug info")  # print 사용 금지
logger.info("test")  # 의미 없는 메시지
```

---

## TypeScript/Next.js Standards

### File Organization

```typescript
// services/web/dashboard/app/dashboard/page.tsx

'use client'  // Client Component인 경우

// 1. React/Next.js imports
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// 2. Third-party imports
import { Card } from '@/components/ui/card'

// 3. Local imports
import { fetchAnalytics } from '@/lib/api'
import { useTranslations } from '@/lib/use-translations'

// 4. Types
interface DashboardProps {
  initialData?: Data
}

// 5. Component
export default function DashboardPage({ initialData }: DashboardProps) {
  // Implementation
}
```

### Naming Conventions

```typescript
// 컴포넌트: PascalCase
function DashboardPage() {}
function UserCard() {}

// 함수, 변수: camelCase
const userData = {}
function fetchUserData() {}

// 상수: UPPER_SNAKE_CASE
const MAX_ITEMS = 100
const API_BASE_URL = "http://localhost:18000"

// 타입/인터페이스: PascalCase
interface User {}
type UserData = {}

// 파일명: kebab-case
// dashboard-page.tsx
// user-card.tsx
```

### Component Structure

```typescript
'use client'

import { useState } from 'react'

interface Props {
  userId: string
  initialScore?: number
}

export default function QualityCard({ userId, initialScore = 0 }: Props) {
  // 1. Hooks
  const [score, setScore] = useState(initialScore)
  const t = useTranslations()

  // 2. Effects
  useEffect(() => {
    // Fetch data
  }, [userId])

  // 3. Handlers
  const handleRefresh = async () => {
    // Handle refresh
  }

  // 4. Render
  return (
    <div className="p-4">
      <h2>{t('quality.score')}</h2>
      <p>{score}</p>
      <button onClick={handleRefresh}>
        {t('common.refresh')}
      </button>
    </div>
  )
}
```

### API Calls

```typescript
// lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:18000'

export async function fetchAnalyticsTrends(hours: number = 24) {
  const response = await fetch(
    `${API_BASE_URL}/analytics/trends?hours=${hours}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store', // Next.js specific
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to fetch trends: ${response.statusText}`)
  }

  return response.json()
}
```

### Tailwind CSS

```typescript
// ✅ 좋은 예 - Tailwind utility classes
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
  <h2 className="text-xl font-bold text-gray-900">Title</h2>
  <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
    Action
  </button>
</div>

// ❌ 나쁜 예 - Inline styles
<div style={{ display: 'flex', padding: '16px' }}>
  ...
</div>
```

---

## API Design

### RESTful Conventions

```python
# ✅ 좋은 예
GET    /analytics/trends              # 목록 조회
GET    /analytics/trends?hours=24     # 필터링
POST   /chat                          # 생성
GET    /alerts/history                # 이력 조회
POST   /evaluate-once                 # 액션 실행

# ❌ 나쁜 예
GET    /getTrends                     # 동사 사용 금지
POST   /analytics/trends/get          # POST for GET
GET    /do-evaluation                 # 동사 사용
```

### Request/Response Format

```python
# Request
class ChatRequest(BaseModel):
    prompt: str
    user_id: str
    model_version: Optional[str] = None

# Response - 성공
class ChatResponse(BaseModel):
    id: int
    response: str
    model_version: str
    latency_ms: float
    created_at: str

# Response - 에러
{
    "detail": "Error message"  # FastAPI standard
}
```

### Pagination

```python
# Query parameters
page: int = Query(1, ge=1)
page_size: int = Query(20, ge=1, le=100)

# Response
class PaginatedResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    page_size: int
    total_pages: int
```

---

## Database

### Query Patterns

```python
# ✅ 좋은 예 - Session management
from sqlalchemy.orm import Session

def get_recent_logs(db: Session, limit: int = 10):
    return db.query(LLMLog)\
        .filter(LLMLog.status == "success")\
        .order_by(LLMLog.created_at.desc())\
        .limit(limit)\
        .all()

# FastAPI dependency
from fastapi import Depends
from .db import get_db

@app.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = get_recent_logs(db)
    return logs
```

### Migrations (수동 관리)

현재는 자동 migration 없음. 스키마 변경 시:

1. `services/*/app/models.py` 수정
2. PostgreSQL에서 수동으로 ALTER TABLE 실행
3. 문서화

---

## Testing

### Test Structure

```python
# services/gateway-api/tests/test_health.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_endpoint_success():
    """Test successful chat request."""
    request_data = {
        "prompt": "Test prompt",
        "user_id": "test-user"
    }
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    assert "response" in response.json()
```

### Test Coverage

- ✅ Health endpoints
- ✅ Happy path
- ✅ Error cases (400, 404, 500)
- ⚠️ Edge cases (선택적)
- ❌ 100% coverage 강제하지 않음

---

## Documentation

### Code Comments

```python
# ✅ 좋은 주석 - 왜(why)를 설명
# Use response.create() instead of chat.completions.create()
# because GPT-5 mini requires the new API
response = client.responses.create(...)

# ✅ 좋은 주석 - 복잡한 로직 설명
# Calculate p95 latency only if we have at least 20 samples
# to ensure statistical significance
if len(latencies) >= 20:
    p95 = statistics.quantiles(latencies, n=20)[18]

# ❌ 나쁜 주석 - 무엇(what)을 반복
# Get user by ID
user = get_user(user_id)

# ❌ 나쁜 주석 - 불필요한 설명
x = x + 1  # Increment x
```

### Docstrings

```python
# ✅ 간단한 함수 - 1줄로 충분
def calculate_score(text: str) -> float:
    """Calculate quality score from text."""
    return len(text) / 100

# ✅ 복잡한 함수 - 상세 설명
def evaluate_batch(
    db: Session,
    limit: int = 10,
    judge_type: str = "rule"
) -> dict:
    """
    Evaluate a batch of unevaluated logs.

    Args:
        db: Database session
        limit: Maximum number of logs to evaluate
        judge_type: Type of judge ('rule', 'llm', or 'both')

    Returns:
        dict with 'evaluated' count and 'judge_model' name

    Note:
        Only processes logs with status='success'
    """
    # Implementation
```

### README Files

각 서비스는 간단한 README 포함:

```markdown
# Gateway API

LLM request gateway with automatic logging.

## Endpoints

- `POST /chat` - Process chat request
- `GET /health` - Health check

## Running

```bash
uv sync
uv run uvicorn app.main:app --reload
```
```

---

## Git Conventions

### Branch Naming

```bash
feat/feature-name       # 새 기능
fix/bug-description     # 버그 수정
docs/doc-update         # 문서 업데이트
refactor/module-name    # 리팩토링
test/test-addition      # 테스트 추가
```

### Commit Messages

```bash
# Format: <type>: <subject>

# Types:
feat: add new analytics endpoint
fix: correct evaluation score calculation
docs: update API guide for v0.6.0
refactor: simplify alert routing logic
test: add tests for /analytics/trends
chore: update dependencies

# ✅ 좋은 예
feat: add /analytics/compare-models endpoint
fix: handle null scores in trend calculation
docs: add testing guide for v0.6.0

# ❌ 나쁜 예
update files
fix bug
WIP
test
```

### Pull Requests

**제목:**
```
feat: Add advanced analytics API endpoints
```

**설명:**
```markdown
## 변경 사항
- `/analytics/trends` 엔드포인트 추가
- `/analytics/compare-models` 엔드포인트 추가
- `/alerts/history` 엔드포인트 추가

## 테스트
- [x] 수동 테스트 완료
- [x] API 문서 업데이트

## 관련 이슈
Closes #123
```

---

## Security

### Secrets Management

```python
# ✅ 환경 변수 사용
from .config import settings

api_key = settings.LLM_API_KEY

# ❌ 하드코딩 절대 금지
api_key = "sk-1234567890"  # NEVER!
```

### Input Validation

```python
# ✅ Pydantic으로 검증
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")

# ✅ SQL Injection 방지 - SQLAlchemy ORM 사용
logs = db.query(LLMLog).filter(LLMLog.user_id == user_id).all()

# ❌ Raw SQL 지양
db.execute(f"SELECT * FROM logs WHERE user_id = '{user_id}'")
```

### CORS (Next.js)

```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
    ]
  },
}
```

---

## 🚫 Anti-Patterns to Avoid

### 1. God Objects
```python
# ❌ 나쁜 예
class SuperService:
    def process_chat(self): ...
    def evaluate(self): ...
    def send_notification(self): ...
    def generate_report(self): ...

# ✅ 좋은 예 - 단일 책임
class ChatService:
    def process(self): ...

class EvaluationService:
    def evaluate(self): ...
```

### 2. Magic Numbers
```python
# ❌ 나쁜 예
if score < 3:
    send_alert()

# ✅ 좋은 예
LOW_QUALITY_THRESHOLD = 3.0

if score < LOW_QUALITY_THRESHOLD:
    send_alert()
```

### 3. Mutable Defaults
```python
# ❌ 나쁜 예
def process_items(items=[]):
    items.append("new")
    return items

# ✅ 좋은 예
def process_items(items=None):
    if items is None:
        items = []
    items.append("new")
    return items
```

---

## 📊 Code Review Checklist

- [ ] 타입 힌트 추가되었는가?
- [ ] 에러 핸들링이 적절한가?
- [ ] 로깅이 추가되었는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 테스트가 작성되었는가?
- [ ] 보안 이슈가 없는가?
- [ ] 성능 문제가 없는가?
- [ ] 기존 패턴을 따르는가?
- [ ] Over-engineering 하지 않았는가?

---

**Remember**: 좋은 코드는 똑똑해 보이는 코드가 아니라, 6개월 후에도 이해할 수 있는 코드입니다.
