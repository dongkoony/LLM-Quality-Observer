# Grafana Dashboard Guide

## LLM Quality Observer Grafana Dashboard Overview

  ![LLM Quality Observer Dashboard](../../images/dashboard-overview.png)

The LLM Quality Observer Grafana dashboard consists of 14 visualization panels that provide real-time monitoring of system performance, quality metrics, and notification status.

**Dashboard Access:**
- URL: http://localhost:3001
- Default Login: admin / admin
- Path: Dashboards → LLM Quality Observer

---

## Dashboard Structure

### 1️⃣ Overview Stats

The top 4 stat panels provide a quick snapshot of the current system state.

#### HTTP Request Rate (req/s)
- **Purpose**: HTTP requests per second received by Gateway API
- **PromQL**: `sum(rate(llm_gateway_http_requests_total[5m]))`
- **Meaning**:
  - Measures incoming traffic volume
  - Calculates average request rate over the last 5 minutes
- **Normal Value**: Varies by usage pattern (low in test environments)
- **No Data Cause**: No requests to Gateway API yet
- **Solution**: Send test request to `/chat` endpoint

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "user_id": "test"}'
```

#### Evaluation Rate (eval/s)
- **Purpose**: Evaluations per second performed by Evaluator service
- **PromQL**: `sum(rate(llm_evaluator_evaluations_total[5m]))`
- **Meaning**:
  - Measures how fast logs are being evaluated
  - Includes both scheduled batch evaluations and manual evaluations
- **Normal Value**: Depends on scheduler configuration
- **No Data Cause**: No evaluations executed yet
- **Solution**: Trigger manual evaluation

```bash
curl -X POST "http://localhost:18001/evaluate-once?limit=5"
```

#### Pending Logs
- **Purpose**: Number of logs not yet evaluated
- **PromQL**: `llm_evaluator_pending_logs`
- **Meaning**:
  - Current count of logs waiting for evaluation (Gauge metric)
  - Continuously increasing value indicates slow evaluation speed
- **Normal Value**:
  - Close to 0 (all logs evaluated)
  - Periodically decreases when scheduler is active
- **No Data Cause**: Evaluator service hasn't updated metrics yet
- **Solution**: Running evaluation once will create the metric

#### Notification Rate (notif/s)
- **Purpose**: Notifications sent per second (Slack, Discord, Email)
- **PromQL**: `sum(rate(llm_evaluator_notifications_sent_total[5m]))`
- **Meaning**:
  - How frequently quality issues or batch completion notifications occur
  - Total count across all channels
- **Normal Value**: Only increases when low-quality logs exist
- **No Data Cause**:
  - No notifications sent yet
  - No scores below `NOTIFICATION_SCORE_THRESHOLD`
- **Solution**: Generate low-quality responses to trigger notifications

---

### 2️⃣ HTTP & LLM Performance

Monitor API response performance and LLM call latency.

#### HTTP Requests by Endpoint
- **Purpose**: Time series distribution of requests by endpoint
- **PromQL**: `sum(rate(llm_gateway_http_requests_total[5m])) by (endpoint)`
- **Meaning**:
  - Identifies which endpoints are most frequently used
  - Separated by `/chat`, `/health`, `/metrics`, etc.
- **Visualization**: Line chart over time
- **Use Cases**:
  - Detect traffic increases to specific endpoints
  - Identify abnormal endpoint call patterns

#### HTTP Request Latency (p50/p95/p99)
- **Purpose**: HTTP request response time percentiles
- **PromQL**:
  ```promql
  histogram_quantile(0.50, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le))  # p50
  histogram_quantile(0.95, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le))  # p95
  histogram_quantile(0.99, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le))  # p99
  ```
- **Meaning**:
  - **p50 (median)**: 50% of requests complete within this time
  - **p95**: 95% of requests complete within this time
  - **p99**: 99% of requests complete within this time
- **Normal Values**:
  - p50: 1-2 seconds (including LLM response time)
  - p95: 3-5 seconds
  - p99: 5-10 seconds
- **Warning**: p99 > 10 seconds indicates potential performance issues
- **No Data Cause**: Insufficient data in histogram buckets

#### LLM Requests by Model
- **Purpose**: LLM API call rate by model
- **PromQL**: `sum(rate(llm_gateway_llm_requests_total[5m])) by (model)`
- **Meaning**:
  - Identifies which LLM models are used most frequently
  - Separated by `gpt-5-mini`, `gpt-4o-mini`, etc.
- **Use Cases**:
  - Track usage by model
  - Analyze model selection for cost optimization

#### LLM Request Latency by Model (p50/p95/p99)
- **Purpose**: LLM API call latency percentiles by model
- **PromQL**:
  ```promql
  histogram_quantile(0.50, sum(rate(llm_gateway_llm_request_duration_seconds_bucket[5m])) by (le, model))
  ```
- **Meaning**:
  - Compare response speed across LLM models
  - Identify performance differences between models
- **Use Cases**:
  - Identify slow models
  - Monitor SLA compliance
- **Note**:
  - gpt-5-mini is typically faster than gpt-4
  - Judge model (gpt-4o-mini) is not tracked here (Evaluator service)

---

### 3️⃣ Quality & Notifications

Track LLM response quality and notification delivery status.

#### Evaluations by Judge Type
- **Purpose**: Evaluation execution rate by evaluation method
- **PromQL**: `sum(rate(llm_evaluator_evaluations_total[5m])) by (judge_type)`
- **Meaning**:
  - Ratio of `rule` (rule-based) vs `llm` (LLM-as-a-Judge)
  - Identifies which evaluation method is used more frequently
- **Configuration**: Controlled by `EVALUATION_JUDGE_TYPE` in `.env.local`
  - `rule`: Fast and cheap, applies simple rules
  - `llm`: Slower and costs money, complex quality evaluation
- **Use Case**: Analyze cost vs accuracy tradeoff

#### Overall Score Distribution (p50/p95)
- **Purpose**: Median and 95th percentile of evaluation scores
- **PromQL**:
  ```promql
  histogram_quantile(0.50, sum(rate(llm_evaluator_evaluation_scores_bucket{score_type="overall"}[5m])) by (le))  # p50
  histogram_quantile(0.95, sum(rate(llm_evaluator_evaluation_scores_bucket{score_type="overall"}[5m])) by (le))  # p95
  ```
- **Meaning**:
  - **p50**: Median evaluation score (quality of most responses)
  - **p95**: Top 95% score (benchmark for excellent responses)
- **Score Range**: 1-5 points
  - 1-2 points: Critical (severe quality issues)
  - 3 points: Warning (needs improvement)
  - 4-5 points: Good
- **Goal**: Maintain p50 at 4 or above
- **No Data Cause**:
  - Evaluation scores not recorded as histograms
  - Insufficient number of evaluations

#### Notifications by Channel
- **Purpose**: Notification delivery success rate by channel over time
- **PromQL**: `sum(rate(llm_evaluator_notifications_sent_total[5m])) by (channel, status)`
- **Meaning**:
  - Track success/failure for Slack, Discord, Email separately
  - Verify notification infrastructure health
- **Channels**:
  - `slack`: Slack webhook
  - `discord`: Discord webhook
  - `email`: SMTP email
- **Status**:
  - `success`: Delivery successful
  - `error`: Delivery failed
- **Warning**: High error rate for specific channel requires configuration check

#### Low Quality Alerts
- **Purpose**: Frequency of low-quality alerts
- **PromQL**: `sum(rate(llm_evaluator_low_quality_alerts_total[5m])) by (judge_type)`
- **Meaning**:
  - How often scores below `NOTIFICATION_SCORE_THRESHOLD` occur
  - Monitor severity of quality issues
- **Goal**: Lower is better
- **Use Cases**:
  - Early detection of quality degradation trends
  - Measure effectiveness after prompt or model changes
- **No Data Cause**: No low-quality responses (good sign!)

---

### 4️⃣ System Health

Monitor scheduler and batch evaluation system operation status.

#### Scheduler Runs
- **Purpose**: Automated evaluation scheduler execution rate
- **PromQL**: `sum(rate(llm_evaluator_scheduler_runs_total[5m]))`
- **Meaning**:
  - Verify scheduler is operating normally
  - Monitor execution at configured intervals
- **Configuration**: `EVALUATION_INTERVAL_MINUTES` in `.env.local`
  - Default: 60 minutes (runs every hour)
- **Normal Value**:
  - For 60-minute interval: 1 run/hour = 0.000277 runs/s
  - Graph increases in step pattern
- **Warning**: Value stops increasing = scheduler stopped
- **Verification**:
  ```bash
  docker logs llm-evaluator | grep "Scheduler"
  ```

#### Batch Evaluation - Logs Processed
- **Purpose**: Cumulative count of logs processed by batch evaluation
- **PromQL**: `sum(llm_evaluator_batch_logs_processed_total)`
- **Meaning**:
  - Track total number of logs evaluated by scheduler
  - Monitor system throughput
- **Visualization**: Cumulative graph (continuously increasing)
- **Configuration**: `EVALUATION_BATCH_SIZE` in `.env.local`
  - Default: 10 (processes 10 at a time)
- **Use Cases**:
  - Optimize batch size
  - Analyze processing speed trends

---

## Troubleshooting No Data

If "No Data" appears in the dashboard, follow these steps:

### 1. Check Prometheus Targets

```bash
# Check target status in Prometheus UI
http://localhost:9090/targets

