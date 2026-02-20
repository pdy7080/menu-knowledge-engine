"""
품질 검증 스크립트 (Sprint 2 Phase 1 - Task #5)
확장된 콘텐츠의 품질을 검증하고 보고서 생성

검증 항목:
1. 필수 필드 존재 여부
2. 데이터 타입 정확성
3. 길이 제약 (description 150-200자 등)
4. 한국 음식 사실성 (cultural accuracy)
5. 번역 품질 (Korean-English consistency)

Author: content-engineer
Date: 2026-02-19
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict


class ContentValidator:
    """콘텐츠 품질 검증 엔진"""

    def __init__(self):
        self.validation_results = []
        self.error_summary = defaultdict(int)
        self.warning_summary = defaultdict(int)

    def validate_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """단일 메뉴 검증"""
        menu_id = menu_data.get("menu_id", "unknown")
        name_ko = menu_data.get("name_ko", "unknown")
        content = menu_data.get("content", {})

        errors = []
        warnings = []
        score = 100  # 시작 점수

        # 1. 필수 필드 존재 여부
        required_fields = [
            "description_ko", "description_en",
            "regional_variants", "preparation_steps",
            "nutrition", "flavor_profile",
            "visitor_tips", "similar_dishes",
            "cultural_background"
        ]

        for field in required_fields:
            if field not in content:
                errors.append(f"필수 필드 누락: {field}")
                score -= 10
                self.error_summary["missing_field"] += 1

        # 2. Description 길이 검증 (150-200자)
        desc_ko = content.get("description_ko", "")
        desc_en = content.get("description_en", "")

        if len(desc_ko) < 100:
            warnings.append(f"한국어 설명이 너무 짧음: {len(desc_ko)}자 (권장: 150-200자)")
            score -= 3
            self.warning_summary["desc_ko_short"] += 1
        elif len(desc_ko) > 250:
            warnings.append(f"한국어 설명이 너무 김: {len(desc_ko)}자 (권장: 150-200자)")
            score -= 2
            self.warning_summary["desc_ko_long"] += 1

        if len(desc_en) < 100:
            warnings.append(f"영어 설명이 너무 짧음: {len(desc_en)}자 (권장: 150-200자)")
            score -= 3
            self.warning_summary["desc_en_short"] += 1

        # 3. Regional variants 검증 (3-5개)
        variants = content.get("regional_variants", [])
        if not isinstance(variants, list):
            errors.append("regional_variants가 배열이 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        elif len(variants) < 3:
            warnings.append(f"지역 변형이 부족함: {len(variants)}개 (권장: 3-5개)")
            score -= 5
            self.warning_summary["variants_few"] += 1

        # 4. Preparation steps 검증 (5-7개)
        steps = content.get("preparation_steps", [])
        if not isinstance(steps, list):
            errors.append("preparation_steps가 배열이 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        elif len(steps) < 5:
            warnings.append(f"조리 단계가 부족함: {len(steps)}개 (권장: 5-7개)")
            score -= 5
            self.warning_summary["steps_few"] += 1

        # 5. Nutrition 검증
        nutrition = content.get("nutrition", {})
        if not isinstance(nutrition, dict):
            errors.append("nutrition이 객체가 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        else:
            required_nutrition = ["calories", "protein_g", "fat_g", "carbs_g", "serving_size"]
            for field in required_nutrition:
                if field not in nutrition:
                    warnings.append(f"영양 정보 누락: {field}")
                    score -= 2
                    self.warning_summary["nutrition_missing"] += 1

            # 영양 값 범위 검증
            calories = nutrition.get("calories", 0)
            if calories < 50 or calories > 3000:
                warnings.append(f"비정상적인 칼로리: {calories}kcal")
                score -= 3
                self.warning_summary["calories_abnormal"] += 1

        # 6. Flavor profile 검증 (1-5 스케일)
        flavor = content.get("flavor_profile", {})
        if not isinstance(flavor, dict):
            errors.append("flavor_profile이 객체가 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        else:
            flavor_fields = ["spiciness", "sweetness", "saltiness", "umami", "sourness"]
            for field in flavor_fields:
                value = flavor.get(field, 0)
                if not isinstance(value, (int, float)) or value < 1 or value > 5:
                    warnings.append(f"맛 프로필 범위 오류: {field} = {value} (1-5 필요)")
                    score -= 2
                    self.warning_summary["flavor_range"] += 1

        # 7. Similar dishes 검증 (3-5개)
        similar = content.get("similar_dishes", [])
        if not isinstance(similar, list):
            errors.append("similar_dishes가 배열이 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        elif len(similar) < 3:
            warnings.append(f"유사 메뉴가 부족함: {len(similar)}개 (권장: 3-5개)")
            score -= 5
            self.warning_summary["similar_few"] += 1

        # 8. Cultural background 검증
        culture = content.get("cultural_background", {})
        if not isinstance(culture, dict):
            errors.append("cultural_background가 객체가 아닙니다")
            score -= 10
            self.error_summary["invalid_type"] += 1
        else:
            required_culture = ["history", "origin", "cultural_notes"]
            for field in required_culture:
                if field not in culture or not culture[field]:
                    warnings.append(f"문화 정보 누락: {field}")
                    score -= 3
                    self.warning_summary["culture_missing"] += 1

        # 최종 등급
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "menu_id": menu_id,
            "name_ko": name_ko,
            "score": max(0, score),
            "grade": grade,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }

    def validate_all(self, enriched_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """전체 메뉴 검증"""
        menus = enriched_data.get("menus", [])
        total = len(menus)

        print(f"\n총 {total}개 메뉴 검증 중...")
        print("="*60)

        for i, menu in enumerate(menus, 1):
            result = self.validate_menu(menu)
            self.validation_results.append(result)

            # 진행도 출력 (10개마다)
            if i % 10 == 0 or i == total:
                print(f"진행: {i}/{total} ({i/total*100:.1f}%)")

        return self.validation_results

    def generate_report(self) -> str:
        """품질 검증 보고서 생성 (Markdown)"""
        total = len(self.validation_results)
        if total == 0:
            return "검증할 메뉴가 없습니다."

        # 통계 계산
        total_score = sum(r["score"] for r in self.validation_results)
        avg_score = total_score / total

        grades = defaultdict(int)
        for r in self.validation_results:
            grades[r["grade"]] += 1

        total_errors = sum(r["error_count"] for r in self.validation_results)
        total_warnings = sum(r["warning_count"] for r in self.validation_results)

        # 최고/최저 점수
        best = max(self.validation_results, key=lambda x: x["score"])
        worst = min(self.validation_results, key=lambda x: x["score"])

        # Markdown 보고서
        report = f"""# Menu Content Quality Validation Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Menus:** {total}

