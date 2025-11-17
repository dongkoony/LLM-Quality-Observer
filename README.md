# LLM-Quality-Observer

[🇰🇷 KR](README.md) | [🇺🇸 EN](docs/README-main-us.md)

---


### 개요

**LLM-Quality-Observer** 는 대형 언어 모델(LLM)의 응답 품질을 **모니터링하고 평가**하기 위한 개인 MLOps 포트폴리오 프로젝트입니다.  
이 프로젝트의 목표는 다음과 같습니다.

- LLM 기반 **Gateway API** 구성
- 프롬프트 / 응답 / 지연 시간(latency) / 모델 버전 등을 **DB에 로깅**
- (향후) 평가 서비스(Evaluator)로 품질 점수 계산
- (향후) 대시보드에서 품질/지연/에러율 등 **지표 시각화**

> 현재 상태: **v1 — Gateway API + Postgres 로깅까지 동작**

---

### 아키텍처 개요

현재 v1 아키텍처:

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

### 기술 스택

* **언어**: Python 3.12
* **LLM Provider**: OpenAI GPT-5 mini (`responses` API 사용)
* **웹 프레임워크**: FastAPI
* **DB**: PostgreSQL 16
* **ORM**: SQLAlchemy
* **설정 관리**: Pydantic Settings
* **의존성 관리**: [`uv`](https://github.com/astral-sh/uv)
* **컨테이너**: Docker, Docker Compose

---

### 프로젝트 구조

대략적인 디렉토리 구조:

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
│       └── .env.local        # local 환경 변수 (git ignore 대상)
└── README.md
```

#### `services/gateway-api`

LLM 호출을 담당하는 **Gateway API 서비스**입니다.

* `/health` : 헬스 체크
* `/chat` : LLM 호출 + DB 로깅

주요 파일:

* `app/app/main.py`

  * FastAPI 엔트리 포인트
  * `/health`, `/chat` 엔드포인트 정의
  * 최초 실행 시 `llm_logs` 테이블 생성
  * LLM 응답을 DB에 저장하고 `ChatResponse`로 반환

* `app/app/config.py`

  * Pydantic `Settings` 정의
  * 환경 변수 로드:

    * `APP_ENV`
    * `DATABASE_URL`
    * `OPENAI_MODEL_MAIN`
    * `LLM_API_BASE_URL`
    * `LLM_API_KEY`
    * `LOG_LEVEL`

* `app/app/llm_client.py`

  * OpenAI Python SDK 래퍼
  * `OPENAI_MODEL_MAIN` 을 기본 모델로 사용
  * `client.responses.create(...)` 호출
  * `(response_text, latency_ms)` 튜플 반환

* `app/app/db.py`

  * SQLAlchemy 엔진 및 세션 생성
  * FastAPI `Depends` 로 사용하는 `get_db()` 제공

* `app/app/models.py`

  * SQLAlchemy ORM 모델: `LLMLog`
  * 컬럼:

    * `id`, `created_at`
    * `user_id`, `prompt`, `response`
    * `model_version`
    * `latency_ms`
    * `status` (예: `"success"`)

* `app/app/schemas.py`

  * Pydantic 스키마:

    * `ChatRequest` (요청)
    * `ChatResponse` (응답)

* `app/pyproject.toml`

  * gateway-api 서비스용 Python 패키지/의존성 정의
  * 로컬 및 Docker 빌드 시 `uv sync`에 사용

#### `services/evaluator` (향후 구현)

* `llm_logs` 테이블을 읽어 LLM 응답의 품질 점수를 계산하는 서비스
* 휴리스틱, LLM-as-a-judge, 사람 피드백 등 다양한 방식의 평가를 시도할 예정
* 현재는 `pyproject.toml`과 `Dockerfile`만 준비된 상태 (스켈레톤)

#### `services/dashboard` (향후 구현)

* 품질 지표, 지연 시간, 에러율 등을 시각화하는 대시보드 서비스
* Streamlit 또는 FastAPI 기반 UI를 고려
* 마찬가지로 `pyproject.toml`과 `Dockerfile`만 준비된 상태

#### `infra/docker`

* `docker-compose.local.yml`

  * 로컬 개발용 Docker Compose 스택:

    * `llm-postgres` (Postgres 16)
    * `llm-gateway-api` (FastAPI + OpenAI client)
    * `llm-evaluator` (placeholder)
    * `llm-dashboard` (placeholder)
  * 기본적으로 gateway-api를 `localhost:18000`에 바인딩

#### `configs/env`

* `.env.local`

  * docker-compose에서 참조하는 local 환경 변수 파일
  * 실제 경로/파일명은 `docker-compose.local.yml` 의 `env_file` 설정과 맞춰 사용

예시 `.env.local`:

```env
# Application
APP_ENV=local
LOG_LEVEL=DEBUG

# LLM
OPENAI_MODEL_MAIN=gpt-5-mini
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality
```

---

### 로컬 실행 방법 (Docker)

#### 1. 리포지토리 클론

```bash
git clone https://github.com/dongkoony/LLM-Quality-Observer.git
cd LLM-Quality-Observer
```

#### 2. `.env.local` 설정

```bash
cp configs/env/.env.local configs/env/.env.local.example  # 필요시 백업
# 이후 configs/env/.env.local 내용을 직접 수정
```

* `LLM_API_KEY` 에 OpenAI API 키 입력
* `OPENAI_MODEL_MAIN` 을 `gpt-5-mini` 로 설정 (또는 다른 모델)

#### 3. Docker Compose 실행

```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

* Gateway API: `http://localhost:18000`
* Postgres: 컨테이너 내부에서 `postgres:5432`

---

### Gateway API 사용법

#### Health 체크

```bash
curl http://localhost:18000/health
# -> { "status": "ok" }
```

#### Swagger UI

브라우저에서:

```text
http://localhost:18000/docs
```

에 접속 후 `POST /chat` 엔드포인트로 테스트 가능.

#### `/chat` 예시 요청

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what LLM-Quality-Observer is in one sentence.",
    "user_id": "test-user",
    "model_version": null
  }'
```

예시 응답:

```json
{
  "response": "LLM-Quality-Observer is a monitoring and evaluation framework that continuously assesses and tracks the quality of large language model outputs.",
  "model_version": "gpt-5-mini",
  "latency_ms": 4735.19
}
```

이 호출 시:

* OpenAI GPT-5 mini가 실제로 호출되고
* 응답과 지연 시간이 계산되며
* `llm_logs` 테이블에 로그가 저장됨

---

### Postgres에서 로그 확인

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

### 로드맵 (Roadmap)

향후 계획:

* **Evaluator Service**

  * `llm_logs` 기반 품질 점수 계산
  * 규칙/휴리스틱 기반 평가
  * LLM-as-a-judge 프롬프트 기반 평가
  * 사람 피드백(RLHF 스타일) 저장 및 활용

* **Dashboard Service**

  * 모델/버전별 평균 점수
  * 지연 시간 분포
  * 에러율, 실패 패턴
  * 기간 / 사용자 / 모델 버전 / 태그별 필터링

* **Alerting / 알림**

  * 점수가 특정 임계값 이하로 떨어질 때 알림
  * p95 latency 가 기준치를 넘을 때 알림
  * Slack / 이메일 연동

* **Cost Awareness**

  * 모델/버전별 토큰 사용량 및 비용 추적
  * 품질 점수와 비용을 함께 보며 cost–quality 트레이드오프 분석

---