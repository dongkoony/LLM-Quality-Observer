# v0.6.0 테스트 가이드

이 문서는 LLM Quality Observer v0.6.0의 모든 새 기능을 체계적으로 테스트하는 방법을 안내합니다.

---

## 📋 목차

1. [사전 준비](#사전-준비)
2. [시스템 시작 및 기본 검증](#시스템-시작-및-기본-검증)
3. [Alertmanager 테스트](#alertmanager-테스트)
4. [Alert Rules 테스트](#alert-rules-테스트)
5. [새 API 엔드포인트 테스트](#새-api-엔드포인트-테스트)
6. [Grafana 대시보드 테스트](#grafana-대시보드-테스트)
7. [통합 시나리오 테스트](#통합-시나리오-테스트)
8. [성능 테스트](#성능-테스트)
9. [문제 해결](#문제-해결)

---

## 사전 준비

### 1. 시스템 요구사항 확인

```bash
# Docker 버전 확인
docker --version  # 20.10 이상 권장

# Docker Compose 버전 확인
docker compose version  # 2.0 이상 권장

# 디스크 공간 확인 (최소 10GB 필요)
df -h
```

### 2. 환경 변수 설정

```bash
# .env.local 파일이 있는지 확인
ls -la /home/sdhcokr/project/LLM-Quality-Observer/configs/env/.env.local

# 필수 환경 변수 확인
grep -E "OPENAI_MODEL_MAIN|LLM_API_KEY|DATABASE_URL" configs/env/.env.local
```

### 3. 포트 충돌 확인

```bash
# 사용할 포트들이 사용 가능한지 확인
for port in 18000 18001 18002 3000 3001 5432 9090 9093; do
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $port is already in use"
  else
    echo "✅ Port $port is available"
  fi
done
```

---

## 시스템 시작 및 기본 검증

### 1. 전체 시스템 시작

```bash
# 작업 디렉토리 이동
cd /home/sdhcokr/project/LLM-Quality-Observer/infra/docker

# 기존 컨테이너 정리 (선택사항)
docker compose -f docker-compose.local.yml down -v

# 전체 빌드 및 시작
docker compose -f docker-compose.local.yml up -d --build

# 컨테이너 시작 대기 (약 30초)
sleep 30
```

### 2. 컨테이너 상태 확인

```bash
# 모든 컨테이너가 Up 상태인지 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 예상 출력:
# NAMES              STATUS              PORTS
# llm-alertmanager   Up X seconds        0.0.0.0:9093->9093/tcp
# llm-prometheus     Up X seconds        0.0.0.0:9090->9090/tcp
# llm-grafana        Up X seconds        0.0.0.0:3001->3000/tcp
# llm-gateway-api    Up X seconds        0.0.0.0:18000->8000/tcp
# llm-evaluator      Up X seconds        0.0.0.0:18001->8000/tcp
# llm-dashboard      Up X seconds        0.0.0.0:18002->8000/tcp
# llm-postgres       Up X seconds        0.0.0.0:5432->5432/tcp
```

**검증 포인트:**
- ✅ 7개 컨테이너 모두 Up 상태
- ✅ 재시작 없이 안정적으로 실행 중

### 3. 서비스 Health Check

```bash
# Gateway API
curl http://localhost:18000/health
# 예상 출력: {"status":"ok"}

# Evaluator
curl http://localhost:18001/health
# 예상 출력: {"status":"ok"}

# Prometheus
curl http://localhost:9090/-/healthy
# 예상 출력: Prometheus is Healthy.

# Alertmanager
curl http://localhost:9093/-/healthy
# 예상 출력: OK
```

**검증 포인트:**
- ✅ 모든 서비스가 healthy 상태 응답

### 4. 로그 확인

```bash
# Alertmanager 로그 확인 (에러 없어야 함)
docker logs llm-alertmanager 2>&1 | grep -i error

# Prometheus 로그 확인
docker logs llm-prometheus 2>&1 | grep -i error

# Gateway API 로그 확인
docker logs llm-gateway-api 2>&1 | tail -20
```

**검증 포인트:**
- ✅ Critical 에러 로그 없음
- ✅ 서비스 시작 로그 정상

---

## Alertmanager 테스트

### 1. Alertmanager UI 접속

```bash
# 브라우저에서 열기
open http://localhost:9093
# 또는
xdg-open http://localhost:9093
```

**검증 포인트:**
- ✅ Alertmanager UI가 정상적으로 로드됨
- ✅ 상단에 "Alertmanager" 제목 표시

### 2. Alertmanager 상태 확인

```bash
# 상태 API 호출
curl -s http://localhost:9093/api/v2/status | python3 -m json.tool

# 예상 출력 (일부):
# {
#     "cluster": {...},
#     "versionInfo": {
#         "version": "0.30.0",
#         ...
#     },
#     "config": {...}
# }
```

**검증 포인트:**
- ✅ version 정보 표시
- ✅ cluster 상태 정상
- ✅ config 로드 성공

### 3. Alert Receivers 설정 확인

```bash
# Alertmanager config 확인
curl -s http://localhost:9093/api/v2/status | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('config', {}).get('receivers', []), indent=2))"

# 예상 출력: 4개 receiver
# - default-receiver
# - critical-alerts
# - warning-alerts
# - ops-team
# - quality-team
```

**검증 포인트:**
- ✅ 5개 receiver 설정 확인
- ✅ receiver 이름 정확

### 4. 현재 Alert 확인

```bash
# 모든 alert 조회
curl -s http://localhost:9093/api/v2/alerts | python3 -m json.tool

# Alert 개수 확인
curl -s http://localhost:9093/api/v2/alerts | \
  python3 -c "import sys, json; print(f'Total alerts: {len(json.load(sys.stdin))}')"
```

**검증 포인트:**
- ✅ Alert 목록 정상 조회
- ✅ 각 alert에 labels, annotations 포함

---

## Alert Rules 테스트

### 1. Prometheus에서 Rule 로드 확인

```bash
# Rule groups 확인
curl -s http://localhost:9090/api/v1/rules | \
  python3 -c "import sys, json; data=json.load(sys.stdin); groups=data['data']['groups']; print(f'Total rule groups: {len(groups)}'); [print(f'- {g[\"name\"]}: {len(g[\"rules\"])} rules') for g in groups]"

# 예상 출력:
# Total rule groups: 4
# - http_alerts: 7 rules
# - llm_alerts: 8 rules
# - evaluation_alerts: 12 rules
# - system_alerts: 15 rules
```

**검증 포인트:**
- ✅ 4개 rule groups 로드
- ✅ 총 42개 rules 확인

### 2. Rule 상세 확인

```bash
# HTTP alerts 확인
curl -s http://localhost:9090/api/v1/rules | \
  python3 -c "import sys, json; data=json.load(sys.stdin); http_group=[g for g in data['data']['groups'] if g['name']=='http_alerts'][0]; [print(f'- {r[\"name\"]}') for r in http_group['rules']]"

# 예상 출력 (7개 alert):
# - HighHTTPErrorRate
# - ElevatedHTTP4xxRate
# - HighHTTPLatencyP95
# - HighHTTPLatencyP99
# - LowRequestRate
# - HTTPRequestSpike
# - NoHTTPRequests
```

**검증 포인트:**
- ✅ 각 rule group의 alert 이름 확인
- ✅ Alert 설명 및 severity 라벨 확인

### 3. 특정 Alert Rule 테스트

#### Test 1: ServiceRestarted Alert (자동 발생)

```bash
# 현재 firing 중인 ServiceRestarted alert 확인
curl -s http://localhost:9090/api/v1/alerts | \
  python3 -c "import sys, json; alerts=json.load(sys.stdin)['data']['alerts']; service_restart=[a for a in alerts if a['labels']['alertname']=='ServiceRestarted']; print(f'ServiceRestarted alerts: {len(service_restart)}'); [print(f'- Service: {a[\"labels\"][\"service\"]}') for a in service_restart]"
```

**검증 포인트:**
- ✅ ServiceRestarted alert 발생 (서비스 재시작 후 5분 이내)
- ✅ service 라벨에 gateway-api, evaluator 포함

#### Test 2: HighHTTPErrorRate Alert (수동 트리거)

```bash
# 에러를 발생시켜 alert 트리거 (잘못된 요청 10회)
for i in {1..10}; do
  curl -s -X POST http://localhost:18000/invalid-endpoint > /dev/null
  echo "Error request $i sent"
done

# 5분 후 alert 확인
sleep 300
curl -s http://localhost:9090/api/v1/alerts | \
  python3 -c "import sys, json; alerts=[a for a in json.load(sys.stdin)['data']['alerts'] if a['labels']['alertname']=='HighHTTPErrorRate']; print(f'HighHTTPErrorRate firing: {len(alerts) > 0}')"
```

**검증 포인트:**
- ✅ 에러율 5% 초과 시 alert 발생
- ✅ Alertmanager로 전달됨

#### Test 3: LowEvaluationScore Alert (데이터로 트리거)

```bash
# 낮은 점수를 유발하는 테스트 데이터 생성
for i in {1..20}; do
  curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"a\", \"user_id\": \"test-user-$i\"}" > /dev/null
  echo "Low-quality request $i sent"
done

# 평가 실행
curl -s -X POST "http://localhost:18001/evaluate-once?limit=20"

# 10분 후 alert 확인
sleep 600
curl -s http://localhost:9090/api/v1/alerts | \
  python3 -c "import sys, json; alerts=[a for a in json.load(sys.stdin)['data']['alerts'] if a['labels']['alertname']=='LowEvaluationScore']; print(f'LowEvaluationScore firing: {len(alerts) > 0}')"
```

**검증 포인트:**
- ✅ 낮은 평가 점수로 alert 발생
- ✅ Severity: critical 확인

### 4. Alert States 확인

```bash
# All alerts with their states
curl -s http://localhost:9090/api/v1/alerts | \
  python3 -c "
import sys, json
alerts = json.load(sys.stdin)['data']['alerts']
states = {}
for a in alerts:
    state = a['state']
    states[state] = states.get(state, 0) + 1
print('Alert States:')
for state, count in states.items():
    print(f'  {state}: {count}')
"
```

**검증 포인트:**
- ✅ pending, firing 상태 확인
- ✅ 각 alert의 for 시간 확인

---

## 새 API 엔드포인트 테스트

### 준비: 테스트 데이터 생성

```bash
# 다양한 테스트 데이터 생성 (총 20개 요청)
for i in {1..20}; do
  MODEL=$( [ $((i % 2)) -eq 0 ] && echo "gpt-4o-mini" || echo "gpt-5-mini" )

  curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Test question $i: Explain quantum computing in simple terms.\",
      \"user_id\": \"test-user-$((i % 5))\",
      \"model_version\": \"$MODEL\"
    }" > /dev/null

  echo "Request $i sent (model: $MODEL)"
  sleep 1
done

# 모든 요청 평가
curl -s -X POST "http://localhost:18001/evaluate-once?limit=20"
echo "Evaluation completed"

# 데이터 확인
echo "Waiting for data to be processed..."
sleep 5
```

### 1. GET /analytics/trends 테스트

#### Test 1-1: 기본 호출 (24시간)

```bash
curl -s "http://localhost:18000/analytics/trends?hours=24" | python3 -m json.tool
```

**예상 출력:**
```json
{
    "data": [
        {
            "hour": "2026-01-02 04:00:00",
            "avg_score": 3.2,
            "avg_latency_ms": 1250.5,
            "total_requests": 20,
            "total_evaluated": 20,
            "error_rate": 0.0
        }
    ],
    "summary": {
        "total_requests": 20,
        "total_errors": 0,
        "overall_error_rate": 0.0,
        "total_evaluated": 20,
        "overall_avg_score": "3.2000000000000000",
        "hours_analyzed": 24
    }
}
```

**검증 포인트:**
- ✅ data 배열에 시간대별 데이터 포함
- ✅ summary에 전체 통계 포함
- ✅ avg_score, avg_latency_ms 계산 정확
- ✅ total_requests와 total_evaluated 일치

#### Test 1-2: 다양한 시간 범위

```bash
# 1시간
curl -s "http://localhost:18000/analytics/trends?hours=1" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Hours analyzed: {data[\"summary\"][\"hours_analyzed\"]}, Data points: {len(data[\"data\"])}')"

# 7일 (168시간)
curl -s "http://localhost:18000/analytics/trends?hours=168" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Hours analyzed: {data[\"summary\"][\"hours_analyzed\"]}, Data points: {len(data[\"data\"])}')"
```

**검증 포인트:**
- ✅ hours 파라미터가 summary에 반영됨
- ✅ 1-168 범위 내에서 정상 작동

#### Test 1-3: 경계값 테스트

```bash
# 최소값 (1시간)
curl -s "http://localhost:18000/analytics/trends?hours=1"
echo "Min hours: OK"

# 최대값 (168시간)
curl -s "http://localhost:18000/analytics/trends?hours=168"
echo "Max hours: OK"

# 범위 초과 (에러 예상)
curl -s "http://localhost:18000/analytics/trends?hours=200"
# 예상: 422 Validation Error

# 음수값 (에러 예상)
curl -s "http://localhost:18000/analytics/trends?hours=-1"
# 예상: 422 Validation Error
```

**검증 포인트:**
- ✅ 유효 범위 (1-168) 내에서 정상 작동
- ✅ 범위 벗어날 시 422 에러 응답

### 2. GET /analytics/compare-models 테스트

#### Test 2-1: 기본 호출 (7일)

```bash
curl -s "http://localhost:18000/analytics/compare-models?days=7" | python3 -m json.tool
```

**예상 출력:**
```json
{
    "models": [
        {
            "model_version": "gpt-5-mini",
            "total_requests": 10,
            "success_rate": 100.0,
            "error_rate": 0.0,
            "avg_latency_ms": 1200.5,
            "p50_latency_ms": 1150.0,
            "p95_latency_ms": 1400.0,
            "p99_latency_ms": null,
            "avg_score": 3.5,
            "total_evaluated": 10,
            "low_quality_count": 2,
            "high_quality_count": 8
        },
        {
            "model_version": "gpt-4o-mini",
            "total_requests": 10,
            "success_rate": 100.0,
            "error_rate": 0.0,
            "avg_latency_ms": 1300.2,
            "p50_latency_ms": 1250.0,
            "p95_latency_ms": null,
            "p99_latency_ms": null,
            "avg_score": 3.2,
            "total_evaluated": 10,
            "low_quality_count": 3,
            "high_quality_count": 7
        }
    ],
    "best_model_by_latency": "gpt-5-mini",
    "best_model_by_quality": "gpt-5-mini",
    "best_model_by_stability": "gpt-5-mini"
}
```

**검증 포인트:**
- ✅ models 배열에 각 모델별 통계 포함
- ✅ success_rate, error_rate 정확 (합계 100%)
- ✅ p50_latency_ms 계산됨 (>=10 samples)
- ✅ p95_latency_ms는 >=20 samples일 때만 계산
- ✅ p99_latency_ms는 >=100 samples일 때만 계산
- ✅ best_model_by_* 필드 올바르게 선정

#### Test 2-2: 품질 분류 확인

```bash
# Low/High quality count 검증
curl -s "http://localhost:18000/analytics/compare-models?days=7" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data['models']:
    print(f\"Model: {model['model_version']}\")
    print(f\"  Low quality (score < 3): {model['low_quality_count']}\")
    print(f\"  High quality (score >= 4): {model['high_quality_count']}\")
    print(f\"  Total evaluated: {model['total_evaluated']}\")
    print()
"
```

**검증 포인트:**
- ✅ low_quality_count: score < 3인 요청 수
- ✅ high_quality_count: score >= 4인 요청 수
- ✅ 합계가 total_evaluated와 일치 (중간 점수 포함)

#### Test 2-3: Best Model 선정 로직 검증

```bash
# Best models 확인
curl -s "http://localhost:18000/analytics/compare-models?days=7" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Best Model Selection:')
print(f\"  By Latency: {data['best_model_by_latency']}\")
print(f\"  By Quality: {data['best_model_by_quality']}\")
print(f\"  By Stability: {data['best_model_by_stability']}\")
"
```

**검증 포인트:**
- ✅ best_model_by_latency: 가장 낮은 avg_latency_ms
- ✅ best_model_by_quality: 가장 높은 avg_score
- ✅ best_model_by_stability: 가장 낮은 error_rate

### 3. GET /alerts/history 테스트

#### Test 3-1: 기본 호출

```bash
curl -s "http://localhost:18000/alerts/history?page=1&page_size=10" | python3 -m json.tool
```

**예상 출력:**
```json
{
    "alerts": [
        {
            "alert_name": "ServiceRestarted",
            "severity": "info",
            "service": "gateway-api",
            "summary": "Service restart detected",
            "description": "Service gateway-api has restarted recently",
            "started_at": "2026-01-02T04:52:09.447191715Z",
            "ended_at": null,
            "duration_seconds": null,
            "status": "firing"
        },
        ...
    ],
    "total": 3,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
}
```

**검증 포인트:**
- ✅ alerts 배열에 alert 정보 포함
- ✅ 페이지네이션 정보 정확 (total, page, page_size, total_pages)
- ✅ status가 "firing" 또는 "pending"

#### Test 3-2: 필터링 테스트

```bash
# Severity 필터 - critical만
curl -s "http://localhost:18000/alerts/history?severity=critical&page=1&page_size=10" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Critical alerts: {data[\"total\"]}'); [print(f'  - {a[\"alert_name\"]}') for a in data['alerts']]"

# Severity 필터 - warning만
curl -s "http://localhost:18000/alerts/history?severity=warning&page=1&page_size=10" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Warning alerts: {data[\"total\"]}')"

# Service 필터 - gateway-api만
curl -s "http://localhost:18000/alerts/history?service=gateway-api&page=1&page_size=10" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Gateway API alerts: {data[\"total\"]}')"

# 복합 필터 - critical + evaluator
curl -s "http://localhost:18000/alerts/history?severity=critical&service=evaluator&page=1&page_size=10" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Critical Evaluator alerts: {data[\"total\"]}')"
```

**검증 포인트:**
- ✅ severity 필터 작동
- ✅ service 필터 작동
- ✅ 복합 필터 작동 (AND 조건)

#### Test 3-3: 페이지네이션 테스트

```bash
# Page 1
curl -s "http://localhost:18000/alerts/history?page=1&page_size=2" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Page 1: {len(data[\"alerts\"])} alerts, Total pages: {data[\"total_pages\"]}')"

# Page 2
curl -s "http://localhost:18000/alerts/history?page=2&page_size=2" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Page 2: {len(data[\"alerts\"])} alerts')"

# 범위 초과 페이지
curl -s "http://localhost:18000/alerts/history?page=999&page_size=10" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Page 999: {len(data[\"alerts\"])} alerts')"
```

**검증 포인트:**
- ✅ page_size 제한 작동
- ✅ total_pages 계산 정확
- ✅ 범위 초과 시 빈 배열 반환

---

## Grafana 대시보드 테스트

### 1. Grafana 접속 및 로그인

```bash
# 브라우저에서 Grafana 열기
open http://localhost:3001
# 또는
xdg-open http://localhost:3001
```

**로그인 정보:**
- Username: `admin`
- Password: `admin`

**검증 포인트:**
- ✅ Grafana UI 정상 로드
- ✅ 로그인 성공

### 2. Datasource 확인

**UI 경로:** Configuration → Data Sources

```bash
# API로 datasource 확인
curl -s -u admin:admin http://localhost:3001/api/datasources | python3 -m json.tool
```

**검증 포인트:**
- ✅ Prometheus datasource 존재
- ✅ URL: http://prometheus:9090
- ✅ Access: proxy

### 3. Dashboard 목록 확인

**UI 경로:** Dashboards → Browse

```bash
# API로 dashboard 목록 확인
curl -s -u admin:admin http://localhost:3001/api/search?type=dash-db | \
  python3 -c "import sys, json; dashboards=json.load(sys.stdin); print(f'Total dashboards: {len(dashboards)}'); [print(f'  - {d[\"title\"]} (uid: {d[\"uid\"]})') for d in dashboards]"

# 예상 출력:
# Total dashboards: 3
#   - LLM Quality Observer (uid: llm-quality-observer)
#   - Alert History & Monitoring (uid: alert-history)
#   - Advanced Analytics Dashboard (uid: advanced-analytics)
```

**검증 포인트:**
- ✅ 3개 대시보드 존재
- ✅ 각 대시보드 UID 정확

### 4. Alert History Dashboard 테스트

**직접 접속:**
```bash
open http://localhost:3001/d/alert-history/alert-history-and-monitoring
```

**패널별 검증:**

| 패널 번호 | 패널 이름 | 검증 포인트 |
|----------|----------|-----------|
| 1 | Currently Firing Alerts | ✅ 현재 firing 상태 alert 표시, 테이블 형식 |
| 2 | Total Active Alerts | ✅ Gauge 차트, 숫자 표시 |
| 3 | Critical Alerts | ✅ Critical severity alert 개수 |
| 4 | Alerts by Severity | ✅ Pie chart, critical/warning/info 분포 |
| 5 | Alerts by Service | ✅ Pie chart, 서비스별 분포 |
| 6 | Alert Frequency | ✅ Time series, alert 발생 추이 |
| 7 | Active Alerts Details | ✅ 테이블, alert 상세 정보 |
| 8 | HTTP Error Rates | ✅ Time series, 5xx/4xx 에러율 |
| 9 | Latency p95 | ✅ Time series, HTTP latency |
| 10 | Evaluation Score Trend | ✅ Time series, 평가 점수 추이 |
| 11 | Pending Logs | ✅ Gauge, 대기 중인 로그 수 |

**수동 검증:**
1. 각 패널이 로드되는지 확인
2. "No data" 패널이 있는지 확인 (데이터 없을 시 정상)
3. Time range 변경 시 데이터 업데이트되는지 확인
4. Refresh 버튼 작동하는지 확인

### 5. Advanced Analytics Dashboard 테스트

**직접 접속:**
```bash
open http://localhost:3001/d/advanced-analytics/advanced-analytics-dashboard
```

**패널별 검증:**

| 패널 번호 | 패널 이름 | 검증 포인트 |
|----------|----------|-----------|
| 1 | Quality Score Trends | ✅ Time series, p50/p95/p99 표시 |
| 2 | Request Rate by Model | ✅ Time series, 모델별 요청률 |
| 3 | Latency p95 by Model | ✅ Time series, 모델별 latency |
| 4 | Error Rate by Model | ✅ Time series, 모델별 에러율 |
| 5 | Success Rate by Model | ✅ Time series, 모델별 성공률 |
| 6 | Model Performance | ✅ 테이블, 모델 비교 통계 |
| 7 | Request Volume | ✅ Bar chart, 모델별 요청 수 |
| 8 | Request Distribution | ✅ Donut chart, 모델별 비율 |
| 9 | Score Moving Averages | ✅ Time series, 이동 평균 |
| 10 | Token Usage Rate | ✅ Time series, 토큰 사용량 |
| 11 | Eval vs Request Rate | ✅ Time series, 평가/요청 비율 |

**수동 검증:**
1. 모든 패널이 데이터 표시하는지 확인 (테스트 데이터 생성 후)
2. Legend가 올바르게 표시되는지 확인
3. Tooltip이 작동하는지 확인
4. 패널 확대/축소 기능 작동하는지 확인

### 6. LLM Quality Observer Dashboard 테스트 (기존)

**직접 접속:**
```bash
open http://localhost:3001/d/llm-quality-observer/llm-quality-observer
```

**검증 포인트:**
- ✅ 14개 패널 모두 로드
- ✅ Overview stats 표시
- ✅ Metrics 그래프 정상

---

## 통합 시나리오 테스트

### 시나리오 1: 품질 저하 감지 및 Alert

**목표:** 낮은 품질의 응답이 많아지면 Alert가 발생하고, 대시보드에 표시되는지 확인

```bash
# Step 1: 저품질 요청 대량 생성 (30개)
echo "Step 1: Generating low-quality requests..."
for i in {1..30}; do
  curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"a\", \"user_id\": \"test-low-quality-$i\"}" > /dev/null
  echo -n "."
done
echo " Done!"

# Step 2: 평가 실행
echo "Step 2: Running evaluation..."
curl -s -X POST "http://localhost:18001/evaluate-once?limit=30"
echo " Done!"

# Step 3: 10분 대기 (alert for 시간)
echo "Step 3: Waiting 10 minutes for alert to fire..."
sleep 600

# Step 4: Alert 확인
echo "Step 4: Checking alerts..."
curl -s http://localhost:9090/api/v1/alerts | \
  python3 -c "
import sys, json
alerts = [a for a in json.load(sys.stdin)['data']['alerts'] if a['labels']['alertname'] == 'LowEvaluationScore']
if len(alerts) > 0:
    print('✅ LowEvaluationScore alert is firing!')
    print(f\"   State: {alerts[0]['state']}\")
    print(f\"   Score: {alerts[0]['annotations'].get('description', 'N/A')}\")
else:
    print('❌ LowEvaluationScore alert not found')
"

# Step 5: Grafana 대시보드 확인
echo "Step 5: Check Grafana dashboards manually:"
echo "  - Alert History: http://localhost:3001/d/alert-history"
echo "  - Advanced Analytics: http://localhost:3001/d/advanced-analytics"
echo "  Verify that score drop is visible in charts"

# Step 6: Analytics API 확인
echo "Step 6: Checking analytics API..."
curl -s "http://localhost:18000/analytics/trends?hours=1" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
if len(data['data']) > 0:
    latest = data['data'][-1]
    print(f\"✅ Latest hour data:\")
    print(f\"   Avg Score: {latest['avg_score']}\")
    print(f\"   Total Requests: {latest['total_requests']}\")
    print(f\"   Total Evaluated: {latest['total_evaluated']}\")
"
```

**예상 결과:**
1. ✅ LowEvaluationScore alert 발생 (state: firing)
2. ✅ Alertmanager에 alert 전달
3. ✅ Alert History 대시보드에 표시
4. ✅ Advanced Analytics에서 score 하락 그래프 확인
5. ✅ /analytics/trends에서 낮은 avg_score 확인

### 시나리오 2: 모델 성능 비교

**목표:** 두 모델의 성능을 비교하고 best model이 올바르게 선정되는지 확인

```bash
# Step 1: gpt-5-mini로 고품질 요청 생성 (20개)
echo "Step 1: Generating high-quality requests for gpt-5-mini..."
for i in {1..20}; do
  curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Explain the concept of machine learning and its applications in modern technology in detail.\",
      \"user_id\": \"test-user-$i\",
      \"model_version\": \"gpt-5-mini\"
    }" > /dev/null
  echo -n "."
done
echo " Done!"

# Step 2: gpt-4o-mini로 일반 품질 요청 생성 (20개)
echo "Step 2: Generating medium-quality requests for gpt-4o-mini..."
for i in {1..20}; do
  curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"What is AI?\",
      \"user_id\": \"test-user-$i\",
      \"model_version\": \"gpt-4o-mini\"
    }" > /dev/null
  echo -n "."
done
echo " Done!"

# Step 3: 평가 실행
echo "Step 3: Running evaluation..."
curl -s -X POST "http://localhost:18001/evaluate-once?limit=40"
echo " Done!"

# Step 4: 모델 비교 API 호출
echo "Step 4: Comparing models..."
curl -s "http://localhost:18000/analytics/compare-models?days=1" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print('\\nModel Comparison Results:')
print('=' * 60)
for model in data['models']:
    print(f\"\\nModel: {model['model_version']}\")
    print(f\"  Total Requests: {model['total_requests']}\")
    print(f\"  Success Rate: {model['success_rate']}%\")
    print(f\"  Avg Latency: {model['avg_latency_ms']:.2f}ms\")
    print(f\"  Avg Score: {model['avg_score']}\")
    print(f\"  Low Quality: {model['low_quality_count']}\")
    print(f\"  High Quality: {model['high_quality_count']}\")

print('\\nBest Models:')
print('=' * 60)
print(f\"  By Latency: {data['best_model_by_latency']}\")
print(f\"  By Quality: {data['best_model_by_quality']}\")
print(f\"  By Stability: {data['best_model_by_stability']}\")
"

# Step 5: Grafana 확인
echo -e "\\nStep 5: Check Advanced Analytics Dashboard:"
echo "  http://localhost:3001/d/advanced-analytics"
echo "  Verify model comparison panels show different metrics"
```

**예상 결과:**
1. ✅ 두 모델의 통계가 다르게 표시
2. ✅ gpt-5-mini의 avg_score가 더 높음
3. ✅ best_model_by_quality = "gpt-5-mini"
4. ✅ Grafana 패널에서 모델별 차이 확인 가능

### 시나리오 3: Alert Routing 테스트

**목표:** 서로 다른 severity의 alert가 올바른 receiver로 라우팅되는지 확인

```bash
# Step 1: Critical alert 트리거 (DB 연결 불가 시뮬레이션은 어려우므로 기존 critical alert 확인)
echo "Step 1: Checking current critical alerts..."
curl -s http://localhost:9093/api/v2/alerts | \
  python3 -c "
import sys, json
alerts = json.load(sys.stdin)
critical = [a for a in alerts if a['labels'].get('severity') == 'critical']
print(f'Critical alerts: {len(critical)}')
for a in critical:
    print(f\"  - {a['labels']['alertname']}\")
    print(f\"    Receiver: {a['receivers'][0]['name'] if a['receivers'] else 'None'}\")
"

# Step 2: Warning alert 확인
echo "Step 2: Checking warning alerts..."
curl -s http://localhost:9093/api/v2/alerts | \
  python3 -c "
import sys, json
alerts = json.load(sys.stdin)
warnings = [a for a in alerts if a['labels'].get('severity') == 'warning']
print(f'Warning alerts: {len(warnings)}')
for a in warnings:
    print(f\"  - {a['labels']['alertname']}\")
    print(f\"    Receiver: {a['receivers'][0]['name'] if a['receivers'] else 'None'}\")
"

# Step 3: Routing 규칙 확인
echo "Step 3: Verifying routing rules..."
echo "Expected routing:"
echo "  - critical alerts → critical-alerts receiver"
echo "  - warning alerts → warning-alerts receiver"
echo "  - info alerts → default-receiver"
```

**예상 결과:**
1. ✅ Critical alerts → critical-alerts receiver
2. ✅ Warning alerts → warning-alerts receiver
3. ✅ Info alerts → default-receiver
4. ✅ Inhibition rules 작동 (critical 있으면 warning 억제)

---

## 성능 테스트

### 1. API 응답 시간 테스트

```bash
# /analytics/trends 성능
echo "Testing /analytics/trends performance..."
for hours in 1 24 168; do
  START=$(date +%s%N)
  curl -s "http://localhost:18000/analytics/trends?hours=$hours" > /dev/null
  END=$(date +%s%N)
  ELAPSED=$(( (END - START) / 1000000 ))
  echo "  hours=$hours: ${ELAPSED}ms"
done

# /analytics/compare-models 성능
echo "Testing /analytics/compare-models performance..."
for days in 1 7 30; do
  START=$(date +%s%N)
  curl -s "http://localhost:18000/analytics/compare-models?days=$days" > /dev/null
  END=$(date +%s%N)
  ELAPSED=$(( (END - START) / 1000000 ))
  echo "  days=$days: ${ELAPSED}ms"
done

# /alerts/history 성능
echo "Testing /alerts/history performance..."
START=$(date +%s%N)
curl -s "http://localhost:18000/alerts/history?page=1&page_size=100" > /dev/null
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "  page_size=100: ${ELAPSED}ms"
```

**성능 기준:**
- ✅ /analytics/trends (24h): < 200ms
- ✅ /analytics/compare-models (7d): < 300ms
- ✅ /alerts/history (100개): < 100ms

### 2. Alert Rule 평가 성능

```bash
# Prometheus 메트릭 확인
curl -s http://localhost:9090/metrics | grep prometheus_rule_evaluation_duration_seconds

# 예상: 42개 rules, 평가 시간 < 100ms
```

**성능 기준:**
- ✅ Rule 평가 시간 < 100ms (총 42개 rules)

### 3. Dashboard 로딩 시간

**수동 테스트:**
1. 브라우저에서 각 대시보드 접속
2. 개발자 도구 → Network 탭에서 로딩 시간 확인

**성능 기준:**
- ✅ Dashboard 초기 로드 < 3초
- ✅ 패널 데이터 로드 < 2초

---

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker logs llm-alertmanager
docker logs llm-prometheus

# 일반적인 문제:
# 1. 파일 권한 문제
find /home/sdhcokr/project/LLM-Quality-Observer/infra -name "*.yml" -exec chmod 644 {} \;

# 2. 포트 충돌
lsof -i :9090  # Prometheus
lsof -i :9093  # Alertmanager

# 3. 볼륨 권한 문제
docker compose -f docker-compose.local.yml down -v
docker volume prune -f
docker compose -f docker-compose.local.yml up -d
```

### Alert가 발생하지 않음

```bash
# 1. Rule이 로드되었는지 확인
curl http://localhost:9090/api/v1/rules | grep -c "alert"

# 2. Metric이 수집되고 있는지 확인
curl http://localhost:9090/api/v1/query?query=llm_gateway_http_requests_total

# 3. Alert 조건 확인
curl -s http://localhost:9090/api/v1/rules | \
  python3 -c "import sys, json; [print(f\"{r['name']}: {r.get('state', 'N/A')}\") for g in json.load(sys.stdin)['data']['groups'] for r in g['rules']]"

# 4. Prometheus → Alertmanager 연결 확인
curl http://localhost:9090/api/v1/alertmanagers
```

### API 응답이 비어있음

```bash
# 1. 데이터가 있는지 확인
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "SELECT COUNT(*) FROM llm_logs;"

# 2. 평가 데이터 확인
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "SELECT COUNT(*) FROM llm_evaluations;"

# 3. 시간 범위 확인
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "SELECT MIN(created_at), MAX(created_at) FROM llm_logs;"
```

### Grafana 대시보드에 데이터가 없음

```bash
# 1. Datasource 연결 확인
curl -s -u admin:admin http://localhost:3001/api/datasources/1/health

# 2. Prometheus에 데이터 있는지 확인
curl "http://localhost:9090/api/v1/query?query=llm_gateway_http_requests_total"

# 3. Time range 확인 (Grafana UI에서)
# - 상단 time picker에서 "Last 24 hours" 선택
# - 또는 "Last 7 days"로 변경
```

---

## 테스트 체크리스트

### 시스템 레벨
- [ ] 7개 컨테이너 모두 Up 상태
- [ ] Health check 모두 통과
- [ ] 로그에 critical 에러 없음

### Alertmanager
- [ ] Alertmanager UI 접속 가능
- [ ] 5개 receiver 설정 확인
- [ ] Alert 수신 확인

### Alert Rules
- [ ] 42개 rules 로드 확인
- [ ] ServiceRestarted alert 발생 확인
- [ ] 수동 트리거 alert 테스트 성공

### API 엔드포인트
- [ ] /analytics/trends 정상 응답
- [ ] /analytics/compare-models 정상 응답
- [ ] /alerts/history 정상 응답
- [ ] 필터링 및 페이지네이션 작동
- [ ] 경계값 검증 성공

### Grafana 대시보드
- [ ] 3개 대시보드 모두 접속 가능
- [ ] Alert History 11개 패널 로드
- [ ] Advanced Analytics 11개 패널 로드
- [ ] 데이터 표시 정상

### 통합 시나리오
- [ ] 품질 저하 감지 시나리오 성공
- [ ] 모델 성능 비교 시나리오 성공
- [ ] Alert routing 시나리오 성공

### 성능
- [ ] API 응답 시간 기준 충족
- [ ] Rule 평가 성능 기준 충족
- [ ] Dashboard 로딩 시간 기준 충족

---

## 테스트 완료 후

```bash
# 테스트 데이터 정리 (선택사항)
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "DELETE FROM llm_logs WHERE user_id LIKE 'test-%';"
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c "DELETE FROM llm_evaluations WHERE log_id NOT IN (SELECT id FROM llm_logs);"

# 시스템 종료 (필요시)
cd /home/sdhcokr/project/LLM-Quality-Observer/infra/docker
docker compose -f docker-compose.local.yml down

# 볼륨까지 삭제 (완전 초기화)
docker compose -f docker-compose.local.yml down -v
```

---

**테스트 완료!**

모든 체크리스트를 완료하면 v0.6.0이 프로덕션 배포 준비가 완료된 것입니다.
