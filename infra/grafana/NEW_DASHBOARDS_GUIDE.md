# New Grafana Dashboards Guide (v0.6.0)

v0.6.0에서 추가된 2개의 새로운 Grafana 대시보드에 대한 가이드입니다.

## 📊 대시보드 목록

### 1. Alert History & Monitoring
- **UID**: `alert-history`
- **목적**: Alert 발생 이력 및 현재 상태 모니터링
- **주요 기능**: 실시간 Alert 추적, Severity 분석, 서비스별 Alert 현황

### 2. Advanced Analytics Dashboard
- **UID**: `advanced-analytics`
- **목적**: 고급 분석 및 모델 비교
- **주요 기능**: 품질 트렌드 분석, 모델별 성능 비교, 토큰 사용량 추적

---

## 🚨 Alert History & Monitoring Dashboard

### 개요

Alert 시스템의 전체적인 상태를 모니터링하고, 발생한 Alert의 이력을 추적하는 대시보드입니다.

### 패널 구성 (총 11개)

#### 1. Currently Firing Alerts (시계열 그래프)
- **위치**: Row 1, 좌측
- **크기**: 12 width
- **설명**: 현재 발생 중인 Alert를 시간별로 표시
- **PromQL**:
  ```promql
  sum by (alertname) (ALERTS{alertstate="firing"})
  ```
- **용도**: Alert 발생 패턴 파악, 반복되는 Alert 식별

#### 2. Total Active Alerts (게이지)
- **위치**: Row 1, 중앙
- **크기**: 6 width
- **설명**: 현재 활성화된 Alert 총 개수
- **임계값**:
  - 초록색: 0
  - 노란색: ≥ 1
  - 빨간색: ≥ 5
- **PromQL**:
  ```promql
  count(ALERTS{alertstate="firing"})
  ```

#### 3. Critical Alerts (게이지)
- **위치**: Row 1, 우측
- **크기**: 6 width
- **설명**: Critical 레벨 Alert 개수
- **임계값**:
  - 초록색: 0
  - 주황색: ≥ 1
- **PromQL**:
  ```promql
  count(ALERTS{alertstate="firing", severity="critical"})
  ```

#### 4. Alerts by Severity (파이 차트)
- **위치**: Row 2, 좌측
- **크기**: 12 width
- **설명**: Severity별 Alert 분포
- **PromQL**:
  ```promql
  sum by (severity) (ALERTS{alertstate="firing"})
  ```
- **용도**: Critical vs Warning Alert 비율 파악

#### 5. Alerts by Service (파이 차트)
- **위치**: Row 2, 우측
- **크기**: 12 width
- **설명**: 서비스별 Alert 분포
- **PromQL**:
  ```promql
  sum by (service) (ALERTS{alertstate="firing"})
  ```
- **용도**: 문제가 있는 서비스 식별

#### 6. Alert Frequency (Last Hour) (막대 그래프)
- **위치**: Row 3, 전체
- **크기**: 24 width
- **설명**: 지난 1시간 동안 Alert 발생 빈도
- **PromQL**:
  ```promql
  changes(ALERTS{alertstate="firing"}[1h])
  ```
- **용도**: Alert flapping 감지 (Alert가 반복적으로 발생/해제되는 현상)

#### 7. Active Alerts Details (테이블)
- **위치**: Row 4, 전체
- **크기**: 24 width
- **설명**: 현재 발생 중인 Alert의 상세 정보
- **표시 항목**: alertname, severity, service, annotations
- **PromQL**:
  ```promql
  ALERTS{alertstate="firing"}
  ```
- **용도**: Alert 원인 파악, 빠른 대응을 위한 상세 정보 제공

#### 8. Error Rates (Alert Triggers) (시계열)
- **위치**: Row 5, 좌측
- **크기**: 12 width
- **설명**: HTTP 5xx 및 LLM 에러율 (Alert 발생 조건)
- **PromQL**:
  ```promql
  # HTTP 5xx Error Rate
  rate(http_requests_total{status=~"5.."}[5m]) * 100 / rate(http_requests_total[5m])

  # LLM Error Rate
  rate(llm_requests_total{status="error"}[5m]) * 100 / rate(llm_requests_total[5m])
  ```
- **용도**: 에러율 Alert 트리거 조건 모니터링

#### 9. Latency p95 (Alert Triggers) (시계열)
- **위치**: Row 5, 우측
- **크기**: 12 width
- **설명**: HTTP 및 LLM p95 레이턴시 (Alert 발생 조건)
- **PromQL**:
  ```promql
  # HTTP p95
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

  # LLM p95
  histogram_quantile(0.95, sum(rate(llm_request_duration_seconds_bucket[5m])) by (le))
  ```
