# Analytics API 가이드 (v0.6.0)

v0.6.0에서 추가된 고급 분석 및 알림 API에 대한 상세 가이드입니다.

## 📊 새로 추가된 엔드포인트

### 1. GET `/analytics/trends` - 시간대별 품질 트렌드 분석
### 2. GET `/analytics/compare-models` - 모델 간 상세 성능 비교
### 3. GET `/alerts/history` - Prometheus Alert 이력 조회

---

## 1. `/analytics/trends` - 시간대별 품질 트렌드 분석

### 개요

최근 N시간 동안의 시간별(hourly) 통계를 제공합니다. 품질 점수, 레이턴시, 에러율을 시간대별로 분석하여 트렌드를 파악할 수 있습니다.

### 엔드포인트

```
GET /analytics/trends
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `hours` | integer | ❌ | 24 | 조회할 시간 (1-168시간, 최대 7일) |

### 응답 스키마

```json
{
  "data": [
    {
      "hour": "2025-12-26 10:00:00",
      "avg_score": 3.8,
      "avg_latency_ms": 1250.5,
      "total_requests": 150,
      "total_evaluated": 145,
      "error_rate": 2.5
    },
    ...
  ],
  "summary": {
    "total_requests": 3500,
    "total_errors": 87,
    "overall_error_rate": 2.49,
    "total_evaluated": 3400,
    "overall_avg_score": 3.75,
    "hours_analyzed": 24
  }
}
```

### 응답 필드 설명

#### `data` (array)
시간대별 데이터 포인트 배열

- **hour** (string): 시간대 (YYYY-MM-DD HH:00:00 형식)
- **avg_score** (float | null): 평균 평가 점수 (1-5)
- **avg_latency_ms** (float | null): 평균 레이턴시 (밀리초)
- **total_requests** (integer): 총 요청 수
- **total_evaluated** (integer): 평가된 요청 수
- **error_rate** (float | null): 에러율 (%)

#### `summary` (object)
전체 기간 통계 요약

- **total_requests** (integer): 전체 요청 수
- **total_errors** (integer): 전체 에러 수
- **overall_error_rate** (float): 전체 에러율 (%)
- **total_evaluated** (integer): 전체 평가 수
- **overall_avg_score** (float | null): 전체 평균 점수
- **hours_analyzed** (integer): 분석한 시간 범위

### 사용 예시

#### 요청: 최근 24시간 트렌드 조회

```bash
curl -X GET "http://localhost:18000/analytics/trends?hours=24"
```

#### 요청: 최근 7일 트렌드 조회

```bash
curl -X GET "http://localhost:18000/analytics/trends?hours=168"
```

#### Python 예시

```python
import requests

# 최근 48시간 트렌드 조회
response = requests.get(
    "http://localhost:18000/analytics/trends",
    params={"hours": 48}
)

data = response.json()

# 시간대별 품질 저하 감지
for point in data["data"]:
    if point["avg_score"] and point["avg_score"] < 3.0:
        print(f"⚠️  {point['hour']}: 품질 저하 감지 (점수: {point['avg_score']})")
    if point["error_rate"] and point["error_rate"] > 5.0:
        print(f"🚨 {point['hour']}: 높은 에러율 (에러: {point['error_rate']}%)")

# 전체 통계 출력
summary = data["summary"]
print(f"\n📊 전체 통계 ({summary['hours_analyzed']}시간)")
print(f"   총 요청: {summary['total_requests']}")
print(f"   에러율: {summary['overall_error_rate']:.2f}%")
print(f"   평균 점수: {summary['overall_avg_score']:.2f}")
```

### 활용 시나리오

1. **품질 변화 감지**: 시간대별 평균 점수를 추적하여 품질 저하 시점 파악
2. **피크 타임 분석**: 요청이 많은 시간대와 품질/에러율 상관관계 분석
3. **에러 패턴 파악**: 특정 시간대에 에러가 집중되는지 확인
4. **SLA 모니터링**: 시간대별 에러율 및 레이턴시 추적

---

## 2. `/analytics/compare-models` - 모델 간 상세 성능 비교

### 개요

지정된 기간 동안 사용된 모든 모델의 상세 성능 지표를 비교합니다. 레이턴시 백분위수(p50, p95, p99), 에러율, 품질 분포 등을 제공합니다.

### 엔드포인트

```
GET /analytics/compare-models
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `days` | integer | ❌ | 7 | 비교할 기간 (1-30일) |

