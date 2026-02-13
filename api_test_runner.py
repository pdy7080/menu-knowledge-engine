"""
Menu Knowledge Engine - Comprehensive API Test Runner
Tests all endpoints for correctness, error handling, and response times.
"""
import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds

# Results storage
results = []
total_passed = 0
total_failed = 0
total_skipped = 0


def test_api(name, method, url, expected_status=200, json_data=None, files=None, validate_fn=None):
    """Execute a single API test and record results."""
    global total_passed, total_failed
    result = {
        "name": name,
        "method": method,
        "url": url,
        "expected_status": expected_status,
        "actual_status": None,
        "response_time_ms": None,
        "passed": False,
        "error": None,
        "response_body": None,
        "validation_notes": [],
    }

    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            if files:
                resp = requests.post(url, files=files, timeout=TIMEOUT)
            else:
                resp = requests.post(url, json=json_data, timeout=TIMEOUT)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=TIMEOUT)
        else:
            result["error"] = f"Unsupported method: {method}"
            results.append(result)
            total_failed += 1
            return result

        elapsed_ms = round((time.time() - start) * 1000, 1)
        result["actual_status"] = resp.status_code
        result["response_time_ms"] = elapsed_ms

        # Try to parse JSON response
        try:
            result["response_body"] = resp.json()
        except Exception:
            result["response_body"] = resp.text[:500]

        # Status check
        if resp.status_code == expected_status:
            result["passed"] = True

            # Response time check (target: < 3000ms)
            if elapsed_ms > 3000:
                result["validation_notes"].append(f"SLOW: {elapsed_ms}ms > 3000ms target")
            elif elapsed_ms > 1000:
                result["validation_notes"].append(f"WARNING: {elapsed_ms}ms approaching limit")

            # Custom validation
            if validate_fn:
                try:
                    notes = validate_fn(resp.json())
                    if notes:
                        result["validation_notes"].extend(notes)
                except Exception as e:
                    result["validation_notes"].append(f"Validation error: {str(e)}")
                    result["passed"] = False

        else:
            result["passed"] = False
            result["error"] = f"Expected {expected_status}, got {resp.status_code}"

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out (>10s)"
        result["passed"] = False
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused - server not running?"
        result["passed"] = False
    except Exception as e:
        result["error"] = str(e)
        result["passed"] = False

    if result["passed"]:
        total_passed += 1
        status_icon = "PASS"
    else:
        total_failed += 1
        status_icon = "FAIL"

    print(f"  [{status_icon}] {name} - {result['actual_status'] or 'N/A'} ({result['response_time_ms'] or 'N/A'}ms)")
    if result["error"]:
        print(f"         Error: {result['error']}")
    for note in result["validation_notes"]:
        print(f"         Note: {note}")

    results.append(result)
    return result


# ==============================================================
# SECTION 1: Health Check & Root Endpoints
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 1: Health Check & Root Endpoints")
print("=" * 60)

test_api(
    "GET /health - Health Check",
    "GET", f"{BASE_URL}/health",
    validate_fn=lambda data: [
        f"Missing 'status' field" if "status" not in data else None,
        f"Status is not 'ok': {data.get('status')}" if data.get("status") != "ok" else None,
        f"Missing 'version' field" if "version" not in data else None,
        f"Missing 'service' field" if "service" not in data else None,
    ]
)

test_api(
    "GET / - Root Endpoint",
    "GET", f"{BASE_URL}/",
    validate_fn=lambda data: [
        f"Missing 'message' field" if "message" not in data else None,
        f"Missing 'docs' field" if "docs" not in data else None,
        f"Missing 'api' field" if "api" not in data else None,
    ]
)

test_api(
    "GET /docs - Swagger UI",
    "GET", f"{BASE_URL}/docs",
)

test_api(
    "GET /openapi.json - OpenAPI Schema",
    "GET", f"{BASE_URL}/openapi.json",
    validate_fn=lambda data: [
        f"Missing 'openapi' field" if "openapi" not in data else None,
        f"Missing 'paths' field" if "paths" not in data else None,
    ]
)

# ==============================================================
# SECTION 2: Menu Data Retrieval APIs
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 2: Menu Data Retrieval APIs")
print("=" * 60)