# Or check via API
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

**Expected Result:**
- `gateway-api`: health = "up"
- `evaluator`: health = "up"

### 2. Check Metrics Endpoints

```bash
# Check Gateway API metrics
curl http://localhost:18000/metrics | grep llm_gateway

# Check Evaluator metrics
curl http://localhost:18001/metrics | grep llm_evaluator
```

If metrics are missing, restart services:
```bash
docker compose -f docker-compose.local.yml restart gateway-api evaluator
```

### 3. Generate Data

Some metrics require activity to generate data:

```bash
# 1. Send request to Gateway API
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt", "user_id": "test-user"}'

# 2. Run evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=5"

# 3. Wait 5-10 minutes and refresh Grafana
```

### 4. Adjust Time Range

Adjust time range in top-right corner of Grafana dashboard:
- Default: Last 1 hour
- If no data: Change to Last 6 hours or Last 24 hours

### 5. Test PromQL Queries

Execute queries directly in Prometheus UI:

```bash
# Prometheus Graph page
http://localhost:9090/graph

# Example queries:
llm_gateway_http_requests_total
llm_evaluator_evaluations_total
llm_evaluator_pending_logs
```

---

## PromQL Query Explanations

### rate() Function
```promql
rate(llm_gateway_http_requests_total[5m])
```
- **Meaning**: Per-second rate of increase over last 5 minutes
- **Usage**: Convert Counter metrics to rates
- **Unit**: Per second

