# Alertmanager 설정 가이드

이 디렉토리는 Prometheus Alertmanager 설정을 포함합니다.

## 📁 파일 구조

```
infra/alertmanager/
├── alertmanager.yml    # Alertmanager 메인 설정 파일
└── README.md           # 이 파일
```

## 🚀 빠른 시작

### 1. Webhook URL 설정

`alertmanager.yml` 파일에서 다음 플레이스홀더를 실제 값으로 교체하세요:

- `YOUR_SLACK_WEBHOOK_URL_HERE` → 실제 Slack Webhook URL
- `YOUR_DISCORD_WEBHOOK_URL_HERE` → 실제 Discord Webhook URL
- `your-email@gmail.com` → 실제 Gmail 주소
- `YOUR_APP_PASSWORD` → Gmail 앱 비밀번호

### 2. 서비스 시작

```bash
cd infra/docker
docker compose -f docker-compose.local.yml up alertmanager -d
```

### 3. 웹 UI 접속

- Alertmanager UI: http://localhost:9093

## ⚙️ 설정 구성 요소

### Global 설정

```yaml
global:
  resolve_timeout: 5m  # 알림 자동 해제 시간
```

### Route 설정

Alert의 그룹화 및 라우팅 규칙:

| 설정 | 값 | 설명 |
|------|-----|------|
| `group_by` | `['alertname', 'severity', 'service']` | 그룹화 기준 |
| `group_wait` | `10s` | 그룹 대기 시간 |
| `group_interval` | `5m` | 그룹 알림 간격 |
| `repeat_interval` | `3h` | 반복 알림 간격 |

#### 라우팅 규칙

1. **Critical Alerts**:
   - Severity가 `critical`인 경우
   - 모든 채널(Slack, Discord, Email)로 즉시 전송
   - 30분마다 재전송

2. **Warning Alerts**:
   - Severity가 `warning`인 경우
   - 표준 채널로 전송
   - 6시간마다 재전송

3. **HTTP Errors**:
   - `HighHTTPErrorRate` 알림
   - Ops 팀 채널로 전송

4. **Quality Issues**:
   - `LowEvaluationScore`, `EvaluationScoreDrop` 알림
   - Quality 팀 채널로 전송

### Receivers 설정

#### 1. default-receiver
기본 수신자 (로그만 기록)

#### 2. critical-alerts
Critical 레벨 알림 수신자:
- Slack: `#llm-alerts-critical`
- Discord: Webhook
- Email: `alerts@example.com`

#### 3. warning-alerts
Warning 레벨 알림 수신자:
- Slack: `#llm-alerts-warning`

#### 4. ops-team
운영 팀 알림 수신자:
- Slack: `#llm-ops`

#### 5. quality-team
품질 팀 알림 수신자:
- Slack: `#llm-quality`

### Inhibit Rules

중복 알림 방지 규칙:

1. **Critical이 Warning 억제**:
   - 동일한 서비스에서 Critical 알림이 발생하면 Warning 알림 억제

2. **Warning/Critical이 Info 억제**:
   - Warning 또는 Critical 알림이 있으면 Info 알림 억제

## 🔔 Slack 설정

### 1. Slack Webhook URL 생성

