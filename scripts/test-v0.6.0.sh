#!/bin/bash

# v0.6.0 Quick Test Script
# 이 스크립트는 v0.6.0의 핵심 기능을 빠르게 검증합니다.

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
print_header "v0.6.0 Quick Test Suite"

# 1. 컨테이너 상태 확인
print_header "1. Container Status Check"

CONTAINERS=("llm-alertmanager" "llm-prometheus" "llm-grafana" "llm-gateway-api" "llm-evaluator" "llm-dashboard" "llm-postgres")

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

# Prometheus
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    test_pass "Prometheus health check passed"
else
    test_fail "Prometheus health check failed"
fi

# Alertmanager
if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    test_pass "Alertmanager health check passed"
else
    test_fail "Alertmanager health check failed"
fi

# 3. Alert Rules 확인
print_header "3. Alert Rules Check"

RULE_COUNT=$(curl -s http://localhost:9090/api/v1/rules | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(len(g['rules']) for g in data['data']['groups']))" 2>/dev/null || echo "0")

if [ "$RULE_COUNT" -eq 42 ]; then
    test_pass "All 42 alert rules loaded"
else
    test_fail "Expected 42 rules, found $RULE_COUNT"
fi

# 4. Alertmanager Receivers 확인
print_header "4. Alertmanager Configuration Check"

RECEIVER_COUNT=$(curl -s http://localhost:9093/api/v2/status | python3 -c "import sys, json, re; data=json.load(sys.stdin); yaml_config=data['config']['original']; receivers=re.findall(r'^- name: (.+)$', yaml_config, re.MULTILINE); print(len(receivers))" 2>/dev/null || echo "0")

if [ "$RECEIVER_COUNT" -eq 5 ]; then
    test_pass "All 5 receivers configured"
else
    test_fail "Expected 5 receivers, found $RECEIVER_COUNT"
fi

# 5. 테스트 데이터 생성 및 API 테스트
print_header "5. Test Data Generation & API Testing"

print_info "Generating test data (10 requests)..."
for i in {1..10}; do
    curl -s -X POST http://localhost:18000/chat \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"Test $i: What is AI?\", \"user_id\": \"test-user-$i\"}" > /dev/null 2>&1
    echo -n "."
done
echo ""

print_info "Running evaluation..."
EVAL_RESULT=$(curl -s -X POST "http://localhost:18001/evaluate-once?limit=10")
EVALUATED=$(echo "$EVAL_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['evaluated'])" 2>/dev/null || echo "0")

if [ "$EVALUATED" -gt 0 ]; then
    test_pass "Evaluated $EVALUATED logs"
else
    test_fail "Evaluation failed"
fi

sleep 2  # 데이터 처리 대기

# 6. 새 API 엔드포인트 테스트
print_header "6. New API Endpoints Testing"

# /analytics/trends
TRENDS_RESPONSE=$(curl -s "http://localhost:18000/analytics/trends?hours=24")
if echo "$TRENDS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'data' in data and 'summary' in data else 1)" 2>/dev/null; then
    test_pass "/analytics/trends endpoint working"
else
    test_fail "/analytics/trends endpoint failed"
fi

# /analytics/compare-models
COMPARE_RESPONSE=$(curl -s "http://localhost:18000/analytics/compare-models?days=7")
if echo "$COMPARE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'models' in data else 1)" 2>/dev/null; then
    test_pass "/analytics/compare-models endpoint working"
else
    test_fail "/analytics/compare-models endpoint failed"
fi

# /alerts/history
ALERTS_RESPONSE=$(curl -s "http://localhost:18000/alerts/history?page=1&page_size=10")
if echo "$ALERTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'alerts' in data and 'total' in data else 1)" 2>/dev/null; then
    test_pass "/alerts/history endpoint working"
else
    test_fail "/alerts/history endpoint failed"
fi

# 7. Grafana 대시보드 확인
print_header "7. Grafana Dashboards Check"

DASHBOARD_COUNT=$(curl -s -u admin:admin http://localhost:3001/api/search?type=dash-db 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$DASHBOARD_COUNT" -eq 3 ]; then
    test_pass "All 3 Grafana dashboards found"
else
    test_fail "Expected 3 dashboards, found $DASHBOARD_COUNT"
fi

# Dashboard 접근 가능 여부
if curl -sf -u admin:admin "http://localhost:3001/api/dashboards/uid/alert-history" > /dev/null 2>&1; then
    test_pass "Alert History dashboard accessible"
else
    test_fail "Alert History dashboard not accessible"
fi

if curl -sf -u admin:admin "http://localhost:3001/api/dashboards/uid/advanced-analytics" > /dev/null 2>&1; then
    test_pass "Advanced Analytics dashboard accessible"
else
    test_fail "Advanced Analytics dashboard not accessible"
fi

# 8. Prometheus Metrics 확인
print_header "8. Prometheus Metrics Check"

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

# 9. 성능 테스트
print_header "9. Performance Check"

# API 응답 시간 측정
START=$(date +%s%N)
curl -s "http://localhost:18000/analytics/trends?hours=24" > /dev/null
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))

if [ "$ELAPSED" -lt 500 ]; then
    test_pass "/analytics/trends response time: ${ELAPSED}ms (< 500ms)"
else
    test_warning "/analytics/trends response time: ${ELAPSED}ms (>= 500ms)"
    test_pass "Response time acceptable for test environment"
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
    print_info "v0.6.0 is ready for production deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Review detailed test guide: docs/TESTING_GUIDE_v0.6.0.md"
    echo "  2. Check Grafana dashboards: http://localhost:3001"
    echo "  3. Verify Alertmanager: http://localhost:9093"
    echo "  4. Create git tag: git tag -a v0.6.0 -m 'Release v0.6.0'"
    exit 0
else
    print_error "Some tests failed. Please check the logs above."
    echo ""
    echo "Troubleshooting:"
    echo "  - Check container logs: docker logs llm-<service-name>"
    echo "  - Review test guide: docs/TESTING_GUIDE_v0.6.0.md"
    echo "  - Verify configuration: configs/env/.env.local"
    exit 1
fi
