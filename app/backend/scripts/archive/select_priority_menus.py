"""
Sprint 2 Phase 2 P1: 우선순위 메뉴 50개 선정
2026-02-19

우선순위 기준:
1. 외국인이 자주 접하는 대표 메뉴 (비빔밥, 불고기 등)
2. enriched content가 없는 메뉴
3. 카테고리별 균형 (stew, soup, grilled, rice, noodles)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import asyncio

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from sqlalchemy import select


# 대표 메뉴 키워드 (외국인이 자주 접하는 메뉴)
POPULAR_KEYWORDS = [
    # 밥류 (Rice)
    "비빔밥",
    "김밥",
    "볶음밥",
    "덮밥",
    "돌솥밥",
    "쌈밥",
    # 찌개/국 (Stew/Soup)
    "김치찌개",
    "된장찌개",
    "순두부찌개",
    "부대찌개",
    "청국장",
    "설렁탕",
    "갈비탕",
    "삼계탕",
    "곰탕",
    "해장국",
    # 구이 (Grilled)
    "불고기",
    "갈비",
    "삼겹살",
    "제육볶음",
    "닭갈비",
    # 면 (Noodles)
    "냉면",
    "칼국수",
    "잔치국수",
    "비빔국수",
    "라면",
    # 전/튀김 (Pancakes/Fried)
    "파전",
    "김치전",
    "해물파전",
    "동그랑땡",
    "튀김",
    # 기타 인기 (Other popular)
    "떡볶이",
    "순대",
    "족발",
    "보쌈",
    "삼겹살",
    "치킨",
]


async def select_priority_menus(limit: int = 50) -> List[Dict[str, Any]]:
    """우선순위 메뉴 선정"""
    async with AsyncSessionLocal() as session:
        # 1. enriched content가 없는 메뉴만 선택
        stmt = select(CanonicalMenu).where(
            CanonicalMenu.status == "active", CanonicalMenu.description_long_ko == None
        )
        result = await session.execute(stmt)
        menus = list(result.scalars().all())

        print(f"\n총 {len(menus)}개 메뉴 중 우선순위 {limit}개 선정 중...")
        print("=" * 60)

        # 2. 우선순위 점수 계산
        scored_menus = []
        for menu in menus:
            score = 0

            # 인기 키워드 매칭 (가장 중요)
            for keyword in POPULAR_KEYWORDS:
                if keyword in menu.name_ko:
                    score += 100
                    break

            # 짧은 이름 (기본 메뉴일 가능성)
            if len(menu.name_ko) <= 4:
                score += 50

            # 이미 이미지가 있으면 추가 점수
            if menu.primary_image:
                score += 30

            # 기본 재료 정보가 있으면 추가 점수
            if menu.main_ingredients and len(menu.main_ingredients) > 0:
                score += 20

            scored_menus.append(
                {
                    "menu": menu,
                    "score": score,
                    "name_ko": menu.name_ko,
                    "name_en": menu.name_en,
                }
            )

        # 3. 점수 순으로 정렬
        scored_menus.sort(key=lambda x: x["score"], reverse=True)

        # 4. 상위 N개 선택
        top_menus = scored_menus[:limit]

        # 5. 결과 출력
        print(f"\n선정된 우선순위 메뉴 {len(top_menus)}개:")
        print("=" * 60)

        category_count = {}
        for i, item in enumerate(top_menus, 1):
            menu = item["menu"]
            category = get_category(menu.name_ko)
            category_count[category] = category_count.get(category, 0) + 1

            print(f"{i:2d}. [{item['score']:3d}점] {menu.name_ko} ({menu.name_en})")

        print("\n카테고리별 분포:")
        print("=" * 60)
        for cat, count in sorted(
            category_count.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {cat:15s}: {count:2d}개")

        # 6. JSON 저장
        output_data = {
            "version": "priority_50",
            "total_candidates": len(menus),
            "selected_count": len(top_menus),
            "selection_criteria": {
                "popular_keywords": "외국인 자주 접하는 메뉴",
                "short_names": "기본 메뉴 (4자 이하)",
                "has_image": "이미지 보유",
                "has_ingredients": "재료 정보 보유",
            },
            "menus": [
                {
                    "id": str(item["menu"].id),
                    "name_ko": item["menu"].name_ko,
                    "name_en": item["menu"].name_en,
                    "score": item["score"],
                    "category": get_category(item["menu"].name_ko),
                }
                for item in top_menus
            ],
        }

        output_path = BASE_DIR.parent.parent / "data" / "priority_menus_50.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 저장 완료: {output_path}")

        return [item["menu"] for item in top_menus]


def get_category(menu_name_ko: str) -> str:
    """메뉴명으로부터 카테고리 자동 감지"""
    if any(k in menu_name_ko for k in ["찌개"]):
        return "stew"
    elif any(k in menu_name_ko for k in ["탕", "국", "해장국"]):
        return "soup"
    elif any(k in menu_name_ko for k in ["구이", "불고기", "갈비", "삼겹"]):
        return "grilled"
    elif any(k in menu_name_ko for k in ["볶음", "떡볶이"]):
        return "stir-fried"
    elif any(k in menu_name_ko for k in ["밥", "비빔밥", "김밥", "덮밥"]):
        return "rice"
    elif any(k in menu_name_ko for k in ["면", "냉면", "국수", "칼국수"]):
        return "noodles"
    else:
        return "other"


async def main():
    """메인 함수"""
    print("=" * 60)
    print("Sprint 2 Phase 2 P1: 우선순위 메뉴 50개 선정")
    print("2026-02-19")
    print("=" * 60)

    # 우선순위 메뉴 선정
    priority_menus = await select_priority_menus(limit=50)

    print("\n다음 단계:")
    print("1. Day 1: 20개 처리 (오늘)")
    print("2. Day 2: 20개 처리 (내일)")
    print("3. Day 3: 10개 처리 (모레)")
    print("\n실행:")
    print("  python app/backend/scripts/enrich_priority_batch.py --batch 1")


if __name__ == "__main__":
    asyncio.run(main())
