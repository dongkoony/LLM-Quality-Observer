# LLM-Quality-Observer

[🇰🇷 KR](README.md) | [🇺🇸 EN](docs/README-main-us.md)

---

## 개요

**LLM-Quality-Observer**는 대형 언어 모델(LLM)의 응답 품질을 **모니터링하고 평가**하기 위한 MLOps 플랫폼입니다.
마이크로서비스 아키텍처 기반으로 구축되어 LLM 상호작용을 로깅하고, 자동으로 품질을 평가하며, 실시간 모니터링 대시보드를 제공합니다.

### 주요 기능

- ✅ **Gateway API**: LLM 요청 처리 및 자동 로깅
- ✅ **자동 평가**: 규칙 기반 + LLM-as-a-Judge 이중 평가 시스템
- ✅ **스케줄러**: 배치 평가 자동 실행 (APScheduler)
- ✅ **다중 채널 알림**: Slack, Discord, Email 통합
- ✅ **모니터링**: Prometheus 메트릭 수집 + Grafana 대시보드
- ✅ **고급 알림**: Alertmanager 통합 (42개 프로덕션 Alert Rules)
- ✅ **고급 분석**: 시간대별 품질 트렌드 + 모델 성능 비교 API
- ✅ **웹 대시보드**: Next.js 기반 실시간 품질 시각화
- ✅ **다국어 지원**: 영어, 한국어, 일본어, 중국어
- ✅ **CI/CD**: GitHub Actions 자동화 파이프라인

> **현재 버전: v0.6.0** — Alertmanager, Alert Rules, 고급 분석 API 추가 완료

---

## 📊 아키텍처

```mermaid
flowchart TB
    subgraph "클라이언트"
        ClientApp[Client/Browser]
    end

    subgraph "프론트엔드"
        WebDashboard["Next.js Dashboard<br/>:3000"]
        Grafana["Grafana<br/>:3001"]
    end

    subgraph "백엔드 서비스"
        Gateway["Gateway API<br/>:18000"]
        Evaluator["Evaluator<br/>:18001"]
        Dashboard["Streamlit Dashboard<br/>:18002"]
    end

    subgraph "데이터베이스"
        Postgres["PostgreSQL<br/>:5432"]
    end

    subgraph "모니터링 & 알림"
        Prometheus["Prometheus<br/>:9090"]
        Alertmanager["Alertmanager<br/>:9093"]
    end

    subgraph "외부 서비스"
        OpenAI_Main["OpenAI GPT<br/>(Main Model)"]
        OpenAI_Judge["OpenAI GPT<br/>(Judge Model)"]
    end

    subgraph "알림 채널"
        Slack["Slack"]
        Discord["Discord"]
        Email["Email<br/>(SMTP)"]
    end

    %% 클라이언트 연결
    ClientApp --> WebDashboard
    ClientApp --> Gateway

    %% Gateway 연결
    Gateway --> OpenAI_Main
    Gateway --> Postgres
    Gateway -.메트릭.-> Prometheus

    %% Evaluator 연결
    Postgres --> Evaluator
    Evaluator --> OpenAI_Judge
    Evaluator --> Slack
    Evaluator --> Discord
    Evaluator --> Email
    Evaluator -.메트릭.-> Prometheus

    %% Dashboard 연결
    Postgres --> Dashboard

    %% 모니터링 연결
    Prometheus --> Grafana
    Prometheus --> Alertmanager
    Alertmanager --> Slack
    Alertmanager --> Discord
    Alertmanager --> Email

    style Gateway fill:#4CAF50
    style Evaluator fill:#2196F3
    style Postgres fill:#FF9800
    style Prometheus fill:#E91E63
    style Alertmanager fill:#F44336
    style Grafana fill:#9C27B0
    style OpenAI_Main fill:#00BCD4
    style OpenAI_Judge fill:#00BCD4
```

### 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| **Gateway API** | 18000 | LLM 요청 처리 및 로깅 (FastAPI) |
| **Evaluator** | 18001 | 자동 평가 및 알림 (FastAPI) |
| **Dashboard** | 18002 | Streamlit 대시보드 (레거시) |
| **Web Dashboard** | 3000 | Next.js 웹 대시보드 |
| **PostgreSQL** | 5432 | 로그 및 평가 결과 저장 |
| **Prometheus** | 9090 | 메트릭 수집 및 Alert Rules |
| **Alertmanager** | 9093 | Alert 라우팅 및 그룹핑 |
| **Grafana** | 3001 | 모니터링 대시보드 (3개 대시보드) |