- **용도**: 레이턴시 Alert 트리거 조건 모니터링

#### 10. Evaluation Score Trend (시계열)
- **위치**: Row 6, 좌측
- **크기**: 12 width
- **설명**: 평가 점수 p50 트렌드
- **임계값 라인**: 3.0 (빨간색)
- **PromQL**:
  ```promql
  histogram_quantile(0.50, sum(rate(evaluation_score_bucket[10m])) by (le))
  ```
- **용도**: 품질 저하 Alert 트리거 조건 모니터링

#### 11. Pending Logs (Alert Trigger) (게이지)
- **위치**: Row 6, 우측
- **크기**: 12 width
- **설명**: 대기 중인 로그 수
- **임계값**:
  - 초록색: < 100
  - 노란색: ≥ 100
  - 빨간색: ≥ 500
- **PromQL**:
  ```promql
  scheduler_pending_logs
  ```

### 사용 시나리오

#### 시나리오 1: Alert 발생 시 대응

1. **Total Active Alerts** 게이지에서 Alert 발생 감지
2. **Alerts by Severity**에서 심각도 확인
3. **Active Alerts Details** 테이블에서 상세 정보 확인
4. 해당 Alert의 트리거 조건 (Error Rate, Latency 등) 그래프 확인
5. 근본 원인 파악 및 조치

#### 시나리오 2: Alert Flapping 감지

1. **Alert Frequency (Last Hour)** 그래프에서 빈번한 변화 확인
2. **Currently Firing Alerts** 그래프에서 반복 패턴 확인
3. Alert 임계값 조정 또는 `for` 값 증가 고려

#### 시나리오 3: 서비스 상태 점검

1. **Alerts by Service** 파이 차트에서 문제 서비스 식별
2. 해당 서비스의 메트릭 (에러율, 레이턴시) 확인
3. 필요 시 서비스 재시작 또는 스케일링

---

## 📈 Advanced Analytics Dashboard

### 개요

LLM 시스템의 성능, 품질, 비용을 심층 분석하는 대시보드입니다. 모델 간 비교, 트렌드 분석, 토큰 사용량 추적 등의 기능을 제공합니다.

### 패널 구성 (총 11개)

#### 1. Quality Score Trends (Percentiles) (시계열)
- **위치**: Row 1, 전체
- **크기**: 24 width
- **설명**: 품질 점수의 p50, p95, p99 트렌드
- **PromQL**:
  ```promql
  # p50 (Median)
  histogram_quantile(0.50, sum(rate(evaluation_score_bucket[10m])) by (le))

  # p95
  histogram_quantile(0.95, sum(rate(evaluation_score_bucket[10m])) by (le))

  # p99
  histogram_quantile(0.99, sum(rate(evaluation_score_bucket[10m])) by (le))
  ```
- **용도**: 품질 변화 추세 파악, 이상 감지

#### 2. Request Rate by Model (시계열)
- **위치**: Row 2, 좌측
- **크기**: 12 width
- **단위**: requests per second (reqps)
- **설명**: 모델별 요청률
- **PromQL**:
  ```promql
  rate(llm_requests_total[5m]) by (model)
  ```
- **용도**: 모델 사용 패턴 파악, 부하 분산 확인

#### 3. Latency p95 by Model (시계열)
- **위치**: Row 2, 우측
- **크기**: 12 width
- **단위**: seconds
- **설명**: 모델별 p95 레이턴시
- **PromQL**:
  ```promql
  histogram_quantile(0.95, sum(rate(llm_request_duration_seconds_bucket[5m])) by (le, model))
  ```
- **용도**: 모델 성능 비교, 느린 모델 식별

#### 4. Error Rate by Model (막대 차트)
- **위치**: Row 3, 좌측
- **크기**: 12 width
- **단위**: percent
- **설명**: 모델별 에러율
- **PromQL**:
  ```promql
  rate(llm_requests_total{status="error"}[5m]) * 100 / rate(llm_requests_total[5m]) by (model)
  ```
- **용도**: 불안정한 모델 식별

#### 5. Success Rate by Model (시계열)
- **위치**: Row 3, 우측
- **크기**: 12 width
- **설명**: 모델별 성공률 (%)
- **PromQL**:
  ```promql
  sum(rate(llm_requests_total{status="success"}[5m])) by (model) / sum(rate(llm_requests_total[5m])) by (model) * 100
  ```
- **용도**: 모델 안정성 비교

