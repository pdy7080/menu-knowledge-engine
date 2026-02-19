"""
고속도로 휴게소 데이터 → canonical_menus 시드 SQL 생성
351개 후보에서 중복 병합 + 카테고리 분류 → INSERT SQL 생성

Author: Claude (Senior Developer)
Date: 2026-02-19
"""
import sys
import io
import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "migrations"


# =====================================================
# 1단계: 동의어 병합 규칙
# =====================================================
MERGE_RULES = {
    # EX라면 계열 → 라면
    "ex라면": "라면",
    "ex-라면": "라면",
    "EX라면": "라면",
    "EX-라면": "라면",
    # 돈가스/돈까스 통일
    "돈까스": "돈가스",
    "치즈돈까스": "치즈돈가스",
    "등심돈까스": "등심돈가스",
    "왕돈까스": "왕돈가스",
    "생선까스": "생선가스",
    # 자장/짜장 통일
    "자장면": "짜장면",
    "자장밥": "짜장밥",
    # 라면 계열 정규화
    "실속라면": "라면",
    # 우동 계열
    "실속우동": "우동",
    # 기타
    "공기밥": None,  # canonical에서 제외 (반찬)
}


# =====================================================
# 2단계: 카테고리 분류 규칙
# =====================================================
def classify_category(name: str) -> tuple:
    """(category_1, category_2) 반환"""
    # 면류
    if any(k in name for k in ["우동", "국수", "소바", "냉면"]):
        return ("면류", "면")
    if any(k in name for k in ["라면"]):
        return ("면류", "라면")
    if any(k in name for k in ["파스타", "스파게티"]):
        return ("면류", "파스타")

    # 밥류
    if any(k in name for k in ["덮밥", "볶음밥"]):
        return ("밥류", "덮밥")
    if any(k in name for k in ["비빔밥", "돌솥비빔"]):
        return ("밥류", "비빔밥")
    if any(k in name for k in ["김밥"]):
        return ("밥류", "김밥")
    if any(k in name for k in ["밥", "정식"]):
        return ("밥류", "기타밥")

    # 국/찌개/탕
    if any(k in name for k in ["찌개"]):
        return ("국/찌개/탕", "찌개")
    if any(k in name for k in ["탕", "해장", "설렁", "곰탕", "갈비탕"]):
        return ("국/찌개/탕", "탕")
    if any(k in name for k in ["국", "육개장"]):
        return ("국/찌개/탕", "국")

    # 돈가스/튀김
    if any(k in name for k in ["돈가스", "돈까스", "커틀릿", "까스"]):
        return ("돈가스/튀김", "돈가스")
    if any(k in name for k in ["튀김"]):
        return ("돈가스/튀김", "튀김")

    # 구이/고기
    if any(k in name for k in ["불고기", "갈비", "삼겹", "숯불", "구이"]):
        return ("구이/고기", "구이")

    # 분식
    if any(k in name for k in ["떡볶이", "순대", "어묵", "핫도그", "토스트"]):
        return ("분식", "분식")

    # 중식
    if any(k in name for k in ["짜장", "짬뽕", "탕수육", "볶음"]) and "밥" not in name:
        return ("중식", "중식")

    # 빵/간식
    if any(k in name for k in ["빵", "호떡", "와플", "붕어빵", "만두"]):
        return ("빵/간식", "간식")

    # 음료
    if any(k in name for k in ["커피", "아메", "라떼", "음료", "주스", "차"]):
        return ("음료", "음료")

    return ("기타", "기타")


# =====================================================
# 3단계: 수식어 분리
# =====================================================
MODIFIERS = {
    "왕": ("size", "x_large"),
    "특": ("size", "large"),
    "대": ("size", "large"),
    "매운": ("taste", "spicy"),
    "얼큰": ("taste", "spicy_hearty"),
    "해물": ("ingredient", "seafood"),
    "치즈": ("ingredient", "cheese"),
    "새우": ("ingredient", "shrimp"),
    "야채": ("ingredient", "vegetable"),
    "등심": ("ingredient", "sirloin"),
    "돌솥": ("cooking", "stone_pot"),
    "뚝배기": ("cooking", "earthen_pot"),
    "숯불": ("cooking", "charcoal"),
}


