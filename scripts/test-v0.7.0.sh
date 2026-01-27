#!/bin/bash

# v0.7.0 Test Script (Phase 1-2: Token & Cost Tracking)
# 이 스크립트는 v0.7.0 Phase 1-2의 핵심 기능을 검증합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

test_pass() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS=$((PASSED_TESTS + 1))
    print_success "$1"
}

test_fail() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS=$((FAILED_TESTS + 1))
    print_error "$1"
}

# 메인 테스트 시작
print_header "v0.7.0 Phase 1-2 Test Suite"
print_info "Testing: Token Tracking & Cost Calculation"

# 1. 컨테이너 상태 확인
print_header "1. Container Status Check"

CONTAINERS=("llm-postgres" "llm-gateway-api" "llm-evaluator" "llm-dashboard" "llm-prometheus" "llm-alertmanager" "llm-grafana")

for container in "${CONTAINERS[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        test_pass "Container $container is running"
    else
        test_fail "Container $container is NOT running"
    fi
done

# 2. Health Check
print_header "2. Service Health Check"

# Gateway API
if curl -sf http://localhost:18000/health > /dev/null 2>&1; then
    test_pass "Gateway API health check passed"
else
    test_fail "Gateway API health check failed"
fi

# Evaluator
if curl -sf http://localhost:18001/health > /dev/null 2>&1; then
    test_pass "Evaluator health check passed"
else
    test_fail "Evaluator health check failed"
fi

# 3. Database Schema Check (v0.7.0)
print_header "3. Database Schema Check (v0.7.0)"

# llm_logs 테이블 토큰 필드 확인
TOKEN_FIELDS=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='llm_logs' AND column_name IN ('input_tokens', 'output_tokens', 'total_tokens', 'cached_tokens', 'reasoning_tokens');" | grep -v '^$' | wc -l)

if [ "$TOKEN_FIELDS" -eq 5 ]; then
    test_pass "All 5 token fields exist in llm_logs"
else
    test_fail "Expected 5 token fields, found $TOKEN_FIELDS"
fi

# llm_logs 테이블 비용 필드 확인
COST_FIELDS=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='llm_logs' AND column_name IN ('cost_input_usd', 'cost_output_usd', 'cost_total_usd');" | grep -v '^$' | wc -l)

if [ "$COST_FIELDS" -eq 3 ]; then
    test_pass "All 3 cost fields exist in llm_logs"
else
    test_fail "Expected 3 cost fields, found $COST_FIELDS"
fi

# llm_model_pricing 테이블 확인
PRICING_TABLE=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='llm_model_pricing';" | tr -d ' ')

if [ "$PRICING_TABLE" -eq 1 ]; then
    test_pass "llm_model_pricing table exists"
else
    test_fail "llm_model_pricing table not found"
fi

# 모델 데이터 확인 (7개 모델)
MODEL_COUNT=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT COUNT(*) FROM llm_model_pricing WHERE is_active=true;" | tr -d ' ')

if [ "$MODEL_COUNT" -eq 7 ]; then
    test_pass "All 7 models configured in pricing table"
else
    test_fail "Expected 7 models, found $MODEL_COUNT"
fi

# 4. Token & Cost API Test (v0.7.0)
print_header "4. Token & Cost API Testing (v0.7.0)"

# 테스트 요청 생성
print_info "Making test /chat request..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:18000/chat \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Explain quantum computing briefly.", "user_id": "test-v0.7.0"}')

# usage 필드 확인
if echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'usage' in data and data['usage'] is not None else 1)" 2>/dev/null; then
    test_pass "API response includes 'usage' field"
else
    test_fail "API response missing 'usage' field"
fi

# cost 필드 확인
if echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'cost' in data and data['cost'] is not None else 1)" 2>/dev/null; then
    test_pass "API response includes 'cost' field"
else
    test_fail "API response missing 'cost' field"
fi

# 토큰 값 검증
INPUT_TOKENS=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['usage']['input_tokens'])" 2>/dev/null || echo "0")
OUTPUT_TOKENS=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['usage']['output_tokens'])" 2>/dev/null || echo "0")
TOTAL_TOKENS=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['usage']['total_tokens'])" 2>/dev/null || echo "0")

if [ "$INPUT_TOKENS" -gt 0 ] && [ "$OUTPUT_TOKENS" -gt 0 ] && [ "$TOTAL_TOKENS" -gt 0 ]; then
    test_pass "Token counts are valid (input=$INPUT_TOKENS, output=$OUTPUT_TOKENS, total=$TOTAL_TOKENS)"
else
    test_fail "Invalid token counts (input=$INPUT_TOKENS, output=$OUTPUT_TOKENS, total=$TOTAL_TOKENS)"
fi

# 비용 값 검증
COST_TOTAL=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; from decimal import Decimal; data=json.load(sys.stdin); print(float(data['cost']['total_usd']))" 2>/dev/null || echo "0")

if python3 -c "import sys; exit(0 if float('$COST_TOTAL') > 0 else 1)" 2>/dev/null; then
    test_pass "Cost calculated successfully (total=\$$COST_TOTAL)"
else
    test_fail "Cost calculation failed (total=\$$COST_TOTAL)"
fi

# 5. Database Persistence Check (v0.7.0)
print_header "5. Database Persistence Check (v0.7.0)"

sleep 1  # DB 저장 대기

# 최근 로그 조회
DB_TOKEN_DATA=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT input_tokens, output_tokens, total_tokens FROM llm_logs WHERE user_id='test-v0.7.0' ORDER BY id DESC LIMIT 1;" | tr -d ' ')

if [ -n "$DB_TOKEN_DATA" ] && [ "$DB_TOKEN_DATA" != "||" ]; then
    test_pass "Token data persisted to database"