test_api(
    "GET /api/v1/concepts - Get Concepts",
    "GET", f"{BASE_URL}/api/v1/concepts",
    validate_fn=lambda data: [
        f"Missing 'total' field" if "total" not in data else None,
        f"Missing 'data' field" if "data" not in data else None,
        f"No concepts found (total=0)" if data.get("total", 0) == 0 else None,
        f"Data is not a list" if not isinstance(data.get("data"), list) else None,
    ]
)

test_api(
    "GET /api/v1/modifiers - Get Modifiers",
    "GET", f"{BASE_URL}/api/v1/modifiers",
    validate_fn=lambda data: [
        f"Missing 'total' field" if "total" not in data else None,
        f"Missing 'data' field" if "data" not in data else None,
        f"Expected ~50 modifiers, got {data.get('total', 0)}" if data.get("total", 0) < 10 else None,
    ]
)

test_api(
    "GET /api/v1/canonical-menus - Get Canonical Menus",
    "GET", f"{BASE_URL}/api/v1/canonical-menus",
    validate_fn=lambda data: [
        f"Missing 'total' field" if "total" not in data else None,
        f"Missing 'data' field" if "data" not in data else None,
        f"Expected ~100 menus, got {data.get('total', 0)}" if data.get("total", 0) < 10 else None,
    ]
)

# ==============================================================
# SECTION 3: Menu Matching API (Core Engine)
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 3: Menu Matching API (Core Engine)")
print("=" * 60)

# Test 1: Exact match
test_api(
    "POST /menu/identify - Exact Match (kimchi-jjigae)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "김치찌개"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
        f"Expected exact_match, got {data.get('match_type')}" if data.get("match_type") not in ["exact_match", "exact"] else None,
        f"Missing 'canonical' field" if "canonical" not in data else None,
    ]
)

