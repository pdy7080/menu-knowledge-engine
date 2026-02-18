#!/bin/bash
# Menu Knowledge Engine - API 종합 테스트 스크립트

BASE_URL="http://localhost:8000"
echo "🧪 Menu Knowledge Engine API 테스트 시작..."
echo "Base URL: $BASE_URL"
echo ""

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_api() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    
    echo -n "Testing: $name ... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        echo "Response: $body" | head -3
        ((FAILED++))
        return 1
    fi
}

echo "========================================="
echo "1. 헬스체크 & 기본 엔드포인트"
echo "========================================="
test_api "Health Check" "$BASE_URL/health"
test_api "Root Endpoint" "$BASE_URL/"
test_api "API Docs (Swagger)" "$BASE_URL/docs"
echo ""

echo "========================================="
echo "2. 메뉴 데이터 조회 API"
echo "========================================="
test_api "Get Concepts" "$BASE_URL/api/v1/concepts"
test_api "Get Modifiers" "$BASE_URL/api/v1/modifiers"
test_api "Get Canonical Menus" "$BASE_URL/api/v1/canonical-menus"
echo ""

echo "========================================="
echo "3. 메뉴 매칭 API (3단계 파이프라인)"
echo "========================================="
test_api "Menu Identify - Exact Match" "$BASE_URL/api/v1/menu/identify" "POST" '{"menu_name_ko":"김치찌개"}'
test_api "Menu Identify - With Modifier" "$BASE_URL/api/v1/menu/identify" "POST" '{"menu_name_ko":"매운 김치찌개"}'
test_api "Menu Identify - New Menu (AI)" "$BASE_URL/api/v1/menu/identify" "POST" '{"menu_name_ko":"테스트신메뉴123"}'
echo ""

echo "========================================="
echo "4. Admin API (통계 & 큐 관리)"
echo "========================================="
test_api "Admin Stats (Redis 캐싱)" "$BASE_URL/api/v1/admin/stats"
test_api "Admin Stats (캐시 히트)" "$BASE_URL/api/v1/admin/stats"
test_api "Admin Queue" "$BASE_URL/api/v1/admin/queue"
echo ""

echo "========================================="
echo "5. B2B API (식당 등록 & 관리)"
echo "========================================="
test_api "List Restaurants" "$BASE_URL/api/v1/b2b/restaurants"

# 식당 등록 테스트
echo -n "Testing: Register Restaurant ... "
restaurant_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/b2b/restaurants" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "테스트 식당",
        "owner_name": "김철수",
        "owner_phone": "010-1234-5678",
        "owner_email": "test@example.com",
        "address": "서울시 강남구",
        "business_license": "TEST-'$(date +%s)'"
    }' 2>&1)
http_code=$(echo "$restaurant_response" | tail -n1)
if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
    ((PASSED++))
    RESTAURANT_ID=$(echo "$restaurant_response" | head -n-1 | grep -o '"restaurant_id":"[^"]*"' | cut -d'"' -f4)
    echo "  → Restaurant ID: $RESTAURANT_ID"
else
    echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
    ((FAILED++))
fi
echo ""

echo "========================================="
echo "📊 테스트 결과 요약"
echo "========================================="
TOTAL=$((PASSED + FAILED))
echo "Total: $TOTAL tests"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 테스트 통과!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  일부 테스트 실패${NC}"
    exit 1
fi
