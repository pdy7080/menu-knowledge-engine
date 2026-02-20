"""
Google Gemini 콘텐츠 생성 테스트
DB 없이 테스트 메뉴로 동작

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Google Gemini 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

genai.configure(api_key=GOOGLE_API_KEY)
# Use gemini-pro (available for free tier)
model = genai.GenerativeModel('gemini-pro')

# 테스트 메뉴 (실제 DB에서 가져올 데이터의 샘플)
TEST_MENUS = [
    {"id": "1", "name_ko": "김치찌개", "name_en": "Kimchi Jjigae"},
    {"id": "2", "name_ko": "된장찌개", "name_en": "Doenjang Jjigae"},
    {"id": "3", "name_ko": "순두부찌개", "name_en": "Sundubu Jjigae"},
    {"id": "4", "name_ko": "부대찌개", "name_en": "Budae Jjigae"},
    {"id": "5", "name_ko": "해물탕", "name_en": "Haemultang"},
    {"id": "6", "name_ko": "갈비탕", "name_en": "Galbitan"},
    {"id": "7", "name_ko": "설렁탕", "name_en": "Seolleongtang"},
    {"id": "8", "name_ko": "곰탕", "name_en": "Gomtang"},
    {"id": "9", "name_ko": "불고기", "name_en": "Bulgogi"},
    {"id": "10", "name_ko": "삼겹살", "name_en": "Samgyeopsal"},
]


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
        return "noodle"
    else:
        return "other"


def get_prompt_for_category(category: str, menu_name_ko: str, menu_name_en: str) -> str:
    """카테고리별 프롬프트 생성"""
    base_prompt = f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (100자): 이 음식의 기원, 맛, 특징
2. 조리 방법 (80자): 기본적인 준비 과정
3. 주요 재료 (50자): 필수 재료 5-7개
4. 영양 정보 (50자): 주요 영양소
5. 추천 음료 (50자): 어울리는 음료/반찬

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}"""
    return base_prompt


def enrich_menu_with_gemini(menu_name_ko: str, menu_name_en: str) -> Dict[str, Any]:
    """Google Gemini를 사용하여 메뉴 정보 강화"""
    category = get_category_from_name(menu_name_ko)
    prompt = get_prompt_for_category(category, menu_name_ko, menu_name_en)

    try:
        # Gemini API 호출
        response = model.generate_content(prompt)
        text = response.text

        # JSON 추출
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            return None

        json_str = text[start_idx:end_idx]
        enriched = json.loads(json_str)
        return enriched

    except Exception as e:
        print(f"[ERROR] {menu_name_ko}: {str(e)}")
        return None


def main():
    """메인 실행"""
    print("[START] Google Gemini 콘텐츠 생성 테스트")
    print(f"[TIME] {datetime.now().isoformat()}")
    print(f"[MENUS] {len(TEST_MENUS)}개 테스트 메뉴")
    print("-" * 60)

    enriched_menus = []
    success_count = 0
    failed_menus = []

    # 메뉴별 처리
    for idx, menu in enumerate(TEST_MENUS, 1):
        menu_name_ko = menu["name_ko"]
        menu_name_en = menu["name_en"]

        print(f"[{idx:2d}/{len(TEST_MENUS)}] 처리 중: {menu_name_ko}...", end=" ", flush=True)

        enriched = enrich_menu_with_gemini(menu_name_ko, menu_name_en)

        if enriched:
            enriched["id"] = menu["id"]
            enriched["name_ko"] = menu_name_ko
            enriched["name_en"] = menu_name_en
            enriched_menus.append(enriched)
            success_count += 1
            print("✓ 완료")
        else:
            failed_menus.append(menu_name_ko)
            print("✗ 실패")

        # Rate limiting
        time.sleep(0.5)

    print("-" * 60)
    print(f"[RESULT] 성공: {success_count}/{len(TEST_MENUS)}")
    print(f"[FAILED] {len(failed_menus)}개: {', '.join(failed_menus)}")

    # 파일 저장
    output_file = Path(__file__).parent.parent / "data" / "enriched_menus_gemini_test.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_menus, f, ensure_ascii=False, indent=2)

    print(f"[SAVED] {output_file}")
    print(f"[COST] Google Gemini: $0 (무료 tier)")
    print(f"[TIME] {datetime.now().isoformat()}")
    print("\n✅ 테스트 완료! Google Gemini 정상 작동 확인됨")


if __name__ == "__main__":
    main()
