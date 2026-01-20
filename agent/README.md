# AI Agent Documentation

> **Purpose**: 이 디렉토리는 AI 코딩 어시스턴트(Claude Code, OpenAI Codex, GitHub Copilot 등)가 LLM Quality Observer 프로젝트를 이해하고 일관성 있게 작업할 수 있도록 돕는 가이드 문서를 포함합니다.

---

## 📚 Documentation Structure

```
agent/
├── README.md                    # 이 파일 (디렉토리 개요)
├── PROJECT_OVERVIEW.md          # 프로젝트 전체 개요
├── CODING_STANDARDS.md          # 코딩 표준 및 컨벤션
└── WORKFLOW.md                  # 개발 워크플로우
```

---

## 🎯 목적

### 왜 이 문서들이 필요한가?

1. **일관성**: 여러 AI 에이전트가 동일한 코딩 스타일과 패턴을 따르도록
2. **효율성**: AI가 프로젝트를 빠르게 이해하고 정확한 코드 생성
3. **품질**: 프로젝트 규칙과 best practice를 자동으로 준수
4. **협업**: 사람과 AI가 동일한 기준으로 작업
5. **지식 전달**: 프로젝트 컨텍스트를 새로운 기여자(사람/AI)에게 전달

### 누가 사용하는가?

- ✅ **Claude Code** (Anthropic) - 주 사용 AI 에이전트
- ✅ **OpenAI Codex** (OpenAI) - 부 사용 AI 에이전트
- ✅ **GitHub Copilot** (Microsoft) - 코드 자동완성
- ✅ **새로운 개발자** - 프로젝트 온보딩
- ✅ **기존 개발자** - 규칙 참고

---

## 📖 각 문서 설명

### 1. [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)

**내용:**
- 프로젝트 정체성 및 목적
- 시스템 아키텍처 (7개 서비스)
- 데이터 플로우 (Request, Evaluation, Alert)
- 데이터베이스 스키마
- 기술 스택
- 프로젝트 구조
- 환경 변수
- 핵심 메트릭
- 문서 인덱스

**언제 읽어야 하나:**
- 처음 프로젝트를 접할 때
- 전체 시스템을 이해하고 싶을 때
- 새 기능이 어디에 속하는지 파악할 때
- 아키텍처 결정을 내릴 때

**AI 에이전트 사용법:**
```
User: "Add a new analytics endpoint"
AI: [Reads PROJECT_OVERVIEW.md]
AI: "I see this project uses FastAPI for the Gateway API.
     Analytics endpoints are defined in services/gateway-api/app/main.py.
     I'll follow the existing pattern..."
```

### 2. [CODING_STANDARDS.md](./CODING_STANDARDS.md)

**내용:**
- General Principles (일반 원칙)
  - Over-Engineering 금지 ⚠️ (매우 중요!)
  - Error Handling 철학
  - Backwards Compatibility 규칙
- Python Standards
  - File Organization
  - Type Hints
  - Naming Conventions
  - Pydantic/SQLAlchemy Patterns
  - Error Handling
  - Logging
- TypeScript/Next.js Standards
  - Component Structure
  - Naming Conventions
  - API Calls
  - Tailwind CSS
- API Design
- Database Patterns
- Testing
- Documentation
- Git Conventions
- Security

**언제 읽어야 하나:**
- 코드를 작성하기 전에
- 코드 리뷰 시
- 스타일 가이드가 궁금할 때
- "이렇게 해도 되나?" 의문이 들 때

**AI 에이전트 사용법:**
```
User: "Add error handling to this function"
AI: [Reads CODING_STANDARDS.md - Error Handling section]
AI: "According to the coding standards, we only add error handling
     at system boundaries (user input, external APIs).
     This is an internal function, so no try-catch needed."
```

**핵심 규칙:**
```python
# ❌ Over-engineering 예시
def save_data(data):
    # 요청: "데이터를 저장하는 함수 작성"
    # 하지만 AI가 과도하게 추가한 것들:
    validator = DataValidator()  # ❌ 요청하지 않음
    logger = CustomLogger()      # ❌ 요청하지 않음
    cache = CacheManager()       # ❌ 요청하지 않음
    # ... 복잡한 추상화 ...

# ✅ Minimal change 예시
def save_data(data):
    # 요청: "데이터를 저장하는 함수 작성"
    db.session.add(data)  # ✅ 요청된 것만
    db.session.commit()   # ✅ 필요한 것만
```

### 3. [WORKFLOW.md](./WORKFLOW.md)

**내용:**
- Development Environment Setup
- Git Workflow (GitHub Flow)
- Feature Development Process
  - Planning Phase
  - Implementation Phase
  - Testing Phase
  - Documentation Phase
- Testing Workflow
- Release Process (Semantic Versioning)
- Hotfix Process
- Code Review Guidelines
- AI Agent Collaboration (Best Practices)

**언제 읽어야 하나:**
- 새 기능을 시작하기 전에
- Git 명령어가 헷갈릴 때
- 릴리즈 프로세스를 진행할 때
- PR을 생성/리뷰할 때
- AI와 협업하는 방법을 알고 싶을 때

**AI 에이전트 사용법:**
```
User: "Let's start a new feature for cost tracking"
AI: [Reads WORKFLOW.md - Feature Development Process]
AI: "Following the workflow:
     1. Planning: I'll check existing patterns first
     2. Implementation: I'll work step-by-step
     3. Testing: I'll verify with curl
     4. Documentation: I'll update API guide

     Let me start by reading existing analytics code..."
```

---

## 🤖 AI 에이전트를 위한 가이드

### 작업 시작 전 체크리스트

