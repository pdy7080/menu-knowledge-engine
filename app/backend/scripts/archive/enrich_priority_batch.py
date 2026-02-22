"""
Sprint 2 Phase 2 P1: 우선순위 메뉴 배치 처리 (Gemini)
2026-02-19

Gemini Free Tier 제약:
- 20 requests/day limit
- Batch 1: 메뉴 1-20 (Day 1)
- Batch 2: 메뉴 21-40 (Day 2)
- Batch 3: 메뉴 41-50 (Day 3)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
import time
import argparse

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings
from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from sqlalchemy import select
import asyncio


# Google Gemini 설정
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")


def get_category_from_name(menu_name_ko: str) -> str:
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


def get_category_context(category: str) -> Dict[str, str]:
    """카테고리별 컨텍스트"""
    contexts = {
        "stew": {
            "cooking_method": "broth-based stew (찌개)",
            "prep_hints": "Mention: preparing broth (육수), simmering time, ingredient order",
            "nutrition_range": "300-450 kcal",
            "similar_category": "other stews (찌개류) like 된장찌개, 청국장찌개, 부대찌개",
            "regional_focus": "broth clarity, fermentation level, saltiness",
        },
        "soup": {
            "cooking_method": "clear soup (탕/국)",
            "prep_hints": "Mention: long simmering, bone broth, clear vs cloudy",
            "nutrition_range": "250-400 kcal",
            "similar_category": "other soups (탕/국류) like 설렁탕, 곰탕, 육개장",
            "regional_focus": "broth depth, meat cuts, seasoning style",
        },
        "grilled": {
            "cooking_method": "grilled/barbecue (구이)",
            "prep_hints": "Mention: marinade preparation, marinating time, grilling method (NOT 육수!)",
            "nutrition_range": "450-600 kcal",
            "similar_category": "other grilled dishes (구이류) like 갈비구이, 삼겹살, 제육볶음",
            "regional_focus": "marinade sweetness, spice level, cooking temperature",
        },
        "stir-fried": {
            "cooking_method": "stir-fried (볶음)",
            "prep_hints": "Mention: sauce preparation, stir-frying technique, heat level",
            "nutrition_range": "350-500 kcal",
            "similar_category": "other stir-fried dishes (볶음류) like 제육볶음, 오징어볶음",
            "regional_focus": "sauce thickness, spice level, ingredient ratio",
        },
        "rice": {
            "cooking_method": "rice-based dish (밥류)",
            "prep_hints": "Mention: rice preparation, topping arrangement, mixing method",
            "nutrition_range": "500-700 kcal",
            "similar_category": "other rice dishes (밥류) like 돌솥비빔밥, 볶음밥, 덮밥",
            "regional_focus": "topping variety, sauce type, presentation style",
        },
        "noodles": {
            "cooking_method": "noodle-based dish (면류)",
            "prep_hints": "Mention: noodle type, broth/sauce, temperature (hot/cold)",
            "nutrition_range": "400-600 kcal",
            "similar_category": "other noodle dishes (면류) like 칼국수, 잔치국수, 비빔국수",
            "regional_focus": "noodle texture, broth flavor, toppings",
        },
    }
    return contexts.get(category, contexts["stew"])


class GeminiBatchEnricher:
    """Gemini 기반 배치 메뉴 확장 엔진"""

    def __init__(self, batch_num: int):
        self.batch_num = batch_num
        self.enriched_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def enrich_menu(
        self, menu: CanonicalMenu, retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """단일 메뉴 콘텐츠 생성 (Gemini)"""
        menu_name = menu.name_ko
        category = get_category_from_name(menu_name)
        spice_level = menu.spice_level or 0

        try:
            ctx = get_category_context(category)
            ingredients_str = ", ".join(
                [ing.get("ko", "") for ing in (menu.main_ingredients or [])]
            )

            # Gemini 프롬프트 (JSON 출력 강제)
            prompt = f"""
