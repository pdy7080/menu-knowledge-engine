"""
콘텐츠 확장 테스트 스크립트 (샘플 데이터 사용)
실제 DB 연결 없이 GPT-4o-mini API 테스트

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
    """테스트 메인"""
    print("="*60)
    print("GPT-4o-mini 콘텐츠 확장 테스트")
    print("="*60)

    # 환경변수 확인
    if not settings.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    # 샘플 데이터 로드
    # BASE_DIR = app/backend, parent = app, parent.parent = project root
    sample_file = BASE_DIR.parent.parent / "data" / "sample_menus_for_enrichment.json"
    with open(sample_file, 'r', encoding='utf-8') as f:
        sample_menus = json.load(f)

    print(f"\n샘플 메뉴: {len(sample_menus)}개")
    print(f"모델: gpt-4o-mini (temperature=0.3)")
    print("="*60)

    # 처리
    results = []
    for menu in sample_menus[:3]:  # 처음 3개만 테스트
        result = await enrich_single_menu(menu)
        if result:
            results.append(result)
        await asyncio.sleep(1)  # Rate limit

    # 결과 저장
    output_path = BASE_DIR.parent.parent / "data" / "test_enriched_menus.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "test_count": len(results),
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "tested_at": datetime.now().isoformat(),
            "menus": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {output_path}")
    print(f"성공: {len(results)}/{len(sample_menus[:3])}개")

    # 샘플 출력
    if results:
        print("\n" + "="*60)
        print(f"샘플 결과: {results[0]['name_ko']}")
        print("="*60)
        content = results[0]['content']
        print(f"\n[설명 (한국어)]")
        print(content.get('description_ko', 'N/A'))
        print(f"\n[설명 (영어)]")
        print(content.get('description_en', 'N/A'))
        print(f"\n[지역 변형] {len(content.get('regional_variants', []))}개")
        for v in content.get('regional_variants', [])[:3]:
            print(f"  - {v.get('name', '')}: {v.get('difference', '')}")
        print(f"\n[조리 단계] {len(content.get('preparation_steps', []))}개")
        for i, step in enumerate(content.get('preparation_steps', [])[:3], 1):
            print(f"  {i}. {step}")
        print(f"\n[영양 정보]")
        nutrition = content.get('nutrition', {})
        print(f"  칼로리: {nutrition.get('calories', 'N/A')}kcal")
        print(f"  단백질: {nutrition.get('protein_g', 'N/A')}g")
        print(f"\n[맛 프로필]")
        flavor = content.get('flavor_profile', {})
        print(f"  매운맛: {flavor.get('spiciness', 0)}/5")
        print(f"  감칠맛: {flavor.get('umami', 0)}/5")

    print("\n[OK] 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
