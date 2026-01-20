# Prometheus Alert Rules 가이드

이 디렉토리는 Prometheus Alert Rules를 포함합니다.

## 📁 파일 구조

```
infra/prometheus/alerts/
├── http_alerts.yml         # HTTP 관련 알림 규칙
├── llm_alerts.yml          # LLM 관련 알림 규칙
├── evaluation_alerts.yml   # 평가 관련 알림 규칙
├── system_alerts.yml       # 시스템 관련 알림 규칙
└── README.md               # 이 파일
```

## 🚨 Alert Rules 개요

### HTTP Alerts (`http_alerts.yml`)

| Alert 이름 | Severity | 조건 | 설명 |
|-----------|----------|------|------|
| `HighHTTPErrorRate` | critical | 5xx 에러율 > 5% | HTTP 5xx 에러율이 높음 |
| `ModerateHTTPErrorRate` | warning | 5xx 에러율 > 2% | HTTP 5xx 에러율이 중간 수준 |
| `HighHTTPLatency` | warning | p95 레이턴시 > 5s | HTTP 요청 레이턴시가 높음 |
| `VeryHighHTTPLatency` | critical | p95 레이턴시 > 10s | HTTP 요청 레이턴시가 매우 높음 |
| `HighHTTP4xxRate` | warning | 4xx 에러율 > 10% | HTTP 4xx 에러율이 높음 |
| `HTTPRequestRateSpike` | warning | 요청률 3배 증가 | HTTP 요청 급증 감지 |
| `NoHTTPRequests` | critical | 5분간 요청 0 | HTTP 요청이 없음 (서비스 다운 가능성) |

### LLM Alerts (`llm_alerts.yml`)

| Alert 이름 | Severity | 조건 | 설명 |
|-----------|----------|------|------|
| `HighLLMErrorRate` | critical | LLM 에러율 > 5% | LLM 요청 에러율이 높음 |
| `ModerateLLMErrorRate` | warning | LLM 에러율 > 2% | LLM 요청 에러율이 중간 수준 |
| `HighLLMLatency` | warning | p95 레이턴시 > 10s | LLM 요청 레이턴시가 높음 |
| `VeryHighLLMLatency` | critical | p95 레이턴시 > 30s | LLM 요청 레이턴시가 매우 높음 |
| `LLMRequestRateDrop` | warning | 요청률 50% 감소 | LLM 요청률 급감 |
| `NoLLMRequests` | warning | 10분간 요청 0 | LLM 요청이 없음 |
| `HighTokenUsage` | warning | 토큰 사용률 > 100k/s | 토큰 사용률이 높음 (비용 주의) |
| `ModelHighErrorRate` | warning | 모델별 에러율 > 10% | 특정 모델의 에러율이 높음 |

### Evaluation Alerts (`evaluation_alerts.yml`)

| Alert 이름 | Severity | 조건 | 설명 |
|-----------|----------|------|------|
| `LowEvaluationScore` | critical | p50 점수 < 3 | 평가 점수 중앙값이 낮음 |
| `VeryLowEvaluationScore` | critical | p50 점수 < 2 | 평가 점수 중앙값이 매우 낮음 |
| `EvaluationScoreDrop` | warning | 점수 20% 하락 | 평가 점수가 급락함 |
| `HighPendingLogs` | warning | Pending logs > 100 | 대기 중인 로그가 많음 |
| `VeryHighPendingLogs` | critical | Pending logs > 500 | 대기 중인 로그가 매우 많음 |
| `EvaluationRateDrop` | warning | 평가율 < 0.01/s | 평가 처리율이 낮음 |
| `NoEvaluationsRunning` | critical | 10분간 평가 0 | 평가가 실행되지 않음 (서비스 다운 가능성) |
| `HighEvaluationErrorRate` | warning | 평가 에러율 > 5% | 평가 에러율이 높음 |
| `SchedulerNotRunning` | critical | 스케줄러 2시간 미실행 | 평가 스케줄러가 작동하지 않음 |
| `HighEvaluationLatency` | warning | p95 레이턴시 > 30s | 평가 레이턴시가 높음 |
| `HighLowQualityRate` | warning | 저품질 알림 > 0.1/s | 저품질 알림이 빈번함 |
| `JudgeTypeHighErrorRate` | warning | Judge 타입별 에러율 > 10% | 특정 Judge 타입의 에러율이 높음 |

### System Alerts (`system_alerts.yml`)

| Alert 이름 | Severity | 조건 | 설명 |
|-----------|----------|------|------|
| `HighDatabaseLatency` | warning | DB p95 레이턴시 > 1s | 데이터베이스 쿼리 레이턴시가 높음 |
| `VeryHighDatabaseLatency` | critical | DB p95 레이턴시 > 5s | 데이터베이스 쿼리 레이턴시가 매우 높음 |
| `DatabaseConnectionErrors` | critical | DB 연결 에러 발생 | 데이터베이스 연결 에러 |
| `SlackNotificationFailures` | warning | Slack 전송 실패율 > 10% | Slack 알림 전송 실패율이 높음 |
| `DiscordNotificationFailures` | warning | Discord 전송 실패율 > 10% | Discord 알림 전송 실패율이 높음 |
| `EmailNotificationFailures` | warning | Email 전송 실패율 > 10% | Email 알림 전송 실패율이 높음 |
| `GatewayAPIDown` | critical | Gateway API 다운 | Gateway API 서비스가 다운됨 |
| `EvaluatorDown` | critical | Evaluator 다운 | Evaluator 서비스가 다운됨 |
| `DashboardDown` | warning | Dashboard 다운 | Dashboard 서비스가 다운됨 |
| `MetricsScrapeFailures` | warning | 메트릭 수집 실패 | Prometheus가 메트릭을 수집할 수 없음 |
| `HighMemoryUsage` | warning | 메모리 사용량 > 2GB | 서비스의 메모리 사용량이 높음 |
| `ServiceRestarted` | info | 서비스 재시작 감지 | 서비스가 최근 재시작됨 |
| `PrometheusStorageNearlyFull` | warning | Prometheus 스토리지 > 90% | Prometheus 스토리지가 거의 가득 참 |
| `SlowBatchProcessing` | warning | 배치 처리 > 300s | 배치 평가 처리가 느림 |
| `LLMJudgeHighErrorRate` | warning | LLM Judge 에러율 > 10% | LLM Judge 요청 에러율이 높음 |