#### 6. Model Performance Comparison (테이블)
- **위치**: Row 4, 전체
- **크기**: 24 width
- **설명**: 모델별 종합 성능 비교 테이블
- **컬럼**:
  - Model: 모델 이름
  - Requests/sec: 초당 요청 수
  - Latency p95 (s): p95 레이턴시
  - Error Rate %: 에러율 (색상 표시: 초록 < 2% < 노랑 < 5% < 빨강)
- **용도**: 한눈에 모델 성능 비교, 최적 모델 선택

#### 7. Request Volume by Model (Last Hour) (막대 그래프)
- **위치**: Row 5, 좌측
- **크기**: 12 width
- **설명**: 지난 1시간 동안 모델별 총 요청 수
- **PromQL**:
  ```promql
  sum(increase(llm_requests_total[1h])) by (model)
  ```
- **용도**: 모델 사용량 파악

#### 8. Request Distribution by Model (24h) (도넛 차트)
- **위치**: Row 5, 우측
- **크기**: 12 width
- **설명**: 지난 24시간 동안 모델별 요청 분포 (백분율)
- **PromQL**:
  ```promql
  sum(increase(llm_requests_total[24h])) by (model)
  ```
- **용도**: 모델 사용 비율 시각화

#### 9. Quality Score Moving Averages (시계열)
- **위치**: Row 6, 전체
- **크기**: 24 width
- **설명**: 1시간, 6시간, 24시간 이동 평균
- **색상**: 연속 그라데이션 (초록 → 노랑 → 빨강)
- **PromQL**:
  ```promql
  # 1h Moving Average
  avg_over_time((histogram_quantile(0.50, sum(rate(evaluation_score_bucket[10m])) by (le)))[1h:5m])

  # 6h Moving Average
  avg_over_time((histogram_quantile(0.50, sum(rate(evaluation_score_bucket[10m])) by (le)))[6h:5m])

  # 24h Moving Average
  avg_over_time((histogram_quantile(0.50, sum(rate(evaluation_score_bucket[10m])) by (le)))[24h:5m])
  ```
- **용도**: 단기/장기 품질 트렌드 비교, 노이즈 제거

#### 10. Token Usage Rate by Model (시계열)
- **위치**: Row 7, 좌측
- **크기**: 12 width
- **단위**: tokens
- **설명**: 모델별 초당 토큰 사용률
- **PromQL**:
  ```promql
  rate(llm_gateway_token_usage_total[5m]) by (model)
  ```
- **용도**: 비용 추적, 토큰 사용량 모니터링

#### 11. Evaluation vs Request Rate (시계열)
- **위치**: Row 7, 우측
- **크기**: 12 width
- **단위**: eval/requests per second
- **설명**: 평가율과 요청율 비교
- **PromQL**:
  ```promql
  # Evaluation Rate
  rate(evaluations_total[5m])

  # LLM Request Rate
  rate(llm_requests_total[5m])
  ```
- **용도**: 평가 지연 감지, Pending logs 증가 원인 파악

### 사용 시나리오

#### 시나리오 1: 모델 성능 비교 및 선택

1. **Model Performance Comparison** 테이블에서 종합 성능 확인
2. **Latency p95 by Model** 그래프에서 응답 속도 비교
3. **Error Rate by Model** 그래프에서 안정성 확인
4. **Token Usage Rate by Model**에서 비용 효율성 확인
5. 성능, 안정성, 비용을 종합하여 최적 모델 선택

#### 시나리오 2: 품질 저하 원인 분석

1. **Quality Score Trends** 그래프에서 품질 하락 시점 확인
2. **Quality Score Moving Averages**에서 단기/장기 트렌드 비교
3. 동일 시간대의 **Request Rate by Model**에서 부하 변화 확인
4. **Evaluation vs Request Rate**에서 평가 지연 여부 확인
5. 근본 원인 파악 (부하 증가, 특정 모델 문제, 평가 시스템 문제 등)

#### 시나리오 3: 비용 최적화

1. **Token Usage Rate by Model**에서 고비용 모델 식별
2. **Request Distribution by Model (24h)**에서 모델 사용 비율 확인
3. **Model Performance Comparison**에서 저비용 대체 모델 검토
4. 품질 저하 없이 비용 효율적인 모델로 트래픽 이동 계획

#### 시나리오 4: 시간대별 패턴 분석

1. **Request Rate by Model** 그래프를 24시간 범위로 설정
2. 피크 시간대, 한가한 시간대 파악
3. **Quality Score Trends**와 비교하여 부하와 품질 상관관계 확인
4. 피크 타임 대비 리소스 계획 수립

---

## 🔧 대시보드 커스터마이징

### 시간 범위 변경

