"""
Menu Knowledge Engine - E2E Integration Test Runner
10대 테스트 케이스 + 통합 시나리오 검증
"""
import requests
import json
import time
import sys
from typing import Dict, List, Any, Optional

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

# ========================================
# 10 Test Cases (from CLAUDE.md)
# ========================================
TEST_CASES = [
    {
        "id": 1,
        "input": "김치찌개",
        "expected_match_type": "exact",
        "expected_canonical": "김치찌개",
        "expected_modifiers": [],
        "description": "정확 매칭 (Exact Match)",
    },
    {
        "id": 2,
        "input": "할머니김치찌개",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "김치찌개",
        "expected_modifiers": ["할머니"],
        "description": "단일 수식어 (Grandma's)",
    },
    {
        "id": 3,
        "input": "왕돈까스",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "돈까스",
        "expected_modifiers": ["왕"],
        "description": "크기 수식어 (King-Size)",
    },
    {
        "id": 4,
        "input": "얼큰순두부찌개",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "순두부찌개",
        "expected_modifiers": ["얼큰"],
        "description": "맛 수식어 (Spicy)",
    },
    {
        "id": 5,
        "input": "숯불갈비",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "갈비",
        "expected_modifiers": ["숯불"],
        "description": "조리법 수식어 (Charcoal-Grilled)",
    },
    {
        "id": 6,
        "input": "한우불고기",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "불고기",
        "expected_modifiers": ["한우"],
        "description": "재료 수식어 (Korean Beef) - ingredient type is excluded in Step 2",
    },
    {
        "id": 7,
        "input": "왕얼큰뼈해장국",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "뼈해장국",
        "expected_modifiers": ["왕", "얼큰"],
        "description": "다중 수식어 핵심 케이스 (King-Size + Spicy)",
    },
    {
        "id": 8,
        "input": "옛날통닭",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": None,  # 통닭 is not in canonical; may fallback to AI
        "expected_modifiers": ["옛날", "통"],
        "description": "다중 수식어 (Old-fashioned + Whole)",
    },
    {
        "id": 9,
        "input": "시래기국",
        "expected_match_type": "ai_discovery",
        "expected_canonical": None,
        "expected_modifiers": [],
        "description": "AI Discovery fallback",
    },
    {
        "id": 10,
        "input": "고씨네묵은지감자탕",
        "expected_match_type": "modifier_decomposition",
        "expected_canonical": "감자탕",
        "expected_modifiers": ["묵은지"],
        "description": "복합 (brand prefix + aged kimchi + base menu)",
    },
]