1. Slack 워크스페이스에서 [Incoming Webhooks](https://api.slack.com/messaging/webhooks) 앱 설치
2. Webhook URL 생성 (예: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)
3. `alertmanager.yml`에서 `YOUR_SLACK_WEBHOOK_URL_HERE`를 교체

### 2. 채널 생성

다음 Slack 채널을 생성하세요:
- `#llm-alerts-critical` - Critical 알림
- `#llm-alerts-warning` - Warning 알림
- `#llm-ops` - 운영 알림
- `#llm-quality` - 품질 알림

## 💬 Discord 설정

### 1. Discord Webhook URL 생성

1. Discord 서버 설정 → 연동 → Webhooks
2. 새 Webhook 생성
3. Webhook URL 복사 (예: `https://discord.com/api/webhooks/123456789/abcdefg`)
4. `alertmanager.yml`에서 `YOUR_DISCORD_WEBHOOK_URL_HERE`를 교체

## 📧 Email 설정

### Gmail 앱 비밀번호 생성

1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 생성
3. `alertmanager.yml`에서 다음 항목 수정:
   - `auth_username`: Gmail 주소
   - `auth_password`: 앱 비밀번호
   - `to`: 수신자 이메일
   - `from`: 발신자 이메일 (Gmail 주소)

## 🧪 테스트

### 1. 설정 검증

```bash
docker exec llm-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
```

### 2. 테스트 알림 전송

```bash
# Alertmanager API를 통한 테스트 알림
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[
    {
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning",
        "service": "test"
      },
      "annotations": {
        "summary": "This is a test alert",
        "description": "Testing Alertmanager configuration"
      }
    }
  ]'
```

### 3. Silence 설정 (알림 일시 중지)

```bash
# Alertmanager UI에서 설정: http://localhost:9093/#/silences
# 또는 CLI 사용:
docker exec llm-alertmanager amtool silence add \
  alertname=TestAlert \
  --duration=1h \
  --comment="Testing silence"
```

## 📊 모니터링

### Alertmanager 상태 확인

```bash
# 컨테이너 상태
docker ps | grep llm-alertmanager

# 로그 확인
docker logs -f llm-alertmanager

# API 상태
curl http://localhost:9093/api/v1/status
```

### 현재 활성 알림 확인

```bash
curl http://localhost:9093/api/v1/alerts
```

## 🔧 문제 해결

### Alertmanager가 시작되지 않음

```bash
# 설정 파일 구문 확인
docker exec llm-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml

# 로그 확인
docker logs llm-alertmanager
```

### Slack 알림이 전송되지 않음

1. Webhook URL이 올바른지 확인
2. Slack 채널이 존재하는지 확인
3. Alertmanager 로그에서 에러 확인:
   ```bash
   docker logs llm-alertmanager | grep -i error
   ```

### Discord 알림이 전송되지 않음

1. Discord Webhook URL이 올바른지 확인
2. Webhook이 활성화되어 있는지 확인
3. Rate limiting 확인 (Discord는 분당 5회 제한)

### Email 알림이 전송되지 않음

1. Gmail 앱 비밀번호가 올바른지 확인
2. 2단계 인증이 활성화되어 있는지 확인
3. SMTP 포트가 올바른지 확인 (587 또는 465)
4. "보안 수준이 낮은 앱" 설정 확인 (필요 시)

## 📚 참고 자료

- [Alertmanager 공식 문서](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Alertmanager 설정 참조](https://prometheus.io/docs/alerting/latest/configuration/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

## 🔐 보안 고려사항

### Webhook URL 보안

**주의**: Webhook URL은 민감한 정보입니다!

1. **Git에 커밋하지 마세요**:
   - `alertmanager.yml`에 실제 URL을 넣은 경우 `.gitignore`에 추가
   - 또는 환경 변수/시크릿 관리 시스템 사용

2. **프로덕션 환경**:
   - Docker Secrets 사용
   - Kubernetes Secrets 사용
   - AWS Secrets Manager / HashiCorp Vault 사용

3. **권한 관리**:
   - Alertmanager UI에 인증 추가 권장
   - 네트워크 방화벽 설정

### 권장 설정 (프로덕션)

```yaml
# docker-compose.yml에서 secrets 사용 예시
services:
  alertmanager:
    secrets:
      - slack_webhook_url
      - discord_webhook_url
      - email_password

secrets:
  slack_webhook_url:
    file: ./secrets/slack_webhook_url.txt
  discord_webhook_url:
    file: ./secrets/discord_webhook_url.txt
  email_password:
    file: ./secrets/email_password.txt
```

---

**마지막 업데이트**: 2025-12-26
**버전**: v0.6.0
