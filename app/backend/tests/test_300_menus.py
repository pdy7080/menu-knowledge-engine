"""
300개 실제 메뉴명 대규모 매칭 테스트
"""

import asyncio
import httpx
import csv
import json
import pytest
from pathlib import Path
from collections import defaultdict, Counter

# Integration test requiring live server on localhost:8002 and CSV data file
pytestmark = pytest.mark.skip(
    reason="Integration test: requires live server on localhost:8002 and data/real_menu_names_300.csv"
)

BASE_URL = "http://localhost:8002"
CSV_PATH = Path(__file__).parent.parent.parent / "data" / "real_menu_names_300.csv"
RESULT_PATH = (
    Path(__file__).parent.parent.parent / "data" / "matching_test_results.json"
)


async def test_300_menus():
    """300개 메뉴명 매칭 테스트"""

    # CSV 파일 읽기
    print(f"Loading CSV from: {CSV_PATH}")
    menu_items = []

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            menu_items.append(
                {
                    "menu_name_ko": row["menu_name_ko"],
                    "expected_concept": row["expected_concept"],
                    "frequency_tier": row["frequency_tier"],
                    "has_modifier": row["has_modifier"] == "Y",
                    "notes": row.get("notes", ""),
                }
            )

    print(f"Loaded {len(menu_items)} menu items")

    # 통계 초기화
    stats = {
        "total": len(menu_items),
        "by_match_type": defaultdict(int),
        "by_frequency": {
            "상": {
                "total": 0,
                "exact": 0,
                "modifier_decomposition": 0,
                "ai_discovery_needed": 0,
            },
            "중": {
                "total": 0,
                "exact": 0,
                "modifier_decomposition": 0,
                "ai_discovery_needed": 0,
            },
            "하": {
                "total": 0,
                "exact": 0,
                "modifier_decomposition": 0,
                "ai_discovery_needed": 0,
            },
        },
        "failed_cases": [],
        "all_results": [],
    }

    # API 호출
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, item in enumerate(menu_items, 1):
            menu_name = item["menu_name_ko"]
            frequency = item["frequency_tier"]

            if i % 50 == 0:
                print(f"Processing {i}/{len(menu_items)}...")

            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/menu/identify", json={"menu_name_ko": menu_name}
                )

                if response.status_code != 200:
                    print(f"  [ERROR] {menu_name}: HTTP {response.status_code}")
                    continue

                result = response.json()
                match_type = result.get("match_type")

                # 전체 통계
                stats["by_match_type"][match_type] += 1

                # 빈도별 통계
                stats["by_frequency"][frequency]["total"] += 1
                stats["by_frequency"][frequency][match_type] += 1

                # 실패 케이스 수집
                if match_type == "ai_discovery_needed":
                    stats["failed_cases"].append(
                        {
                            "menu_name_ko": menu_name,
                            "frequency_tier": frequency,
                            "expected_concept": item["expected_concept"],
                            "modifiers_found": [
                                m["text_ko"] for m in result.get("modifiers", [])
                            ],
                            "notes": item["notes"],
                        }
                    )

                # 전체 결과 저장
                stats["all_results"].append(
                    {
                        "menu_name_ko": menu_name,
                        "match_type": match_type,
                        "canonical": (
                            result.get("canonical", {}).get("name_ko")
                            if result.get("canonical")
                            else None
                        ),
                        "modifiers": [
                            m["text_ko"] for m in result.get("modifiers", [])
                        ],
                        "confidence": result.get("confidence", 0.0),
                        "frequency_tier": frequency,
                        "expected_concept": item["expected_concept"],
                    }
                )

            except Exception as e:
                print(f"  [EXCEPTION] {menu_name}: {str(e)}")
                continue

    # 실패 패턴 분석 (TOP 20)
    failed_patterns = Counter()
    for case in stats["failed_cases"]:
        # 패턴: 빈도 + 기대 concept
        pattern = f"{case['frequency_tier']} - {case['expected_concept']}"
        failed_patterns[pattern] += 1

    # 결과 정리
    total = stats["total"]
    exact_count = stats["by_match_type"]["exact"]
    modifier_count = stats["by_match_type"]["modifier_decomposition"]
    similarity_count = stats["by_match_type"]["similarity"]
    ai_needed_count = stats["by_match_type"]["ai_discovery_needed"]

    success_count = exact_count + modifier_count + similarity_count
    success_rate = (success_count / total * 100) if total > 0 else 0

    # 결과 출력
    print("\n" + "=" * 80)
    print("300개 메뉴명 매칭 테스트 결과")
    print("=" * 80)

    print(f"\n1. 전체 매칭률 ({total}개)")
    print(
        f"   - exact_match:             {exact_count:3d}개 ({exact_count/total*100:5.1f}%)"
    )
    print(
        f"   - modifier_decomposition:  {modifier_count:3d}개 ({modifier_count/total*100:5.1f}%)"
    )
    print(
        f"   - similarity:              {similarity_count:3d}개 ({similarity_count/total*100:5.1f}%)"
    )
    print(
        f"   - ai_discovery_needed:     {ai_needed_count:3d}개 ({ai_needed_count/total*100:5.1f}%)"
    )
    print(
        f"\n   [OK] 성공률 (exact + modifier + similarity): {success_count}/{total} ({success_rate:.1f}%)"
    )

    print("\n2. 빈도별 매칭률")
    for freq in ["상", "중", "하"]:
        freq_stats = stats["by_frequency"][freq]
        freq_total = freq_stats["total"]
        if freq_total == 0:
            continue

        freq_success = freq_stats["exact"] + freq_stats["modifier_decomposition"]
        freq_success_rate = (freq_success / freq_total * 100) if freq_total > 0 else 0

        print(
            f"   - {freq}(기본형): {freq_success}/{freq_total}개 ({freq_success_rate:.1f}%)"
        )
        print(
            f"       exact: {freq_stats['exact']}, modifier: {freq_stats['modifier_decomposition']}, ai_needed: {freq_stats['ai_discovery_needed']}"
        )

    print("\n3. 실패 케이스 TOP 20 (ai_discovery_needed)")
    for i, (pattern, count) in enumerate(failed_patterns.most_common(20), 1):
        print(f"   {i:2d}. {pattern}: {count}개")

    # 목표 달성 여부
    print("\n" + "=" * 80)
    if success_rate >= 60:
        print(f"[OK] 목표 달성! 성공률 {success_rate:.1f}% >= 60%")
    else:
        print(f"[WARN] 목표 미달. 성공률 {success_rate:.1f}% < 60%")
    print("=" * 80 + "\n")

    # 결과 파일 저장
    result_data = {
        "summary": {
            "total": total,
            "success_count": success_count,
            "success_rate": success_rate,
            "by_match_type": dict(stats["by_match_type"]),
            "by_frequency": stats["by_frequency"],
        },
        "failed_patterns_top20": [
            {"pattern": pattern, "count": count}
            for pattern, count in failed_patterns.most_common(20)
        ],
        "failed_cases": stats["failed_cases"],
        "all_results": stats["all_results"],
    }

    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"결과 파일 저장: {RESULT_PATH}")

    return success_rate >= 60


if __name__ == "__main__":
    success = asyncio.run(test_300_menus())
    exit(0 if success else 1)