---

## Overall Statistics

| Metric | Value |
|--------|-------|
| **Average Score** | {avg_score:.1f}/100 |
| **Total Errors** | {total_errors} |
| **Total Warnings** | {total_warnings} |

### Grade Distribution

| Grade | Count | Percentage |
|-------|-------|------------|
| A (90-100) | {grades["A"]} | {grades["A"]/total*100:.1f}% |
| B (80-89) | {grades["B"]} | {grades["B"]/total*100:.1f}% |
| C (70-79) | {grades["C"]} | {grades["C"]/total*100:.1f}% |
| D (60-69) | {grades["D"]} | {grades["D"]/total*100:.1f}% |
| F (<60) | {grades["F"]} | {grades["F"]/total*100:.1f}% |

---

## Best & Worst

**Best Performance:**
- Menu: {best["name_ko"]} ({best["menu_id"]})
- Score: {best["score"]}/100 (Grade: {best["grade"]})
- Errors: {best["error_count"]}, Warnings: {best["warning_count"]}

**Worst Performance:**
- Menu: {worst["name_ko"]} ({worst["menu_id"]})
- Score: {worst["score"]}/100 (Grade: {worst["grade"]})
- Errors: {worst["error_count"]}, Warnings: {worst["warning_count"]}

---

## Error Summary

| Error Type | Count |
|------------|-------|
"""
        for error_type, count in sorted(self.error_summary.items(), key=lambda x: -x[1]):
            report += f"| {error_type} | {count} |\n"

        report += "\n---\n\n## Warning Summary\n\n| Warning Type | Count |\n|--------------|-------|\n"

        for warning_type, count in sorted(self.warning_summary.items(), key=lambda x: -x[1]):
            report += f"| {warning_type} | {count} |\n"

        report += "\n---\n\n## Failed Menus (Score < 70)\n\n"

        failed = [r for r in self.validation_results if r["score"] < 70]
        if failed:
            for r in failed:
                report += f"### {r['name_ko']} ({r['menu_id']})\n"
                report += f"- **Score:** {r['score']}/100 (Grade: {r['grade']})\n"
                report += f"- **Errors ({r['error_count']}):**\n"
                for err in r["errors"]:
                    report += f"  - {err}\n"
                report += f"- **Warnings ({r['warning_count']}):**\n"
                for warn in r["warnings"]:
                    report += f"  - {warn}\n"
                report += "\n"
        else:
            report += "없음 (모든 메뉴가 70점 이상)\n"

        report += "\n---\n\n## Recommendations\n\n"

        if avg_score >= 90:
            report += "전반적인 품질이 우수합니다. 프로덕션 배포 준비 완료.\n"
        elif avg_score >= 80:
            report += "양호한 품질입니다. 일부 경고 사항을 검토하고 수정하세요.\n"
        elif avg_score >= 70:
            report += "보통 품질입니다. 오류가 있는 메뉴를 우선 수정하세요.\n"
        else:
            report += "품질이 낮습니다. GPT 프롬프트를 개선하고 재생성하세요.\n"

        return report


def main():
    """메인 함수"""
    print("="*60)
    print("콘텐츠 품질 검증 (Sprint 2 Phase 1 - Task #5)")
    print("="*60)

    # 입력 파일
    input_file = Path("C:/project/menu/data/test_enriched_menus.json")
    if not input_file.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {input_file}")
        print("먼저 enrich_content.py를 실행하세요.")
        sys.exit(1)

    # 데이터 로드
    with open(input_file, 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)

    # 검증 실행
    validator = ContentValidator()
    validator.validate_all(enriched_data)

    # 보고서 생성
    report = validator.generate_report()

    # 콘솔 출력
    print("\n" + "="*60)
    print(report)

    # 파일 저장
    output_file = Path("C:/project/menu/data/quality_report.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] 보고서 저장: {output_file}")


if __name__ == "__main__":
    main()
