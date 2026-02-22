"""
300개 메뉴 콘텐츠 전체 확장 - Google Gemini 버전
Team Lead 승인 (2026-02-19)

Features:
- Google Gemini API 사용 (무료, OpenAI billing limit 우회)
- Category-aware prompts (6 categories)
- Menu-specific content generation
- Error handling with retry (max 3 attempts)
- Checkpoint saves (every 10 menus)
- Progress monitoring
- Fast batch processing

Author: Claude (Senior Developer)
Date: 2026-02-19
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import google.generativeai as genai

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
model = genai.GenerativeModel("gemini-1.5-flash")


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
    category_prompts = {
        "stew": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 찌개의 기원, 맛의 특징, 주재료 설명
2. 조리 방법 (100자): 기본적인 준비 과정과 조리 시간
3. 주요 재료 (50자): 필수 재료 5-7개 나열
4. 영양 정보 (50자): 주요 영양소와 건강 효능
5. 추천 음료 (50자): 어울리는 음료 또는 반찬 추천

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "soup": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 국의 유래, 맛 프로필, 주요 특징
2. 조리 방법 (100자): 육수 내기부터 완성까지의 과정
3. 주요 재료 (50자): 필수 재료와 선택 재료
4. 영양 정보 (50자): 몸을 따뜻하게 하는 효능
5. 추천 조합 (50자): 밥, 반찬과의 조화

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "grilled": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 구이의 종류, 고기 부위, 맛의 특징
2. 조리 방법 (100자): 불 조절, 구이 시간, 팁
3. 주요 재료 (50자): 고기 부위와 곁재료
4. 영양 정보 (50자): 단백질, 철분 등 영양가
5. 추천 소스 (50자): 어울리는 양념과 먹는 방법

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "stir-fried": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 볶음 요리의 특징, 맛, 적절한 때
2. 조리 방법 (100자): 재료 준비, 불 조절, 볶음 팁
3. 주요 재료 (50자): 핵심 재료와 향신료
4. 영양 정보 (50자): 비타민과 미네랄
5. 추천 반찬 (50자): 어울리는 밥과 반찬

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "rice": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 밥 요리의 특징, 역사, 맛
2. 조리 방법 (100자): 밥 준비부터 완성까지 과정
3. 주요 재료 (50자): 쌀과 고명, 양념
4. 영양 정보 (50자): 탄수화물과 기타 영양소
5. 추천 국/반찬 (50자): 어울리는 국과 반찬

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "noodle": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 면 요리의 기원, 특징, 계절성
2. 조리 방법 (100자): 면 삶기부터 양념까지 과정
3. 주요 재료 (50자): 면, 육수, 고명
4. 영양 정보 (50자): 탄수화물과 단백질
5. 추천 먹는 방법 (50자): 계절별, 취향별 먹는 팁

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
        "other": f"""한국의 '{menu_name_ko}'({menu_name_en})에 대해 다음을 생성해주세요:

1. 상세 설명 (150자): 이 음식의 의의, 맛, 특징
2. 조리 방법 (100자): 기본적인 만드는 방법
3. 주요 재료 (50자): 필수 재료
4. 영양 정보 (50자): 주요 영양소
5. 추천 함께 먹을 것 (50자): 어울리는 음식

