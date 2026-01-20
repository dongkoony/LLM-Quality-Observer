# Release Notes - v0.5.0

**Release Date:** 2024-12-22
**Focus:** Monitoring & Observability Enhancement

## Overview

v0.5.0 introduces comprehensive monitoring and observability capabilities through Prometheus metrics collection and Grafana dashboards, along with email notification support. This release enables real-time visibility into system performance, LLM quality metrics, and automated alerting across multiple channels.

---

## 🎯 Key Features

### 1. Prometheus Metrics Integration

Complete metrics instrumentation across all services:

**Gateway API Metrics:**
- HTTP request rate and latency (p50/p95/p99)
- LLM API call rate and latency by model
- Database query performance
- Success/error rates

**Evaluator Service Metrics:**
- Evaluation rate and duration
- Score distribution (overall, instruction-following, truthfulness)
- Batch evaluation statistics
- Scheduler health monitoring
- Pending logs gauge

**Notification Metrics:**
- Notification delivery rates by channel (Slack, Discord, Email)
- Low-quality alert frequency
- Success/failure tracking

### 2. Grafana Dashboards

Pre-configured dashboard with 14 visualization panels:
- **Overview Stats**: Request rate, evaluation rate, pending logs, notification rate
- **HTTP Performance**: Request distribution, latency percentiles
- **LLM Metrics**: Request rates by model, latency analysis
- **Quality Scores**: Score distribution by judge type
- **Notifications**: Delivery rates, alert tracking
- **System Health**: Scheduler runs, batch processing stats

### 3. Email Notification System

SMTP-based email alerting:
- Low-quality alerts with detailed evaluation context
- Batch evaluation summaries
- Multi-recipient support
- HTML and plain text formatting
- Integrated with existing Slack/Discord notifications

---

## 📦 What's New

### New Services

- **Prometheus** (port 9090): Metrics collection and time-series database
- **Grafana** (port 3000): Visualization and dashboarding platform

### New Dependencies

- `prometheus-client>=0.19.0` - Metrics instrumentation library
- `aiosmtplib>=3.0` - Async SMTP client for email notifications
- `email-validator>=2.0` - Email address validation

### New Endpoints

- `GET /metrics` (Gateway API) - Prometheus metrics endpoint
- `GET /metrics` (Evaluator) - Prometheus metrics endpoint

### New Configuration Options

```bash
# Email Notification Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

---

## 🚀 Getting Started

### Starting the Full Stack

```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

This will start:
- Gateway API (port 18000)
- Evaluator Service (port 18001)
- Dashboard Service (port 8501)
- Prometheus (port 9090)
- Grafana (port 3000)
- PostgreSQL (port 5432)

### Accessing Monitoring Tools

**Prometheus:**
```bash
# Access Prometheus UI
http://localhost:9090

# View all metrics
http://localhost:9090/graph

# Check targets
http://localhost:9090/targets
```

**Grafana:**
```bash
# Access Grafana dashboard
http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

The LLM Quality Observer dashboard will be automatically provisioned and available under "Dashboards".

### Viewing Metrics

**Gateway API Metrics:**
```bash
curl http://localhost:18000/metrics
```

**Evaluator Metrics:**
```bash
curl http://localhost:18001/metrics
```

### Configuring Email Notifications

1. Update your `.env.local` file:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=team@example.com,oncall@example.com
```

2. For Gmail, create an App Password:
   - Go to Google Account Settings → Security → 2-Step Verification → App Passwords
   - Generate a new app password for "Mail"
   - Use this password in `SMTP_PASSWORD`

3. Restart the evaluator service:
```bash
docker compose -f docker-compose.local.yml restart evaluator
```

---

## 📊 Metrics Guide

### Key Metrics to Monitor

**Performance:**
- `llm_gateway_http_request_duration_seconds` - API response time
- `llm_gateway_llm_request_duration_seconds` - LLM call latency
- `llm_evaluator_evaluation_duration_seconds` - Evaluation processing time

**Quality:**
- `llm_evaluator_evaluation_scores` - Score distribution
- `llm_evaluator_low_quality_alerts_total` - Alert frequency
- `llm_evaluator_evaluations_total{status="error"}` - Evaluation failures

**System Health:**
- `llm_evaluator_pending_logs` - Evaluation backlog
- `llm_evaluator_scheduler_runs_total` - Scheduler execution rate
- `llm_evaluator_notifications_sent_total` - Notification delivery

