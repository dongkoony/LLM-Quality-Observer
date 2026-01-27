# Architecture Design - v0.8.0: Authentication & User Management

> **Version**: v0.8.0
> 
> **Created**: 2026-01-27
> 
> **Status**: 설계 단계 (Design Phase)
> 
> **Theme**: 보안 강화 및 사용자 관리

---

## 목차

1. [개요](#개요)
2. [현재 문제점](#현재-문제점)
3. [설계 목표](#설계-목표)
4. [인증 아키텍처](#인증-아키텍처)
5. [데이터베이스 스키마](#데이터베이스-스키마)
6. [API 설계](#api-설계)
7. [보안 요구사항](#보안-요구사항)
8. [구현 계획](#구현-계획)

---

## 개요

v0.8.0은 **Authentication & User Management**를 도입하여 시스템 보안을 강화하고, 사용자별 리소스 격리 및 추적을 가능하게 합니다.

### 핵심 기능

1. **JWT 기반 인증**: 세션 없는 인증 시스템
2. **API Key 관리**: 프로그래밍 방식 인증
3. **RBAC**: Admin, Developer, Viewer 역할 기반 권한 관리
4. **Rate Limiting**: 사용자/IP별 요청 제한
5. **Audit Log**: 사용자 활동 추적

---

## 현재 문제점

### v0.7.0의 보안 취약점

```python
# 현재: 인증 없음, 누구나 접근 가능
@app.post("/chat")
def chat(request: ChatRequest):
    # user_id는 클라이언트가 임의로 설정
    # 검증 없음, 인가 없음, 추적 불가
    pass
```

**문제점**:
1. ❌ **인증 없음**: 누구나 API 호출 가능
2. ❌ **신원 확인 불가**: user_id를 클라이언트가 임의 설정
3. ❌ **권한 관리 없음**: 모든 사용자 동일 권한
4. ❌ **비용 격리 불가**: 사용자별 비용 제한 불가능
5. ❌ **추적 불가**: 누가 무엇을 했는지 추적 불가
6. ❌ **Rate limit 없음**: 무제한 요청 가능 (DoS 취약)

---

## 설계 목표

### 기능 목표

1. **강력한 인증**: JWT + API Key 이중 인증 방식
2. **세밀한 권한 관리**: RBAC 기반 3단계 권한
3. **비용 격리**: 사용자별 비용 추적 및 제한
4. **추적 가능성**: 모든 중요 작업에 대한 감사 로그
5. **보안 강화**: SQL Injection, XSS 방어

### 비기능 목표

1. **성능**: 인증 오버헤드 < 10ms
2. **확장성**: 10,000+ 동시 사용자 지원
3. **하위 호환성**: 기존 API 동작 유지 (인증 선택적 적용)
4. **관리 편의성**: 사용자 관리 UI 제공

---

## 인증 아키텍처

### 인증 방식 비교

| 방식 | 사용 사례 | 장점 | 단점 |
|------|----------|------|------|
| **JWT** | 웹 대시보드 | 상태 없음, 확장성 좋음 | 토큰 취소 어려움 |
| **API Key** | 프로그래밍 방식 | 간단, 영구 사용 가능 | 키 노출 시 위험 |
| **OAuth 2.0** | 소셜 로그인 | 사용자 편의성 | 복잡한 구현 |

### 선택: JWT + API Key 혼용

```mermaid
graph TB
    A[Client Request] --> B{Auth Type?}
    B -->|JWT Token| C[JWT Middleware]
    B -->|API Key| D[API Key Middleware]
    C --> E[Extract User from JWT]
    D --> F[Lookup User by API Key]
    E --> G[Inject User Context]
    F --> G
    G --> H[Route Handler]
```

### 인증 흐름

### 1. JWT 인증 (웹 대시보드)

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway API
    participant D as Database

    C->>G: POST /auth/login\n{email, password}
    G->>D: Query user
    D-->>G: User data
    G->>G: Verify password
    G-->>C: JWT token

    C->>G: GET /chat\nAuthorization: Bearer <token>
    G->>G: Verify JWT
    G->>G: Extract user_id
    G-->>C: Response
```

### 2. API Key 인증 (프로그래밍)

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway API
    participant D as Database

    C->>G: POST /chat\nX-API-Key: sk-proj-...
    G->>D: Lookup key
    D-->>G: User + metadata
    G->>G: Check rate limit
    G-->>C: Response
```

---

## 데이터베이스 스키마

### 1. users 테이블

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt
    full_name VARCHAR(128),

    -- Role-Based Access Control
    role VARCHAR(32) NOT NULL DEFAULT 'viewer',
    -- Roles: 'admin', 'developer', 'viewer'

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- Limits
    max_requests_per_hour INTEGER DEFAULT 1000,
    max_cost_per_month_usd DECIMAL(10, 2) DEFAULT 100.00,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

### 2. api_keys 테이블

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Key information
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA-256 hash
    key_prefix VARCHAR(16) NOT NULL,  -- "sk-proj-xxxx" for display
    name VARCHAR(128) NOT NULL,  -- User-defined name

    -- Permissions
    scopes TEXT[] DEFAULT ARRAY['chat:read', 'chat:write'],

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Rate limiting
    max_requests_per_hour INTEGER DEFAULT 1000,

    -- Usage tracking
    last_used_at TIMESTAMP,
    total_requests INTEGER DEFAULT 0,

    -- Expiration
    expires_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
```

### 3. audit_logs 테이블

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Who
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL,

    -- What
    action VARCHAR(64) NOT NULL,
    -- Actions: 'auth.login', 'auth.logout', 'chat.create',
    --          'api_key.create', 'api_key.revoke', 'user.update'

    resource_type VARCHAR(64),  -- 'chat', 'api_key', 'user'
    resource_id INTEGER,

    -- When & Where
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,

    -- Details
    status VARCHAR(32) DEFAULT 'success',  -- 'success', 'failure'
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

### 4. llm_logs 테이블 수정

```sql
-- v0.8.0: Add user_id foreign key
ALTER TABLE llm_logs
ADD COLUMN authenticated_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL;

-- user_id는 기존 유지 (하위 호환성)
-- authenticated_user_id는 인증된 사용자 ID
```

---

## API 설계

### Authentication Endpoints

#### 1. POST /auth/register

사용자 등록

**Request**:
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "role": "viewer",
  "created_at": "2026-01-27T10:00:00Z"
}
```

#### 2. POST /auth/login

로그인 (JWT 발급)

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "role": "viewer"
  }
}
```

#### 3. POST /auth/refresh

JWT 토큰 갱신

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. POST /auth/logout

로그아웃 (토큰 무효화)

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

### API Key Management

#### 1. GET /api-keys

사용자의 API Key 목록 조회

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "api_keys": [
    {
      "id": 1,
      "name": "Production Key",
      "key_prefix": "sk-proj-abc1",
      "scopes": ["chat:read", "chat:write"],
      "is_active": true,
      "created_at": "2026-01-27T10:00:00Z",
      "last_used_at": "2026-01-27T11:30:00Z",
      "total_requests": 1523
    }
  ]
}
```

#### 2. POST /api-keys

새 API Key 생성

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "name": "Development Key",
  "scopes": ["chat:read", "chat:write"],
  "expires_in_days": 90
}
```

**Response**:
```json
{
  "id": 2,
  "name": "Development Key",
  "api_key": "sk-proj-xyz789...",  // Only shown once!
  "key_prefix": "sk-proj-xyz7",
  "scopes": ["chat:read", "chat:write"],
  "expires_at": "2026-04-27T10:00:00Z",
  "created_at": "2026-01-27T10:00:00Z"
}
```

⚠️ **Warning**: API Key는 생성 시 한 번만 표시됩니다. 안전하게 저장하세요.

#### 3. DELETE /api-keys/{key_id}

API Key 폐기

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "API key revoked successfully"
}
```

### User Management

#### 1. GET /users/me

현재 사용자 정보 조회

**Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`

**Response**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "developer",
  "is_active": true,
  "max_requests_per_hour": 1000,
  "max_cost_per_month_usd": "100.00",
  "current_month_cost_usd": "23.45",
  "created_at": "2026-01-01T00:00:00Z",
  "last_login_at": "2026-01-27T10:00:00Z"
}
```

#### 2. PATCH /users/me

현재 사용자 정보 수정

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "full_name": "John Smith",
  "metadata": {
    "department": "Engineering"
  }
}
```

#### 3. PUT /users/me/password

비밀번호 변경

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

### Audit Logs

#### 1. GET /audit-logs

감사 로그 조회 (Admin only)

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `user_id`: 사용자 ID 필터
- `action`: 액션 필터
- `start_date`: 시작 날짜
- `end_date`: 종료 날짜
- `page`: 페이지 번호
- `page_size`: 페이지 크기

**Response**:
```json
{
  "logs": [
    {
      "id": 12345,
      "user_id": 1,
      "username": "johndoe",
      "action": "chat.create",
      "resource_type": "chat",
      "resource_id": 456,
      "status": "success",
      "ip_address": "192.168.1.1",
      "created_at": "2026-01-27T10:30:00Z"
    }
  ],
  "total": 1523,
  "page": 1,
  "page_size": 20
}
```

### Modified Existing Endpoints

#### POST /chat (v0.8.0+)

**Before v0.8.0**:
```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "user_id": "any-string"}'
```

**After v0.8.0** (인증 필수):
```bash
# Option 1: JWT
curl -X POST "http://localhost:18000/chat" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'

# Option 2: API Key
curl -X POST "http://localhost:18000/chat" \
  -H "X-API-Key: sk-proj-xyz789..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'
```

**Response** (동일, user_id 자동 설정):
```json
{
  "response": "Hello! How can I help?",
  "model_version": "gpt-5-mini",
  "latency_ms": 1234.5,
  "usage": {...},
  "cost": {...}
}
```

**Changes**:
- `user_id` 필드 제거 (JWT/API Key에서 자동 추출)
- `authenticated_user_id`로 DB 저장
- Rate limiting 자동 적용

---

## 보안 요구사항

### 1. 비밀번호 보안

```python
# bcrypt 사용 (cost factor: 12)
import bcrypt

password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(rounds=12)
)
```

**요구사항**:
- 최소 8자 이상
- 대문자, 소문자, 숫자, 특수문자 각 1개 이상
- 일반적인 비밀번호 금지 (dictionary attack 방지)

### 2. JWT 보안

```python
# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit random
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
```

**보안 조치**:
- Secret Key: 256-bit 랜덤 생성
- 토큰 만료: Access 1시간, Refresh 30일
- Refresh token rotation
- 토큰 블랙리스트 (Redis)

### 3. API Key 보안

```python
# API Key 생성
import secrets

# 32-byte random key
raw_key = secrets.token_urlsafe(32)
# Format: sk-proj-{random}
api_key = f"sk-proj-{raw_key}"

# DB에는 해시 저장
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
```

**보안 조치**:
- 평문 저장 금지 (SHA-256 해시)
- Prefix 사용 (`sk-proj-`)
- 생성 시 1회만 표시
- Expiration 설정 권장

### 4. Rate Limiting

```python
# Redis 기반 Rate Limiting
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/chat", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
def chat(...):
    pass
```

**제한**:
- Per User: 1000 req/hour (기본값)
- Per IP: 100 req/hour (미인증)
- Admin: 무제한

### 5. SQL Injection 방어

```python
# ✅ GOOD: Parameterized query
user = db.query(User).filter(User.email == email).first()

# ❌ BAD: String concatenation
user = db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

**조치**:
- SQLAlchemy ORM 사용
- Raw query 금지
- Input validation

### 6. XSS 방어

```python
# Response 헤더
app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy="default-src 'self'",
    x_content_type_options="nosniff",
    x_frame_options="DENY"
)
```

---

## 구현 계획

### Phase 1: 기본 인증 (Week 1)

**주요 작업**:
- [ ] Database schema 추가 (users, api_keys, audit_logs)
- [ ] Migration script 작성
- [ ] User model 구현
- [ ] Password hashing (bcrypt)
- [ ] JWT 토큰 생성/검증 로직
- [ ] `/auth/register` 엔드포인트
- [ ] `/auth/login` 엔드포인트
- [ ] 기본 테스트

**예상 시간**: 5일

### Phase 2: API Key & Middleware (Week 2)

**주요 작업**:
- [ ] API Key 생성/해시/검증 로직
- [ ] `/api-keys` CRUD 엔드포인트
- [ ] 인증 미들웨어 구현
  - JWT 검증 미들웨어
  - API Key 검증 미들웨어
- [ ] User context injection
- [ ] 기존 `/chat` 엔드포인트 수정
- [ ] 테스트

**예상 시간**: 5일

### Phase 3: RBAC & Rate Limiting (Week 3)

**주요 작업**:
- [ ] Role-based permissions 구현
- [ ] Permission decorator (`@require_role('admin')`)
- [ ] Redis 통합 (rate limiting)
- [ ] Rate limiter 미들웨어
- [ ] User별/IP별 제한 적용
- [ ] 테스트

**예상 시간**: 4일

### Phase 4: Audit Log & Security (Week 4)

**주요 작업**:
- [ ] Audit log 기록 로직
- [ ] `/audit-logs` 조회 엔드포인트
- [ ] SQL Injection 테스트
- [ ] XSS 방어 테스트
- [ ] HTTPS 설정 (프로덕션)
- [ ] Security headers
- [ ] 통합 테스트
- [ ] 문서화

**예상 시간**: 6일

---

## 기술 스택

### Backend

```toml
# pyproject.toml
dependencies = [
  # 기존
  "fastapi",
  "sqlalchemy>=2.0",
  "psycopg2-binary",

  # 새로 추가 (v0.8.0)
  "python-jose[cryptography]",  # JWT
  "passlib[bcrypt]",  # Password hashing
  "python-multipart",  # Form data
  "redis>=5.0.0",  # Rate limiting
  "fastapi-limiter",  # Rate limiting
]
```

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis (Rate Limiting)
REDIS_URL=redis://localhost:6379/0

# Security
ENABLE_AUTHENTICATION=true  # v0.8.0+
REQUIRE_AUTHENTICATION=true  # Enforce auth on all endpoints
```

---

## 하위 호환성

### 마이그레이션 전략

v0.7.0 → v0.8.0 전환 시 기존 사용자 영향 최소화

#### Option 1: Soft Launch (추천)

```python
# 인증 선택적 적용
ENABLE_AUTHENTICATION = os.getenv("ENABLE_AUTHENTICATION", "false") == "true"

@app.post("/chat")
def chat(request: ChatRequest, user: User = Depends(get_current_user_optional)):
    if ENABLE_AUTHENTICATION and not user:
        raise HTTPException(401, "Authentication required")

    # user가 있으면 authenticated_user_id 사용
    # 없으면 기존 user_id 사용 (하위 호환)
```

#### Option 2: Grace Period

1. **Week 1-2**: 인증 선택 (경고 메시지)
2. **Week 3-4**: 인증 필수 (예외 허용)
3. **Week 5+**: 완전 적용

---

## 테스트 계획

### 단위 테스트

```python
# tests/test_auth.py
def test_register_user():
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200

def test_login_success():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_jwt_authentication():
    token = get_test_token()
    response = client.get("/users/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
```

### 통합 테스트

```bash
# Integration test script
bash scripts/test-v0.8.0.sh
```

**테스트 항목**:
- [ ] 사용자 등록 → 로그인 → API 호출
- [ ] API Key 생성 → API 호출
- [ ] Rate limiting 동작 확인
- [ ] RBAC 권한 검증
- [ ] Audit log 기록 확인

---

## 다음 단계

1. ✅ 브랜치 생성 (`feat/authentication-v0.8.0`)
2. ⏳ 아키텍처 설계 문서 작성 (현재)
3. ⏳ Database schema 구현
4. ⏳ JWT 인증 구현
5. ⏳ API Key 관리 구현
6. ⏳ 미들웨어 및 RBAC
7. ⏳ 테스트 및 문서화

---

