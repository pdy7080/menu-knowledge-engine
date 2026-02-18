#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10대 테스트 케이스 전체 검증
Sprint 1 Week 2 - Task #5
"""
import sys
import io
import requests
import json
from typing import Dict, List, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://menu-knowledge.chargeapp.net"

# 10대 테스트 케이스 정의
TEST_CASES = [
    ("TC-01", "김치찌개", "Kimchi", True, "정확 매칭"),
    ("TC-02", "할머니김치찌개", "Kimchi", True, "브랜드명(할머니) 제거"),
    ("TC-03", "왕돈까스", "Donkatsu", True, "크기 수식어(왕)"),
    ("TC-04", "얼큰순두부찌개", "Sundubu", True, "맛 수식어(얼큰)"),
    ("TC-05", "숯불갈비", "Galbi", True, "조리법 수식어(숯불)"),
    ("TC-06", "한우불고기", "Bulgogi", True, "재료 수식어(한우)"),
    ("TC-07", "왕얼큰뼈해장국", "Haejangguk", True, "다중 수식어(왕+얼큰)"),
    ("TC-08", "옛날통닭", "Tongdak", True, "브랜드명(옛날) + 신규 canonical(통닭)"),
    ("TC-09", "시래기국", "Siraegi", False, "AI Discovery (v0.2)"),
    ("TC-10", "고씨네묵은지감자탕", "Gamjatang", True, "브랜드명(고씨네) + 재료(묵은지)"),
]

def test_menu(tc_id: str, menu_name: str, expected_keyword: str, should_pass: bool, note: str) -> Dict:
    """단일 테스트 케이스 실행"""
    url = f"{API_BASE}/api/v1/menu/identify"
    payload = {"menu_name_ko": menu_name}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        # 판정 기준
        match_type = result.get('match_type', 'N/A')
        canonical = result.get('canonical')
        confidence = result.get('confidence', 0.0)

        # 성공 판정
        if should_pass:
            # TC-09는 AI Discovery 필요 (v0.2 예정)
            success = (
                canonical is not None and
                match_type != 'ai_discovery_needed' and
                confidence >= 0.7
            )
        else:
            # AI Discovery가 필요한 케이스는 ai_discovery_needed가 정상
            success = match_type == 'ai_discovery_needed'

        # 결과 정리
        canonical_name = canonical.get('name_en', 'N/A') if canonical else 'N/A'

        return {
            "tc_id": tc_id,
            "menu_name": menu_name,
            "status": "PASS" if success else "FAIL",
            "match_type": match_type,
            "canonical": canonical_name,
            "confidence": confidence,
            "note": note,
        }

    except Exception as e:
        return {
            "tc_id": tc_id,
            "menu_name": menu_name,
            "status": "ERROR",
            "error": str(e),
            "note": note,
        }


def main():
    """메인 테스트 실행"""
    print("=" * 80)
    print("🧪 Menu Knowledge Engine - 10대 테스트 케이스 전체 검증")
    print("=" * 80)
    print()

    results = []

    for tc_id, menu_name, expected, should_pass, note in TEST_CASES:
        print(f"{tc_id}: {menu_name}...", end=" ")
        result = test_menu(tc_id, menu_name, expected, should_pass, note)
        results.append(result)

        status = result['status']
        if status == "PASS":
            print(f"✅ {status}")
        elif status == "FAIL":
            print(f"❌ {status}")
        else:
            print(f"⚠️ {status}")

    # 결과 테이블
    print()
    print("=" * 80)
    print("📊 상세 결과")
    print("=" * 80)
    print(f"{'TC':<8} {'메뉴명':<20} {'상태':<8} {'매칭방법':<25} {'신뢰도':<8}")
    print("-" * 80)

    for r in results:
        tc_id = r['tc_id']
        menu = r['menu_name'][:18]
        status = r['status']
        match_type = r.get('match_type', 'N/A')[:23]
        confidence = f"{r.get('confidence', 0):.2f}" if r.get('confidence') else 'N/A'

        print(f"{tc_id:<8} {menu:<20} {status:<8} {match_type:<25} {confidence:<8}")

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
    if pass_rate >= 90:
        print("🎉 목표 달성! (90% 이상)")
        print("✅ Sprint 1 성공!")
    elif pass_rate >= 80:
        print("✅ 양호 (80% 이상)")
        print("⚠️ 추가 개선 권장")
    else:
        print("⚠️ 목표 미달 (90% 미만)")
        print("❌ 추가 작업 필요")

    return pass_rate >= 90


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
