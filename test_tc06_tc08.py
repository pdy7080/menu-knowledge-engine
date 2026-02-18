#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-06, TC-08 테스트 스크립트
Issue #1 (한우), Issue #2 (통닭) 수정 검증
"""
import sys
import io
import requests
import json
from typing import Dict, Any

# Windows 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://menu-knowledge.chargeapp.net"

def test_menu_identify(menu_name: str, test_case: str) -> Dict[str, Any]:
    """메뉴 식별 API 호출"""
    url = f"{API_BASE}/api/v1/menu/identify"
    payload = {"menu_name_ko": menu_name}

    print(f"\n{'='*60}")
    print(f"🧪 {test_case}")
    print(f"입력: {menu_name}")
    print(f"{'='*60}")

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        # 결과 출력
        print(f"\n📊 결과:")
        print(f"  - 매칭 방법: {result.get('match_method', 'N/A')}")
        print(f"  - 성공 여부: {result.get('success', False)}")

        if result.get('canonical'):
            canonical = result['canonical']
            print(f"\n✅ Canonical Menu:")
            print(f"  - 한글명: {canonical.get('name_ko', 'N/A')}")
            print(f"  - 영문명: {canonical.get('name_en', 'N/A')}")
            print(f"  - 매운맛: {canonical.get('spice_level', 0)}/5")
            print(f"  - 난이도: {canonical.get('difficulty_score', 0)}/5")

        if result.get('modifiers'):
            print(f"\n🔧 Modifiers ({len(result['modifiers'])}개):")
            for mod in result['modifiers']:
                print(f"  - {mod.get('text_ko')} ({mod.get('type')}) - {mod.get('translation_en')}")

        if result.get('decomposition'):
            decomp = result['decomposition']
            print(f"\n🔍 분해 결과:")
            print(f"  - 수식어: {', '.join(decomp.get('modifiers', []))}")
            print(f"  - 기본 메뉴: {decomp.get('base')}")
            print(f"  - 방법: {decomp.get('method')}")

        # 성공/실패 판정 (match_type이 ai_discovery_needed가 아니고, canonical이 있으면 성공)
        if result.get('canonical') and result.get('match_type') != 'ai_discovery_needed':
            print(f"\n✅ 테스트 통과!")
            return {"status": "PASS", "result": result}
        else:
            print(f"\n❌ 테스트 실패 - Canonical 매칭 안됨")
            return {"status": "FAIL", "result": result}

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API 호출 실패: {e}")
        return {"status": "ERROR", "error": str(e)}
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        return {"status": "ERROR", "error": str(e)}


def main():
    """메인 테스트 실행"""
    print("="*60)
    print("🚀 Menu Knowledge Engine - TC-06, TC-08 검증")
    print("="*60)

    # TC-06: 한우불고기 (Issue #1 검증)
    tc06_result = test_menu_identify("한우불고기", "TC-06: 한우불고기")

    # TC-08: 옛날통닭 (Issue #2 검증)
    tc08_result = test_menu_identify("옛날통닭", "TC-08: 옛날통닭")

    # 최종 결과
    print(f"\n{'='*60}")
    print("📊 최종 결과")
    print(f"{'='*60}")

    results = {
        "TC-06 (한우불고기)": tc06_result["status"],
        "TC-08 (옛날통닭)": tc08_result["status"],
    }

    for tc, status in results.items():
        emoji = "✅" if status == "PASS" else "❌"
        print(f"{emoji} {tc}: {status}")

    # 통과율 계산
    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)
    pass_rate = (passed / total) * 100

    print(f"\n🎯 통과율: {passed}/{total} ({pass_rate:.0f}%)")

    if pass_rate == 100:
        print("\n🎉 Issue #1, #2 수정 완료 검증 성공!")
    else:
        print("\n⚠️ 일부 테스트 실패 - 추가 디버깅 필요")

    return pass_rate == 100


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
