"""
Claude API 강화 데이터 → DB 로드 스크립트 (Direct SQL)
ORM 우회하여 직접 SQL UPDATE 실행

Author: terminal-developer
Date: 2026-02-19
"""
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any
from sqlalchemy import text
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

from database import engine


def transform_content(raw_content: Dict[str, Any]) -> Dict[str, Any]:
    """Claude API 결과를 DB 스키마에 맞게 변환"""
    # regional_variants
    regional_variants = []
    for variant in raw_content.get("regional_variants", []):
        regional_variants.append({
            "region": variant.get("name", ""),
            "differences": variant.get("difference", ""),
            "local_name": variant.get("name", "")
        })

    # preparation_steps
    prep_steps = raw_content.get("preparation_steps", [])
    preparation_steps = {
        "steps": prep_steps,
        "serving_suggestions": [],
        "etiquette": []
    }

    # nutrition_detail
    nutrition = raw_content.get("nutrition", {})
    nutrition_detail = {
        "calories": nutrition.get("calories", 0),
        "protein": nutrition.get("protein_g", 0.0),
        "carbs": nutrition.get("carbs_g", 0.0),
        "fat": nutrition.get("fat_g", 0.0),
        "sodium": 0,
        "serving_size": nutrition.get("serving_size", "1인분")
    }

    # flavor_profile
    flavor = raw_content.get("flavor_profile", {})
    flavor_profile = {
        "primary": [],
        "balance": {
            "sweet": flavor.get("sweetness", 0),
            "salty": flavor.get("saltiness", 0),
            "sour": flavor.get("sourness", 0),
            "bitter": 0,
            "umami": flavor.get("umami", 0)
        }
    }

    # visitor_tips
    tips = raw_content.get("visitor_tips", {})
    visitor_tips = {
        "common_mistakes": [],
        "ordering_tips": [tips.get("ordering", "")],
        "pairing": [tips.get("pairing", "")],
        "eating_method": tips.get("eating", "")
    }

    # similar_dishes
    similar = raw_content.get("similar_dishes", [])
    similar_dishes = []
    for dish in similar:
        similar_dishes.append({
            "name_ko": dish.get("name", ""),
            "name_en": "",
            "similarity_reason": dish.get("similarity", ""),
            "difference": ""
        })

    # cultural_context
    cultural = raw_content.get("cultural_background", {})
    cultural_context = {
        "history": cultural.get("history", ""),
        "origin": cultural.get("origin", ""),
        "significance": cultural.get("cultural_notes", "")
    }

    return {
        "description_long_ko": raw_content.get("description_ko", ""),
        "description_long_en": raw_content.get("description_en", ""),
        "regional_variants": regional_variants if regional_variants else None,
        "preparation_steps": preparation_steps if prep_steps else None,
        "nutrition_detail": nutrition_detail if nutrition.get("calories") else None,
        "flavor_profile": flavor_profile,
        "visitor_tips": visitor_tips,
        "similar_dishes": similar_dishes if similar_dishes else None,
        "cultural_context": cultural_context if cultural.get("history") else None
    }


def calculate_completeness(transformed: Dict[str, Any]) -> float:
    """콘텐츠 완성도 계산 (0-100)"""
    fields = [
        "description_long_ko",
        "description_long_en",
        "regional_variants",
        "preparation_steps",
        "nutrition_detail",
        "flavor_profile",
        "visitor_tips",
        "similar_dishes",
        "cultural_context"
    ]
    filled = sum(1 for f in fields if transformed.get(f))
    return round((filled / len(fields)) * 100, 2)


async def load_enriched_data():
    """메인 로드 함수 (Direct SQL)"""
    print("=" * 60)
    print("Claude API 강화 데이터 → DB 로드 (Direct SQL)")
    print("=" * 60)

    # JSON 파일 로드
    json_path = BASE_DIR / "data" / "enriched_menus_claude.json"
    print(f"\n파일 읽기: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    menus = data.get("menus", [])
    print(f"  ✅ {len(menus)}개 메뉴 로드 완료\n")

    # DB 연결
    async with engine.begin() as conn:
        updated = 0
        skipped = 0
        errors = 0

        for i, menu_data in enumerate(menus, 1):
            name_ko = menu_data.get("name_ko")
            print(f"[{i}/{len(menus)}] {name_ko} 처리 중...")

            try:
                # 기존 메뉴 조회
                result = await conn.execute(
                    text("SELECT id FROM canonical_menus WHERE name_ko = :name_ko"),
                    {"name_ko": name_ko}
                )
                existing = result.fetchone()

                if not existing:
                    print(f"  ⚠️  DB에 없음 - 스킵")
                    skipped += 1
                    continue

                # 콘텐츠 변환
                raw_content = menu_data.get("content", {})
                transformed = transform_content(raw_content)
                completeness = calculate_completeness(transformed)

                # Direct SQL UPDATE (CAST 함수 사용)
                update_query = text("""
                    UPDATE canonical_menus
                    SET
                        description_long_ko = :description_long_ko,
                        description_long_en = :description_long_en,
                        regional_variants = CAST(:regional_variants AS jsonb),
                        preparation_steps = CAST(:preparation_steps AS jsonb),
                        nutrition_detail = CAST(:nutrition_detail AS jsonb),
                        flavor_profile = CAST(:flavor_profile AS jsonb),
                        visitor_tips = CAST(:visitor_tips AS jsonb),
                        similar_dishes = CAST(:similar_dishes AS jsonb),
                        cultural_context = CAST(:cultural_context AS jsonb),
                        content_completeness = :content_completeness
                    WHERE id = :menu_id
                """)

                # JSON 직렬화
                params = {
                    "menu_id": existing[0],
                    "description_long_ko": transformed["description_long_ko"],
                    "description_long_en": transformed["description_long_en"],
                    "regional_variants": json.dumps(transformed["regional_variants"]) if transformed["regional_variants"] else None,
                    "preparation_steps": json.dumps(transformed["preparation_steps"]) if transformed["preparation_steps"] else None,
                    "nutrition_detail": json.dumps(transformed["nutrition_detail"]) if transformed["nutrition_detail"] else None,
                    "flavor_profile": json.dumps(transformed["flavor_profile"]),
                    "visitor_tips": json.dumps(transformed["visitor_tips"]),
                    "similar_dishes": json.dumps(transformed["similar_dishes"]) if transformed["similar_dishes"] else None,
                    "cultural_context": json.dumps(transformed["cultural_context"]) if transformed["cultural_context"] else None,
                    "content_completeness": completeness
                }

                await conn.execute(update_query, params)

                print(f"  ✅ 업데이트 완료 (완성도: {completeness}%)")
                updated += 1

            except Exception as e:
                print(f"  ❌ 오류: {str(e)}")
                errors += 1

        print("\n" + "=" * 60)
        print(f"✅ 업데이트: {updated}개")
        print(f"⚠️  스킵: {skipped}개")
        print(f"❌ 오류: {errors}개")
        print(f"성공률: {(updated / len(menus) * 100):.1f}%")


if __name__ == "__main__":
    asyncio.run(load_enriched_data())