- **Alert History Dashboard**: 기본 6시간 (`now-6h` to `now`)
- **Advanced Analytics Dashboard**: 기본 24시간 (`now-24h` to `now`)

우측 상단 시간 선택기에서 변경 가능:
- Last 1 hour
- Last 6 hours
- Last 24 hours
- Last 7 days
- Last 30 days
- Custom range

### 자동 새로고침 설정

기본값: 30초 (`refresh: "30s"`)

우측 상단 새로고침 아이콘에서 변경 가능:
- Off
- 10s
- 30s (기본값)
- 1m
- 5m

### 패널 추가/수정

1. 대시보드 우측 상단 "Settings" (톱니바퀴) 클릭
2. "JSON Model" 탭에서 JSON 편집
3. 또는 "Add panel" 버튼으로 UI에서 패널 추가

### 변수 (Variables) 추가

모델명을 변수로 만들어 필터링:

```json
{
  "templating": {
    "list": [
      {
        "name": "model",
        "type": "query",
        "datasource": "prometheus",
        "query": "label_values(llm_requests_total, model)",
        "multi": true,
        "includeAll": true
      }
    ]
  }
}
```

---

## 📊 메트릭 요구사항

### Alert History Dashboard

필수 메트릭:
- `ALERTS{alertstate, severity, service, alertname}` - Prometheus Alert 메트릭
- `http_requests_total{status}` - HTTP 요청 메트릭
- `llm_requests_total{status}` - LLM 요청 메트릭
- `http_request_duration_seconds_bucket` - HTTP 레이턴시 히스토그램
- `llm_request_duration_seconds_bucket` - LLM 레이턴시 히스토그램
- `evaluation_score_bucket` - 평가 점수 히스토그램
- `scheduler_pending_logs` - Pending logs 게이지

### Advanced Analytics Dashboard

필수 메트릭:
- `evaluation_score_bucket` - 평가 점수 히스토그램
- `llm_requests_total{model, status}` - 모델별 LLM 요청 메트릭
- `llm_request_duration_seconds_bucket{model}` - 모델별 레이턴시 히스토그램
- `llm_gateway_token_usage_total{model}` - 모델별 토큰 사용량
- `evaluations_total` - 평가 카운터

---

## 🚀 빠른 시작

### 1. 대시보드 확인

Grafana UI 접속 후:
1. http://localhost:3001 열기 (기본 계정: admin/admin)
2. 좌측 메뉴에서 "Dashboards" 클릭
3. "LLM Quality Observer" 폴더에서 대시보드 선택:
   - Alert History & Monitoring
   - Advanced Analytics Dashboard
   - LLM Quality Observer (기존)

### 2. 즐겨찾기 설정

자주 사용하는 대시보드:
1. 대시보드 열기
2. 우측 상단 별 아이콘 클릭
3. 홈 화면에서 "Starred" 섹션에 표시됨

### 3. 알림 설정

특정 패널에 알림 추가:
1. 패널 제목 클릭 → "Edit"
2. "Alert" 탭 클릭
3. "Create alert rule from this panel"
4. 조건 및 알림 채널 설정

---

## 🔍 문제 해결

### 대시보드가 표시되지 않음

**원인**: Provisioning 실패 또는 권한 문제

**해결**:
```bash
# Grafana 로그 확인
docker logs llm-grafana

# 대시보드 파일 권한 확인
ls -la /home/sdhcokr/project/LLM-Quality-Observer/infra/grafana/dashboards/

# Grafana 재시작
docker compose -f docker-compose.local.yml restart grafana
```

### "No Data" 표시됨

**원인 1**: Prometheus가 메트릭을 수집하지 못함

**해결**:
```bash
# Prometheus targets 확인
curl http://localhost:9090/api/v1/targets

# 서비스가 실행 중인지 확인
docker ps | grep -E "gateway-api|evaluator"
```

**원인 2**: 아직 데이터가 생성되지 않음

**해결**:
- Gateway API에 요청 전송
- Evaluator가 평가 실행
- 5-10분 대기 후 다시 확인

### 패널이 깨져 보임

**원인**: Grafana 버전 호환성 문제

**해결**:
- Grafana 10.0.0 이상 사용 권장
- 대시보드 JSON에서 `schemaVersion: 38` 확인

---

## 📚 추가 자료

- [Grafana 공식 문서](https://grafana.com/docs/grafana/latest/)
- [Prometheus Query 가이드](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL 함수 레퍼런스](https://prometheus.io/docs/prometheus/latest/querying/functions/)

---

**작성일**: 2025-12-26
**버전**: v0.6.0
**대상 Grafana 버전**: 10.0.0+