```markdown
AI Agent가 새 작업을 시작할 때:

1. [ ] PROJECT_OVERVIEW.md 읽기
   - 프로젝트 구조 이해
   - 관련 서비스 파악
   - 기존 패턴 확인

2. [ ] CODING_STANDARDS.md 참고
   - 해당 언어(Python/TypeScript) 섹션 확인
   - Over-engineering 주의사항 숙지
   - 네이밍 규칙 확인

3. [ ] WORKFLOW.md 참고
   - 적절한 브랜치 전략 확인
   - 커밋 메시지 형식 확인
   - 테스트 요구사항 확인

4. [ ] 기존 코드 읽기 (Read tool)
   - 유사한 기능의 코드 확인
   - 패턴 일치 여부 검증

5. [ ] 구현 시작
   - 점진적으로 작업
   - 각 단계마다 테스트
   - 문서 업데이트
```

### 좋은 AI 에이전트 행동 패턴

```python
# ✅ Good Pattern
AI: "Before implementing, let me check the existing code..."
[Uses Read tool on relevant files]
AI: "I see the pattern. I'll follow it exactly."
[Implements matching pattern]
AI: "Implementation complete. Testing..."
[Uses Bash tool to test]
AI: "Test passed. Updating documentation..."
[Updates docs]
AI: "All done! Here's what changed: ..."

# ❌ Bad Pattern
AI: "I'll implement this my way."
[Creates code without checking existing patterns]
[Skips testing]
[Doesn't update docs]
AI: "Done!"
```

### AI 에이전트가 피해야 할 것들

```markdown
❌ 절대 하지 말 것:

1. 요청하지 않은 리팩토링
   "While I'm here, let me also refactor this old code..."

2. 불필요한 추상화
   "I'll create a ConfigManager, CacheManager, and..."

3. 과도한 에러 핸들링
   "Let me add try-catch to every function..."

4. 스타일 변경
   "I prefer single quotes, so I'll change all double quotes..."

5. 문서 없이 구현
   "Code is self-documenting, no need for docs..."

6. 테스트 없이 커밋
   "It looks correct, should work..."
```

---

## 🔄 문서 업데이트

### 언제 업데이트하나?

이 문서들은 프로젝트와 함께 진화해야 합니다:

- **PROJECT_OVERVIEW.md**: 아키텍처 변경, 새 서비스 추가, 기술 스택 변경 시
- **CODING_STANDARDS.md**: 새로운 규칙 도입, 패턴 변경 시
- **WORKFLOW.md**: 프로세스 변경, 새 도구 도입 시

### 누가 업데이트하나?

- 프로젝트 리드 (@dongkoony)
- 주요 기여자
- AI 에이전트 (사용자 승인 하에)

### 업데이트 프로세스

```bash
1. agent/ 디렉토리의 문서 수정
2. PR 생성 (feat/update-agent-docs)
3. 리뷰 및 머지
4. 모든 AI 에이전트에게 변경사항 공지
```

---

## 📊 문서 우선순위

AI 에이전트가 읽어야 할 우선순위:

```
1. 🔴 HIGH: CODING_STANDARDS.md
   → 코드 작성 전 필독!
   → Over-engineering 방지

2. 🟡 MEDIUM: PROJECT_OVERVIEW.md
   → 프로젝트 이해 필수
   → 첫 작업 시 읽기

3. 🟢 LOW: WORKFLOW.md
   → 필요 시 참고
   → 특정 프로세스 확인 시
```

---

## 🎓 학습 경로

### 새로운 AI 에이전트를 위한 학습 순서

```markdown
Day 1: 프로젝트 이해
1. README.md (프로젝트 루트)
2. PROJECT_OVERVIEW.md
3. 실제 코드 탐색 (Read tool)

Day 2: 규칙 학습
1. CODING_STANDARDS.md 정독
2. 기존 코드와 규칙 비교
3. 예제 코드 분석

Day 3: 실습
1. WORKFLOW.md 읽기
2. 간단한 작업 수행 (문서 수정 등)
3. 피드백 받기

Day 4-7: 점진적 복잡도 증가
1. 간단한 버그 수정
2. 작은 기능 추가
3. 복잡한 기능 구현
```

---

## 🔗 관련 문서

### 프로젝트 루트

- [README.md](../README.md) - 프로젝트 소개
- [CLAUDE.md](../CLAUDE.md) - Claude Code 전용 가이드 (이 디렉토리의 요약본)

### 기술 문서

- [API_GUIDE_v0.6.0.md](../docs/API_GUIDE_v0.6.0.md) - API 사용법
- [TESTING_GUIDE_v0.6.0.md](../docs/TESTING_GUIDE_v0.6.0.md) - 테스트 가이드
- [ROADMAP.md](../docs/ROADMAP.md) - 로드맵

### 인프라 문서

- [Alertmanager README](../infra/alertmanager/README.md)
- [Alert Rules README](../infra/prometheus/alerts/README.md)
- [Grafana Dashboard Guide](../infra/grafana/NEW_DASHBOARDS_GUIDE.md)

---

## 💬 피드백

이 문서에 대한 피드백이나 개선 제안이 있다면:

1. GitHub Issue 생성
2. PR로 직접 수정 제안
3. 프로젝트 리드에게 연락

---

## 📜 라이선스

이 문서는 LLM Quality Observer 프로젝트의 일부로, 프로젝트와 동일한 라이선스를 따릅니다.

---

**Last Updated**: 2026-01-02
**Version**: 1.0.0
**Maintained by**: @dongkoony

**AI Agents**: 이 문서를 읽었다면, 당신은 이제 LLM Quality Observer에 기여할 준비가 되었습니다! 🤖✨