### 응답 스키마

```json
{
  "models": [
    {
      "model_version": "gpt-4o-mini",
      "total_requests": 5000,
      "success_rate": 97.5,
      "error_rate": 2.5,
      "avg_latency_ms": 1250.3,
      "p50_latency_ms": 1100.0,
      "p95_latency_ms": 2500.0,
      "p99_latency_ms": 3200.0,
      "avg_score": 3.8,
      "total_evaluated": 4800,
      "low_quality_count": 150,
      "high_quality_count": 3200
    },
    ...
  ],
  "best_model_by_latency": "gpt-4o-mini",
  "best_model_by_quality": "gpt-4",
  "best_model_by_stability": "gpt-4o-mini"
}
```

### 응답 필드 설명

#### `models` (array)
모델별 상세 성능 데이터

- **model_version** (string): 모델 이름
- **total_requests** (integer): 총 요청 수
- **success_rate** (float): 성공률 (%)
- **error_rate** (float): 에러율 (%)
- **avg_latency_ms** (float | null): 평균 레이턴시 (ms)
- **p50_latency_ms** (float | null): p50 레이턴시 - 중앙값 (ms)
- **p95_latency_ms** (float | null): p95 레이턴시 (ms)
- **p99_latency_ms** (float | null): p99 레이턴시 (ms)
- **avg_score** (float | null): 평균 품질 점수 (1-5)
- **total_evaluated** (integer): 평가된 요청 수
- **low_quality_count** (integer): 저품질 응답 수 (점수 < 3)
- **high_quality_count** (integer): 고품질 응답 수 (점수 ≥ 4)

#### Best Model 판정

- **best_model_by_latency** (string | null): 가장 빠른 모델 (p50 기준)
- **best_model_by_quality** (string | null): 가장 품질이 좋은 모델 (평균 점수 기준)
- **best_model_by_stability** (string | null): 가장 안정적인 모델 (에러율 기준)

### 사용 예시

#### 요청: 최근 7일간 모델 비교

```bash
curl -X GET "http://localhost:18000/analytics/compare-models?days=7"
```

#### 요청: 최근 30일간 모델 비교

```bash
curl -X GET "http://localhost:18000/analytics/compare-models?days=30"
```

#### Python 예시

```python
import requests
import pandas as pd

# 최근 14일간 모델 비교
response = requests.get(
    "http://localhost:18000/analytics/compare-models",
    params={"days": 14}
)

data = response.json()

# 모델 데이터를 DataFrame으로 변환
df = pd.DataFrame(data["models"])

# 성능 지표별 정렬
print("📊 모델 성능 비교 (최근 14일)")
print("\n=== 레이턴시 기준 (낮을수록 좋음) ===")
print(df[["model_version", "p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]]
      .sort_values("p50_latency_ms"))

print("\n=== 품질 기준 (높을수록 좋음) ===")
print(df[["model_version", "avg_score", "high_quality_count", "low_quality_count"]]
      .sort_values("avg_score", ascending=False))

print("\n=== 안정성 기준 (에러율 낮을수록 좋음) ===")
print(df[["model_version", "error_rate", "success_rate", "total_requests"]]
      .sort_values("error_rate"))

# Best models
print(f"\n🏆 최고의 모델")
print(f"   속도: {data['best_model_by_latency']}")
print(f"   품질: {data['best_model_by_quality']}")
print(f"   안정성: {data['best_model_by_stability']}")

# 비용 효율성 계산 (품질 대비 속도)
df["efficiency_score"] = df["avg_score"] / (df["p50_latency_ms"] / 1000)
best_efficiency = df.loc[df["efficiency_score"].idxmax()]
print(f"   비용효율: {best_efficiency['model_version']}")
```

### 활용 시나리오

1. **모델 선택**: 새로운 모델 도입 시 성능 비교를 통한 의사결정
2. **모델 A/B 테스트**: 여러 모델을 동시에 운영하며 성능 모니터링
3. **비용 최적화**: 품질 대비 레이턴시가 좋은 모델 식별
4. **품질 관리**: 저품질 응답이 많은 모델 파악 및 개선
5. **SLA 준수**: p95, p99 레이턴시를 통한 worst-case 성능 확인

