"""
Canonical Menus 확충 스크립트
실패 케이스 분석하여 부족한 메뉴 추가
"""

import json
import sys
from pathlib import Path

# Path 설정
BASE_DIR = Path(__file__).parent.parent
RESULTS_PATH = BASE_DIR.parent / "data" / "matching_test_results.json"
SEED_FILE = BASE_DIR / "seeds" / "seed_canonical_menus.py"

# 결과 파일 로드
with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 현재 canonical_menus 로드
sys.path.insert(0, str(BASE_DIR / "seeds"))
from seed_canonical_menus import get_canonical_menu_seeds

current_menus = get_canonical_menu_seeds()
current_menu_names = {m["name_ko"] for m in current_menus}

print(f"현재 Canonical Menus: {len(current_menus)}개")

# 1. 필수 메뉴 확인
required_menus = {
    "비빔밥": (
        "비빔밥",
        "Bibimbap (Mixed Rice with Vegetables)",
        "밥에 여러 가지 나물과 고기를 얹어 비벼 먹는 요리",
    ),
    "냉면": (
        "냉면",
        "Naengmyeon (Cold Noodles)",
        "차가운 육수에 메밀면을 말아 먹는 여름 별미",
    ),
    "칼국수": (
        "칼국수",
        "Kalguksu (Hand-cut Noodle Soup)",
        "칼로 썬 밀가루 면을 국물에 넣어 끓인 요리",
    ),
    "국수": ("국수", "Noodles (Guksu)", "밀가루나 메밀로 만든 가늘고 긴 면 요리"),
    "돈까스": ("돈까스", "Donkatsu (Pork Cutlet)", "돼지고기를 튀긴 일본식 돈가스"),
    "육회": ("육회", "Yukhoe (Korean Beef Tartare)", "생소고기를 채 썰어 양념한 요리"),
    "김밥": (
        "김밥",
        "Gimbap (Seaweed Rice Roll)",
        "김에 밥과 여러 재료를 싸서 만 요리",
    ),
}

missing_required = []
for menu_name, info in required_menus.items():
    if menu_name not in current_menu_names:
        missing_required.append(info)
        print(f"  [X] {menu_name}: 없음 (추가 필요)")
    else:
        print(f"  [O] {menu_name}: 있음")

# 2. AI Discovery Needed 케이스에서 핵심 메뉴 추출
core_menus = {}  # {핵심메뉴명: {expected_concept, count}}

for result in data["all_results"]:
    if result["match_type"] == "ai_discovery_needed":
        menu_name = result["menu_name_ko"]
        modifiers = result.get("modifiers", [])
        expected_concept = result["expected_concept"]

        # 수식어 제거
        remaining = menu_name
        for mod in modifiers:
            remaining = remaining.replace(mod, "")

        remaining = remaining.strip()

        # 2글자 이상, 현재 canonical에 없는 것만
        if remaining and len(remaining) >= 2 and remaining not in current_menu_names:
            if remaining not in core_menus:
                core_menus[remaining] = {"concept": expected_concept, "count": 0}
            core_menus[remaining]["count"] += 1

print(f"\n추출된 핵심 메뉴: {len(core_menus)}개")

# 빈도순 정렬
sorted_core_menus = sorted(
    core_menus.items(), key=lambda x: x[1]["count"], reverse=True
)

print("\n상위 30개 핵심 메뉴 (빈도순):")
for i, (menu_name, info) in enumerate(sorted_core_menus[:30], 1):
    print(f"  {i:2d}. {menu_name:15s} ({info['concept']:10s}) - {info['count']}회")

# 3. 추가할 메뉴 결정
# 필수 메뉴 + 빈도 2회 이상인 핵심 메뉴
menus_to_add = []

# 필수 메뉴 추가
for name_ko, name_en, desc_ko in missing_required:
    concept = (
        "비빔밥"
        if "비빔" in name_ko
        else (
            "냉면"
            if "냉면" in name_ko
            else (
                "칼국수"
                if "칼국수" in name_ko
                else (
                    "면류"
                    if "국수" in name_ko or "면" in name_ko
                    else (
                        "튀김"
                        if "까스" in name_ko
                        else (
                            "육류안주"
                            if "육회" in name_ko
                            else "밥류" if "김밥" in name_ko else "기타"
                        )
                    )
                )
            )
        )
    )

    menus_to_add.append(
        {
            "name_ko": name_ko,
            "name_en": name_en,
            "concept": concept,
            "description_ko": desc_ko,
            "description_en": (
                name_en.split("(")[1].replace(")", "") if "(" in name_en else name_en
            ),
            "primary_ingredients": [],
            "allergens": [],
            "spice_level": 0,
            "difficulty_score": 1,
        }
    )

# 빈도 2회 이상인 핵심 메뉴 추가 (최대 100개까지)
for menu_name, info in sorted_core_menus:
    if len(menus_to_add) >= 120:  # 필수 + 추가 = 최대 120개 추가
        break

    if info["count"] >= 2:  # 빈도 2회 이상
        menus_to_add.append(
            {
                "name_ko": menu_name,
                "name_en": f"{menu_name} (Korean)",  # 임시 영문명
                "concept": info["concept"],
                "description_ko": f"{menu_name} 요리",
                "description_en": f"{menu_name} dish",
                "primary_ingredients": [],
                "allergens": [],
                "spice_level": 0,
                "difficulty_score": 1,
            }
        )

print(f"\n추가할 메뉴: {len(menus_to_add)}개")
print(f"최종 Canonical Menus: {len(current_menus) + len(menus_to_add)}개")

# 4. 추가할 메뉴 목록 JSON 출력
output_path = BASE_DIR.parent / "data" / "additional_canonical_menus.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(menus_to_add, f, ensure_ascii=False, indent=2)

print(f"\n추가할 메뉴 목록 저장: {output_path}")

# 5. seed_canonical_menus.py에 추가할 코드 생성
print("\n=== seed_canonical_menus.py에 추가할 코드 ===")
print("\n    # 추가 메뉴 (AI Discovery 분석 결과)")
print("    menus.extend([")
for menu in menus_to_add[:20]:  # 샘플로 20개만 출력
    print("        {")
    print(f"            \"name_ko\": \"{menu['name_ko']}\",")
    print(f"            \"name_en\": \"{menu['name_en']}\",")
    print(f"            \"concept\": \"{menu['concept']}\",")
    print(f"            \"description_ko\": \"{menu['description_ko']}\",")
    print(f"            \"description_en\": \"{menu['description_en']}\",")
    print('            "primary_ingredients": [],')
    print('            "allergens": [],')
    print('            "spice_level": 0,')
    print('            "difficulty_score": 1,')
    print("        },")
if len(menus_to_add) > 20:
    print(f"        # ... 외 {len(menus_to_add) - 20}개 더")
print("    ])")