---

## 🚀 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- OpenAI API Key
- (선택) Slack/Discord Webhook URL
- (선택) Gmail SMTP 계정

### 설치

1. **리포지토리 클론**
```bash
git clone https://github.com/dongkoony/LLM-Quality-Observer.git
cd LLM-Quality-Observer
```

2. **환경 변수 설정**
```bash
cp configs/env/.env.local.example configs/env/.env.local
# .env.local 파일 편집하여 API 키 설정
```

3. **서비스 시작**
```bash
cd infra/docker
docker compose -f docker-compose.local.yml up --build
```

4. **서비스 확인**
```bash
# Gateway API
curl http://localhost:18000/health

# Evaluator
curl http://localhost:18001/health

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3001  # admin/admin
```

---

## 📖 사용 가이드

### 1. LLM 요청 전송

```bash
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "user_id": "test-user",
    "model_version": "gpt-5-mini"
  }'
```

**응답 예시:**
```json
{
  "id": 1,
  "prompt": "Explain quantum computing...",
  "response": "Quantum computing is...",
  "model_version": "gpt-5-mini",
  "latency_ms": 1234,
  "status": "success"
}
```

### 2. 평가 실행

**수동 평가:**
```bash
# 규칙 기반 평가
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=rule"

# LLM-as-a-Judge 평가
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=llm"
```

**자동 평가:** 스케줄러가 설정된 간격(기본 60분)마다 자동 실행

### 3. 대시보드 확인

**Grafana 대시보드:**
1. http://localhost:3001 접속
2. admin/admin으로 로그인
3. Dashboards → LLM Quality Observer 선택

**포함된 메트릭:**
- HTTP 요청 비율 및 지연시간
- LLM 모델별 성능
- 평가 점수 분포
- 알림 전송 현황
- 스케줄러 실행 상태

### 4. 데이터베이스 조회

```bash
# PostgreSQL 접속
docker exec -it llm-postgres psql -U llm_user -d llm_quality

# 최근 로그 확인
SELECT id, created_at, user_id,
       LEFT(prompt, 50) AS prompt,
       model_version, latency_ms, status
FROM llm_logs
ORDER BY id DESC
LIMIT 10;

# 평가 결과 확인
SELECT l.id, l.prompt,
       e.score_overall, e.score_instruction_following, e.score_truthfulness,
       e.judge_type, e.comments
FROM llm_logs l
JOIN llm_evaluations e ON l.id = e.log_id
ORDER BY e.created_at DESC
LIMIT 10;
```

---

## 🔧 주요 기능 상세

### Gateway API (v0.1.0+)

**엔드포인트:**
- `GET /health` - 헬스 체크
- `POST /chat` - LLM 요청 처리
- `GET /docs` - Swagger UI
- `GET /metrics` - Prometheus 메트릭

**기능:**
- OpenAI GPT 모델 호출
- 자동 로깅 (프롬프트, 응답, 지연시간, 상태)
- 모델 버전 추적
- Prometheus 메트릭 수출

### Evaluator Service (v0.2.0+)

**평가 방식:**

1. **규칙 기반 평가** (빠름, 저렴):
   - 응답 길이 검사
   - 키워드 검증
   - 포맷 준수 확인

2. **LLM-as-a-Judge** (v0.3.0+, 정확, 비용 발생):
   - GPT-4 기반 품질 평가
   - 다차원 점수 (전체, 지시사항 준수, 진실성)
   - 상세한 평가 코멘트

**자동 스케줄러** (v0.4.0+):
- APScheduler로 주기적 평가
- 설정 가능한 간격 및 배치 크기
- 자동 시작/정지

**알림 시스템** (v0.4.0+, v0.5.0):
- **Slack**: 웹훅 통합
- **Discord**: 웹훅 통합
- **Email** (v0.5.0): SMTP (Gmail 등)
- 낮은 품질 즉시 알림
- 배치 평가 요약

### 모니터링 (v0.5.0)

**Prometheus 메트릭:**
- `llm_gateway_http_requests_total` - HTTP 요청 수
- `llm_gateway_http_request_duration_seconds` - 요청 지연시간
- `llm_gateway_llm_requests_total` - LLM 호출 수
- `llm_evaluator_evaluations_total` - 평가 수
- `llm_evaluator_evaluation_scores` - 점수 분포
- `llm_evaluator_notifications_sent_total` - 알림 전송 수
- `llm_evaluator_pending_logs` - 평가 대기 로그 수

