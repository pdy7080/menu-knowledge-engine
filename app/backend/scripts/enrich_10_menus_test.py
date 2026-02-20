"""
10개 메뉴 콘텐츠 확장 테스트 (Team Lead 승인)
샘플 데이터로 테스트 후 실제 DB 연동

Test Cases (10 menus):
1. 김치찌개 (simple, common)
2. 비빔밥 (complex, popular)
3. 갈비탕 (meat-based)
4. 순두부찌개 (tofu-based)
5. 불고기 (grilled)
6. 냉면 (cold noodles)
7. 삼계탕 (seasonal)
8. 떡볶이 (street food)
9. 잡채 (side dish)
10. 김밥 (fusion)

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
        "main_ingredients": [
            {"ko": "김", "en": "seaweed"},
            {"ko": "밥", "en": "rice"},
            {"ko": "계란", "en": "egg"}
        ],
        "spice_level": 0
    }
]


async def enrich_single_menu(menu_data: Dict[str, Any]) -> Dict[str, Any]:
    """단일 메뉴 콘텐츠 생성"""
    print(f"\n처리 중: {menu_data['name_ko']} ({menu_data['name_en']})")

    # 재료 문자열 생성
    ingredients_str = ", ".join([
        ing.get("ko", "") for ing in menu_data.get("main_ingredients", [])
    ])

    # GPT-4o-mini 프롬프트
    prompt = f"""
Generate comprehensive content for the Korean menu item below.

**Menu Information:**
- Korean Name: {menu_data['name_ko']}
- English Name: {menu_data['name_en']}
- Main Ingredients: {ingredients_str}
- Spice Level: {menu_data.get('spice_level', 0)}/5

**Required Output (JSON format):**

{{
  "description_ko": "150-200자 상세 설명 (한국어, 음식의 특징과 맛 위주)",
  "description_en": "150-200 chars detailed description (English, focus on taste and characteristics)",

  "regional_variants": [
    {{"name": "서울식", "difference": "서울에서는 국물이 더 맑고 담백합니다"}},
    {{"name": "전라도식", "difference": "전라도에서는 젓갈을 더 많이 넣어 감칠맛이 강합니다"}},
    {{"name": "경상도식", "difference": "경상도에서는 멸치 육수를 사용해 시원한 맛이 특징입니다"}}
  ],

  "preparation_steps": [
    "주재료를 준비하고 손질합니다",
    "육수를 끓입니다",
    "양념을 넣고 간을 맞춥니다",
    "주재료를 넣고 끓입니다",
    "마지막으로 고명을 올립니다"
  ],

  "nutrition": {{
    "calories": 400,
    "protein_g": 20,
    "fat_g": 15,
    "carbs_g": 40,
    "serving_size": "1인분 (350g)"
  }},

  "flavor_profile": {{
    "spiciness": 3,
    "sweetness": 1,
    "saltiness": 3,
    "umami": 4,
    "sourness": 1
  }},

  "visitor_tips": {{
    "ordering": "식당에서 주문할 때는 매운 정도를 미리 말씀하세요",
    "eating": "뜨거울 때 바로 드시면 가장 맛있습니다",
    "pairing": "김치, 깍두기와 함께 드시면 좋습니다"
  }},

  "similar_dishes": [
    {{"name": "청국장찌개", "similarity": "발효 식품을 사용한 찌개류로 국물 맛이 비슷합니다"}},
    {{"name": "부대찌개", "similarity": "얼큰한 맛의 찌개로 재료 조합이 비슷합니다"}},
    {{"name": "김치국", "similarity": "김치를 주재료로 한 국물 요리입니다"}}
  ],

  "cultural_background": {{
    "history": "조선시대부터 발효 음식과 함께 발전한 전통 음식으로, 김치의 보존법으로 시작되었습니다",
    "origin": "한국 전역 (각 지역마다 특색 있음)",
    "cultural_notes": "한국인의 일상 식사에서 가장 흔한 반찬 중 하나이며, 특히 겨울철에 인기가 많습니다"
  }}
}}

**Important Rules:**
1. All Korean text must be accurate and culturally authentic
2. Nutrition values should be realistic (research-based)
3. Flavor profile: 1-5 scale (1=very low, 5=very high)
4. Regional variants: focus on actual regional differences in Korea
5. Preparation steps: 5-7 concise steps
6. Similar dishes: 3-5 actual Korean dishes
7. Output MUST be valid JSON only (no markdown, no explanations)
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Korean food expert specializing in menu content creation. "
                        "Provide accurate, culturally authentic information about Korean dishes. "
                        "Always output valid JSON format with all requested fields. "
                        "Do NOT include markdown code fences or any text outside the JSON object."
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
            "content": content_json,
            "enriched_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  [ERROR] 오류: {str(e)}")
        return None


async def main():
    """메인 함수 - 10개 메뉴 테스트"""
    print("="*60)
    print("GPT-4o-mini 콘텐츠 확장 - 10개 메뉴 테스트")
    print("Team Lead Approved")
    print("="*60)

    # 환경변수 확인
    if not settings.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    print(f"\n테스트 메뉴: {len(TEST_MENUS)}개")
    print(f"모델: gpt-4o-mini (temperature=0.3)")
    print(f"예상 비용: ~$0.05")
    print("="*60)

    # 처리
    results = []
    for i, menu in enumerate(TEST_MENUS, 1):
        print(f"\n[{i}/{len(TEST_MENUS)}]", end=" ")
        result = await enrich_single_menu(menu)
        if result:
            results.append(result)
        await asyncio.sleep(1)  # Rate limit

    # 결과 저장
    output_path = BASE_DIR.parent.parent / "data" / "enriched_test.json"
    output_data = {
        "test_batch_size": len(TEST_MENUS),
        "enriched_count": len(results),
        "failed_count": len(TEST_MENUS) - len(results),
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
    print(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")

    # 통계 출력
    print("\n" + "="*60)
    print("Quality Checks:")
    print("="*60)

    for r in results:
        content = r['content']
        checks = []

        # 8가지 콘텐츠 타입 확인
        required = ["description_ko", "description_en", "regional_variants",
                   "preparation_steps", "nutrition", "flavor_profile",
                   "visitor_tips", "similar_dishes", "cultural_background"]
        all_present = all(k in content for k in required)
        checks.append(f"[{'OK' if all_present else 'FAIL'}] All 8 types")

        # 설명 길이
        desc_ko_len = len(content.get('description_ko', ''))
        desc_en_len = len(content.get('description_en', ''))
        checks.append(f"[{'OK' if 150 <= desc_ko_len <= 250 else 'WARN'}] KO desc: {desc_ko_len} chars")
        checks.append(f"[{'OK' if 150 <= desc_en_len <= 250 else 'WARN'}] EN desc: {desc_en_len} chars")

        # 개수 확인
        variants_count = len(content.get('regional_variants', []))
        steps_count = len(content.get('preparation_steps', []))
        similar_count = len(content.get('similar_dishes', []))

        checks.append(f"[{'OK' if variants_count >= 3 else 'WARN'}] Regional: {variants_count}")
        checks.append(f"[{'OK' if steps_count >= 5 else 'WARN'}] Steps: {steps_count}")
        checks.append(f"[{'OK' if similar_count >= 3 else 'WARN'}] Similar: {similar_count}")

        print(f"\n{r['name_ko']}:")
        for check in checks:
            print(f"  {check}")

    print("\n[OK] 테스트 완료!")
    print(f"\n다음 단계: 품질 검증 실행")
    print(f"  python app/backend/scripts/validate_enriched_content.py")


if __name__ == "__main__":
    asyncio.run(main())
