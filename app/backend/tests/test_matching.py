"""
Menu Matching Engine Tests
8개 테스트 케이스로 3단계 매칭 파이프라인 검증
"""

import asyncio
import httpx
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# Integration test requiring a live server on localhost:8002
pytestmark = pytest.mark.skip(
    reason="Integration test: requires live server on localhost:8002"
)

BASE_URL = "http://localhost:8002"


async def test_matching_engine():
    """
    매칭 엔진 테스트
    """
    test_cases = [
        {
            "name": "Test 1: 김치찌개 - Exact Match",
            "input": "김치찌개",
            "expected_match_type": "exact",
            "expected_canonical_name": "김치찌개",
        },
        {
            "name": "Test 2: 왕갈비탕 - Modifier Decomposition",
            "input": "왕갈비탕",
            "expected_match_type": "modifier_decomposition",
            "expected_canonical_name": "갈비탕",
            "expected_modifiers": ["왕"],
        },
        {
            "name": "Test 3: 얼큰순두부찌개 - Modifier Decomposition",
            "input": "얼큰순두부찌개",
            "expected_match_type": "modifier_decomposition",
            "expected_canonical_name": "순두부찌개",
            "expected_modifiers": ["얼큰"],
        },
        {
            "name": "Test 4: 떡볶이 - Exact Match",
            "input": "떡볶이",
            "expected_match_type": "exact",
            "expected_canonical_name": "떡볶이",
        },
        {
            "name": "Test 5: 제육볶음 - Exact Match",
            "input": "제육볶음",
            "expected_match_type": "exact",
            "expected_canonical_name": "제육볶음",
        },
        {
            "name": "Test 6: 원조할매순대국밥 - Modifier Decomposition",
            "input": "원조할매순대국밥",
            "expected_match_type": "modifier_decomposition",
            "expected_canonical_name": "순대국밥",
            "expected_modifiers": ["할매", "원조"],
        },
        {
            "name": "Test 7: 김치찌게 (오타) - Similarity Match",
            "input": "김치찌게",
            "expected_match_type": "similarity",
            "expected_canonical_name": "김치찌개",
        },
        {
            "name": "Test 8: 부대찌개 - Exact Match",
            "input": "부대찌개",
            "expected_match_type": "exact",
            "expected_canonical_name": "부대찌개",
        },
    ]

    async with httpx.AsyncClient() as client:
        print("\n" + "=" * 80)
        print("Menu Matching Engine Test")
        print("=" * 80 + "\n")

        passed = 0
        failed = 0

        for i, test in enumerate(test_cases, 1):
            print(f"\n[{i}/8] {test['name']}")
            print(f"Input: '{test['input']}'")

            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/menu/identify",
                    json={"menu_name_ko": test["input"]},
                    timeout=10.0,
                )

                if response.status_code != 200:
                    print(f"[FAIL] HTTP {response.status_code}: {response.text}")
                    failed += 1
                    continue

                result = response.json()

                # 결과 출력
                print(f"Match Type: {result['match_type']}")
                if result.get("canonical"):
                    print(
                        f"Canonical: {result['canonical']['name_ko']} ({result['canonical']['name_en']})"
                    )
                if result.get("modifiers"):
                    modifier_texts = [m["text_ko"] for m in result["modifiers"]]
                    print(f"Modifiers: {', '.join(modifier_texts)}")
                print(f"Confidence: {result['confidence']:.2f}")

                # 검증
                success = True

                # match_type 검증
                if result["match_type"] != test["expected_match_type"]:
                    print(
                        f"[FAIL] Expected match_type '{test['expected_match_type']}', got '{result['match_type']}'"
                    )
                    success = False

                # canonical_name 검증 (ai_discovery_needed 제외)
                if test["expected_match_type"] != "ai_discovery_needed":
                    if not result.get("canonical"):
                        print("[FAIL] No canonical menu found")
                        success = False
                    elif result["canonical"]["name_ko"] != test.get(
                        "expected_canonical_name"
                    ):
                        print(
                            f"[FAIL] Expected canonical '{test.get('expected_canonical_name')}', got '{result['canonical']['name_ko']}'"
                        )
                        success = False

                # modifiers 검증
                if "expected_modifiers" in test:
                    found_modifiers = [
                        m["text_ko"] for m in result.get("modifiers", [])
                    ]
                    for expected_mod in test["expected_modifiers"]:
                        if expected_mod not in found_modifiers:
                            print(
                                f"[FAIL] Expected modifier '{expected_mod}' not found"
                            )
                            success = False

                if success:
                    print("[OK] Test passed")
                    passed += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"[FAIL] Exception: {str(e)}")
                failed += 1

        # 최종 결과
        print("\n" + "=" * 80)
        print(f"Test Results: {passed}/8 passed, {failed}/8 failed")
        print("=" * 80 + "\n")

        return passed, failed


if __name__ == "__main__":
    passed, failed = asyncio.run(test_matching_engine())
    sys.exit(0 if failed == 0 else 1)
