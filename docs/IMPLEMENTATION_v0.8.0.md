# Implementation Guide - v0.8.0: Authentication & User Management

> **Version**: v0.8.0
>
> **Last Updated**: 2026-02-02
>
> **Status**: Phase 1 완료, Phase 2-4 진행 예정

---

## 목차

1. [개요](#개요)
2. [Phase 1 구현 완료 (2026-02-02)](#phase-1-구현-완료)
3. [파일 구조](#파일-구조)
4. [API 엔드포인트](#api-엔드포인트)
5. [데이터베이스 스키마](#데이터베이스-스키마)
6. [테스트 방법](#테스트-방법)
7. [환경 설정](#환경-설정)
8. [다음 단계](#다음-단계)

---

## 개요

v0.8.0은 LLM Quality Observer에 인증 및 사용자 관리 기능을 추가하는 버전입니다.

### 주요 기능
- JWT 기반 인증 (웹 대시보드용)
- API Key 인증 (프로그래밍 방식)
- RBAC (Admin, Developer, Viewer)
- Rate Limiting (Redis 기반)
- Audit Log (사용자 활동 추적)

### 구현 단계
| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | 기본 인증 (Users, JWT, Register/Login) | ✅ 완료 |
| 2 | API Key & 미들웨어 | ⏳ 예정 |
| 3 | RBAC & Rate Limiting | ⏳ 예정 |
| 4 | Audit Log & 보안 강화 | ⏳ 예정 |

---

## Phase 1 구현 완료

### 완료 날짜
2026-02-02

### 구현 항목

#### 1. 데이터베이스 모델
- `User`: 사용자 정보, 역할, 비용 제한
- `APIKey`: API Key 해시, 스코프, 만료일
- `AuditLog`: 감사 로그 (누가/언제/무엇을)
- `LLMLog` 수정: `authenticated_user_id`, `api_key_id` 필드 추가

#### 2. 인증 기능
- 비밀번호 해싱 (bcrypt)
- JWT 토큰 생성/검증 (python-jose)
- API Key 생성/검증 (SHA-256 해시)
- 이중 인증 지원 (JWT 또는 API Key)

#### 3. API 엔드포인트
- `POST /auth/register`: 회원가입
- `POST /auth/login`: 로그인 (JWT 발급)
- `POST /auth/login/form`: OAuth2 호환 로그인
- `POST /auth/refresh`: 토큰 갱신
- `POST /auth/logout`: 로그아웃
- `GET /auth/me`: 현재 사용자 정보
- `PATCH /auth/me`: 사용자 정보 수정
- `PUT /auth/me/password`: 비밀번호 변경
- `GET /auth/api-keys`: API Key 목록
- `POST /auth/api-keys`: API Key 생성
- `DELETE /auth/api-keys/{key_id}`: API Key 폐기

#### 4. 감사 로그
모든 인증 관련 액션이 자동으로 `audit_logs` 테이블에 기록됨:
- `auth.register`: 회원가입
- `auth.login`: 로그인 (성공/실패)
- `auth.logout`: 로그아웃
- `user.update`: 사용자 정보 수정
- `user.password_change`: 비밀번호 변경
- `api_key.create`: API Key 생성
- `api_key.revoke`: API Key 폐기

---

## 파일 구조

### 새로 생성된 파일

```
services/gateway-api/app/auth/
├── __init__.py          # 모듈 초기화 및 exports
├── schemas.py           # Pydantic 스키마 (요청/응답)
├── utils.py             # 유틸리티 (해싱, JWT, 의존성)
└── router.py            # FastAPI 라우터 (엔드포인트)
```

### 수정된 파일

#### `services/gateway-api/pyproject.toml`
새 의존성 추가:
```toml
# Authentication (v0.8.0)
"python-jose[cryptography]>=3.3.0",
"passlib[bcrypt]>=1.7.4",
"bcrypt>=4.0.0,<5.0.0",  # Fix compatibility with passlib
"python-multipart>=0.0.6",
"email-validator>=2.0.0",
```

#### `services/gateway-api/app/config.py`
JWT 설정 추가:
```python
# JWT Authentication (v0.8.0)
jwt_secret_key: str = "change-this-secret-key-in-production"
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 60
jwt_refresh_token_expire_days: int = 30

# Authentication settings (v0.8.0)
enable_authentication: bool = False
require_authentication: bool = False
```

#### `services/gateway-api/app/models.py`
새 모델 추가:
- `User`: 사용자 테이블
- `APIKey`: API Key 테이블
- `AuditLog`: 감사 로그 테이블
- `LLMLog`: `authenticated_user_id`, `api_key_id` 필드 추가

#### `services/gateway-api/app/main.py`
Auth 라우터 등록:
```python
from .auth import auth_router
app.include_router(auth_router)
```

#### `configs/env/.env.local.example`
JWT 환경변수 추가:
```bash
# JWT Authentication (v0.8.0)
JWT_SECRET_KEY=change-this-to-a-secure-random-256-bit-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Authentication settings (v0.8.0)
ENABLE_AUTHENTICATION=false
REQUIRE_AUTHENTICATION=false
```

---

## API 엔드포인트

### 회원가입

```bash
curl -X POST http://localhost:18000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**비밀번호 요구사항**:
- 최소 8자 이상
- 대문자 1개 이상
- 소문자 1개 이상
- 숫자 1개 이상
- 특수문자 1개 이상

### 로그인

```bash
curl -X POST http://localhost:18000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**응답**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "role": "viewer"
  }
}
```

### JWT 인증 요청

```bash
curl http://localhost:18000/auth/me \
  -H 'Authorization: Bearer <access_token>'
```

### API Key 생성

```bash
curl -X POST http://localhost:18000/auth/api-keys \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Production Key",
    "scopes": ["chat:read", "chat:write"],
    "expires_in_days": 90
  }'
```

**응답** (API Key는 생성 시 1회만 표시):
```json
{
  "id": 1,
  "name": "Production Key",
  "api_key": "sk-proj-abc123...",
  "key_prefix": "sk-proj-abc1",
  "scopes": ["chat:read", "chat:write"],
  "expires_at": "2026-05-02T10:00:00Z"
}
```

### API Key 인증 요청

```bash
curl http://localhost:18000/auth/me \
  -H 'X-API-Key: sk-proj-abc123...'
```

---

## 데이터베이스 스키마

### users 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| email | VARCHAR(255) | 이메일 (unique) |
| username | VARCHAR(64) | 사용자명 (unique) |
| password_hash | VARCHAR(255) | bcrypt 해시 |
| full_name | VARCHAR(128) | 이름 |
| role | VARCHAR(32) | 역할 (admin/developer/viewer) |
| is_active | BOOLEAN | 활성 상태 |
| is_verified | BOOLEAN | 이메일 인증 여부 |
| max_requests_per_hour | INTEGER | 시간당 요청 제한 |
| max_cost_per_month_usd | DECIMAL(10,2) | 월 비용 제한 |
| created_at | TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | 수정일 |
| last_login_at | TIMESTAMP | 마지막 로그인 |
| metadata | JSONB | 추가 메타데이터 |

### api_keys 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | Primary Key |
| user_id | INTEGER | FK → users.id |
| key_hash | VARCHAR(255) | SHA-256 해시 (unique) |
| key_prefix | VARCHAR(16) | 표시용 prefix |
| name | VARCHAR(128) | 키 이름 |
| scopes | TEXT[] | 권한 스코프 |
| is_active | BOOLEAN | 활성 상태 |
| max_requests_per_hour | INTEGER | 시간당 요청 제한 |
| last_used_at | TIMESTAMP | 마지막 사용 |
| total_requests | INTEGER | 총 요청 수 |
| expires_at | TIMESTAMP | 만료일 |
| created_at | TIMESTAMP | 생성일 |
| revoked_at | TIMESTAMP | 폐기일 |

### audit_logs 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL | Primary Key |
| user_id | INTEGER | FK → users.id |
| api_key_id | INTEGER | FK → api_keys.id |
| action | VARCHAR(64) | 액션 유형 |
| resource_type | VARCHAR(64) | 리소스 유형 |
| resource_id | INTEGER | 리소스 ID |
| created_at | TIMESTAMP | 생성일 |
| ip_address | INET | 클라이언트 IP |
| user_agent | TEXT | User-Agent |
| status | VARCHAR(32) | 성공/실패 |
| error_message | TEXT | 에러 메시지 |
| metadata | JSONB | 추가 데이터 |

---

## 테스트 방법

### 1. 컨테이너 재빌드

```bash
cd infra/docker
docker compose -f docker-compose.local.yml up gateway-api --build -d
```

### 2. 헬스 체크

```bash
curl http://localhost:18000/health
```

### 3. 회원가입 테스트

```bash
curl -X POST http://localhost:18000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","username":"testuser","password":"SecurePass1!","full_name":"Test User"}'
```

### 4. 로그인 테스트

```bash
curl -X POST http://localhost:18000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"SecurePass1!"}'
```

### 5. DB 테이블 확인

```bash
docker exec llm-postgres psql -U llm_user -d llm_quality -c "\dt"
docker exec llm-postgres psql -U llm_user -d llm_quality -c "SELECT * FROM users;"
docker exec llm-postgres psql -U llm_user -d llm_quality -c "SELECT id, user_id, action, status FROM audit_logs;"
```

---

## 환경 설정

### 필수 환경 변수

```bash
# JWT (v0.8.0)
JWT_SECRET_KEY=<256-bit-random-secret>  # 프로덕션에서는 반드시 변경!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Authentication
ENABLE_AUTHENTICATION=true   # 인증 기능 활성화
REQUIRE_AUTHENTICATION=false # true면 모든 요청에 인증 필수
```

### JWT Secret Key 생성

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 다음 단계

### Phase 2: API Key & 미들웨어

- [ ] 인증 미들웨어 구현 (JWT/API Key 검증)
- [ ] User context injection
- [ ] `/chat` 엔드포인트에 인증 적용
- [ ] `authenticated_user_id` 자동 설정
- [ ] 하위 호환성 유지 (인증 선택적 적용)

### Phase 3: RBAC & Rate Limiting

- [ ] Redis 통합
- [ ] Role-based permission decorator
- [ ] Per-user rate limiting
- [ ] Per-IP rate limiting (미인증 요청)
- [ ] 비용 제한 적용

### Phase 4: Audit Log & 보안

- [ ] `/audit-logs` 조회 엔드포인트 (Admin only)
- [ ] SQL Injection 테스트
- [ ] XSS 방어 테스트
- [ ] Security headers 미들웨어
- [ ] 통합 테스트
- [ ] 문서화 완료

---

## 관련 문서

- [Architecture Design v0.8.0](./ARCHITECTURE_v0.8.0.md)
- [API Guide v0.6.0](./API_GUIDE_v0.6.0.md)
- [CLAUDE.md](../CLAUDE.md)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-02-02 | Phase 1 구현 완료 (기본 인증, JWT, API Key) |