## 📊 Severity 레벨

| Severity | 의미 | 대응 시간 | 알림 채널 |
|----------|------|-----------|-----------|
| **critical** | 즉시 대응 필요 | < 15분 | Slack, Discord, Email |
| **warning** | 주의 필요 | < 1시간 | Slack |
| **info** | 정보성 | 참고용 | 로그만 |

## 🔧 Alert Rules 수정

### 1. 임계값 조정

Alert 임계값을 조정하려면 해당 `.yml` 파일을 수정하세요:

```yaml
# 예: HTTP 에러율 임계값 변경 (5% → 10%)
- alert: HighHTTPErrorRate
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
    ) * 100 > 10  # 5에서 10으로 변경
  for: 2m
```

### 2. 대기 시간 조정

`for` 값을 변경하여 알림 발생 전 대기 시간을 조정:

```yaml
for: 5m  # 5분 동안 조건이 유지되어야 알림 발생
```

### 3. 새 Alert 추가

새로운 Alert를 추가하려면 적절한 파일에 다음 형식으로 추가:

```yaml
- alert: MyNewAlert
  expr: |
    metric_name > threshold
  for: duration
  labels:
    severity: warning|critical|info
    service: service_name
  annotations:
    summary: "Brief description"
    description: "Detailed description with {{ $value }}"
```

### 4. 설정 검증

변경 후 설정을 검증:

```bash
# Prometheus 설정 검증
docker exec llm-prometheus promtool check rules /etc/prometheus/alerts/*.yml

# Prometheus 설정 리로드
curl -X POST http://localhost:9090/-/reload
```

## 🧪 테스트

### 1. Alert Rules 구문 검증

```bash
docker exec llm-prometheus promtool check rules /etc/prometheus/alerts/*.yml
```

### 2. 특정 Alert 쿼리 테스트

Prometheus UI에서 쿼리 테스트:
1. http://localhost:9090 접속
2. Alert 쿼리 입력
3. "Execute" 클릭하여 결과 확인

### 3. Alert 강제 발생 (테스트용)

테스트 메트릭을 생성하여 Alert 발생 확인:

```python
# 예: 높은 에러율 시뮬레이션
# Gateway API에 많은 실패 요청 전송
for i in range(100):
    requests.post('http://localhost:18000/chat',
                  json={'invalid': 'data'})
```

## 📝 PromQL 쿼리 설명

### 에러율 계산

```promql
(
  sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
  sum(rate(http_requests_total[5m]))
) * 100
```

- `rate(...[5m])`: 5분 동안의 초당 평균 증가율
- `sum()`: 모든 레이블의 합계
- `status=~"5.."`: 정규식으로 5xx 상태 코드 매칭
- `* 100`: 백분율로 변환

### 백분위수 (Percentile) 계산

```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

- `histogram_quantile(0.95, ...)`: 95번째 백분위수 (p95)
- `http_request_duration_seconds_bucket`: Histogram 메트릭
- `by (le)`: `le` (less than or equal) 레이블로 그룹화

### 비율 변화 감지

```promql
(
  rate(llm_requests_total[1m])
  /
  avg_over_time(rate(llm_requests_total[1m])[15m:1m])
)
```

- 현재 1분 평균을 15분 평균과 비교
- `> 3`: 3배 증가
- `< 0.5`: 50% 감소

## 🔍 모니터링 대시보드

### Prometheus Alerts UI

http://localhost:9090/alerts

- 모든 Alert 규칙 확인
- 현재 발생 중인 Alert 확인
- Alert 상태 (Pending, Firing, Resolved)

### Alertmanager UI

http://localhost:9093

- 발생한 Alert 확인
- Silence 설정
- Alert 그룹화 확인

### Grafana Dashboards

http://localhost:3001

- Alert History Dashboard (추가 예정)
- 실시간 메트릭 시각화

## 🚀 프로덕션 배포 시 고려사항

### 1. 임계값 튜닝

초기 임계값은 기본값입니다. 프로덕션 환경에서:
- 2-4주 동안 메트릭 수집
- 정상 범위 파악 (p50, p95, p99)
- 임계값을 정상 범위의 120-150%로 설정

### 2. Alert 피로 방지

너무 많은 Alert가 발생하면:
- `repeat_interval` 증가
- 덜 중요한 Alert의 `severity`를 낮춤
- `for` 값을 증가시켜 일시적 현상 무시

### 3. On-call 로테이션

Critical Alert의 경우:
- 24/7 on-call 체제 구축
- Escalation 정책 정의
- Runbook 문서화

## 📚 참고 자료

- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [PromQL Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Alert Best Practices](https://prometheus.io/docs/practices/alerting/)

---

**마지막 업데이트**: 2025-12-26
**버전**: v0.6.0