---

## 3. `/alerts/history` - Prometheus Alert 이력 조회

### 개요

Prometheus에서 발생한 Alert의 이력을 조회합니다. 현재 활성화된 Alert와 과거 Alert를 확인할 수 있습니다.

### 엔드포인트

```
GET /alerts/history
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `page` | integer | ❌ | 1 | 페이지 번호 (1부터 시작) |
| `page_size` | integer | ❌ | 20 | 페이지당 Alert 수 (1-100) |
| `severity` | string | ❌ | null | Severity 필터 (critical, warning, info) |
| `service` | string | ❌ | null | Service 필터 (gateway-api, evaluator, etc.) |

### 응답 스키마

```json
{
  "alerts": [
    {
      "alert_name": "HighHTTPErrorRate",
      "severity": "critical",
      "service": "gateway-api",
      "summary": "High HTTP 5xx error rate detected",
      "description": "HTTP 5xx error rate is 7.5% (threshold: 5%)",
      "started_at": "2025-12-26T10:15:30Z",
      "ended_at": null,
      "duration_seconds": null,
      "status": "firing"
    },
    ...
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 응답 필드 설명

#### `alerts` (array)
Alert 정보 배열

- **alert_name** (string): Alert 이름 (예: HighHTTPErrorRate)
- **severity** (string): 심각도 (critical, warning, info)
- **service** (string): 서비스 이름 (gateway-api, evaluator 등)
- **summary** (string | null): Alert 요약
- **description** (string | null): Alert 상세 설명
- **started_at** (string): Alert 시작 시간 (ISO 8601 형식)
- **ended_at** (string | null): Alert 종료 시간 (해결되지 않으면 null)
- **duration_seconds** (integer | null): Alert 지속 시간 (초)
- **status** (string): Alert 상태 (firing, resolved)

#### 페이지네이션

- **total** (integer): 전체 Alert 수
- **page** (integer): 현재 페이지 번호
- **page_size** (integer): 페이지당 Alert 수
- **total_pages** (integer): 전체 페이지 수

### 사용 예시

#### 요청: 모든 Alert 조회 (첫 페이지)

```bash
curl -X GET "http://localhost:18000/alerts/history"
```

#### 요청: Critical Alert만 필터링

```bash
curl -X GET "http://localhost:18000/alerts/history?severity=critical"
```

#### 요청: 특정 서비스의 Alert만 조회

```bash
curl -X GET "http://localhost:18000/alerts/history?service=gateway-api"
```

#### 요청: 페이지네이션

```bash
curl -X GET "http://localhost:18000/alerts/history?page=2&page_size=10"
```

#### Python 예시

```python
import requests
from datetime import datetime

# Critical Alert 조회
response = requests.get(
    "http://localhost:18000/alerts/history",
    params={
        "severity": "critical",
        "page_size": 50
    }
)

data = response.json()

print(f"🚨 Critical Alerts: {data['total']}개\n")

for alert in data["alerts"]:
    started = datetime.fromisoformat(alert["started_at"].replace("Z", "+00:00"))

    print(f"Alert: {alert['alert_name']}")
    print(f"  Service: {alert['service']}")
    print(f"  Summary: {alert['summary']}")
    print(f"  Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Status: {alert['status']}")
    print()

# 서비스별 Alert 집계
service_counts = {}
for alert in data["alerts"]:
    service = alert["service"]
    service_counts[service] = service_counts.get(service, 0) + 1

print("📊 서비스별 Critical Alert 수:")
for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {service}: {count}개")
```

#### Alert 모니터링 스크립트

```python
import requests
import time

def check_alerts():
    """주기적으로 Alert를 확인하고 Critical Alert 발생 시 알림"""
    response = requests.get(
        "http://localhost:18000/alerts/history",
        params={"severity": "critical"}
    )

    data = response.json()

    if data["total"] > 0:
        print(f"⚠️  {data['total']}개의 Critical Alert 발생!")
        for alert in data["alerts"]:
            if alert["status"] == "firing":
                print(f"   🔥 {alert['alert_name']} ({alert['service']})")
                print(f"      {alert['summary']}")
    else:
        print("✅ Critical Alert 없음")

# 5분마다 Alert 확인
while True:
    check_alerts()
    time.sleep(300)  # 5분
```

### 활용 시나리오

1. **실시간 모니터링**: 현재 발생 중인 Alert 확인
2. **Alert 이력 분석**: 과거 Alert 패턴 파악
3. **서비스 상태 점검**: 특정 서비스의 Alert 빈도 확인
4. **On-call 대응**: Critical Alert 발생 시 즉시 알림 및 대응
5. **장애 후 분석**: 장애 기간 동안 발생한 Alert 추적

### 주의사항

- 현재 구현은 Prometheus의 **활성 Alert**만 조회합니다
- 과거 해결된 Alert 이력은 Alertmanager API 또는 별도 저장소 필요
- Prometheus 연결 실패 시 빈 배열 반환
- 대량의 Alert 조회 시 페이지네이션 사용 권장

---

## 🔧 API 에러 처리

### 공통 HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 파라미터 (예: hours > 168) |
| 422 | Unprocessable Entity | 유효성 검증 실패 |
| 500 | Internal Server Error | 서버 내부 오류 |

### 에러 응답 예시

```json
{
  "detail": [
    {
      "loc": ["query", "hours"],
      "msg": "ensure this value is less than or equal to 168",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## 📊 성능 고려사항

### `/analytics/trends`

- **쿼리 복잡도**: O(hours) - 시간 범위에 비례
- **권장 범위**: 최대 168시간 (7일)
- **응답 시간**: 일반적으로 < 500ms (데이터 10만 건 기준)

**최적화 팁**:
- 자주 조회하는 범위(24h, 48h)는 캐싱 고려
- 168시간(7일) 조회는 부하가 높으므로 필요 시만 사용

### `/analytics/compare-models`

- **쿼리 복잡도**: O(models × requests) - 모델 수와 데이터 양에 비례
- **권장 범위**: 최대 30일
- **응답 시간**: 일반적으로 < 1s (모델 3개, 데이터 10만 건 기준)

**최적화 팁**:
- 백분위수 계산은 메모리 내에서 수행되므로 데이터가 많으면 느려질 수 있음
- 모델이 5개 이상이고 기간이 30일인 경우 캐싱 권장

### `/alerts/history`

- **쿼리 복잡도**: O(1) - Prometheus API 호출
- **응답 시간**: 일반적으로 < 100ms
- **제한사항**: Prometheus 타임아웃 5초

**최적화 팁**:
- 페이지네이션은 메모리 내에서 수행 (Prometheus는 페이지네이션 미지원)
- Alert가 수백 개 이상이면 페이지 크기를 줄이는 것이 좋음

---

## 🧪 테스트

### 헬스체크

```bash
# Gateway API 상태 확인
curl http://localhost:18000/health
```

### Swagger UI

FastAPI 자동 문서:
```
http://localhost:18000/docs
```

- 모든 엔드포인트를 브라우저에서 테스트 가능
- Request/Response 스키마 확인
- "Try it out" 버튼으로 즉시 테스트

### 샘플 데이터 생성

```python
import requests

# 샘플 요청 생성 (테스트 데이터 생성용)
for i in range(100):
    requests.post(
        "http://localhost:18000/chat",
        json={
            "prompt": f"Test prompt {i}",
            "user_id": f"user_{i % 10}",
            "model_version": "gpt-4o-mini"
        }
    )
```

---

## 📚 추가 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Prometheus API 문서](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)

---

## 🆘 문제 해결

### 문제: "No data" 응답

**원인**: 데이터베이스에 데이터가 없음

**해결**:
1. Gateway API에 요청 전송하여 데이터 생성
2. Evaluator가 실행 중인지 확인
3. 데이터 생성 후 5-10분 대기

### 문제: Alert History가 비어있음

**원인**: Prometheus/Alertmanager가 실행 중이 아니거나 Alert가 없음

**해결**:
```bash
# Prometheus 상태 확인
curl http://localhost:9090/api/v1/alerts

# Docker 컨테이너 확인
docker ps | grep -E "prometheus|alertmanager"
```

### 문제: "Connection refused" 에러

**원인**: Prometheus가 실행 중이 아님

**해결**:
```bash
# Prometheus 시작
cd infra/docker
docker compose -f docker-compose.local.yml up prometheus -d
```

---

**작성일**: 2025-12-26
**버전**: v0.6.0
**대상 서비스**: Gateway API (port 18000)
