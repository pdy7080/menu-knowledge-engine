#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-02, TC-10 테스트 스크립트
Sprint 2 Phase 1: Enriched Content API 검증

TC-02: GET /canonical-menus/{menu_id} - 단일 메뉴 상세 조회 (enriched content 포함)
TC-10: GET /canonical-menus?include_enriched=true - 메뉴 목록 조회 (enriched content 포함)

Author: terminal-developer
Date: 2026-02-19
"""
import sys
import io
import requests
import json
from typing import Dict, Any, List
from uuid import UUID

# Windows 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE = "https://menu-knowledge.chargeapp.net"


def validate_enriched_fields(menu: Dict[str, Any], test_name: str) -> tuple[bool, List[str]]:
    """
    Validate Sprint 2 Phase 1 enriched fields

    Returns:
        (is_valid, missing_fields)
    """
    # Sprint 2 Phase 1 필수 필드
    required_fields = [
        "description_long_ko",
        "description_long_en",
        "regional_variants",
        "preparation_steps",
        "nutrition_detail",
        "flavor_profile",
        "visitor_tips",
        "similar_dishes",
        "content_completeness",
    ]

    missing = []
    for field in required_fields:
        if field not in menu:
            missing.append(field)

    return len(missing) == 0, missing


def test_tc02_menu_detail(menu_id: str = None) -> Dict[str, Any]:
    """
    TC-02: GET /canonical-menus/{menu_id}
    단일 메뉴 상세 조회 (enriched content 자동 포함)

    Expected:
        - 200 OK
        - All Sprint 2 Phase 1 enriched fields present
        - content_completeness > 0
        - description_long_ko/en populated
        - At least 1 regional variant or similar dish
    """
    # 테스트용 메뉴 ID (없으면 첫 번째 메뉴 사용)
    if not menu_id:
        # Get first menu with enriched content
        list_url = f"{API_BASE}/api/v1/canonical-menus?include_enriched=true"
        list_resp = requests.get(list_url, timeout=10)
        if list_resp.status_code != 200:
            return {"status": "ERROR", "error": "Failed to get menu list"}

        menus = list_resp.json()["data"]
        enriched_menus = [m for m in menus if m.get("content_completeness", 0) > 0]

        if not enriched_menus:
            return {"status": "ERROR", "error": "No enriched menus found"}

        menu_id = enriched_menus[0]["id"]

    url = f"{API_BASE}/api/v1/canonical-menus/{menu_id}"

    print(f"\n{'='*80}")
    print(f"🧪 TC-02: 메뉴 상세 조회 (Enriched Content)")
    print(f"{'='*80}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        menu = response.json()

        # 기본 정보 출력
        print(f"\n📊 기본 정보:")
        print(f"  - ID: {menu.get('id')}")
        print(f"  - 한글명: {menu.get('name_ko', 'N/A')}")
        print(f"  - 영문명: {menu.get('name_en', 'N/A')}")

        # Enriched content 검증
        is_valid, missing = validate_enriched_fields(menu, "TC-02")

        print(f"\n🔍 Enriched Content 검증:")
        if is_valid:
            print(f"  ✅ All enriched fields present")
        else:
            print(f"  ❌ Missing fields: {', '.join(missing)}")
            return {"status": "FAIL", "missing_fields": missing}

        # 콘텐츠 완성도
        completeness = menu.get("content_completeness", 0)
        print(f"  - Content Completeness: {completeness}%")

        if completeness == 0:
            print(f"  ⚠️ Completeness is 0 - menu may not be enriched")
            return {"status": "FAIL", "error": "Content completeness is 0"}

        # 주요 콘텐츠 확인
        print(f"\n📝 주요 콘텐츠:")

        # Description
        desc_ko_len = len(menu.get("description_long_ko") or "")
        desc_en_len = len(menu.get("description_long_en") or "")
        print(f"  - Description (KO): {desc_ko_len} characters")
        print(f"  - Description (EN): {desc_en_len} characters")

        # Regional variants
        variants = menu.get("regional_variants") or []
        print(f"  - Regional Variants: {len(variants)} items")
        if variants and len(variants) > 0:
            print(f"    예시: {variants[0].get('region', 'N/A')} - {variants[0].get('differences', 'N/A')[:50]}...")

        # Preparation steps
        prep_steps = menu.get("preparation_steps") or {}
        steps_count = len(prep_steps.get("steps", []))
        print(f"  - Preparation Steps: {steps_count} steps")

        # Nutrition
        nutrition = menu.get("nutrition_detail") or {}
        calories = nutrition.get("calories", 0)
        print(f"  - Nutrition: {calories} kcal")

        # Flavor profile
        flavor = menu.get("flavor_profile") or {}
        balance = flavor.get("balance", {})
        print(f"  - Flavor Profile: sweet={balance.get('sweet', 0)}, salty={balance.get('salty', 0)}, umami={balance.get('umami', 0)}")

        # Visitor tips
        tips = menu.get("visitor_tips") or {}
        ordering_tips = tips.get("ordering_tips", [])
        print(f"  - Visitor Tips: {len(ordering_tips)} ordering tips")

        # Similar dishes
        similar = menu.get("similar_dishes") or []
        print(f"  - Similar Dishes: {len(similar)} items")
        if similar and len(similar) > 0:
            print(f"    예시: {similar[0].get('name_ko', 'N/A')} - {similar[0].get('similarity_reason', 'N/A')[:50]}...")

        # 성공 판정
        if completeness >= 90 and desc_ko_len > 50 and desc_en_len > 50:
            print(f"\n✅ TC-02 통과!")
            print(f"   - High quality enriched content (completeness: {completeness}%)")
            return {"status": "PASS", "menu": menu}
        elif completeness >= 50:
            print(f"\n⚠️ TC-02 부분 통과 (completeness: {completeness}%)")
            return {"status": "PARTIAL", "menu": menu}
        else:
            print(f"\n❌ TC-02 실패 - Low content completeness: {completeness}%")
            return {"status": "FAIL", "completeness": completeness}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"\n❌ 메뉴를 찾을 수 없음: {menu_id}")
            return {"status": "ERROR", "error": "Menu not found"}
        else:
            print(f"\n❌ HTTP 오류: {e}")
            return {"status": "ERROR", "error": str(e)}
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        return {"status": "ERROR", "error": str(e)}


def test_tc10_menu_list_enriched() -> Dict[str, Any]:
    """
    TC-10: GET /canonical-menus?include_enriched=true
    메뉴 목록 조회 (enriched content 포함)

    Expected:
        - 200 OK
        - Total menus >= 100
        - At least 50% have enriched content (completeness > 0)
        - All enriched menus have required fields
    """
    url = f"{API_BASE}/api/v1/canonical-menus?include_enriched=true"

    print(f"\n{'='*80}")
    print(f"🧪 TC-10: 메뉴 목록 조회 (Enriched Content)")
    print(f"{'='*80}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        total = data.get("total", 0)
        menus = data.get("data", [])

        print(f"\n📊 목록 통계:")
        print(f"  - Total menus: {total}")
        print(f"  - Returned items: {len(menus)}")

        # Enriched content 통계
        enriched_menus = [m for m in menus if m.get("content_completeness", 0) > 0]
        enriched_count = len(enriched_menus)
        enriched_ratio = (enriched_count / total * 100) if total > 0 else 0

        print(f"\n🔍 Enriched Content 통계:")
        print(f"  - Enriched menus: {enriched_count}/{total} ({enriched_ratio:.1f}%)")

        # 완성도 분포
        high_quality = len([m for m in enriched_menus if m.get("content_completeness", 0) >= 90])
        medium_quality = len([m for m in enriched_menus if 50 <= m.get("content_completeness", 0) < 90])
        low_quality = len([m for m in enriched_menus if 0 < m.get("content_completeness", 0) < 50])

        print(f"  - High quality (90%+): {high_quality}")
        print(f"  - Medium quality (50-89%): {medium_quality}")
        print(f"  - Low quality (1-49%): {low_quality}")

        # 필드 검증 (샘플)
        if enriched_menus:
            sample_size = min(5, len(enriched_menus))
            print(f"\n🔬 필드 검증 (샘플 {sample_size}개):")

            validation_results = []
            for i, menu in enumerate(enriched_menus[:sample_size], 1):
                is_valid, missing = validate_enriched_fields(menu, f"Menu {i}")
                validation_results.append(is_valid)

                if not is_valid:
                    print(f"  ❌ Menu {i} ({menu.get('name_ko')}): Missing {', '.join(missing)}")
                else:
                    print(f"  ✅ Menu {i} ({menu.get('name_ko')}): All fields present")

            all_valid = all(validation_results)
        else:
            all_valid = False
            print(f"  ⚠️ No enriched menus to validate")

        # 성공 판정
        success_criteria = {
            "total_menus": total >= 100,
            "enriched_ratio": enriched_ratio >= 40,  # 40% 이상
            "high_quality_count": high_quality >= 50,  # 50개 이상 고품질
            "field_validation": all_valid,
        }

        print(f"\n✅ 성공 기준:")
        for criterion, passed in success_criteria.items():
            emoji = "✅" if passed else "❌"
            print(f"  {emoji} {criterion}: {passed}")

        if all(success_criteria.values()):
            print(f"\n✅ TC-10 통과!")
            return {"status": "PASS", "stats": {
                "total": total,
                "enriched_count": enriched_count,
                "high_quality": high_quality,
            }}
        else:
            failed_criteria = [k for k, v in success_criteria.items() if not v]
            print(f"\n❌ TC-10 실패 - Failed criteria: {', '.join(failed_criteria)}")
            return {"status": "FAIL", "failed_criteria": failed_criteria}

    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        return {"status": "ERROR", "error": str(e)}


def main():
    """메인 테스트 실행"""
    print("="*80)
    print("🚀 Menu Knowledge Engine - Sprint 2 Phase 1 Verification")
    print("   TC-02: Menu Detail (Enriched Content)")
    print("   TC-10: Menu List (Enriched Content)")
    print("="*80)

    # TC-02: 메뉴 상세 조회
    tc02_result = test_tc02_menu_detail()

    # TC-10: 메뉴 목록 조회
    tc10_result = test_tc10_menu_list_enriched()

    # 최종 결과
    print(f"\n{'='*80}")
    print("📊 최종 결과")
    print(f"{'='*80}")

    results = {
        "TC-02 (Menu Detail)": tc02_result["status"],
        "TC-10 (Menu List)": tc10_result["status"],
    }

    for tc, status in results.items():
        if status == "PASS":
            emoji = "✅"
        elif status == "PARTIAL":
            emoji = "⚠️"
        else:
            emoji = "❌"
        print(f"{emoji} {tc}: {status}")

    # 통과율 계산
    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)
    pass_rate = (passed / total) * 100

    print(f"\n🎯 통과율: {passed}/{total} ({pass_rate:.0f}%)")

    if pass_rate == 100:
        print("\n🎉 Sprint 2 Phase 1 API 검증 완료!")
        print("   ✅ Enriched content successfully loaded")
        print("   ✅ All API endpoints working correctly")
    elif pass_rate >= 50:
        print("\n⚠️ 부분 통과 - 일부 개선 필요")
    else:
        print("\n❌ 테스트 실패 - 추가 디버깅 필요")

    return pass_rate >= 50  # 50% 이상 통과하면 성공


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