### histogram_quantile() Function
```promql
histogram_quantile(0.95, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le))
```
- **Meaning**: Calculate 95th percentile from histogram
- **le**: less than or equal (bucket upper bound)
- **Usage**: Latency and score distribution analysis

### sum() by (label)
```promql
sum(rate(llm_gateway_http_requests_total[5m])) by (endpoint)
```
- **Meaning**: Calculate sum grouped by label
- **Usage**: Separate by endpoint, model, channel

---

## Usage Tips

### 1. Detect Performance Issues
- **HTTP Request Latency p99** > 10 seconds: Performance degradation
- **LLM Request Latency p95** > 5 seconds: LLM API delay

Response:
```bash
# Check slow request logs
docker logs llm-gateway-api | grep "latency"

# Check database query performance (can add db_query_duration metric)
```

### 2. Track Quality Degradation
- **Overall Score p50** < 3: Quality issues occurring
- **Low Quality Alerts** spike: Requires immediate investigation

Response:
```bash
# Check recent low-score logs
docker exec -it llm-postgres psql -U llm_user -d llm_quality -c \
  "SELECT l.id, l.prompt, l.response, e.overall_score
   FROM llm_logs l
   JOIN llm_evaluations e ON l.id = e.log_id
   WHERE e.overall_score <= 3
   ORDER BY l.created_at DESC
   LIMIT 5;"
```

