"""
10개 메뉴 콘텐츠 확장 V2 - 메뉴별 맞춤형 콘텐츠
Team Lead Feedback 반영: 카테고리 인식, 실제 지역 차이, 메뉴별 맞춤 정보

Improvements:
1. Menu category detection (stew/soup, grilled, rice/noodles, etc.)
2. Category-specific preparation steps
3. Realistic nutrition values by category
4. Menu-specific regional variants
5. Category-matching similar dishes
6. Accurate cultural background per dish

Author: content-engineer
Date: 2026-02-19
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import openai

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings

# OpenAI 클라이언트
client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# 10개 테스트 메뉴 데이터
TEST_MENUS = [
    {
        "id": "test-001",
        "name_ko": "김치찌개",
        "name_en": "Kimchi Jjigae (Kimchi Stew)",
        "category": "stew",
        "main_ingredients": [
            {"ko": "김치", "en": "kimchi"},
            {"ko": "돼지고기", "en": "pork"},
            {"ko": "두부", "en": "tofu"}
        ],
        "spice_level": 3
    },
    {
        "id": "test-002",
        "name_ko": "비빔밥",
        "name_en": "Bibimbap (Mixed Rice with Vegetables)",
        "category": "rice",
        "main_ingredients": [
            {"ko": "밥", "en": "rice"},
            {"ko": "나물", "en": "seasoned vegetables"},
            {"ko": "고추장", "en": "gochujang"}
        ],
        "spice_level": 2
    },
    {
        "id": "test-003",
        "name_ko": "갈비탕",
        "name_en": "Galbitang (Short Rib Soup)",
        "category": "soup",
        "main_ingredients": [
            {"ko": "소갈비", "en": "beef short ribs"},
            {"ko": "무", "en": "radish"},
            {"ko": "대파", "en": "green onions"}
        ],
        "spice_level": 0
    },
    {
        "id": "test-004",
        "name_ko": "순두부찌개",
        "name_en": "Sundubu Jjigae (Soft Tofu Stew)",
        "category": "stew",
        "main_ingredients": [
            {"ko": "순두부", "en": "soft tofu"},
            {"ko": "해산물", "en": "seafood"},
            {"ko": "고춧가루", "en": "red pepper flakes"}
        ],
        "spice_level": 3
    },
    {
        "id": "test-005",
        "name_ko": "불고기",
        "name_en": "Bulgogi (Korean BBQ Beef)",
        "category": "grilled",
        "main_ingredients": [
            {"ko": "소고기", "en": "beef"},
            {"ko": "양파", "en": "onion"},
            {"ko": "당근", "en": "carrot"}
        ],
        "spice_level": 0
    },
    {
        "id": "test-006",
        "name_ko": "냉면",
        "name_en": "Naengmyeon (Cold Noodles)",
        "category": "noodles",
        "main_ingredients": [
            {"ko": "메밀면", "en": "buckwheat noodles"},
            {"ko": "육수", "en": "broth"},
            {"ko": "무", "en": "radish"}
        ],
        "spice_level": 1
    },
    {
        "id": "test-007",
        "name_ko": "삼계탕",
        "name_en": "Samgyetang (Ginseng Chicken Soup)",
        "category": "soup",
        "main_ingredients": [
            {"ko": "영계", "en": "young chicken"},
            {"ko": "인삼", "en": "ginseng"},
            {"ko": "찹쌀", "en": "glutinous rice"}
        ],
        "spice_level": 0
    },
    {
        "id": "test-008",
        "name_ko": "떡볶이",
        "name_en": "Tteokbokki (Spicy Rice Cakes)",
        "category": "stir-fried",
        "main_ingredients": [
            {"ko": "떡", "en": "rice cakes"},
            {"ko": "고추장", "en": "gochujang"},
            {"ko": "어묵", "en": "fish cakes"}
        ],
        "spice_level": 4
    },
    {
        "id": "test-009",
        "name_ko": "잡채",
        "name_en": "Japchae (Stir-fried Glass Noodles)",
        "category": "stir-fried",
        "main_ingredients": [
            {"ko": "당면", "en": "glass noodles"},
            {"ko": "야채", "en": "vegetables"},
            {"ko": "소고기", "en": "beef"}
        ],
        "spice_level": 0
    },
    {
        "id": "test-010",
        "name_ko": "김밥",
        "name_en": "Gimbap (Seaweed Rice Roll)",
        "category": "rice",
        "main_ingredients": [
            {"ko": "김", "en": "seaweed"},
            {"ko": "밥", "en": "rice"},
            {"ko": "계란", "en": "egg"}
        ],
        "spice_level": 0
    }
]


def get_category_context(category: str, menu_name_ko: str) -> Dict[str, str]:
    """카테고리별 컨텍스트 정보 생성"""
    contexts = {
        "stew": {
            "cooking_method": "broth-based stew (찌개)",
            "prep_hints": "Mention: preparing broth (육수), simmering time, ingredient order",
            "nutrition_range": "300-450 kcal (moderate)",
            "similar_category": "other stews (찌개류) like 된장찌개, 청국장찌개, 부대찌개",
            "regional_focus": "broth clarity, fermentation level, saltiness"
        },
        "soup": {
            "cooking_method": "clear soup (탕/국)",
            "prep_hints": "Mention: long simmering, bone broth, clear vs cloudy",
            "nutrition_range": "250-400 kcal (light to moderate)",
            "similar_category": "other soups (탕/국류) like 설렁탕, 곰탕, 육개장",
            "regional_focus": "broth depth, meat cuts, seasoning style"
        },
        "grilled": {
            "cooking_method": "grilled/barbecue (구이)",
            "prep_hints": "Mention: marinade preparation, marinating time, grilling method (NOT 육수!)",
            "nutrition_range": "450-600 kcal (high protein)",
            "similar_category": "other grilled dishes (구이류) like 갈비구이, 삼겹살, 제육볶음",
            "regional_focus": "marinade sweetness, spice level, cooking temperature"
        },
        "stir-fried": {
            "cooking_method": "stir-fried (볶음)",
            "prep_hints": "Mention: sauce preparation, stir-frying technique, heat level",
            "nutrition_range": "350-500 kcal (moderate to high)",
            "similar_category": "other stir-fried dishes (볶음류) like 제육볶음, 오징어볶음, 낙지볶음",
            "regional_focus": "sauce thickness, spice level, ingredient ratio"
        },
        "rice": {
            "cooking_method": "rice-based dish (밥류)",
            "prep_hints": "Mention: rice preparation, topping arrangement, mixing method",
            "nutrition_range": "500-700 kcal (filling meal)",
            "similar_category": "other rice dishes (밥류) like 돌솥비빔밥, 볶음밥, 덮밥",
            "regional_focus": "topping variety, sauce type, presentation style"
        },
        "noodles": {
            "cooking_method": "noodle-based dish (면류)",
            "prep_hints": "Mention: noodle type, broth/sauce, temperature (hot/cold)",
            "nutrition_range": "400-600 kcal (moderate to high)",
            "similar_category": "other noodle dishes (면류) like 칼국수, 잔치국수, 비빔국수",
            "regional_focus": "noodle texture, broth flavor, toppings"
        }
    }
    return contexts.get(category, contexts["stew"])


async def enrich_single_menu(menu_data: Dict[str, Any]) -> Dict[str, Any]:
    """단일 메뉴 콘텐츠 생성 (V2 - 카테고리 인식)"""
    menu_name = menu_data['name_ko']
    category = menu_data.get('category', 'stew')
    spice_level = menu_data.get('spice_level', 0)

    print(f"\n처리 중: {menu_name} ({menu_data['name_en']}) [Category: {category}]")

    # 카테고리별 컨텍스트
    ctx = get_category_context(category, menu_name)

    # 재료 문자열
    ingredients_str = ", ".join([
        ing.get("ko", "") for ing in menu_data.get("main_ingredients", [])
    ])

    # 개선된 GPT-4o-mini 프롬프트
    prompt = f"""
