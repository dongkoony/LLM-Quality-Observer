# Development Workflow Guide

> **AI Agent Guide**: 이 문서는 LLM Quality Observer 프로젝트의 개발 워크플로우를 정의합니다.

---

## 📋 Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Git Workflow](#git-workflow)
3. [Feature Development Process](#feature-development-process)
4. [Testing Workflow](#testing-workflow)
5. [Release Process](#release-process)
6. [Hotfix Process](#hotfix-process)
7. [Code Review Guidelines](#code-review-guidelines)
8. [AI Agent Collaboration](#ai-agent-collaboration)

---

## Development Environment Setup

### Prerequisites

```bash
# Required
- Docker & Docker Compose v2.0+
- Git 2.30+
- Python 3.12+
- Node.js 18+ (for Next.js dashboard)

# Optional
- uv (Python package manager)
- VS Code with extensions:
  - Python
  - Pylance
  - ESLint
  - Tailwind CSS IntelliSense
```

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/dongkoony/LLM-Quality-Observer.git
cd LLM-Quality-Observer

# 2. Setup environment variables
cp configs/env/.env.local.example configs/env/.env.local
# Edit .env.local with your API keys

# 3. Start services
cd infra/docker
docker compose -f docker-compose.local.yml up -d --build

# 4. Verify installation
docker ps  # Should see 7 containers running
curl http://localhost:18000/health  # Should return {"status":"ok"}
```

### Python Development Setup (각 서비스별)

```bash
# Gateway API
cd services/gateway-api
uv sync  # Install dependencies
uv run uvicorn app.main:app --reload  # Run development server

# Evaluator
cd services/evaluator
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

### Next.js Development Setup

```bash
cd services/web/dashboard
npm install
npm run dev  # Run on http://localhost:3000
```

---

## Git Workflow

### Branch Strategy

우리는 **GitHub Flow** 기반 전략을 사용합니다:

```
main (production-ready)
  ├── feat/alertmanager-integration
  ├── feat/analytics-api
  ├── fix/evaluation-score-bug
  └── docs/api-guide-update
```

**Main Branch:**
- 항상 배포 가능한 상태 유지
- Direct push 금지
- PR을 통해서만 머지

**Feature Branches:**
- `feat/` - 새 기능
- `fix/` - 버그 수정
- `docs/` - 문서 업데이트
- `refactor/` - 리팩토링
- `test/` - 테스트 추가

### Daily Workflow

```bash
# 1. 최신 main 코드 받기
git checkout main
git pull origin main

# 2. 새 feature branch 생성
git checkout -b feat/new-feature-name

# 3. 작업 진행
# ... code, test, commit ...

# 4. 정기적으로 commit
git add .
git commit -m "feat: add initial structure for new feature"

# 5. Remote에 push
git push origin feat/new-feature-name

# 6. PR 생성 (GitHub web)
# - Base: main
# - Compare: feat/new-feature-name
# - Fill in PR template

# 7. Review 받고 머지
# 8. 로컬 branch 정리
git checkout main
git pull origin main
git branch -d feat/new-feature-name
```

### Commit Guidelines

**Format:**
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**Examples:**

```bash
# Good commits
git commit -m "feat: add /analytics/trends endpoint"
git commit -m "fix: handle null values in score calculation"
git commit -m "docs: update API guide with new endpoints"
git commit -m "test: add integration tests for alert routing"

# Bad commits (avoid)
git commit -m "update"
git commit -m "fix bug"
git commit -m "WIP"
git commit -m "asdf"
```

### 중요: Git 안전 수칙

```bash
# ✅ 안전한 명령어
git pull origin main
git push origin feat/my-branch
git merge main  # feature branch에서

# ⚠️ 주의해서 사용
git push --force origin feat/my-branch  # 본인 feature branch만
git rebase main  # feature branch에서만

# ❌ 절대 금지
git push --force origin main  # NEVER!
git reset --hard HEAD~10  # 공유 branch에서 금지
git rebase main  # main branch에서 금지
```

---

## Feature Development Process

### 1. Planning Phase

```bash
# AI Agent가 받은 요청:
User: "Add a new endpoint to compare model performance"

# AI Agent가 해야 할 일:
1. ✅ 요구사항 이해
2. ✅ 영향받는 파일 파악
3. ✅ 기존 패턴 확인 (Read tool 사용)
4. ✅ 변경 계획 수립
5. ❌ 즉시 코드 작성 시작 (X)
```

**Good Practice:**
```
AI: "이 기능을 추가하려면:
1. services/gateway-api/app/schemas.py - 새 스키마 추가
2. services/gateway-api/app/main.py - 새 엔드포인트 추가
3. docs/API_GUIDE_v0.6.0.md - 문서 업데이트

기존 /analytics/trends 엔드포인트와 유사한 패턴을 따르겠습니다.
진행할까요?"
```

### 2. Implementation Phase

**Step-by-step approach:**

```python
# Step 1: Schema 정의 (services/gateway-api/app/schemas.py)
class ModelComparisonDetail(BaseModel):
    model_version: str
    total_requests: int
    avg_score: float
    # ... 필요한 필드만

# Step 2: 엔드포인트 추가 (services/gateway-api/app/main.py)
@app.get("/analytics/compare-models", response_model=ModelComparisonResponse)
def compare_models(days: int = Query(7, ge=1, le=30)):
    # Implementation
    pass

# Step 3: 테스트
# curl로 수동 테스트

# Step 4: 문서 업데이트
# docs/API_GUIDE_v0.6.0.md
```

**중요: 점진적 개발**
- ✅ 한 번에 하나의 파일 수정
- ✅ 각 단계마다 테스트
- ✅ 작은 커밋으로 자주 저장
- ❌ 여러 파일 동시에 수정 (X)

### 3. Testing Phase

```bash
# 1. 로컬 테스트
curl http://localhost:18000/analytics/compare-models?days=7

# 2. Docker 환경 테스트
cd infra/docker
docker compose -f docker-compose.local.yml restart gateway-api
curl http://localhost:18000/analytics/compare-models?days=7

# 3. 자동화 테스트 (있는 경우)
pytest services/gateway-api/tests/

# 4. 통합 테스트
bash scripts/test-v0.6.0.sh
```

### 4. Documentation Phase

**항상 업데이트해야 할 문서:**
- [ ] API 가이드 (docs/API_GUIDE_v*.md)
- [ ] README.md (새 기능 추가 시)
- [ ] CHANGELOG.md (릴리즈 준비 시)

**선택적 문서:**
- [ ] 아키텍처 다이어그램 (구조 변경 시)
- [ ] 설정 가이드 (새 환경 변수 추가 시)

---

## Testing Workflow

### 1. Unit Testing

```python
# services/gateway-api/tests/test_analytics.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_compare_models_success():
    """Test successful model comparison."""
    response = client.get("/analytics/compare-models?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data

def test_compare_models_invalid_days():
    """Test with invalid days parameter."""
    response = client.get("/analytics/compare-models?days=999")
    assert response.status_code == 422  # Validation error
```

**실행:**
```bash
cd services/gateway-api
pytest tests/ -v
```

### 2. Integration Testing

```bash
# 전체 시스템 테스트
bash scripts/test-v0.6.0.sh

# 예상 출력:
# ✅ All tests passed! ✨
# Total Tests: 23
# Passed: 23
# Failed: 0
```

### 3. Manual Testing

```bash
# 1. 시스템 시작
cd infra/docker
docker compose -f docker-compose.local.yml up -d

# 2. 테스트 데이터 생성
for i in {1..10}; do
  curl -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test $i\", \"user_id\": \"test-user\"}"
done

# 3. 평가 실행
curl -X POST http://localhost:18001/evaluate-once?limit=10

# 4. API 테스트
curl http://localhost:18000/analytics/trends?hours=1
curl http://localhost:18000/analytics/compare-models?days=1

# 5. Grafana 확인
open http://localhost:3001
```

---

## Release Process

### Semantic Versioning

우리는 **Semantic Versioning (SemVer)**을 따릅니다:

```
v0.6.0
  │ │ │
  │ │ └─ PATCH: 버그 수정, 문서 업데이트
  │ └─── MINOR: 새 기능 추가 (하위 호환)
  └───── MAJOR: Breaking changes (v1.0.0부터)
```

**Examples:**
- `v0.5.0 → v0.6.0`: 새 기능 (Alertmanager, Analytics API)
- `v0.6.0 → v0.6.1`: 버그 수정, 문서 업데이트
- `v0.6.0 → v1.0.0`: Breaking changes (API 변경 등)

### Release Checklist

**v0.x.0 Minor Release:**

```bash
# 1. 모든 기능 완료 확인
- [ ] 새 기능 개발 완료
- [ ] 테스트 통과 (100%)
- [ ] 문서 업데이트 완료
- [ ] PR 머지 완료

# 2. Release Notes 작성
# docs/release_notes/RELEASE_NOTES_v0.x.0.md
- [ ] Overview 작성
- [ ] Key Features 나열
- [ ] Breaking Changes (있는 경우)
- [ ] Upgrade Guide 작성

# 3. 버전 업데이트
- [ ] ROADMAP.md 업데이트 (현재 버전)
- [ ] README.md 업데이트 (현재 버전)
- [ ] package.json, pyproject.toml (필요 시)

# 4. Git Tag 생성
git checkout main
git pull origin main
git tag -a v0.x.0 -m "Release v0.x.0: <title>"
git push origin v0.x.0

# 5. GitHub Release 생성
- [ ] GitHub UI에서 Release 작성
- [ ] Release Notes 복사
- [ ] Assets 첨부 (필요 시)
- [ ] Publish

# 6. 배포 (필요 시)
- [ ] Production 환경 배포
- [ ] Smoke test 실행
- [ ] 모니터링 확인
```

### Release Notes Template

```markdown
# Release Notes - v0.x.0

**Release Date:** YYYY-MM-DD
**Focus:** <Main theme>

## Overview

<Brief description of this release>

## 🎯 Key Features

### 1. <Feature Name>

<Description>

**Benefits:**
- ...

### 2. <Feature Name>

...

## 📦 What's New

- New service X
- New endpoints Y
- New dashboards Z

## 🔄 Breaking Changes

None / <List if any>

## 🚀 Upgrade Guide

<Step-by-step upgrade instructions>

## 📚 Documentation

- [Full Release Notes](link)
- [API Guide](link)

---

**Full Changelog:** v0.x-1.0...v0.x.0
```

---

## Hotfix Process

**긴급 버그 수정 (Patch Release):**

```bash
# 1. main에서 hotfix branch 생성
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# 2. 버그 수정
# ... fix the bug ...

# 3. 테스트
bash scripts/test-v0.6.0.sh

# 4. Commit & Push
git add .
git commit -m "fix: critical bug in evaluation scoring"
git push origin hotfix/critical-bug-fix

# 5. PR 생성 (긴급 리뷰)
# Label: hotfix, priority: high

# 6. 머지 후 즉시 릴리즈
git checkout main
git pull origin main
git tag -a v0.6.1 -m "Hotfix v0.6.1: Fix critical evaluation bug"
git push origin v0.6.1

# 7. GitHub Release (간단한 노트)
# Title: v0.6.1 - Critical Bugfix
# Body:
# ## Bugfix
# - Fixed critical bug in evaluation scoring logic
#
# **Full Changelog:** v0.6.0...v0.6.1
```

---

## Code Review Guidelines

### For Reviewers (Human or AI)

**Check List:**

```markdown
## Functionality
- [ ] 코드가 요구사항을 충족하는가?
- [ ] Edge cases가 처리되는가?
- [ ] 에러 핸들링이 적절한가?

## Code Quality
- [ ] 타입 힌트가 있는가? (Python)
- [ ] 네이밍이 명확한가?
- [ ] 불필요한 복잡성이 없는가? (over-engineering)
- [ ] 기존 패턴을 따르는가?

## Testing
- [ ] 테스트가 작성되었는가?
- [ ] 테스트가 통과하는가?
- [ ] 수동 테스트가 완료되었는가?

## Documentation
- [ ] 코드 주석이 적절한가?
- [ ] API 문서가 업데이트되었는가?
- [ ] README가 업데이트되었는가? (필요 시)

## Security
- [ ] 보안 취약점이 없는가?
- [ ] Secrets이 노출되지 않았는가?
- [ ] Input validation이 있는가?

## Performance
- [ ] 성능 문제가 없는가?
- [ ] N+1 쿼리가 없는가?
- [ ] 메모리 누수가 없는가?
```

### Review Comments

**좋은 리뷰 코멘트:**

```markdown
# 칭찬
✅ Good use of type hints here!
✅ Nice error handling pattern.

# 제안
💡 Consider using a constant for this threshold.
💡 This could be simplified by using a list comprehension.

# 필수 수정
⚠️ This introduces a security vulnerability. Please validate user input.
⚠️ This breaks the existing API contract. Needs discussion.

# 질문
❓ Why did you choose this approach instead of X?
❓ Have you considered the performance impact?
```

**나쁜 리뷰 코멘트:**

```markdown
# 너무 모호함
❌ This is wrong.
❌ Fix this.
❌ Bad code.

# 너무 주관적
❌ I don't like this.
❌ This feels weird.
```

---

## AI Agent Collaboration

### Best Practices for AI Agents

**1. Context Awareness:**

```python
# ✅ Good - AI reads existing code first
AI: "Let me first read the existing analytics endpoints to understand the pattern."
[Uses Read tool on services/gateway-api/app/main.py]
AI: "I see the existing pattern uses Pydantic models and follows RESTful conventions.
     I'll follow the same pattern for the new endpoint."

# ❌ Bad - AI doesn't check existing code
AI: "I'll create a new endpoint using my preferred style."
[Creates code that doesn't match project patterns]
```

**2. Incremental Changes:**

```python
# ✅ Good - Step by step
AI: "I'll make changes in this order:
     1. First, add the Pydantic schema
     2. Then, implement the endpoint
     3. Finally, update the documentation
     Let me start with step 1..."

# ❌ Bad - All at once
AI: "I'll update all files simultaneously."
[Makes changes to 10 files at once, harder to review]
```

**3. Ask Before Major Changes:**

```python
# ✅ Good - Clarify before acting
AI: "I notice the current code uses rule-based evaluation.
     To add LLM-based evaluation, I have two options:
     1. Replace the existing system
     2. Add it as an additional option
     Which approach do you prefer?"

# ❌ Bad - Assume and act
AI: "I'll replace the rule-based evaluation with LLM-based."
[Makes breaking changes without asking]
```

**4. Testing:**

```python
# ✅ Good - Test after implementation
AI: "I've added the new endpoint. Let me test it:"
[Uses Bash tool to curl the endpoint]
AI: "The endpoint works correctly. Response: {expected output}"

# ❌ Bad - No testing
AI: "I've added the endpoint. It should work."
[Doesn't verify the implementation]
```

### Communication Templates for AI

**Starting a task:**
```
"I'll work on [task]. Here's my plan:
1. [Step 1]
2. [Step 2]
3. [Step 3]
Proceeding with step 1..."
```

**Encountering ambiguity:**
```
"I need clarification on [issue].
Option A: [description]
Option B: [description]
Which approach do you prefer?"
```

**Completing a task:**
```
"Task completed! Summary:
- Added: [list]
- Modified: [list]
- Tested: [what was tested]
Next steps: [if any]"
```

**Finding an issue:**
```
"I found a potential issue: [description]
Impact: [assessment]
Recommendation: [suggestion]
Should I proceed with the fix?"
```

---

## 📊 Workflow Metrics

### Development Velocity

**Target metrics:**
- Feature branch 수명: < 3일
- PR review 시간: < 24시간
- Release 주기: 2-4주 (minor releases)
- Hotfix 배포: < 4시간

### Quality Metrics

**Target metrics:**
- Test coverage: > 70% (핵심 기능)
- Bug escape rate: < 5% (production)
- PR approval rate: > 90% (first review)

---

## 🚀 Quick Reference

### Common Commands

```bash
# Development
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml logs -f gateway-api
docker compose -f docker-compose.local.yml restart gateway-api

# Testing
bash scripts/test-v0.6.0.sh
pytest services/gateway-api/tests/ -v
curl http://localhost:18000/health

# Git
git checkout -b feat/new-feature
git add .
git commit -m "feat: add new feature"
git push origin feat/new-feature

# Release
git tag -a v0.x.0 -m "Release v0.x.0"
git push origin v0.x.0
```

### Important URLs

```
Local Development:
- Gateway API: http://localhost:18000
- Evaluator: http://localhost:18001
- Next.js Dashboard: http://localhost:3000
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

Documentation:
- GitHub Repo: https://github.com/dongkoony/LLM-Quality-Observer
- Issues: https://github.com/dongkoony/LLM-Quality-Observer/issues
- Releases: https://github.com/dongkoony/LLM-Quality-Observer/releases
```

---

**Remember**: 빠르게 실패하고, 자주 커밋하고, 항상 테스트하라! 🚀
