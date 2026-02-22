"""
Sprint 2 Phase 2 P1: 나머지 149개 메뉴 콘텐츠 확장 (Gemini)
2026-02-19

Features:
- Google Gemini API 사용 (무료, OpenAI quota 우회)
- enriched content가 없는 메뉴만 선택
- Category-aware prompts (6 categories)
- Error handling with retry (max 3 attempts)
- Checkpoint saves (every 10 menus)
- Sequential processing (Gemini rate limit 고려)

Based on: enrich_remaining_149_menus.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
import time

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
    elif any(k in menu_name_ko for k in ["면", "냉면", "국수", "칼국수", "잔치국수"]):
        return "noodles"
    else:
        return "stew"  # 기본값


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


class GeminiEnricher:
    """Gemini 기반 메뉴 콘텐츠 확장 엔진"""

    def __init__(self):
        self.enriched_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.checkpoint_interval = 10

    def enrich_menu(
        self, menu: CanonicalMenu, retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """단일 메뉴 콘텐츠 생성 (Gemini, 동기)"""
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
            print(f"  ✅ {menu_name}")
            return result

        except Exception as e:
            if retry_count < 3:
                print(f"  [RETRY {retry_count + 1}/3] {menu_name}: {str(e)[:50]}")
                time.sleep(2)
                return self.enrich_menu(menu, retry_count + 1)
            else:
                print(f"  ❌ {menu_name}: {str(e)[:50]}")
                self.failed_count += 1
                self.errors.append(
                    {
                        "menu_id": str(menu.id),
                        "name_ko": menu_name,
                        "error": str(e),
                        "retry_count": retry_count,
                    }
                )
                return None

    async def enrich_remaining_menus(self, limit: int = 200) -> List[Dict[str, Any]]:
        """enriched content가 없는 메뉴만 처리"""
        async with AsyncSessionLocal() as session:
            # enriched content가 없는 메뉴만 선택
            stmt = (
                select(CanonicalMenu)
                .where(
                    CanonicalMenu.status == "active",
                    CanonicalMenu.description_long_ko == None,
                )
                .limit(limit)
            )
            result = await session.execute(stmt)
            menus = list(result.scalars().all())

            total = len(menus)
            print(f"\n총 {total}개 메뉴 처리 시작 (Gemini 2.5 Flash)")
            print("카테고리: 6개 (stew, soup, grilled, stir-fried, rice, noodles)")
            print("=" * 60)

            # 순차 처리 (Gemini rate limit 고려)
            for i, menu in enumerate(menus, 1):
                result = self.enrich_menu(menu)

                if result:
                    self.results.append(result)

                # 진행도 출력
                progress = i / total * 100
                if i % 10 == 0:
                    print(
                        f"\n[{i}/{total}] 진행: {progress:.1f}% | 성공: {self.enriched_count} | 실패: {self.failed_count}"
                    )

                # 체크포인트 저장 (10개마다)
                if i % (self.checkpoint_interval * 5) == 0:
                    self.save_checkpoint(i)

                # Rate limit (Gemini free tier: 15 RPM)
                time.sleep(1)

            print("\n" + "=" * 60)
            print(f"[OK] 완료: {self.enriched_count}개")
            print(f"[FAIL] 실패: {self.failed_count}개")
            if total > 0:
                print(f"성공률: {self.enriched_count / total * 100:.1f}%")

            return self.results

    def save_checkpoint(self, count: int):
        """체크포인트 저장"""
        checkpoint_path = (
            BASE_DIR.parent.parent / "data" / f"checkpoint_gemini_{count}.json"
        )
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "checkpoint_count": count,
                    "enriched_count": self.enriched_count,
                    "failed_count": self.failed_count,
                    "menus": self.results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"  [CHECKPOINT] 저장: {checkpoint_path.name}")

    def save_results(self, output_path: Path):
        """최종 결과 저장"""
        output_data = {
            "version": "gemini_remaining_149",
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
            "categories": ["stew", "soup", "grilled", "stir-fried", "rice", "noodles"],
            "menus": self.results,
            "errors": self.errors,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 결과 저장: {output_path}")
        print(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")


async def main():
    """메인 함수"""
    print("=" * 60)
    print("Sprint 2 Phase 2 P1: 나머지 149개 메뉴 (Gemini)")
    print("2026-02-19")
    print("=" * 60)

    # 환경변수 확인
    if not settings.GOOGLE_API_KEY:
        print("[ERROR] GOOGLE_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    # Enricher 생성
    enricher = GeminiEnricher()

    # 나머지 메뉴 처리
    await enricher.enrich_remaining_menus(limit=200)

    # 결과 저장
    output_path = BASE_DIR.parent.parent / "data" / "enriched_remaining_gemini_149.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enricher.save_results(output_path)

    # 통계 출력
    print("\n" + "=" * 60)
    print("최종 통계")
    print("=" * 60)
    print(f"처리된 메뉴: {enricher.enriched_count + enricher.failed_count}")
    print(f"성공: {enricher.enriched_count}개")
    print(f"실패: {enricher.failed_count}개")
    if enricher.enriched_count + enricher.failed_count > 0:
        print(
            f"성공률: {enricher.enriched_count / (enricher.enriched_count + enricher.failed_count) * 100:.1f}%"
        )
    print("\n다음 단계: DB 업데이트")
    print(f"  python app/backend/scripts/update_enriched_to_db.py {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