Generate comprehensive, menu-specific content for the Korean dish below.

**Menu Information:**
- Korean Name: {menu_name}
- English Name: {menu_data['name_en']}
- Category: {ctx['cooking_method']}
- Main Ingredients: {ingredients_str}
- Spice Level: {spice_level}/5

**CRITICAL INSTRUCTIONS - Menu Category Awareness:**

This is a **{ctx['cooking_method']}** dish.

1. **Regional Variants** - Research ACTUAL regional differences for {menu_name}:
   - Focus on: {ctx['regional_focus']}
   - DO NOT use generic templates
   - Each region MUST have unique, factual differences
   - Examples: ingredient substitutions, cooking methods, flavor profiles

2. **Preparation Steps** - {ctx['prep_hints']}:
   - Steps MUST match this cooking method
   - Be specific to {menu_name}
   - 5-7 detailed, sequential steps

3. **Nutrition** - Realistic values for {ctx['cooking_method']}:
   - Target range: {ctx['nutrition_range']}
   - Research typical serving size for {menu_name}
   - Adjust protein/fat/carbs based on main ingredients

4. **Flavor Profile** - Based on actual taste:
   - Spiciness: {spice_level}/5 (MUST match spice_level)
   - Other flavors: research {menu_name} typical taste

5. **Visitor Tips**:
   - Ordering: specific to {menu_name} (variations, portion size)
   - Eating: proper way to eat {menu_name}
   - Pairing: traditional side dishes for this category
   {"- DO NOT mention spice level if spiciness is 0" if spice_level == 0 else "- Mention spice customization"}