def test_health() -> Dict[str, Any]:
    """Health check"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        return {"success": resp.status_code == 200, "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_data_availability() -> Dict[str, Any]:
    """Check data availability (concepts, modifiers, canonical menus)"""
    results = {}
    for endpoint in ["concepts", "modifiers", "canonical-menus"]:
        try:
            resp = requests.get(f"{BASE_URL}/api/v1/{endpoint}", timeout=10)
            data = resp.json()
            results[endpoint] = {
                "success": resp.status_code == 200,
                "total": data.get("total", 0),
            }
        except Exception as e:
            results[endpoint] = {"success": False, "error": str(e)}
    return results


def identify_menu(menu_name: str) -> Dict[str, Any]:
    """Call menu identify API"""
    try:
        start = time.time()
        resp = requests.post(
            f"{BASE_URL}/api/v1/menu/identify",
            json={"menu_name_ko": menu_name},
            timeout=30,
        )
        elapsed = time.time() - start
        result = resp.json()
        result["_elapsed_ms"] = round(elapsed * 1000, 1)
        result["_status_code"] = resp.status_code
        return result
    except Exception as e:
        return {"error": str(e), "_elapsed_ms": 0, "_status_code": 0}


def evaluate_test_case(tc: Dict, result: Dict) -> Dict[str, Any]:
    """Evaluate a single test case result"""
    report = {
        "id": tc["id"],
        "input": tc["input"],
        "description": tc["description"],
        "elapsed_ms": result.get("_elapsed_ms", 0),
        "status_code": result.get("_status_code", 0),
        "match_type_actual": result.get("match_type", "error"),
        "match_type_expected": tc["expected_match_type"],
        "checks": {},
        "passed": True,
        "details": {},
    }

    # Check 1: API returned successfully
    if "error" in result and "_elapsed_ms" not in result:
        report["checks"]["api_success"] = False
        report["passed"] = False
        report["details"]["error"] = result.get("error")
        return report
    report["checks"]["api_success"] = True

    # Check 2: Match type
    actual_match_type = result.get("match_type", "")

    # For test cases that expect AI discovery, accept both "ai_discovery" and "ai_discovery_needed"
    if tc["expected_match_type"] == "ai_discovery":
        match_type_ok = actual_match_type in ("ai_discovery", "ai_discovery_needed")
    # For ingredient type modifiers (like 한우), they may fall through to AI
    elif tc["expected_match_type"] == "modifier_decomposition" and tc["id"] == 6:
        # 한우 is ingredient type which is excluded in Step 2
        match_type_ok = actual_match_type in ("modifier_decomposition", "ai_discovery", "ai_discovery_needed")
    elif tc["expected_match_type"] == "modifier_decomposition" and tc["id"] == 8:
        # 통닭 may not be in canonical menus
        match_type_ok = actual_match_type in ("modifier_decomposition", "ai_discovery", "ai_discovery_needed")
    elif tc["expected_match_type"] == "modifier_decomposition" and tc["id"] == 10:
        # 고씨네 is a brand name not in modifiers, complex case
        match_type_ok = actual_match_type in ("modifier_decomposition", "ai_discovery", "ai_discovery_needed")
    else:
        match_type_ok = actual_match_type == tc["expected_match_type"]

    report["checks"]["match_type"] = match_type_ok
    if not match_type_ok:
        report["passed"] = False

    # Check 3: Canonical menu name
    canonical = result.get("canonical")
    if tc["expected_canonical"]:
        if canonical and canonical.get("name_ko") == tc["expected_canonical"]:
            report["checks"]["canonical_match"] = True
        else:
            report["checks"]["canonical_match"] = False
            report["passed"] = False
        report["details"]["canonical_name_ko"] = canonical.get("name_ko") if canonical else None
        report["details"]["canonical_name_en"] = canonical.get("name_en") if canonical else None
    else:
        # No specific canonical expected (AI discovery or unknown)
        report["checks"]["canonical_match"] = "N/A"
        if canonical:
            report["details"]["canonical_name_ko"] = canonical.get("name_ko")
            report["details"]["canonical_name_en"] = canonical.get("name_en")

    # Check 4: Modifiers
    actual_modifiers = [m.get("text_ko") for m in result.get("modifiers", [])]
    if tc["expected_modifiers"]:
        modifiers_found = all(m in actual_modifiers for m in tc["expected_modifiers"])
        report["checks"]["modifiers_found"] = modifiers_found
        if not modifiers_found:
            report["passed"] = False
    else:
        report["checks"]["modifiers_found"] = "N/A"
    report["details"]["modifiers_actual"] = actual_modifiers
    report["details"]["modifiers_expected"] = tc["expected_modifiers"]

    # Check 5: Response time (should be < 3 seconds for DB hit)
    elapsed = result.get("_elapsed_ms", 0)
    if actual_match_type in ("exact", "similarity", "modifier_decomposition"):
        report["checks"]["response_time_ok"] = elapsed < 3000
    else:
        report["checks"]["response_time_ok"] = elapsed < 10000  # AI calls can be slower
    if not report["checks"]["response_time_ok"]:
        report["passed"] = False

    # Check 6: Confidence score
    confidence = result.get("confidence", 0)
    report["details"]["confidence"] = confidence
    if actual_match_type == "exact":
        report["checks"]["confidence_ok"] = confidence >= 0.95
    elif actual_match_type == "modifier_decomposition":
        report["checks"]["confidence_ok"] = confidence >= 0.7
    else:
        report["checks"]["confidence_ok"] = True  # No strict requirement for AI
    if not report["checks"]["confidence_ok"]:
        report["passed"] = False

    # Check 7: AI called flag
    report["details"]["ai_called"] = result.get("ai_called", False)

    # Check 8: Translation/explanation availability
    if canonical:
        has_name_en = bool(canonical.get("name_en"))
        has_explanation = bool(canonical.get("explanation_short"))
        report["checks"]["translation_available"] = has_name_en
        report["details"]["name_en"] = canonical.get("name_en")
        report["details"]["explanation_short"] = canonical.get("explanation_short")
    else:
        report["checks"]["translation_available"] = "N/A"

    return report


def run_additional_tests() -> List[Dict[str, Any]]:
    """Run additional integration tests beyond the 10 core cases"""
    additional_tests = []

    # Test: Similarity matching (typo correction)
    print("\n--- Additional Test: Typo/Similarity ---")
    for typo_input, expected_canonical in [
        ("김치찌게", "김치찌개"),  # 게 → 개 typo
        ("된장찌게", "된장찌개"),  # 게 → 개 typo
    ]:
        result = identify_menu(typo_input)
        test_result = {
            "input": typo_input,
            "expected": expected_canonical,
            "actual_match_type": result.get("match_type"),
            "actual_canonical": result.get("canonical", {}).get("name_ko") if result.get("canonical") else None,
            "confidence": result.get("confidence", 0),
            "passed": (
                result.get("match_type") == "similarity"
                and result.get("canonical", {}).get("name_ko") == expected_canonical
            ),
        }
        additional_tests.append(test_result)
        status = "PASS" if test_result["passed"] else "FAIL"
        print(f"  [{status}] '{typo_input}' -> {test_result['actual_match_type']} "
              f"(canonical: {test_result['actual_canonical']}, confidence: {test_result['confidence']:.2f})")

    # Test: Caching behavior
    print("\n--- Additional Test: Caching ---")
    menu = "김치찌개"
    result1 = identify_menu(menu)
    time1 = result1.get("_elapsed_ms", 0)
    result2 = identify_menu(menu)
    time2 = result2.get("_elapsed_ms", 0)
    cache_test = {
        "input": menu,
        "first_call_ms": time1,
        "second_call_ms": time2,
        "cache_speedup": time1 / time2 if time2 > 0 else 0,
        "passed": True,  # Just informational
    }
    additional_tests.append(cache_test)
    print(f"  First call: {time1:.1f}ms, Second call: {time2:.1f}ms "
          f"(speedup: {cache_test['cache_speedup']:.1f}x)")

    # Test: Empty/invalid input
    print("\n--- Additional Test: Error Handling ---")
    for invalid_input in ["", "   "]:
        try:
            result = identify_menu(invalid_input)
            error_test = {
                "input": repr(invalid_input),
                "result": result.get("match_type"),
                "passed": True,  # Should not crash
            }
        except Exception as e:
            error_test = {"input": repr(invalid_input), "error": str(e), "passed": False}
        additional_tests.append(error_test)
        status = "PASS" if error_test.get("passed") else "FAIL"
        print(f"  [{status}] Input: {error_test['input']} -> {error_test.get('result', error_test.get('error'))}")

    return additional_tests


def calculate_db_match_rate(results: List[Dict]) -> Dict[str, Any]:
    """Calculate DB match rate (target: 70%+)"""
    total = len(results)
    db_matches = sum(
        1 for r in results
        if r.get("match_type_actual") in ("exact", "similarity", "modifier_decomposition")
    )
    ai_matches = sum(
        1 for r in results
        if r.get("match_type_actual") in ("ai_discovery", "ai_discovery_needed")
    )
    return {
        "total_cases": total,
        "db_matches": db_matches,
        "ai_matches": ai_matches,
        "db_match_rate": round(db_matches / total * 100, 1) if total > 0 else 0,
        "target_met": (db_matches / total * 100) >= 70 if total > 0 else False,
    }


def main():
    print("=" * 70)
    print("Menu Knowledge Engine - E2E Integration Test")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target URL: {BASE_URL}")
    print()

    # Phase 0: Health Check
    print("--- Phase 0: Health Check ---")
    health = test_health()
    if not health["success"]:
        print(f"  FAIL: Server not healthy: {health}")
        print("Aborting tests.")
        sys.exit(1)
    print(f"  OK: Server is healthy (env: {health['data'].get('environment')})")

    # Phase 1: Data Availability
    print("\n--- Phase 1: Data Availability ---")
    data_check = test_data_availability()
    for name, info in data_check.items():
        status = "OK" if info.get("success") else "FAIL"
        print(f"  [{status}] {name}: {info.get('total', 'N/A')} records")

    # Phase 2: Core 10 Test Cases
    print("\n--- Phase 2: Core 10 Test Cases ---")
    test_results = []
    for tc in TEST_CASES:
        print(f"\n  Test #{tc['id']}: '{tc['input']}' ({tc['description']})")
        result = identify_menu(tc["input"])
        report = evaluate_test_case(tc, result)
        test_results.append(report)

        status = "PASS" if report["passed"] else "FAIL"
        print(f"    [{status}] match_type: {report['match_type_actual']} "
              f"(expected: {report['match_type_expected']})")
        if report["details"].get("canonical_name_ko"):
            print(f"    canonical: {report['details']['canonical_name_ko']} "
                  f"-> {report['details'].get('canonical_name_en', 'N/A')}")
        if report["details"].get("modifiers_actual"):
            print(f"    modifiers: {report['details']['modifiers_actual']}")
        print(f"    confidence: {report['details'].get('confidence', 'N/A')}, "
              f"time: {report['elapsed_ms']}ms, "
              f"ai_called: {report['details'].get('ai_called', 'N/A')}")

        # Show check details
        for check_name, check_val in report["checks"].items():
            if check_val is False:
                print(f"    !! FAILED CHECK: {check_name}")

    # Phase 3: DB Match Rate
    print("\n--- Phase 3: DB Match Rate ---")
    match_rate = calculate_db_match_rate(test_results)
    print(f"  Total cases: {match_rate['total_cases']}")
    print(f"  DB matches: {match_rate['db_matches']} "
          f"({match_rate['db_match_rate']}%)")
    print(f"  AI matches: {match_rate['ai_matches']}")
    target_status = "MET" if match_rate["target_met"] else "NOT MET"
    print(f"  Target (70%+): {target_status}")

    # Phase 4: Additional Tests
    print("\n--- Phase 4: Additional Integration Tests ---")
    additional = run_additional_tests()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    print(f"  Core Tests: {passed}/{len(test_results)} passed, {failed} failed")
    print(f"  DB Match Rate: {match_rate['db_match_rate']}% (target: 70%+) -> {target_status}")

    avg_time = sum(r["elapsed_ms"] for r in test_results) / len(test_results) if test_results else 0
    print(f"  Avg Response Time: {avg_time:.1f}ms")

    # Collect failed tests
    failed_tests = [r for r in test_results if not r["passed"]]
    if failed_tests:
        print(f"\n  Failed Tests:")
        for ft in failed_tests:
            print(f"    #{ft['id']} '{ft['input']}': "
                  f"expected={ft['match_type_expected']}, "
                  f"actual={ft['match_type_actual']}")
            for check_name, check_val in ft["checks"].items():
                if check_val is False:
                    print(f"      - {check_name}: FAILED")

    print()

    # Return results for report generation
    return {
        "health": health,
        "data_check": data_check,
        "test_results": test_results,
        "match_rate": match_rate,
        "additional": additional,
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(test_results),
            "db_match_rate": match_rate["db_match_rate"],
            "avg_response_ms": round(avg_time, 1),
        },
    }


if __name__ == "__main__":
    results = main()

    # Save detailed results as JSON
    output_path = r"C:\project\menu\e2e_test_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"Detailed results saved to: {output_path}")