JSON 형식으로 응답:
{{
    "description_ko": "...",
    "preparation_ko": "...",
    "ingredients_ko": "...",
    "nutrition_ko": "...",
    "pairing_ko": "..."
}}""",
    }
    return category_prompts.get(category, category_prompts["other"])


async def enrich_menu_with_gemini(
    menu_name_ko: str, menu_name_en: str
) -> Dict[str, Any]:
    """Google Gemini를 사용하여 메뉴 정보 강화"""
    category = get_category_from_name(menu_name_ko)
    prompt = get_prompt_for_category(category, menu_name_ko, menu_name_en)

    try:
        # Gemini API 호출 (동기)
        response = model.generate_content(prompt)

        # 응답에서 JSON 추출
        text = response.text

        # JSON 파싱
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            return None

        json_str = text[start_idx:end_idx]
        enriched = json.loads(json_str)

        return enriched
    except Exception as e:
        print(f"[ERROR] {menu_name_ko}: {str(e)}")
        return None


async def load_menus_from_db() -> List[Dict[str, str]]:
    """DB에서 메뉴 목록 로드"""
    async with AsyncSessionLocal() as session:
        query = select(CanonicalMenu).limit(300)
        result = await session.execute(query)
        menus = result.scalars().all()

        return [
            {
                "id": str(menu.id),
                "name_ko": menu.name_ko,
                "name_en": menu.name_en or menu.name_ko,
            }
            for menu in menus
        ]


async def enrich_all_menus(max_retries=3):
    """모든 메뉴 정보 강화"""
    print("[START] 300개 메뉴 콘텐츠 생성 시작 (Google Gemini 사용)")
    print(f"[TIME] {datetime.now().isoformat()}")
    print("-" * 60)

    # DB에서 메뉴 로드
    menus = await load_menus_from_db()
    print(f"[INFO] 로드된 메뉴: {len(menus)}개\n")

    enriched_menus = []
    success_count = 0
    failed_menus = []

    # 메뉴별 처리
    for idx, menu in enumerate(menus, 1):
        menu_name_ko = menu["name_ko"]
        menu_name_en = menu["name_en"]

        # 재시도 로직
        for attempt in range(max_retries):
            enriched = await enrich_menu_with_gemini(menu_name_ko, menu_name_en)

            if enriched:
                enriched["id"] = menu["id"]
                enriched["name_ko"] = menu_name_ko
                enriched["name_en"] = menu_name_en
                enriched_menus.append(enriched)
                success_count += 1

                print(f"[{idx:3d}/{len(menus)}] ✓ {menu_name_ko}")
                break
            elif attempt < max_retries - 1:
                print(f"[{idx:3d}/{len(menus)}] ⚠ {menu_name_ko} (retry {attempt + 1})")
                await asyncio.sleep(1)
            else:
                failed_menus.append(menu_name_ko)
                print(
                    f"[{idx:3d}/{len(menus)}] ✗ {menu_name_ko} (failed after {max_retries} attempts)"
                )

        # 10개마다 진행도 및 체크포인트
        if idx % 10 == 0:
            print(
                f"\n[PROGRESS] {idx}/{len(menus)} ({idx/len(menus)*100:.1f}%) - 성공: {success_count}"
            )

            # 체크포인트 저장
            checkpoint_file = (
                BASE_DIR / "data" / f"enriched_menus_checkpoint_{idx}.json"
            )
            checkpoint_file.parent.mkdir(exist_ok=True)
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(enriched_menus, f, ensure_ascii=False, indent=2)
            print(f"[CHECKPOINT] {checkpoint_file.name} 저장됨\n")

        # Rate limiting (Google Gemini는 빠르므로 1초 정도면 충분)
        await asyncio.sleep(0.5)

    print("-" * 60)
    print("[COMPLETE] 처리 완료")
    print(
        f"[RESULT] 성공: {success_count}/{len(menus)} ({success_count/len(menus)*100:.1f}%)"
    )
    print(
        f"[FAILED] {len(failed_menus)}개 실패: {', '.join(failed_menus[:5])}{'...' if len(failed_menus) > 5 else ''}"
    )

    # 최종 파일 저장
    output_file = BASE_DIR / "data" / "enriched_menus_full_gemini.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched_menus, f, ensure_ascii=False, indent=2)

    print(f"[SAVED] {output_file}")
    print("[COST] Google Gemini: $0 (무료 tier)")
    print(f"[TIME] {datetime.now().isoformat()}")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(enrich_all_menus())
