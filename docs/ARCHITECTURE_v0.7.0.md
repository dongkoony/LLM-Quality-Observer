# LLM Quality Observer v0.7.0 - Architecture Design

> **Version**: v0.7.0
> **Theme**: Cost Tracking & Multi-Model Support
> **Status**: 설계 단계 (Design Phase)
> **Last Updated**: 2026-01-20

---

## 📋 목차

1. [개요](#개요)
2. [OpenAI API Token Usage 조사 결과](#openai-api-token-usage-조사-결과)
3. [데이터베이스 스키마 설계](#데이터베이스-스키마-설계)
4. [비용 계산 로직](#비용-계산-로직)
5. [다중 모델 통합 전략](#다중-모델-통합-전략)
6. [API 엔드포인트 설계](#api-엔드포인트-설계)
7. [Prometheus 메트릭 설계](#prometheus-메트릭-설계)
8. [마이그레이션 계획](#마이그레이션-계획)
9. [구현 우선순위](#구현-우선순위)

---

## 개요

v0.7.0은 **비용 추적(Cost Tracking)**과 **다중 모델 지원**을 핵심 기능으로 추가합니다.

### 목표

1. **토큰 사용량 기록**: 모든 LLM 요청의 입력/출력 토큰 수 저장
2. **실시간 비용 계산**: 모델별 단가 기반 비용 자동 계산
3. **비용 분석**: 사용자별/모델별/시간별 비용 집계 및 시각화
4. **다중 모델 지원**: LiteLLM 통합으로 100+ 모델 지원
5. **비용 최적화**: 모델 성능 대비 비용 효율성 분석

---

## OpenAI API Token Usage 조사 결과

### API 응답 구조

OpenAI Responses API는 다음과 같은 토큰 정보를 제공합니다:

```python
response = client.responses.create(
    model="gpt-5-mini",
    input="Who is the father of Python?"
)

# 응답 구조:
{
    "output_text": "...",
    "usage": {
        "input_tokens": 13,
        "cached_tokens": 0,
        "output_tokens": 216,
        "reasoning_tokens": 192,  # GPT-5 추론 모델 전용
        "total_tokens": 229
    }
}
```

### 토큰 타입

| 토큰 타입 | 설명 | 요금 산정 |
|---------|------|----------|
| `input_tokens` | 프롬프트 입력 토큰 | ✅ 입력 단가 적용 |
| `cached_tokens` | 캐시된 입력 토큰 | ✅ 할인 또는 무료 (모델별 상이) |
| `output_tokens` | 응답 생성 토큰 | ✅ 출력 단가 적용 |
| `reasoning_tokens` | 추론 단계 토큰 (GPT-5 계열) | ✅ 출력 토큰에 포함 |
| `total_tokens` | 전체 토큰 합계 | ℹ️ 참고용 |

### 2026년 LLM 가격 정보

| 모델 | 입력 가격 ($/1M tokens) | 출력 가격 ($/1M tokens) | Context Window |
|-----|------------------------|------------------------|----------------|
| **GPT-5** | $1.25 | $10.00 | 400K |
| **GPT-5 mini** | $0.25 | $2.00 | 400K |
| **GPT-5 nano** | $0.05 | $0.40 | 200K |
| **GPT-4o** | $2.50 | $10.00 | 128K |
| **GPT-4o-mini** | $0.15 | $0.60 | 128K |
| **Claude Sonnet 4** | $0.30 | $1.50 | 200K |
| **Claude Haiku 4** | $0.25 | $1.25 | 200K |

**Sources**:
- [OpenAI Pricing 2026](https://platform.openai.com/docs/pricing)
- [LLM API Pricing Comparison 2025-2026](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025)
- [GPT-5 API Pricing 2026](https://pricepertoken.com/pricing-page/model/openai-gpt-5)

---

## 데이터베이스 스키마 설계

### 1. 기존 테이블 수정: `llm_logs`

```sql
ALTER TABLE llm_logs
ADD COLUMN input_tokens INTEGER,
ADD COLUMN output_tokens INTEGER,
ADD COLUMN total_tokens INTEGER,
ADD COLUMN cached_tokens INTEGER DEFAULT 0,
ADD COLUMN reasoning_tokens INTEGER DEFAULT 0,
ADD COLUMN cost_input_usd DECIMAL(10, 6),
ADD COLUMN cost_output_usd DECIMAL(10, 6),
ADD COLUMN cost_total_usd DECIMAL(10, 6);
```

**수정된 스키마 (전체)**:

```sql
CREATE TABLE llm_logs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 요청 정보
    user_id VARCHAR(128),
    prompt TEXT NOT NULL,
    response TEXT,

    -- 모델 정보
    model_version VARCHAR(64),

    -- 성능 메트릭
    latency_ms FLOAT,
    status VARCHAR(32) DEFAULT 'success',

    -- 토큰 사용량 (NEW in v0.7.0)
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cached_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,

    -- 비용 정보 (NEW in v0.7.0)
    cost_input_usd DECIMAL(10, 6),
    cost_output_usd DECIMAL(10, 6),
    cost_total_usd DECIMAL(10, 6)
);

CREATE INDEX idx_llm_logs_user_id ON llm_logs(user_id);
CREATE INDEX idx_llm_logs_model_version ON llm_logs(model_version);
CREATE INDEX idx_llm_logs_created_at ON llm_logs(created_at DESC);
CREATE INDEX idx_llm_logs_cost ON llm_logs(cost_total_usd DESC);
```

### 2. 새 테이블: `llm_model_pricing`

모델별 토큰 단가를 관리하는 설정 테이블입니다.

```sql
CREATE TABLE llm_model_pricing (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(128) UNIQUE NOT NULL,
    provider VARCHAR(64) NOT NULL,  -- 'openai', 'anthropic', 'google', etc.

    -- 가격 정보 (USD per 1M tokens)
    price_input_per_1m DECIMAL(10, 4) NOT NULL,
    price_output_per_1m DECIMAL(10, 4) NOT NULL,
    price_cached_per_1m DECIMAL(10, 4) DEFAULT 0,  -- 캐시된 토큰 할인가

    -- 모델 스펙
    context_window INTEGER,
    max_output_tokens INTEGER,

    -- 메타데이터
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 설명 및 태그
    description TEXT,
    tags VARCHAR(64)[]  -- 예: ['chat', 'reasoning', 'fast']
);

-- 초기 데이터
INSERT INTO llm_model_pricing (model_name, provider, price_input_per_1m, price_output_per_1m, context_window) VALUES
('gpt-5', 'openai', 1.25, 10.00, 400000),
('gpt-5-mini', 'openai', 0.25, 2.00, 400000),
('gpt-5-nano', 'openai', 0.05, 0.40, 200000),
('gpt-4o', 'openai', 2.50, 10.00, 128000),
('gpt-4o-mini', 'openai', 0.15, 0.60, 128000),
('claude-sonnet-4', 'anthropic', 0.30, 1.50, 200000),
('claude-haiku-4', 'anthropic', 0.25, 1.25, 200000);
```

### 3. 새 테이블: `llm_cost_summary` (선택적)

일별/사용자별 비용 집계를 위한 Materialized View 또는 집계 테이블입니다.

```sql
CREATE TABLE llm_cost_summary (
    id SERIAL PRIMARY KEY,

    -- 집계 키
    summary_date DATE NOT NULL,
    user_id VARCHAR(128),
    model_version VARCHAR(64),

    -- 집계 메트릭
    total_requests INTEGER DEFAULT 0,
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(10, 2) DEFAULT 0,

    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(summary_date, user_id, model_version)
);

CREATE INDEX idx_cost_summary_date ON llm_cost_summary(summary_date DESC);
CREATE INDEX idx_cost_summary_user ON llm_cost_summary(user_id);
```

**Note**: 실시간 집계가 가능하다면 이 테이블은 v0.8.0 이후로 이연 가능합니다.

---

## 비용 계산 로직

### 계산 공식

```python
def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int,
    model_pricing: ModelPricing
) -> tuple[float, float, float]:
    """
    비용 계산 함수

    Returns:
        (cost_input, cost_output, cost_total) in USD
    """
    # 입력 비용 (캐시된 토큰 할인 적용)
    uncached_input_tokens = input_tokens - cached_tokens
    cost_input = (
        (uncached_input_tokens * model_pricing.price_input_per_1m / 1_000_000) +
        (cached_tokens * model_pricing.price_cached_per_1m / 1_000_000)
    )

    # 출력 비용 (reasoning tokens 포함)
    cost_output = output_tokens * model_pricing.price_output_per_1m / 1_000_000

    # 총 비용
    cost_total = cost_input + cost_output

    return (cost_input, cost_output, cost_total)
```

### 구현 위치

**Gateway API** (`services/gateway-api/app/llm_client.py`):

```python
def call_llm(prompt: str, model_version: str | None = None) -> dict:
    """
    LLM 호출 및 토큰/비용 계산

    Returns:
        {
            "response": str,
            "latency_ms": float,
            "usage": {
                "input_tokens": int,
                "output_tokens": int,
                "total_tokens": int,
                "cached_tokens": int,
                "reasoning_tokens": int
            },
            "cost": {
                "input_usd": float,
                "output_usd": float,
                "total_usd": float
            }
        }
    """
    model = _resolve_model(model_version)

    start = time.perf_counter()

    # OpenAI API 호출
    response = client.responses.create(
        model=model,
        input=prompt,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    # Usage 정보 추출
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "total_tokens": response.usage.total_tokens,
        "cached_tokens": getattr(response.usage, "cached_tokens", 0),
        "reasoning_tokens": getattr(response.usage, "reasoning_tokens", 0),
    }

    # 비용 계산
    pricing = get_model_pricing(model)  # DB에서 가격 정보 조회
    cost = calculate_cost(
        usage["input_tokens"],
        usage["output_tokens"],
        usage["cached_tokens"],
        pricing
    )

    return {
        "response": response.output_text,
        "latency_ms": elapsed_ms,
        "usage": usage,
        "cost": {
            "input_usd": cost[0],
            "output_usd": cost[1],
            "total_usd": cost[2],
        }
    }
```

---

## 다중 모델 통합 전략

### LiteLLM 채택

**LiteLLM**을 사용하여 100+ LLM 제공자를 통합합니다.

#### 선택 이유

1. ✅ **통일된 인터페이스**: OpenAI 호환 API로 모든 모델 호출
2. ✅ **내장 비용 추적**: 자동 비용 계산 기능
3. ✅ **고성능**: 8ms P95 latency at 1k RPS
4. ✅ **광범위한 지원**: OpenAI, Anthropic, Google, AWS Bedrock 등 100+ 모델
5. ✅ **프로덕션 준비**: 안정적이고 활발히 유지보수됨

**Sources**:
- [LiteLLM Documentation](https://docs.litellm.ai/docs/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [LiteLLM Providers](https://docs.litellm.ai/docs/providers)

#### 설치

```bash
pip install 'litellm[proxy]'
```

#### 아키텍처 변경

**Before (v0.6.0)**:
```
Gateway API → OpenAI SDK → OpenAI API
```

**After (v0.7.0)**:
```
Gateway API → LiteLLM → [OpenAI API | Anthropic API | Google API | ...]
```

#### 구현 예시

```python
# services/gateway-api/app/llm_client.py (v0.7.0)

from litellm import completion
from .config import settings

def call_llm(prompt: str, model_version: str | None = None) -> dict:
    """
    LiteLLM을 사용한 범용 LLM 호출
    """
    model = _resolve_model(model_version)

    start = time.perf_counter()

    # LiteLLM 호출 (OpenAI 호환 인터페이스)
    response = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        api_key=settings.llm_api_key,
        api_base=settings.llm_api_base_url,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    # LiteLLM은 표준화된 usage 정보 제공
    usage = {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "cached_tokens": 0,  # 모델에 따라 제공
        "reasoning_tokens": 0,  # GPT-5 계열만
    }

    # LiteLLM 내장 비용 계산 활용
    cost_total = response._hidden_params.get("response_cost", 0)

    return {
        "response": response.choices[0].message.content,
        "latency_ms": elapsed_ms,
        "usage": usage,
        "cost": {
            "total_usd": cost_total,
            # 입력/출력 분리는 별도 계산
        }
    }
```

### Fallback 모델 설정

```python
# config.py
class Settings(BaseSettings):
    # 기존 설정
    openai_model_main: str = "gpt-5-mini"
    openai_model_judge: str = "gpt-4o-mini"

    # NEW: Fallback 모델 (v0.7.0)
    fallback_models: list[str] = [
        "gpt-4o-mini",  # Primary fallback
        "claude-haiku-4",  # Secondary fallback
    ]

    # 모델 타임아웃 (초)
    llm_timeout_seconds: int = 30
```

### 모델 자동 전환 로직

```python
def call_llm_with_fallback(prompt: str, model: str) -> dict:
    """
    Fallback을 지원하는 LLM 호출
    """
    models_to_try = [model] + settings.fallback_models

    for attempt_model in models_to_try:
        try:
            return call_llm(prompt, attempt_model)
        except Exception as e:
            logger.warning(f"Model {attempt_model} failed: {e}")
            continue

    raise Exception("All models failed")
```

---

## API 엔드포인트 설계

### 새 엔드포인트: `/cost/*`

#### 1. `GET /cost/summary`

사용자별/모델별 비용 요약

**Query Parameters**:
- `user_id` (optional): 특정 사용자 필터
- `model_version` (optional): 특정 모델 필터
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)

**Response**:
```json
{
  "total_cost_usd": 123.45,
  "total_requests": 10000,
  "total_input_tokens": 5000000,
  "total_output_tokens": 2000000,
  "breakdown_by_model": [
    {
      "model_version": "gpt-5-mini",
      "cost_usd": 80.00,
      "requests": 8000,
      "avg_cost_per_request": 0.01
    }
  ],
  "breakdown_by_user": [
    {
      "user_id": "user-123",
      "cost_usd": 50.00,
      "requests": 4000
    }
  ]
}
```

#### 2. `GET /cost/trends`

시간별 비용 추이

**Query Parameters**:
- `granularity`: `hour` | `day` | `week` | `month`
- `hours` or `days`: 조회 기간

**Response**:
```json
{
  "data": [
    {
      "timestamp": "2026-01-20 10:00:00",
      "cost_usd": 12.34,
      "requests": 500,
      "input_tokens": 250000,
      "output_tokens": 100000
    }
  ]
}
```

#### 3. `GET /cost/models`

모델 성능 대비 비용 효율성 분석

**Response**:
```json
{
  "models": [
    {
      "model_version": "gpt-5-mini",
      "avg_cost_per_request": 0.01,
      "avg_quality_score": 4.2,
      "cost_per_quality_point": 0.0024,
      "recommendation": "최고 가성비 모델"
    }
  ]
}
```

#### 4. `GET /models/pricing`

등록된 모델 가격 정보 조회

**Response**:
```json
{
  "models": [
    {
      "model_name": "gpt-5-mini",
      "provider": "openai",
      "price_input_per_1m": 0.25,
      "price_output_per_1m": 2.00,
      "context_window": 400000
    }
  ]
}
```

#### 5. `POST /models/pricing` (Admin only)

모델 가격 정보 추가/수정

---

## Prometheus 메트릭 설계

### 새 메트릭: Cost Tracking

```python
# services/gateway-api/app/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 토큰 사용량 메트릭
llm_token_usage_total = Counter(
    'llm_gateway_token_usage_total',
    'Total tokens used by type',
    ['model_version', 'token_type']  # token_type: input, output, cached, reasoning
)

# 비용 메트릭
llm_cost_usd_total = Counter(
    'llm_gateway_cost_usd_total',
    'Total cost in USD',
    ['model_version', 'user_id']
)

# 비용 분포 (히스토그램)
llm_cost_per_request = Histogram(
    'llm_gateway_cost_per_request_usd',
    'Cost per request in USD',
    ['model_version'],
    buckets=[0.0001, 0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# 일일 비용 (Gauge)
llm_daily_cost_usd = Gauge(
    'llm_gateway_daily_cost_usd',
    'Daily cost accumulator in USD',
    ['model_version']
)
```

### 메트릭 기록 로직

```python
# main.py의 /chat 엔드포인트에서

result = call_llm(request.prompt, request.model_version)

# 토큰 메트릭 기록
llm_token_usage_total.labels(
    model_version=result["model_version"],
    token_type="input"
).inc(result["usage"]["input_tokens"])

llm_token_usage_total.labels(
    model_version=result["model_version"],
    token_type="output"
).inc(result["usage"]["output_tokens"])

# 비용 메트릭 기록
llm_cost_usd_total.labels(
    model_version=result["model_version"],
    user_id=request.user_id or "anonymous"
).inc(result["cost"]["total_usd"])

llm_cost_per_request.labels(
    model_version=result["model_version"]
).observe(result["cost"]["total_usd"])
```

---

## 마이그레이션 계획

### 1. 데이터베이스 마이그레이션

#### 스크립트: `scripts/migrate_v0.7.0.sql`

```sql
-- v0.7.0 Migration Script
-- Adds cost tracking and token usage fields

BEGIN;

-- 1. llm_logs 테이블 수정
ALTER TABLE llm_logs
ADD COLUMN input_tokens INTEGER,
ADD COLUMN output_tokens INTEGER,
ADD COLUMN total_tokens INTEGER,
ADD COLUMN cached_tokens INTEGER DEFAULT 0,
ADD COLUMN reasoning_tokens INTEGER DEFAULT 0,
ADD COLUMN cost_input_usd DECIMAL(10, 6),
ADD COLUMN cost_output_usd DECIMAL(10, 6),
ADD COLUMN cost_total_usd DECIMAL(10, 6);

-- 2. 인덱스 추가
CREATE INDEX idx_llm_logs_cost ON llm_logs(cost_total_usd DESC);

-- 3. llm_model_pricing 테이블 생성
CREATE TABLE llm_model_pricing (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(128) UNIQUE NOT NULL,
    provider VARCHAR(64) NOT NULL,
    price_input_per_1m DECIMAL(10, 4) NOT NULL,
    price_output_per_1m DECIMAL(10, 4) NOT NULL,
    price_cached_per_1m DECIMAL(10, 4) DEFAULT 0,
    context_window INTEGER,
    max_output_tokens INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    tags VARCHAR(64)[]
);

-- 4. 초기 가격 데이터 삽입
INSERT INTO llm_model_pricing (model_name, provider, price_input_per_1m, price_output_per_1m, context_window, description) VALUES
('gpt-5', 'openai', 1.25, 10.00, 400000, 'GPT-5 flagship model with reasoning capabilities'),
('gpt-5-mini', 'openai', 0.25, 2.00, 400000, 'Cost-efficient GPT-5 variant'),
('gpt-5-nano', 'openai', 0.05, 0.40, 200000, 'Ultra-fast lightweight GPT-5'),
('gpt-4o', 'openai', 2.50, 10.00, 128000, 'GPT-4 optimized for speed'),
('gpt-4o-mini', 'openai', 0.15, 0.60, 128000, 'Compact GPT-4o'),
('claude-sonnet-4', 'anthropic', 0.30, 1.50, 200000, 'Claude Sonnet 4 - balanced performance'),
('claude-haiku-4', 'anthropic', 0.25, 1.25, 200000, 'Claude Haiku 4 - fast and affordable');

COMMIT;
```

#### 실행 방법

```bash
# Docker 환경
docker exec -i llm-postgres psql -U llm_user -d llm_quality < scripts/migrate_v0.7.0.sql

# 또는 Docker Compose 실행 시 자동 마이그레이션
# (init.sql에 포함)
```

### 2. 코드 마이그레이션

1. **의존성 추가**:
   ```bash
   cd services/gateway-api
   uv add litellm
   ```

2. **llm_client.py 교체**:
   - OpenAI SDK → LiteLLM 전환
   - 토큰 및 비용 계산 로직 추가

3. **models.py 업데이트**:
   - `LLMLog` 모델에 필드 추가
   - `LLMModelPricing` 모델 추가

4. **schemas.py 업데이트**:
   - `ChatResponse`에 usage, cost 필드 추가
   - 새 Cost API 스키마 추가

5. **main.py 수정**:
   - `/chat` 엔드포인트에서 토큰/비용 저장
   - 새 `/cost/*` 엔드포인트 추가

### 3. 하위 호환성

- **기존 데이터**: 토큰/비용 필드는 NULL 허용 → 기존 로그는 영향 없음
- **기존 API**: `/chat` 응답 스키마에 선택적 필드 추가 → 하위 호환
- **환경 변수**: 새 설정은 기본값 제공 → 기존 배포 영향 없음

---

## 구현 우선순위

### Phase 1: 기본 토큰 추적 (Week 1)

- [ ] 데이터베이스 마이그레이션 스크립트 작성
- [ ] `llm_logs` 테이블에 토큰 필드 추가
- [ ] `llm_model_pricing` 테이블 생성 및 초기 데이터
- [ ] Gateway API `llm_client.py`에서 토큰 정보 추출
- [ ] 토큰 정보 DB 저장
- [ ] 단위 테스트 작성

### Phase 2: 비용 계산 (Week 1-2)

- [ ] 비용 계산 로직 구현 (`calculate_cost()`)
- [ ] 모델 가격 조회 서비스 구현
- [ ] 비용 정보 DB 저장
- [ ] Prometheus 비용 메트릭 추가
- [ ] 통합 테스트

### Phase 3: 비용 분석 API (Week 2)

- [ ] `GET /cost/summary` 구현
- [ ] `GET /cost/trends` 구현
- [ ] `GET /cost/models` 구현
- [ ] `GET /models/pricing` 구현
- [ ] API 문서 업데이트

### Phase 4: LiteLLM 통합 (Week 2-3)

- [ ] LiteLLM 의존성 추가
- [ ] `llm_client.py` LiteLLM으로 전환
- [ ] Fallback 모델 로직 구현
- [ ] 다중 제공자 테스트 (OpenAI, Anthropic)
- [ ] 성능 벤치마크

### Phase 5: 대시보드 및 문서 (Week 3)

- [ ] Grafana 비용 대시보드 추가
- [ ] Next.js 대시보드에 Cost 페이지 추가
- [ ] API 가이드 업데이트
- [ ] 마이그레이션 가이드 작성
- [ ] 릴리즈 노트 작성

---

## 다음 단계

1. ✅ **OpenAI API 조사 완료** (2026-01-20)
2. ✅ **아키텍처 설계 문서 작성** (2026-01-20)
3. ⏳ **팀 리뷰 및 피드백** (예정)
4. ⏳ **구현 시작**: Phase 1부터 순차 진행

---

**작성자**: AI Agent (Claude Code)
**검토자**: @dongkoony
**승인 대기 중**