### Example PromQL Queries

**Average LLM latency by model (last 5 minutes):**
```promql
rate(llm_gateway_llm_request_duration_seconds_sum[5m]) /
rate(llm_gateway_llm_request_duration_seconds_count[5m])
```

**Error rate percentage:**
```promql
(sum(rate(llm_gateway_http_requests_total{status=~"5.."}[5m])) /
 sum(rate(llm_gateway_http_requests_total[5m]))) * 100
```

**Evaluation backlog trend:**
```promql
llm_evaluator_pending_logs
```

---

## 🔄 Upgrade Guide

### From v0.4.0 to v0.5.0

1. **Update dependencies:**
```bash
# Gateway API
cd services/gateway-api
uv sync

# Evaluator
cd services/evaluator
uv sync
```

2. **Update environment configuration:**
```bash
# Copy new config options from example
cp configs/env/.env.local.example configs/env/.env.local

# Add email settings if needed (optional)
# SMTP_HOST, SMTP_PORT, SMTP_USERNAME, etc.
```

3. **Update Docker Compose:**
```bash
# The docker-compose.local.yml now includes Prometheus and Grafana
# No manual changes needed - just restart
cd infra/docker
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up --build
```

4. **Verify metrics collection:**
```bash
# Check Gateway API metrics
curl http://localhost:18000/metrics | grep llm_gateway

# Check Evaluator metrics
curl http://localhost:18001/metrics | grep llm_evaluator

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

5. **Access Grafana dashboard:**
   - Navigate to http://localhost:3000
   - Login with admin/admin
   - Go to Dashboards → LLM Quality Observer

### Breaking Changes

None. This release is fully backward compatible with v0.4.0.

### New Environment Variables (Optional)

```bash
# Email notifications (all optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient@example.com
```

---

## 📁 File Structure Changes

### New Files

```
infra/
├── prometheus/
│   └── prometheus.yml                    # Prometheus scrape configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml            # Grafana datasource config
│   │   └── dashboards/
│   │       └── default.yml               # Dashboard provisioning config
│   └── dashboards/
│       └── llm-quality-observer.json     # Main dashboard definition

services/
├── gateway-api/
│   └── app/
│       └── metrics.py                    # Gateway metrics definitions
└── evaluator/
    └── app/
        └── metrics.py                    # Evaluator metrics definitions
```

### Modified Files

```
services/
├── gateway-api/
│   ├── pyproject.toml                    # Added prometheus-client
│   └── app/
│       └── main.py                       # Added /metrics endpoint
├── evaluator/
│   ├── pyproject.toml                    # Added prometheus-client, aiosmtplib
│   └── app/
│       ├── config.py                     # Added SMTP config
│       ├── main.py                       # Added /metrics endpoint
│       ├── scheduler.py                  # Added metrics recording
│       └── notifier.py                   # Added email notification

infra/docker/
└── docker-compose.local.yml              # Added Prometheus and Grafana services

configs/env/
└── .env.local.example                    # Added SMTP configuration
```

---

## 🐛 Bug Fixes

- None in this release (feature-focused)

---

## 🔒 Security Notes

- Email passwords should use app-specific passwords, not account passwords
- SMTP credentials are stored in environment variables (not committed to git)
- Grafana default password should be changed in production
- Prometheus metrics do not expose sensitive data (no API keys, passwords, or user data)

---

## 📚 Documentation

- [Prometheus Setup Guide](../infra/prometheus/README.md)
- [Grafana Dashboard Guide](../infra/grafana/README.md)
- [Email Notification Setup](../docs/EMAIL_SETUP.md)
- [Metrics Reference](../docs/METRICS.md)

---

## 🎯 Next Steps (v0.6.0 Preview)

Potential features for next release:
- Advanced alerting rules in Prometheus
- Custom dashboard templates
- Metric retention policies
- Performance optimization dashboard
- A/B testing analytics
- Advanced filtering and search UI

---

## 🤝 Contributors

- Claude Sonnet 4.5 (Implementation)
- sdhcokr (Project Lead)

---

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/llm-quality-observer/issues
- Documentation: https://github.com/your-org/llm-quality-observer/docs

---

**Full Changelog:** v0.4.0...v0.5.0
