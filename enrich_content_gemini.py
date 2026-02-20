"""
Gemini 2.0 Flash 콘텐츠 강화 스크립트 (무료 tier)
시드 데이터 → Gemini API → 112 menus 콘텐츠 생성

Author: terminal-developer
Date: 2026-02-19
Cost: $0 (무료 tier: 15 RPM, 1,500 RPD)
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Gemini API
import google.generativeai as genai

# Gemini API 설정
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
genai.configure(api_key=GEMINI_API_KEY)

# 모델 초기화 (Gemini 2.0 Flash - 무료)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config={
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
)

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

# 시드 데이터 import
from seeds.seed_canonical_menus import get_canonical_menu_seeds


class GeminiContentEnricher:
    """Gemini 기반 콘텐츠 확장 엔진"""

    def __init__(self):
        self.model_name = "gemini-2.0-flash-exp"
        self.enriched_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def enrich_menu(self, menu_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """단일 메뉴 콘텐츠 생성 (동기 버전)"""
        name_ko = menu_data["name_ko"]
        name_en = menu_data["name_en"]

        print(f"\n[{self.enriched_count + 1}] {name_ko} ({name_en}) 처리 중...")

        try:
            # Gemini 프롬프트 생성
            prompt = self._build_prompt(menu_data)

            # API 호출 (동기)
            response = model.generate_content(prompt)

            # JSON 파싱 (Gemini 응답에서 JSON 추출)
            response_text = response.text.strip()

            # JSON 코드 블록 제거 (```json ... ```)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            content_json = json.loads(response_text.strip())

            # 검증
            if not self._validate_content(content_json):
                print(f"  ❌ 검증 실패")
                self.failed_count += 1
                return None

            # 결과 저장
            result = {
                "name_ko": name_ko,
                "name_en": name_en,
                "concept": menu_data.get("concept", ""),
                "content": content_json,
                "enriched_at": datetime.now().isoformat()
            }

            self.enriched_count += 1
            elapsed = time.time() - self.start_time
            avg_time = elapsed / self.enriched_count
            remaining = (112 - self.enriched_count) * avg_time
            print(f"  ✅ 완료 ({self.enriched_count}개) - 예상 남은 시간: {remaining/60:.1f}분")

            return result

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 파싱 오류: {str(e)}")
            print(f"  응답: {response_text[:200]}...")
            self.failed_count += 1
            return None
        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")
            self.failed_count += 1
            return None

    def _build_prompt(self, menu: Dict[str, Any]) -> str:
        """Gemini 프롬프트 생성"""
        ingredients_str = ", ".join(menu.get("primary_ingredients", []))
        existing_desc_ko = menu.get("description_ko", "")
        existing_desc_en = menu.get("description_en", "")
        spice_level = menu.get("spice_level", 0)

        prompt = f"""You are a Korean food expert. Generate comprehensive content for this Korean menu item in valid JSON format.

**Menu Information:**
- Korean Name: {menu["name_ko"]}
- English Name: {menu["name_en"]}
- Concept: {menu.get("concept", "N/A")}
- Main Ingredients: {ingredients_str}
- Spice Level: {spice_level}/5
- Existing Description (KO): {existing_desc_ko}
- Existing Description (EN): {existing_desc_en}

**Required Output (MUST be valid JSON):**

{{
  "description_ko": "150-200자 상세 설명 (한국어)",
  "description_en": "150-200 chars detailed description (English)",

  "regional_variants": [
    {{"name": "서울식", "difference": "서울에서의 특징"}},
    {{"name": "전라도식", "difference": "전라도에서의 특징"}},
    {{"name": "경상도식", "difference": "경상도에서의 특징"}}
  ],

  "preparation_steps": [
    "1단계: 재료 준비",
    "2단계: 육수 끓이기",
    "3단계: 양념 넣기",
    "4단계: 주재료 넣기",
    "5단계: 완성"
  ],

  "nutrition": {{
    "calories": 450,
    "protein_g": 20,
    "fat_g": 15,
    "carbs_g": 50,
    "serving_size": "1인분 (400g)"
  }},

  "flavor_profile": {{
    "spiciness": {spice_level},
    "sweetness": 1,
    "saltiness": 3,
    "umami": 4,
    "sourness": 1
  }},

  "visitor_tips": {{
    "ordering": "주문 시 팁",
    "eating": "먹는 방법",
    "pairing": "함께 먹으면 좋은 음식"
  }},

  "similar_dishes": [
    {{"name": "유사 메뉴 1", "similarity": "유사점"}},
    {{"name": "유사 메뉴 2", "similarity": "유사점"}},
    {{"name": "유사 메뉴 3", "similarity": "유사점"}}
  ],

  "cultural_background": {{
    "history": "역사적 배경 (2-3문장)",
    "origin": "기원 지역",
    "cultural_notes": "문화적 특징 (2-3문장)"
  }}
}}