# Test 2: Single modifier
test_api(
    "POST /menu/identify - Single Modifier (halmeoni-kimchi-jjigae)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "할머니김치찌개"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 3: Size modifier
test_api(
    "POST /menu/identify - Size Modifier (wang-donkatsu)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "왕돈까스"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 4: Taste modifier
test_api(
    "POST /menu/identify - Taste Modifier (eolkeun-sundubu-jjigae)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "얼큰순두부찌개"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 5: Cooking method modifier
test_api(
    "POST /menu/identify - Cooking Modifier (sutbul-galbi)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "숯불갈비"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 6: Multiple modifiers (key test case)
test_api(
    "POST /menu/identify - Multi Modifier (wang-eolkeun-ppyeo-haejangguk)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "왕얼큰뼈해장국"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 7: AI Discovery needed
test_api(
    "POST /menu/identify - AI Discovery (sirae-gi-guk)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "시래기국"},
    validate_fn=lambda data: [
        f"Missing 'match_type' field" if "match_type" not in data else None,
    ]
)

# Test 8: Error case - empty input
test_api(
    "POST /menu/identify - Empty Input (error case)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": ""},
    expected_status=422,  # or 400 - validation error
)

# Test 9: Error case - missing field
test_api(
    "POST /menu/identify - Missing Field (error case)",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={},
    expected_status=422,
)

# ==============================================================
# SECTION 4: Admin APIs
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 4: Admin APIs")
print("=" * 60)

test_api(
    "GET /api/v1/admin/stats - Engine Statistics",
    "GET", f"{BASE_URL}/api/v1/admin/stats",
    validate_fn=lambda data: [
        f"Missing 'canonical_count'" if "canonical_count" not in data else None,
        f"Missing 'modifier_count'" if "modifier_count" not in data else None,
        f"Missing 'pending_queue_count'" if "pending_queue_count" not in data else None,
        f"Missing 'scans_7d'" if "scans_7d" not in data else None,
        f"Missing 'db_hit_rate_7d'" if "db_hit_rate_7d" not in data else None,
    ]
)

# Test cache hit (second call should be faster)
test_api(
    "GET /api/v1/admin/stats - Cache Hit (2nd call)",
    "GET", f"{BASE_URL}/api/v1/admin/stats",
    validate_fn=lambda data: [
        f"Missing 'canonical_count'" if "canonical_count" not in data else None,
    ]
)

test_api(
    "GET /api/v1/admin/queue - Menu Queue (all)",
    "GET", f"{BASE_URL}/api/v1/admin/queue",
    validate_fn=lambda data: [
        f"Missing 'total' field" if "total" not in data else None,
        f"Missing 'data' field" if "data" not in data else None,
    ]
)

test_api(
    "GET /api/v1/admin/queue?status=pending - Queue (pending filter)",
    "GET", f"{BASE_URL}/api/v1/admin/queue?status=pending",
)

test_api(
    "GET /api/v1/admin/queue?source=b2c - Queue (B2C filter)",
    "GET", f"{BASE_URL}/api/v1/admin/queue?source=b2c",
)

test_api(
    "POST /api/v1/admin/queue/{bad_id}/approve - 404 Error",
    "POST", f"{BASE_URL}/api/v1/admin/queue/00000000-0000-0000-0000-000000000000/approve",
    json_data={"action": "approve"},
    expected_status=404,
)

# ==============================================================
# SECTION 5: B2B APIs (Restaurant Management)
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 5: B2B APIs (Restaurant Management)")
print("=" * 60)

test_api(
    "GET /api/v1/b2b/restaurants - List Restaurants",
    "GET", f"{BASE_URL}/api/v1/b2b/restaurants",
    validate_fn=lambda data: [
        f"Missing 'total' field" if "total" not in data else None,
        f"Missing 'data' field" if "data" not in data else None,
    ]
)

test_api(
    "GET /api/v1/b2b/restaurants?status=active - Filter by Status",
    "GET", f"{BASE_URL}/api/v1/b2b/restaurants?status=active",
)

# Register a test restaurant
unique_license = f"TEST-API-{int(time.time())}"
register_result = test_api(
    "POST /api/v1/b2b/restaurants - Register Restaurant",
    "POST", f"{BASE_URL}/api/v1/b2b/restaurants",
    json_data={
        "name": "API Test Restaurant",
        "owner_name": "Test Owner",
        "owner_phone": "010-0000-0000",
        "owner_email": "apitest@example.com",
        "address": "Seoul Test Address",
        "business_license": unique_license,
    },
    validate_fn=lambda data: [
        f"Missing 'restaurant_id'" if "restaurant_id" not in data else None,
        f"Missing 'status'" if "status" not in data else None,
    ]
)

# Get the registered restaurant ID
restaurant_id = None
if register_result["passed"] and register_result["response_body"]:
    restaurant_id = register_result["response_body"].get("restaurant_id")
    print(f"         Registered restaurant ID: {restaurant_id}")

# Test getting the restaurant
if restaurant_id:
    test_api(
        "GET /api/v1/b2b/restaurants/{id} - Get Restaurant",
        "GET", f"{BASE_URL}/api/v1/b2b/restaurants/{restaurant_id}",
        validate_fn=lambda data: [
            f"Missing 'id' field" if "id" not in data else None,
            f"Missing 'name' field" if "name" not in data else None,
        ]
    )

# Test duplicate registration (same business license)
test_api(
    "POST /api/v1/b2b/restaurants - Duplicate License (error case)",
    "POST", f"{BASE_URL}/api/v1/b2b/restaurants",
    json_data={
        "name": "Duplicate Restaurant",
        "owner_name": "Owner",
        "owner_phone": "010-0000-0001",
        "address": "Seoul",
        "business_license": unique_license,
    },
    expected_status=400,
)

# Test 404 for non-existent restaurant
test_api(
    "GET /api/v1/b2b/restaurants/{bad_id} - 404 Error",
    "GET", f"{BASE_URL}/api/v1/b2b/restaurants/00000000-0000-0000-0000-000000000000",
    expected_status=404,
)

# Test approve restaurant
if restaurant_id:
    test_api(
        "POST /api/v1/b2b/restaurants/{id}/approve - Approve Restaurant",
        "POST", f"{BASE_URL}/api/v1/b2b/restaurants/{restaurant_id}/approve",
        json_data={
            "action": "approve",
            "admin_user_id": "test-admin",
        },
        validate_fn=lambda data: [
            f"Missing 'success' field" if "success" not in data else None,
        ]
    )

# Test invalid approval action
if restaurant_id:
    test_api(
        "POST /api/v1/b2b/restaurants/{id}/approve - Invalid Action (error case)",
        "POST", f"{BASE_URL}/api/v1/b2b/restaurants/{restaurant_id}/approve",
        json_data={
            "action": "invalid_action",
            "admin_user_id": "test-admin",
        },
        expected_status=400,
    )

# ==============================================================
# SECTION 6: OCR / Menu Recognition API
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 6: OCR / Menu Recognition API")
print("=" * 60)

# Test without file (error case)
test_api(
    "POST /api/v1/menu/recognize - No File (error case)",
    "POST", f"{BASE_URL}/api/v1/menu/recognize",
    expected_status=422,
)

# ==============================================================
# SECTION 7: QR Menu Page
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 7: QR Menu Page")
print("=" * 60)

test_api(
    "GET /qr/INVALID_CODE - Non-existent Shop (404 page)",
    "GET", f"{BASE_URL}/qr/INVALID_CODE",
    expected_status=200,  # Returns HTML 200 with friendly error page
)

test_api(
    "GET /qr/INVALID_CODE?lang=ja - 404 page (Japanese)",
    "GET", f"{BASE_URL}/qr/INVALID_CODE?lang=ja",
    expected_status=200,
)

test_api(
    "GET /qr/INVALID_CODE?lang=zh - 404 page (Chinese)",
    "GET", f"{BASE_URL}/qr/INVALID_CODE?lang=zh",
    expected_status=200,
)

# ==============================================================
# SECTION 8: Edge Cases & Error Handling
# ==============================================================
print("\n" + "=" * 60)
print("SECTION 8: Edge Cases & Error Handling")
print("=" * 60)

test_api(
    "GET /nonexistent - 404 for Unknown Route",
    "GET", f"{BASE_URL}/nonexistent",
    expected_status=404,
)

test_api(
    "POST /api/v1/menu/identify - Very Long Input",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "A" * 1000},
)

test_api(
    "POST /api/v1/menu/identify - Special Characters",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "!@#$%^&*()"},
)

test_api(
    "POST /api/v1/menu/identify - Korean + English Mix",
    "POST", f"{BASE_URL}/api/v1/menu/identify",
    json_data={"menu_name_ko": "BBQ 치킨"},
)

# ==============================================================
# Generate Report
# ==============================================================
print("\n" + "=" * 60)
print("TEST RESULTS SUMMARY")
print("=" * 60)

total = total_passed + total_failed
print(f"Total Tests: {total}")
print(f"Passed:      {total_passed}")
print(f"Failed:      {total_failed}")
print(f"Pass Rate:   {total_passed/total*100:.1f}%" if total > 0 else "N/A")

# Calculate average response time
response_times = [r["response_time_ms"] for r in results if r["response_time_ms"] is not None]
if response_times:
    avg_time = sum(response_times) / len(response_times)
    max_time = max(response_times)
    min_time = min(response_times)
    print(f"Avg Response: {avg_time:.1f}ms")
    print(f"Min Response: {min_time:.1f}ms")
    print(f"Max Response: {max_time:.1f}ms")
    slow_count = len([t for t in response_times if t > 3000])
    print(f"Slow (>3s):  {slow_count}")

# List all failed tests
if total_failed > 0:
    print(f"\nFailed Tests:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['name']}: {r['error'] or 'validation failed'}")

# Export detailed JSON results
report_data = {
    "test_date": datetime.now().isoformat(),
    "base_url": BASE_URL,
    "summary": {
        "total": total,
        "passed": total_passed,
        "failed": total_failed,
        "pass_rate": f"{total_passed/total*100:.1f}%" if total > 0 else "N/A",
        "avg_response_ms": round(avg_time, 1) if response_times else None,
        "max_response_ms": round(max_time, 1) if response_times else None,
        "min_response_ms": round(min_time, 1) if response_times else None,
        "slow_requests": slow_count if response_times else 0,
    },
    "results": results,
}

# Write JSON report
with open("C:/project/menu/api_test_results.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nDetailed JSON report: C:/project/menu/api_test_results.json")

print("\nDone.")