**Grafana 대시보드:**
- 14개 시각화 패널
- 실시간 성능 모니터링
- 품질 추세 분석
- 알림 현황 추적

---

## ⚙️ 설정

### 환경 변수

```bash
# 애플리케이션
APP_ENV=local
LOG_LEVEL=DEBUG

# LLM 모델
OPENAI_MODEL_MAIN=gpt-5-mini          # Gateway에서 사용할 모델
OPENAI_MODEL_JUDGE=gpt-4o-mini        # 평가에 사용할 모델
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...

# 데이터베이스
DATABASE_URL=postgresql://llm_user:llm_password@postgres:5432/llm_quality

# 배치 평가 스케줄러 (v0.4.0+)
ENABLE_AUTO_EVALUATION=true           # 자동 평가 활성화
EVALUATION_INTERVAL_MINUTES=60        # 평가 주기 (분)
EVALUATION_BATCH_SIZE=10              # 배치 크기
EVALUATION_JUDGE_TYPE=rule            # 기본 평가 방식 (rule/llm)

# 알림 설정 (v0.4.0+)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
NOTIFICATION_SCORE_THRESHOLD=3        # 알림 임계값 (≤ 3점)

# 이메일 알림 (v0.5.0+)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAILS=recipient1@example.com,recipient2@example.com
```

---

## 🏗️ 프로젝트 구조

```
LLM-Quality-Observer/
├── services/
│   ├── gateway-api/           # Gateway API 서비스
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI 앱
│   │   │   ├── config.py      # 설정
│   │   │   ├── llm_client.py  # OpenAI 클라이언트
│   │   │   ├── db.py          # 데이터베이스
│   │   │   ├── models.py      # SQLAlchemy 모델
│   │   │   ├── schemas.py     # Pydantic 스키마
│   │   │   └── metrics.py     # Prometheus 메트릭
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── evaluator/             # Evaluator 서비스
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI 앱
│   │   │   ├── rules.py       # 규칙 기반 평가
│   │   │   ├── llm_judge.py   # LLM-as-a-Judge
│   │   │   ├── scheduler.py   # APScheduler
│   │   │   ├── notifier.py    # 알림 시스템
│   │   │   ├── metrics.py     # Prometheus 메트릭
│   │   │   └── utils.py       # 유틸리티
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── dashboard/             # Streamlit 대시보드
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── web/                   # Next.js 웹 대시보드
│       └── dashboard/
│           ├── app/
│           ├── components/
│           ├── locales/       # 다국어 지원
│           └── lib/
│
├── infra/
│   ├── docker/
│   │   └── docker-compose.local.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       ├── dashboards/
│       └── DASHBOARD_GUIDE-ko.md
│
├── configs/
│   └── env/
│       ├── .env.local.example
│       └── .env.local          # gitignored
│
├── docs/
│   ├── release_notes/         # 릴리즈 노트
│   │   ├── RELEASE_NOTES_v0.1.0.md
│   │   ├── RELEASE_NOTES_v0.2.0.md
│   │   ├── RELEASE_NOTES_v0.3.0.md
│   │   ├── RELEASE_NOTES_v0.4.0.md
│   │   └── RELEASE_NOTES_v0.5.0.md
│   ├── RELEASE_NOTES_v0.5.0_ko.md
│   ├── METRICS.md
│   ├── EMAIL_SETUP.md
│   └── README-main-us.md
│
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
│
├── .flake8                    # Flake8 설정
└── README.md
```

---

## 🧪 테스트

### 헬스 체크 테스트

```bash
# 모든 서비스 헬스 체크
curl http://localhost:18000/health  # Gateway API
curl http://localhost:18001/health  # Evaluator
curl http://localhost:9090/-/healthy # Prometheus
curl http://localhost:3001/api/health # Grafana
```

### 통합 테스트

```bash
# 1. LLM 요청 전송
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "user_id": "test"}'

# 2. 평가 실행
curl -X POST "http://localhost:18001/evaluate-once?limit=1"

# 3. 메트릭 확인
curl http://localhost:18000/metrics | grep llm_gateway
curl http://localhost:18001/metrics | grep llm_evaluator

# 4. Grafana 대시보드 확인
open http://localhost:3001
```

### 자동화 테스트

```bash
# CI/CD 파이프라인 로컬 실행
cd services/gateway-api
pytest tests/

cd ../evaluator
pytest tests/

# Lint 체크
flake8 services/
```