def extract_base_and_modifiers(name: str) -> tuple:
    """(base_name, modifier_list) 반환"""
    remaining = name
    found_modifiers = []

    for mod, (mod_type, mod_key) in MODIFIERS.items():
        if remaining.startswith(mod) and len(remaining) > len(mod):
            found_modifiers.append({
                "text": mod,
                "type": mod_type,
                "key": mod_key,
            })
            remaining = remaining[len(mod):]

    return remaining, found_modifiers


# =====================================================
# 메인 처리
# =====================================================
def main():
    print("=" * 60)
    print("canonical_menus 시드 데이터 생성")
    print(f"시간: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. 후보 데이터 로드
    candidates_file = DATA_DIR / "highway_food_canonical_candidates.json"
    with open(candidates_file, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    print(f"\n[1] 후보 로드: {len(candidates)}개")

    # 2. 동의어 병합
    print(f"\n[2] 동의어 병합")
    print("-" * 40)
    merged = defaultdict(lambda: {
        "occurrence_count": 0,
        "rest_area_count": 0,
        "prices": [],
        "is_best": False,
        "is_recommend": False,
        "raw_names": [],
        "routes": [],
    })

    skipped = 0
    for item in candidates:
        name = item["name_ko"]
        target = MERGE_RULES.get(name, name)

        if target is None:
            skipped += 1
            continue

        m = merged[target]
        m["occurrence_count"] += item["occurrence_count"]
        m["rest_area_count"] = max(m["rest_area_count"], item["rest_area_count"])
        if item["avg_price"] > 0:
            m["prices"].append(item["avg_price"])
        if item.get("is_best"):
            m["is_best"] = True
        if item.get("is_recommend"):
            m["is_recommend"] = True
        m["raw_names"].append(name)
        m["routes"].extend(item.get("routes", []))

    print(f"  병합 전: {len(candidates)}개")
    print(f"  병합 후: {len(merged)}개 (제외: {skipped}개)")

    # 3. 정렬 + 상위 선정
    sorted_menus = sorted(
        merged.items(),
        key=lambda x: (x[1]["rest_area_count"], x[1]["occurrence_count"]),
        reverse=True,
    )

    # 5곳 이상 판매 메뉴만 → canonical 대상
    canonical_list = [
        (name, data) for name, data in sorted_menus
        if data["rest_area_count"] >= 5
    ]
    print(f"\n[3] canonical 대상 (5곳+): {len(canonical_list)}개")

    # 4. 카테고리 분류 + SQL 생성
    print(f"\n[4] 카테고리 분류 + SQL 생성")
    print("-" * 40)

    category_counts = Counter()
    sql_values = []
    seed_data = []

    for i, (name, data) in enumerate(canonical_list, 1):
        cat1, cat2 = classify_category(name)
        category_counts[cat1] += 1

        avg_price = sum(data["prices"]) // len(data["prices"]) if data["prices"] else 0
        base_name, modifiers = extract_base_and_modifiers(name)

        # canonical인지 variant인지 판단
        # 수식어가 없으면 canonical, 있으면 variant 후보
        is_canonical = len(modifiers) == 0

        entry = {
            "name_ko": name,
            "base_name": base_name,
            "modifiers": modifiers,
            "category_1": cat1,
            "category_2": cat2,
            "occurrence_count": data["occurrence_count"],
            "rest_area_count": data["rest_area_count"],
            "avg_price": avg_price,
            "is_best": data["is_best"],
            "is_recommend": data["is_recommend"],
            "is_canonical": is_canonical,
            "raw_names": data["raw_names"],
        }
        seed_data.append(entry)

        # SQL INSERT 값 (canonical만)
        # JSONB 기본 번역
        translations = json.dumps({"ko": name}, ensure_ascii=False)
        description = json.dumps({"ko": f"{cat1} > {cat2}"}, ensure_ascii=False)
        tags = json.dumps([cat1, cat2], ensure_ascii=False)

        sql_val = (
            f"  (gen_random_uuid(), "
            f"'{name}', "
            f"'{translations.replace(chr(39), chr(39)+chr(39))}', "
            f"'{description.replace(chr(39), chr(39)+chr(39))}', "
            f"NULL, "  # concept_id
            f"'{tags.replace(chr(39), chr(39)+chr(39))}', "
            f"'highway_food_data', "  # source
            f"'{cat1}', "  # category_1
            f"'{cat2}', "  # category_2
            f"NULL, "  # serving_size
            f"'{{}}', "  # nutrition_info
            f"NULL, "  # last_nutrition_updated
            f"NOW(), NOW())"
        )
        sql_values.append(sql_val)

    for cat, count in category_counts.most_common():
        print(f"  {cat:<15} {count:4d}개")

    # 5. SQL 파일 생성
    OUTPUT_DIR.mkdir(exist_ok=True)
    sql_file = OUTPUT_DIR / "sprint0_seed_canonical_menus.sql"

    sql_content = f"""-- ============================================================
-- canonical_menus 시드 데이터 (고속도로 휴게소 음식 기반)
-- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
-- 소스: data.ex.co.kr 휴게소 음식 메뉴 API (7,009건)
-- 대상: 5곳 이상 휴게소에서 판매되는 보편적 메뉴 {len(canonical_list)}개
-- ============================================================

-- 기존 시드 데이터 정리 (필요시)
-- DELETE FROM canonical_menus WHERE source = 'highway_food_data';

INSERT INTO canonical_menus (
    id, name_ko, translations, description, concept_id,
    tags, source, category_1, category_2, serving_size,
    nutrition_info, last_nutrition_updated,
    created_at, updated_at
) VALUES
{',\n'.join(sql_values)};

-- 인덱스 확인
-- CREATE INDEX IF NOT EXISTS idx_cm_category ON canonical_menus(category_1, category_2);
-- CREATE INDEX IF NOT EXISTS idx_cm_name_ko ON canonical_menus(name_ko);
"""

    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    print(f"\n  [SAVED] {sql_file.name} ({len(sql_values)}개 INSERT)")

    # 6. JSON 시드 데이터 저장 (분석용)
    seed_file = DATA_DIR / "canonical_seed_data.json"
    with open(seed_file, 'w', encoding='utf-8') as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {seed_file.name} ({len(seed_data)}개)")

    # 7. canonical vs variant 분류 통계
    print(f"\n[5] canonical vs variant 분류")
    print("-" * 40)
    canonicals = [e for e in seed_data if e["is_canonical"]]
    variants = [e for e in seed_data if not e["is_canonical"]]
    print(f"  canonical (수식어 없음): {len(canonicals)}개")
    print(f"  variant 후보 (수식어 있음): {len(variants)}개")

    print(f"\n  canonical 상위 20개:")
    for e in canonicals[:20]:
        print(f"    {e['name_ko']:<20} {e['rest_area_count']:3d}곳 | avg {e['avg_price']:>6,}원 | {e['category_1']}/{e['category_2']}")

    print(f"\n  variant 후보 상위 15개:")
    for e in variants[:15]:
        mods_str = "+".join(m["text"] for m in e["modifiers"])
        print(f"    {e['name_ko']:<20} = [{mods_str}] + {e['base_name']} | {e['rest_area_count']:3d}곳")

    # 8. 최종 통계
    print(f"\n{'=' * 60}")
    print(f"최종 통계:")
    print(f"  시드 메뉴 총 수: {len(seed_data)}개")
    print(f"  canonical: {len(canonicals)}개")
    print(f"  variant 후보: {len(variants)}개")
    print(f"  카테고리: {len(category_counts)}개")
    print(f"  SQL 파일: {sql_file.name}")
    print(f"  JSON 파일: {seed_file.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