### 3. Notification System Health
- **Notifications by Channel** - error rate > 10%: Check configuration

Response:
```bash
# Check notification errors in Evaluator logs
docker logs llm-evaluator | grep -i "notification.*fail"

# Check SMTP configuration
docker logs llm-evaluator | grep -i "smtp"
```

### 4. Monitor Scheduler
- **Scheduler Runs** stops increasing: Scheduler stopped

Response:
```bash
# Check scheduler logs
docker logs llm-evaluator | grep "Scheduler\|APScheduler"

# Restart Evaluator
docker compose -f docker-compose.local.yml restart evaluator
```

### 5. Pending Logs Accumulation
- **Pending Logs** continuously increasing: Evaluation speed < Log creation speed

Response:
```bash
# Increase batch size (.env.local)
EVALUATION_BATCH_SIZE=20  # Increase from 10

# Reduce evaluation interval
EVALUATION_INTERVAL_MINUTES=30  # Reduce from 60

# Restart
docker compose -f docker-compose.local.yml restart evaluator
```

---

## Dashboard Customization

### Adding Panels

1. Click "Add panel" in Grafana UI
2. Enter PromQL query
3. Select visualization type (Stat, Time series, Gauge, etc.)
4. Save

### Useful Additional Panel Examples

#### Error Rate Percentage
```promql
(sum(rate(llm_gateway_http_requests_total{status=~"5.."}[5m])) /
 sum(rate(llm_gateway_http_requests_total[5m]))) * 100
```

#### Score Comparison by Evaluation Type
```promql
histogram_quantile(0.50, sum(rate(llm_evaluator_evaluation_scores_bucket{score_type="instruction_following"}[5m])) by (le))
```

#### Error Rate by Model
```promql
sum(rate(llm_gateway_llm_requests_total{status="error"}[5m])) by (model)
```

---

## Alert Rules (Coming in Future Release)

Prometheus Alertmanager integration planned for v0.6.0:

```yaml
# Example: High HTTP error rate alert
- alert: HighHTTPErrorRate
  expr: |
    (sum(rate(llm_gateway_http_requests_total{status=~"5.."}[5m])) /
     sum(rate(llm_gateway_http_requests_total[5m]))) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "HTTP error rate exceeds 5%"
```

---

## Troubleshooting

### Grafana Cannot Connect to Prometheus

**Symptom**: "Post http://localhost:9090/api/v1/query_range: connection refused"

**Solution**:
1. Check Datasource configuration
   - Settings → Data Sources → Prometheus
   - Verify URL is `http://prometheus:9090` (not localhost!)

2. Check Prometheus container status
   ```bash
   docker ps | grep prometheus
   docker logs llm-prometheus
   ```

3. Check Docker network
   ```bash
   docker network inspect docker_default
   # gateway-api, evaluator, prometheus, grafana must be on same network
   ```

### Dashboard Not Auto-Loading

**Solution**:
```bash
# Check Grafana provisioning logs
docker logs llm-grafana | grep provision

# Check permissions
ls -la /home/sdhcokr/project/LLM-Quality-Observer/infra/grafana/

# Fix permissions if needed
chmod -R 755 /home/sdhcokr/project/LLM-Quality-Observer/infra/grafana/
```

---

## References

- [Prometheus Configuration Guide](../prometheus/README.md)
- [Metrics Reference](../../docs/METRICS.md)
- [Release Notes v0.5.0](../../docs/RELEASE_NOTES_v0.5.0.md)
- [Grafana Official Documentation](https://grafana.com/docs/)
- [PromQL Query Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**Last Updated**: 2025-12-23
**Dashboard Version**: v0.5.0