6. **Similar Dishes** - SAME category only:
   - Recommend: {ctx['similar_category']}
   - NO cross-category mixing (no soups if this is grilled!)
   - Explain similarity (cooking method, ingredients, or flavor)

7. **Cultural Background** - Research {menu_name} specifically:
   - Actual historical origin of THIS dish
   - Regional significance
   - Cultural context (seasonal, ceremonial, daily meal, etc.)
   - DO NOT use generic Korean food history

**Output Format (JSON):**

{{
  "description_ko": "150-200자 상세 설명 (한국어, {menu_name}의 고유한 특징과 맛)",
  "description_en": "150-200 chars detailed description (English, unique characteristics of {menu_name})",

  "regional_variants": [
    {{"name": "지역명1", "difference": "{menu_name}의 실제 지역별 차이점"}},
    {{"name": "지역명2", "difference": "다른 지역의 고유한 특징"}},
    {{"name": "지역명3", "difference": "또 다른 지역의 차별점"}}
  ],

  "preparation_steps": [
    "{menu_name}에 맞는 구체적인 조리 1단계",
    "2단계...",
    "5-7단계까지"
  ],

  "nutrition": {{
    "calories": {ctx['nutrition_range'].split('-')[0].split()[0]},
    "protein_g": 20,
    "fat_g": 15,
    "carbs_g": 40,
    "serving_size": "1인분 (적절한 g)"
  }},

  "flavor_profile": {{
    "spiciness": {spice_level},
    "sweetness": 1-5,
    "saltiness": 1-5,
    "umami": 1-5,
    "sourness": 1-5
  }},

  "visitor_tips": {{
    "ordering": "{menu_name} 주문 팁",
    "eating": "{menu_name} 먹는 법",
    "pairing": "{category}에 어울리는 반찬"
  }},

  "similar_dishes": [
    {{"name": "{category}의 유사 메뉴1", "similarity": "유사점 설명"}},
    {{"name": "{category}의 유사 메뉴2", "similarity": "유사점 설명"}},
    {{"name": "{category}의 유사 메뉴3", "similarity": "유사점 설명"}}
  ],

  "cultural_background": {{
    "history": "{menu_name}의 실제 역사 (2-3문장)",
    "origin": "{menu_name}의 기원 지역 또는 시대",
    "cultural_notes": "{menu_name}의 문화적 의미 (2-3문장)"
  }}
}}

**REMEMBER**: Every field must be specific to {menu_name}, not generic Korean food templates!
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Korean food historian and culinary expert. "
                        "You have deep knowledge of regional variations, traditional cooking methods, "
                        "and cultural significance of Korean dishes. "
                        "Provide accurate, menu-specific information based on actual culinary research. "
                        "Output ONLY valid JSON, no markdown fences."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content_text = response.choices[0].message.content.strip()
        content_json = json.loads(content_text)

        print("  [OK] 완료")
        return {
            "menu_id": menu_data["id"],
            "name_ko": menu_data["name_ko"],
            "name_en": menu_data["name_en"],
            "category": category,
            "content": content_json,
            "enriched_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  [ERROR] 오류: {str(e)}")
        return None


async def main():
    """메인 함수 - V2 개선 버전"""
    print("="*60)
    print("GPT-4o-mini 콘텐츠 확장 V2 - 메뉴별 맞춤형")
    print("Team Lead Feedback 반영")
    print("="*60)

    if not settings.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"\n테스트 메뉴: {len(TEST_MENUS)}개")
    print(f"개선 사항:")
    print("  - 카테고리별 맞춤 조리법")
    print("  - 실제 지역 차이 반영")
    print("  - 메뉴별 정확한 영양정보")
    print("  - 카테고리 일치 유사 메뉴")
    print("="*60)

    results = []
    for i, menu in enumerate(TEST_MENUS, 1):
        print(f"\n[{i}/{len(TEST_MENUS)}]", end=" ")
        result = await enrich_single_menu(menu)
        if result:
            results.append(result)
        await asyncio.sleep(1.5)  # 조금 더 여유있는 rate limit

    # 결과 저장
    output_path = BASE_DIR.parent.parent / "data" / "enriched_test_v2.json"
    output_data = {
        "version": "v2",
        "improvements": "category-aware, menu-specific content",
        "test_batch_size": len(TEST_MENUS),
        "enriched_count": len(results),
        "success_rate": len(results) / len(TEST_MENUS) if TEST_MENUS else 0,
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "tested_at": datetime.now().isoformat(),
        "menus": results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n\n결과 저장: {output_path}")
    print(f"성공: {len(results)}/{len(TEST_MENUS)}개")

    print("\n[OK] V2 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
