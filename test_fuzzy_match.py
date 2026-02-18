#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pg_trgm Fuzzy Matching 테스트
Task #8: 오타 자동 교정 검증
"""
import sys
import io
import requests
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://menu-knowledge.chargeapp.net"

# 테스트 케이스: (입력 오타, 예상 교정 결과)
FUZZY_TEST_CASES = [
    ("김치찌게", "김치찌개", "1글자 오타"),
    ("떡복이", "떡볶이", "1글자 오타"),
    ("비빔밥", "비빔밥", "정확 매칭"),
    ("삼겹살", "삼겹살", "정확 매칭"),
    ("불고기", "불고기", "정확 매칭"),
]

def test_fuzzy_match(input_text: str, expected: str, note: str):
    """단일 fuzzy match 테스트"""
    url = f"{API_BASE}/api/v1/menu/identify"
    payload = {"menu_name_ko": input_text}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        match_type = result.get('match_type', 'N/A')
        canonical = result.get('canonical')
        confidence = result.get('confidence', 0.0)

        if canonical:
            canonical_name = canonical.get('name_ko', 'N/A')
        else:
            canonical_name = 'N/A'

        # 성공 판정: canonical이 예상 결과와 일치
        success = canonical_name == expected

        return {
            "input": input_text,
            "expected": expected,
            "actual": canonical_name,
            "match_type": match_type,
            "confidence": confidence,
            "status": "PASS" if success else "FAIL",
            "note": note,
        }

    except Exception as e:
        return {
            "input": input_text,
            "expected": expected,
            "actual": "ERROR",
            "match_type": "ERROR",
            "confidence": 0.0,
            "status": "ERROR",
            "error": str(e),
            "note": note,
        }


def main():
    """메인 테스트 실행"""
    print("=" * 80)
    print("🧪 pg_trgm Fuzzy Matching 테스트 - Task #8")
    print("=" * 80)
    print()

    results = []

    for input_text, expected, note in FUZZY_TEST_CASES:
        print(f"입력: {input_text:10s} 예상: {expected:10s} ({note})...", end=" ")
        result = test_fuzzy_match(input_text, expected, note)
        results.append(result)

        status = result['status']
        if status == "PASS":
            print(f"✅ {status} ({result['match_type']}, {result['confidence']:.2f})")
        elif status == "FAIL":
            print(f"❌ {status} (actual: {result['actual']})")
        else:
            print(f"⚠️ {status}")

    # 결과 테이블
    print()
    print("=" * 80)
    print("📊 상세 결과")
    print("=" * 80)
    print(f"{'입력':<12} {'예상':<12} {'실제':<12} {'매칭방법':<15} {'신뢰도':<8} {'상태':<8}")
    print("-" * 80)

    for r in results:
        input_text = r['input'][:10]
        expected = r['expected'][:10]
        actual = r['actual'][:10]
        match_type = r['match_type'][:13]
        confidence = f"{r['confidence']:.2f}" if r.get('confidence') else 'N/A'
        status = r['status']

        print(f"{input_text:<12} {expected:<12} {actual:<12} {match_type:<15} {confidence:<8} {status:<8}")

    # 통계
    print()
    print("=" * 80)
    print("📈 통과율")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    pass_rate = (passed / total) * 100

    print(f"총 테스트: {total}개")
    print(f"  ✅ 통과: {passed}개")
    print(f"  ❌ 실패: {failed}개")
    print(f"  ⚠️ 에러: {errors}개")
    print()
    print(f"🎯 통과율: {passed}/{total} ({pass_rate:.0f}%)")

    # 목표 달성 여부
    print()
    print("=" * 80)
    if pass_rate >= 100:
        print("🎉 완벽! 모든 테스트 통과!")
        print("✅ pg_trgm Fuzzy Matching 정상 작동")
    elif pass_rate >= 80:
        print("✅ 양호 (80% 이상)")
        print("⚠️ 일부 개선 필요")
    else:
        print("⚠️ 목표 미달")
        print("❌ 추가 작업 필요")

    return pass_rate >= 80


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