Generate comprehensive, menu-specific content for the Korean dish below.
Output ONLY a valid JSON object, no additional text.

**Menu Information:**
- Korean Name: {menu_name}
- English Name: {menu.name_en}
- Category: {ctx['cooking_method']}
- Main Ingredients: {ingredients_str}
- Spice Level: {spice_level}/5

**CRITICAL - Menu-Specific Content Rules:**

This is a **{ctx['cooking_method']}** dish.

1. **Regional Variants** - Research ACTUAL differences for {menu_name}:
   - Focus: {ctx['regional_focus']}
   - 3-5 unique regional variations with factual differences

2. **Preparation Steps** - {ctx['prep_hints']}:
   - 5-7 steps specific to {menu_name}
   - Match cooking method category

3. **Nutrition** - Realistic for {ctx['cooking_method']}:
   - Range: {ctx['nutrition_range']}
   - Adjust based on ingredients

4. **Flavor Profile** - Actual taste:
   - Spiciness MUST be {spice_level}/5
   {"- NO spice mention if 0" if spice_level == 0 else ""}

5. **Similar Dishes** - Same category only:
   - {ctx['similar_category']}
   - 3-5 recommendations

6. **Cultural Background** - {menu_name} specific history

Output JSON with 8 fields:
{{
  "description_ko": "Korean description 150-200 chars",
  "description_en": "English description 150-200 chars",
  "regional_variants": [{{"region": "지역명", "differences": "차이점"}}],
  "preparation_steps": [{{"step": 1, "instruction_ko": "한국어 지시", "instruction_en": "English instruction"}}],
  "nutrition": {{"calories": 350, "protein_g": 15, "fat_g": 10, "carbs_g": 45}},
  "flavor_profile": {{"spiciness": {spice_level}, "sweetness": 2, "saltiness": 3, "umami": 4}},
  "visitor_tips": {{"ordering": "주문 팁", "eating": "먹는 법", "pairing": ["추천 반찬1", "추천 반찬2"]}},
  "similar_dishes": ["메뉴1", "메뉴2", "메뉴3"],
  "cultural_background": "역사 및 문화적 의의"
}}
"""

            # Gemini API 호출
            response = model.generate_content(prompt)
            text = response.text

            # JSON 파싱 (Gemini는 종종 마크다운 코드 블록으로 감쌈)
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_str = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                json_str = text[start:end].strip()
            else:
                # JSON 객체만 추출
                start_idx = text.find("{")
                end_idx = text.rfind("}") + 1
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON object found in response")
                json_str = text[start_idx:end_idx]

            content_json = json.loads(json_str)

            result = {
                "menu_id": str(menu.id),
                "name_ko": menu_name,
                "name_en": menu.name_en,
                "category": category,
                "content": content_json,
                "enriched_at": datetime.now().isoformat(),
            }

            self.enriched_count += 1
            print(f"  ✅ [{self.enriched_count:2d}] {menu_name}")
            return result

        except Exception as e:
            error_msg = str(e)

            # Rate limit 에러 감지
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                print(f"\n⚠️  Rate limit 도달! 오늘은 {self.enriched_count}개 완료.")
                print(
                    f"   내일 다시 실행하세요: python scripts/enrich_priority_batch.py --batch {self.batch_num}"
                )
                # Rate limit 도달 시 즉시 종료
                raise Exception("RATE_LIMIT_REACHED")

            if retry_count < 3:
                print(f"  [RETRY {retry_count + 1}/3] {menu_name}: {error_msg[:50]}")
                time.sleep(2)
                return self.enrich_menu(menu, retry_count + 1)
            else:
                print(f"  ❌ {menu_name}: {error_msg[:50]}")
                self.failed_count += 1
                self.errors.append(
                    {
                        "menu_id": str(menu.id),
                        "name_ko": menu_name,
                        "error": error_msg,
                        "retry_count": retry_count,
                    }
                )
                return None

    async def enrich_batch(self) -> List[Dict[str, Any]]:
        """배치별 메뉴 처리"""
        # 우선순위 메뉴 목록 로드
        priority_file = BASE_DIR.parent.parent / "data" / "priority_menus_50.json"
        if not priority_file.exists():
            print(f"❌ 우선순위 파일 없음: {priority_file}")
            print("먼저 실행하세요: python scripts/select_priority_menus.py")
            return []

        with open(priority_file, "r", encoding="utf-8") as f:
            priority_data = json.load(f)

        # 배치 범위 결정
        batch_ranges = {
            1: (0, 20),  # Day 1: 1-20
            2: (20, 40),  # Day 2: 21-40
            3: (40, 50),  # Day 3: 41-50
        }

        if self.batch_num not in batch_ranges:
            print(f"❌ 잘못된 배치 번호: {self.batch_num} (1-3만 가능)")
            return []

        start, end = batch_ranges[self.batch_num]
        batch_menu_ids = [m["id"] for m in priority_data["menus"][start:end]]

        print(
            f"\nBatch {self.batch_num}: 메뉴 {start+1}-{end} ({len(batch_menu_ids)}개)"
        )
        print("=" * 60)

        # DB에서 메뉴 조회
        async with AsyncSessionLocal() as session:
            menus = []
            for menu_id in batch_menu_ids:
                stmt = select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
                result = await session.execute(stmt)
                menu = result.scalars().first()
                if menu:
                    menus.append(menu)

            print(f"DB에서 {len(menus)}개 메뉴 로드 완료\n")

            # 순차 처리 (Rate limit 고려)
            try:
                for i, menu in enumerate(menus, 1):
                    print(f"[{i}/{len(menus)}] ", end="")
                    result = self.enrich_menu(menu)

                    if result:
                        self.results.append(result)

                    # Rate limit 방지 (1초 대기)
                    if i < len(menus):
                        time.sleep(1)

            except Exception as e:
                if "RATE_LIMIT_REACHED" in str(e):
                    # Rate limit 도달 시 현재까지 결과 저장
                    pass
                else:
                    raise

            print("\n" + "=" * 60)
            print(f"완료: {self.enriched_count}개 | 실패: {self.failed_count}개")

            return self.results

    def save_results(self):
        """배치 결과 저장"""
        output_path = (
            BASE_DIR.parent.parent / "data" / f"enriched_batch_{self.batch_num}.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "version": f"priority_batch_{self.batch_num}",
            "batch_number": self.batch_num,
            "total_processed": self.enriched_count + self.failed_count,
            "enriched_count": self.enriched_count,
            "failed_count": self.failed_count,
            "success_rate": (
                self.enriched_count / (self.enriched_count + self.failed_count)
                if (self.enriched_count + self.failed_count) > 0
                else 0
            ),
            "enriched_at": datetime.now().isoformat(),
            "model": "gemini-2.5-flash",
            "menus": self.results,
            "errors": self.errors,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 결과 저장: {output_path}")
        print(f"   파일 크기: {output_path.stat().st_size / 1024:.1f} KB")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="우선순위 메뉴 배치 처리")
    parser.add_argument(
        "--batch",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="배치 번호 (1=Day1, 2=Day2, 3=Day3)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(f"Sprint 2 Phase 2 P1: Batch {args.batch} 처리 (Gemini)")
    print("2026-02-19")
    print("=" * 60)

    # 환경변수 확인
    if not settings.GOOGLE_API_KEY:
        print("[ERROR] GOOGLE_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    # Enricher 생성
    enricher = GeminiBatchEnricher(batch_num=args.batch)

    # 배치 처리
    await enricher.enrich_batch()

    # 결과 저장
    enricher.save_results()

    # 다음 단계 안내
    if args.batch < 3 and enricher.enriched_count > 0:
        print("\n다음 단계 (내일):")
        print(f"  python scripts/enrich_priority_batch.py --batch {args.batch + 1}")


if __name__ == "__main__":
    asyncio.run(main())
