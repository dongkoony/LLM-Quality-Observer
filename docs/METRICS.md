# Metrics Reference Guide

This document provides a comprehensive reference for all Prometheus metrics exposed by the LLM Quality Observer system.

## Table of Contents

- [Gateway API Metrics](#gateway-api-metrics)
- [Evaluator Service Metrics](#evaluator-service-metrics)
- [Common Labels](#common-labels)
- [Example Queries](#example-queries)

---

## Gateway API Metrics

All Gateway API metrics are prefixed with `llm_gateway_`.

### HTTP Request Metrics

#### `llm_gateway_http_requests_total`
- **Type:** Counter
- **Description:** Total number of HTTP requests received
- **Labels:**
  - `method`: HTTP method (GET, POST, etc.)
  - `endpoint`: Request endpoint (/chat, /health, /metrics)
  - `status`: HTTP status code (200, 400, 500, etc.)

#### `llm_gateway_http_request_duration_seconds`
- **Type:** Histogram
- **Description:** HTTP request latency in seconds
- **Labels:**
  - `method`: HTTP method
  - `endpoint`: Request endpoint
- **Buckets:** 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0

#### `llm_gateway_active_requests`
- **Type:** Gauge
- **Description:** Number of currently active HTTP requests

### LLM Request Metrics

#### `llm_gateway_llm_requests_total`
- **Type:** Counter
- **Description:** Total number of LLM API calls made
- **Labels:**
  - `model`: LLM model used (gpt-5-mini, etc.)
  - `status`: Request status (success, error)

#### `llm_gateway_llm_request_duration_seconds`
- **Type:** Histogram
- **Description:** LLM API call latency in seconds
- **Labels:**
  - `model`: LLM model used
- **Buckets:** 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0

### Database Metrics

#### `llm_gateway_db_queries_total`
- **Type:** Counter
- **Description:** Total number of database queries executed
- **Labels:**
  - `operation`: Query type (select, insert, update, delete)
  - `table`: Database table name
  - `status`: Query status (success, error)

#### `llm_gateway_db_query_duration_seconds`
- **Type:** Histogram
- **Description:** Database query latency in seconds
- **Labels:**
  - `operation`: Query type
  - `table`: Database table name
- **Buckets:** 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0

#### `llm_gateway_logs_saved_total`
- **Type:** Counter
- **Description:** Total number of log entries saved to database
- **Labels:**
  - `status`: Save status (success, error)

### Application Info

#### `llm_gateway_info`
- **Type:** Info
- **Description:** Gateway API application metadata
- **Labels:**
  - `version`: Application version
  - `environment`: Deployment environment (local, dev, prod)

---

## Evaluator Service Metrics

All Evaluator metrics are prefixed with `llm_evaluator_`.

### Evaluation Metrics

#### `llm_evaluator_evaluations_total`
- **Type:** Counter
- **Description:** Total number of evaluations performed
- **Labels:**
  - `judge_type`: Type of judge used (rule, llm)
  - `status`: Evaluation status (success, error)

#### `llm_evaluator_evaluation_duration_seconds`
- **Type:** Histogram
- **Description:** Time taken to complete an evaluation
- **Labels:**
  - `judge_type`: Type of judge used
- **Buckets:** 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0

#### `llm_evaluator_evaluation_scores`
- **Type:** Histogram
- **Description:** Distribution of evaluation scores
- **Labels:**
  - `judge_type`: Type of judge used
  - `score_type`: Type of score (overall, instruction, truthfulness)
- **Buckets:** 1, 2, 3, 4, 5

### Batch Evaluation Metrics

#### `llm_evaluator_batch_evaluations_total`
- **Type:** Counter
- **Description:** Total number of batch evaluation runs
- **Labels:**
  - `judge_type`: Type of judge used

#### `llm_evaluator_batch_logs_processed`
- **Type:** Counter
- **Description:** Total number of logs processed in batch evaluations
- **Labels:**
  - `judge_type`: Type of judge used

### Notification Metrics

#### `llm_evaluator_notifications_sent_total`
- **Type:** Counter
- **Description:** Total number of notifications sent
- **Labels:**
  - `channel`: Notification channel (slack, discord, email)
  - `type`: Notification type (alert, summary)
  - `status`: Delivery status (success, error)

#### `llm_evaluator_low_quality_alerts_total`
- **Type:** Counter
- **Description:** Total number of low-quality alerts triggered
- **Labels:**
  - `judge_type`: Type of judge that detected low quality

### Scheduler Metrics

#### `llm_evaluator_scheduler_runs_total`
- **Type:** Counter
- **Description:** Total number of scheduler executions
- **Labels:**
  - `status`: Execution status (success, error)

#### `llm_evaluator_pending_logs`
- **Type:** Gauge
- **Description:** Current number of logs pending evaluation

### LLM Judge Metrics

#### `llm_evaluator_llm_judge_requests_total`
- **Type:** Counter
- **Description:** Total number of LLM judge API calls
- **Labels:**
  - `model`: Judge model used
  - `status`: Request status (success, error)

#### `llm_evaluator_llm_judge_request_duration_seconds`
- **Type:** Histogram
- **Description:** LLM judge API call latency
- **Labels:**
  - `model`: Judge model used
- **Buckets:** 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0

### Application Info

#### `llm_evaluator_info`
- **Type:** Info
- **Description:** Evaluator service application metadata
- **Labels:**
  - `version`: Application version
  - `environment`: Deployment environment

---

## Common Labels

### Environment Labels (Added by Prometheus)

All metrics automatically include these labels from Prometheus configuration:
- `service`: Service name (gateway-api, evaluator)
- `environment`: Deployment environment (local, dev, prod)
- `instance`: Container instance ID
- `job`: Prometheus job name

---

## Example Queries

### Performance Monitoring

**Average request latency (p50, p95, p99):**
```promql
# p50
histogram_quantile(0.50, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# p95
histogram_quantile(0.95, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# p99
histogram_quantile(0.99, sum(rate(llm_gateway_http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```

**Request rate per second:**
```promql
sum(rate(llm_gateway_http_requests_total[1m])) by (endpoint)
```

**Error rate percentage:**
```promql
(sum(rate(llm_gateway_http_requests_total{status=~"5.."}[5m])) /
 sum(rate(llm_gateway_http_requests_total[5m]))) * 100
```

### LLM Performance

**Average LLM latency by model:**
```promql
rate(llm_gateway_llm_request_duration_seconds_sum[5m]) /
rate(llm_gateway_llm_request_duration_seconds_count[5m])
```

**LLM error rate:**
```promql
sum(rate(llm_gateway_llm_requests_total{status="error"}[5m])) by (model)
```

**LLM requests per minute:**
```promql
sum(rate(llm_gateway_llm_requests_total[1m])) by (model) * 60
```

### Evaluation Quality

**Average score by judge type:**
```promql
sum(rate(llm_evaluator_evaluation_scores_sum{score_type="overall"}[5m])) by (judge_type) /
sum(rate(llm_evaluator_evaluation_scores_count{score_type="overall"}[5m])) by (judge_type)
```

**Low quality alert rate:**
```promql
sum(rate(llm_evaluator_low_quality_alerts_total[5m])) by (judge_type)
```

**Evaluation throughput:**
```promql
sum(rate(llm_evaluator_evaluations_total[5m])) by (judge_type)
```

### System Health

**Pending logs trend:**
```promql
llm_evaluator_pending_logs
```

**Scheduler success rate:**
```promql
sum(rate(llm_evaluator_scheduler_runs_total{status="success"}[5m])) /
sum(rate(llm_evaluator_scheduler_runs_total[5m]))
```

**Notification delivery rate:**
```promql
sum(rate(llm_evaluator_notifications_sent_total{status="success"}[5m])) by (channel) /
sum(rate(llm_evaluator_notifications_sent_total[5m])) by (channel)
```

### Resource Utilization

**Active requests gauge:**
```promql
llm_gateway_active_requests
```

**Database query rate:**
```promql
sum(rate(llm_gateway_db_queries_total[5m])) by (operation, table)
```

**Batch processing rate:**
```promql
sum(rate(llm_evaluator_batch_logs_processed[5m])) by (judge_type)
```

### Alerting Rules Examples

**High error rate alert:**
```yaml
- alert: HighErrorRate
  expr: |
    (sum(rate(llm_gateway_http_requests_total{status=~"5.."}[5m])) /
     sum(rate(llm_gateway_http_requests_total[5m]))) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

**High LLM latency alert:**
```yaml
- alert: HighLLMLatency
  expr: |
    histogram_quantile(0.95,
      sum(rate(llm_gateway_llm_request_duration_seconds_bucket[5m])) by (le, model)
    ) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High LLM latency detected"
    description: "p95 latency is {{ $value }}s for model {{ $labels.model }}"
```

**Growing backlog alert:**
```yaml
- alert: GrowingEvaluationBacklog
  expr: |
    llm_evaluator_pending_logs > 100
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Evaluation backlog is growing"
    description: "{{ $value }} logs pending evaluation"
```

---

## Best Practices

1. **Use rate() for counters:** Always use `rate()` function with counters to get per-second rates
2. **Appropriate time ranges:** Use longer time ranges (5m-15m) for alerts to avoid flapping
3. **Label cardinality:** Be mindful of label combinations - avoid high-cardinality labels like user_id
4. **Histogram buckets:** Current buckets cover common latency ranges, adjust if your use case differs
5. **Recording rules:** Consider creating recording rules for frequently used complex queries
6. **Retention:** Default Prometheus retention is 15 days - adjust based on your needs

---

## Troubleshooting

**Metrics not appearing:**
1. Check service is running: `docker compose ps`
2. Verify metrics endpoint: `curl http://localhost:18000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Review Prometheus logs: `docker compose logs prometheus`

**Incorrect values:**
1. Verify time range in queries
2. Check label filters are correct
3. Ensure rate() is used with counters
4. Validate histogram_quantile() syntax

**Performance issues:**
1. Reduce query time range
2. Add more specific label filters
3. Use recording rules for complex queries
4. Increase Prometheus resources if needed

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Templating](https://grafana.com/docs/grafana/latest/dashboards/variables/)