else
    test_fail "Token data not found in database"
fi

DB_COST_DATA=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT cost_input_usd, cost_output_usd, cost_total_usd FROM llm_logs WHERE user_id='test-v0.7.0' ORDER BY id DESC LIMIT 1;" | tr -d ' ')

if [ -n "$DB_COST_DATA" ] && [ "$DB_COST_DATA" != "||" ]; then
    test_pass "Cost data persisted to database"
else
    test_fail "Cost data not found in database"
fi

# DB의 토큰/비용이 API 응답과 일치하는지 확인
DB_TOTAL_TOKENS=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT total_tokens FROM llm_logs WHERE user_id='test-v0.7.0' ORDER BY id DESC LIMIT 1;" | tr -d ' ')

if [ "$DB_TOTAL_TOKENS" -eq "$TOTAL_TOKENS" ]; then
    test_pass "DB token count matches API response ($DB_TOTAL_TOKENS = $TOTAL_TOKENS)"
else
    test_fail "DB token count mismatch (DB=$DB_TOTAL_TOKENS, API=$TOTAL_TOKENS)"
fi

# 6. Cost Calculation Accuracy (v0.7.0)
print_header "6. Cost Calculation Accuracy (v0.7.0)"

# gpt-5-mini 가격 조회
GPT5_MINI_INPUT_PRICE=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT price_input_per_1m FROM llm_model_pricing WHERE model_name='gpt-5-mini';" | tr -d ' ')
GPT5_MINI_OUTPUT_PRICE=$(docker exec llm-postgres psql -U llm_user -d llm_quality -t -c "SELECT price_output_per_1m FROM llm_model_pricing WHERE model_name='gpt-5-mini';" | tr -d ' ')

if [ -n "$GPT5_MINI_INPUT_PRICE" ] && [ -n "$GPT5_MINI_OUTPUT_PRICE" ]; then
    test_pass "GPT-5 mini pricing: \$$GPT5_MINI_INPUT_PRICE/\$$GPT5_MINI_OUTPUT_PRICE per 1M tokens"
else
    test_fail "Failed to retrieve GPT-5 mini pricing"
fi

# 수동 비용 계산
EXPECTED_COST=$(python3 -c "
input_tokens = $INPUT_TOKENS
output_tokens = $OUTPUT_TOKENS
input_price = float('$GPT5_MINI_INPUT_PRICE')
output_price = float('$GPT5_MINI_OUTPUT_PRICE')
expected = (input_tokens * input_price / 1_000_000) + (output_tokens * output_price / 1_000_000)
print(f'{expected:.6f}')
" 2>/dev/null || echo "0")

# 실제 비용과 비교 (소수점 6자리 반올림 고려)
COST_MATCH=$(python3 -c "
expected = float('$EXPECTED_COST')
actual = float('$COST_TOTAL')
diff = abs(expected - actual)
# 반올림 오차 허용 (0.000001 = 1마이크로달러)
print('match' if diff < 0.000001 else 'mismatch')
" 2>/dev/null || echo "error")

if [ "$COST_MATCH" = "match" ]; then
    test_pass "Cost calculation is accurate (expected=\$$EXPECTED_COST, actual=\$$COST_TOTAL)"
else
    test_fail "Cost calculation mismatch (expected=\$$EXPECTED_COST, actual=\$$COST_TOTAL)"
fi

# 7. Prometheus Metrics Check
print_header "7. Prometheus Metrics Check"

# Gateway metrics
if curl -s http://localhost:18000/metrics | grep -q "llm_gateway_http_requests_total"; then
    test_pass "Gateway API metrics exposed"
else
    test_fail "Gateway API metrics not found"
fi

# Evaluator metrics
if curl -s http://localhost:18001/metrics | grep -q "llm_evaluator_evaluations_total"; then
    test_pass "Evaluator metrics exposed"
else
    test_fail "Evaluator metrics not found"
fi

# 8. Grafana Check (port 13000)
print_header "8. Grafana Status Check"

if curl -sf http://localhost:13000/api/health > /dev/null 2>&1; then
    test_pass "Grafana accessible on port 13000"
else
    test_fail "Grafana not accessible on port 13000"
fi

# 최종 결과
print_header "Test Results Summary"

echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "Pass Rate: ${BLUE}${PASS_RATE}%${NC}\n"

if [ "$FAILED_TESTS" -eq 0 ]; then
    print_success "All tests passed! ✨"
    print_info "v0.7.0 Phase 1-2 is working correctly!"
    echo ""
    echo "Phase 1-2 Complete:"
    echo "  ✅ Token tracking (input/output/total/cached/reasoning)"
    echo "  ✅ Cost calculation (input/output/total in USD)"
    echo "  ✅ Database persistence"
    echo "  ✅ Model pricing table (7 models)"
    echo ""
    echo "Remaining v0.7.0 phases:"
    echo "  ⏳ Phase 3: Cost Analysis API endpoints"
    echo "  ⏳ Phase 4: LiteLLM integration (multi-model support)"
    echo "  ⏳ Phase 5: Dashboard updates & documentation"
    echo ""
    echo "Next steps:"
    echo "  1. Continue with Phase 3-5 implementation"
    echo "  2. Or create git tag: git tag -a v0.7.0-phase1-2 -m 'Release Phase 1-2'"
    exit 0
else
    print_error "Some tests failed. Please check the logs above."
    echo ""
    echo "Troubleshooting:"
    echo "  - Check container logs: docker logs llm-<service-name>"
    echo "  - Verify migration: scripts/migrate_v0.7.0.sql"
    echo "  - Review architecture: docs/ARCHITECTURE_v0.7.0.md"
    exit 1
fi