---

## 📈 모니터링 가이드

### Prometheus 쿼리 예시

```promql
# HTTP 요청 비율
sum(rate(llm_gateway_http_requests_total[5m]))

# LLM 지연시간 p95
histogram_quantile(0.95, sum(rate(llm_gateway_llm_request_duration_seconds_bucket[5m])) by (le, model))

# 평가 점수 중앙값
histogram_quantile(0.50, sum(rate(llm_evaluator_evaluation_scores_bucket{score_type="overall"}[5m])) by (le))

# 평가 대기 로그 수
llm_evaluator_pending_logs
```

### Grafana 대시보드 사용

자세한 가이드는 [Grafana 대시보드 가이드](./infra/grafana/DASHBOARD_GUIDE-ko.md) 참조

---

## 📚 문서

### 릴리즈 노트

- [v0.5.0 (Latest)](./docs/RELEASE_NOTES_v0.5.0_ko.md) - Prometheus, Grafana, 이메일 알림
- [v0.4.0](./docs/release_notes/RELEASE_NOTES_v0.4.0.md) - 스케줄러, Slack/Discord 알림, CI/CD
- [v0.3.0](./docs/release_notes/RELEASE_NOTES_v0.3.0.md) - LLM-as-a-Judge, 다국어 지원
- [v0.2.0](./docs/release_notes/RELEASE_NOTES_v0.2.0.md) - Dashboard, CORS, 규칙 기반 평가
- [v0.1.0](./docs/release_notes/RELEASE_NOTES_v0.1.0.md) - 초기 릴리즈 (Gateway + Evaluator)

### 기술 문서

- [메트릭 참조](./docs/METRICS.md) - Prometheus 메트릭 상세
- [이메일 설정 가이드](./docs/EMAIL_SETUP.md) - Gmail SMTP 설정
- [Grafana 대시보드 가이드](./infra/grafana/DASHBOARD_GUIDE-ko.md) - 대시보드 사용법

---

## 🛣️ 로드맵

### 완료된 기능

- ✅ v0.1.0: Gateway API + Evaluator 기본 구조
- ✅ v0.2.0: 웹 대시보드 + 규칙 기반 평가
- ✅ v0.3.0: LLM-as-a-Judge + 다국어 지원
- ✅ v0.4.0: 자동 스케줄러 + Slack/Discord 알림
- ✅ v0.5.0: Prometheus + Grafana + 이메일 알림

### 향후 계획 (v0.6.0+)

- [ ] **Alertmanager 통합**: 고급 알림 규칙 및 라우팅
- [ ] **다중 LLM 제공자 지원**: Anthropic Claude, Google Gemini 등
- [ ] **비용 추적**: 토큰 사용량 및 비용 모니터링
- [ ] **A/B 테스트**: 프롬프트 및 모델 비교
- [ ] **사용자 피드백**: RLHF 스타일 사람 평가
- [ ] **Kubernetes 배포**: Helm 차트 및 배포 가이드
- [ ] **API 인증**: JWT 기반 보안
- [ ] **Rate Limiting**: 요청 제한 및 할당량 관리

---

## 🔒 보안

### 주의사항

- `.env.local` 파일을 절대 커밋하지 마세요 (gitignored)
- OpenAI API 키를 안전하게 보관하세요
- Slack/Discord 웹훅 URL을 공개하지 마세요
- SMTP 비밀번호는 앱 비밀번호를 사용하세요 (Gmail)

### 권장사항

- 프로덕션에서는 환경 변수를 시크릿 관리자에 저장
- API 엔드포인트에 인증 추가 (v0.6.0+)
- HTTPS/TLS 사용
- 정기적인 의존성 업데이트

---

## 🤝 기여

기여를 환영합니다! 다음 절차를 따라주세요:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

### 개발 가이드라인

- Python 코드는 Flake8 스타일 가이드 준수
- 모든 PR은 CI 테스트 통과 필수
- 커밋 메시지는 Conventional Commits 형식 사용
- 새 기능에는 테스트 추가

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 👥 제작자

**Dong-hyeon Shin (dongkoony)**
- GitHub: [@dongkoony](https://github.com/dongkoony)
- Email: dhyeon.shin@icloud.com

---


## 📞 문의 및 지원

- **Issues**: [GitHub Issues](https://github.com/dongkoony/LLM-Quality-Observer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dongkoony/LLM-Quality-Observer/discussions)
- **Email**: dhyeon.shin@icloud.com

---

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!**