**Important:**
1. Output ONLY the JSON object, nothing else
2. All Korean text must be culturally authentic
3. Nutrition values should be realistic
4. Minimum 3 regional variants, 5 preparation steps, 3 similar dishes
5. No markdown formatting, just pure JSON"""
        return prompt

    def _validate_content(self, content: Dict[str, Any]) -> bool:
        """콘텐츠 검증"""
        required_keys = [
            "description_ko", "description_en",
            "regional_variants", "preparation_steps",
            "nutrition", "flavor_profile",
            "visitor_tips", "similar_dishes",
            "cultural_background"
        ]

        for key in required_keys:
            if key not in content:
                print(f"  ⚠️  누락: {key}")
                return False

        # 최소 개수 검증
        if len(content.get("regional_variants", [])) < 3:
            print(f"  ⚠️  regional_variants 부족: {len(content.get('regional_variants', []))}개")
            return False
        if len(content.get("preparation_steps", [])) < 5:
            print(f"  ⚠️  preparation_steps 부족: {len(content.get('preparation_steps', []))}개")
            return False
        if len(content.get("similar_dishes", [])) < 3:
            print(f"  ⚠️  similar_dishes 부족: {len(content.get('similar_dishes', []))}개")
            return False

        return True

    def enrich_all_menus(self, menus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """전체 메뉴 처리 (동기 버전, Rate limit 고려)"""
        print(f"\n총 {len(menus)}개 메뉴 처리 시작...")
        print(f"모델: {self.model_name}")
        print(f"무료 tier: 15 RPM (분당 15 requests)")
        print("="*60)

        for i, menu in enumerate(menus):
            result = self.enrich_menu(menu)

            if result is not None:
                self.results.append(result)

            # 진행도
            progress = (i + 1) / len(menus) * 100
            print(f"\n진행도: {progress:.1f}% ({self.enriched_count}/{len(menus)})")

            # Rate limit 방지 (15 RPM = 4초 간격)
            if i < len(menus) - 1:
                time.sleep(4)

        print("\n" + "="*60)
        print(f"✅ 완료: {self.enriched_count}개")
        print(f"❌ 실패: {self.failed_count}개")
        success_rate = (self.enriched_count / len(menus) * 100) if len(menus) > 0 else 0
        print(f"성공률: {success_rate:.1f}%")

        total_time = time.time() - self.start_time
        print(f"총 소요 시간: {total_time/60:.1f}분")

        return self.results

    def save_results(self, output_path: Path):
        """결과 저장"""
        output_data = {
            "enriched_count": self.enriched_count,
            "failed_count": self.failed_count,
            "success_rate": (self.enriched_count / (self.enriched_count + self.failed_count)) if (self.enriched_count + self.failed_count) > 0 else 0,
            "enriched_at": datetime.now().isoformat(),
            "model": self.model_name,
            "provider": "Google Gemini",
            "menus": self.results
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n결과 저장: {output_path}")
        print(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """메인 함수"""
    print("="*60)
    print("Gemini 2.0 Flash 콘텐츠 강화 (무료 tier)")
    print("="*60)

    # 시드 데이터 로드
    print("\n시드 데이터 로드 중...")
    menus = get_canonical_menu_seeds()
    print(f"  ✅ {len(menus)}개 메뉴 로드 완료")

    # Enricher 생성
    enricher = GeminiContentEnricher()

    # 전체 메뉴 처리
    enricher.enrich_all_menus(menus)

    # 결과 저장
    output_path = BASE_DIR / "data" / "enriched_menus.json"
    enricher.save_results(output_path)

    print("\n✅ 모든 작업 완료!")
    print(f"비용: $0 (무료 tier)")


if __name__ == "__main__":
    main()
