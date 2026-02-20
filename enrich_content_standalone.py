"""
Standalone 콘텐츠 강화 스크립트 (DB 불필요)
시드 데이터에서 직접 메뉴 로드 → GPT-4o-mini 콘텐츠 생성

Author: terminal-developer
Date: 2026-02-19
Cost: ~$0.20 (112 menus × GPT-4o-mini)
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# OpenAI 클라이언트
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

# 시드 데이터 import
from seeds.seed_canonical_menus import get_canonical_menu_seeds


class ContentEnricher:
    """메뉴 콘텐츠 확장 엔진 (DB 불필요 버전)"""

    def __init__(self):
        self.model = "gpt-4o-mini"
        self.temperature = 0.3
        self.enriched_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []

    async def enrich_menu(self, menu_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """단일 메뉴 콘텐츠 생성"""
        name_ko = menu_data["name_ko"]
        name_en = menu_data["name_en"]

        print(f"\n[{self.enriched_count + 1}] {name_ko} ({name_en}) 처리 중...")

        try:
            # GPT-4o-mini 프롬프트 생성
            prompt = self._build_prompt(menu_data)

            # API 호출
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Korean food expert. "
                            "Provide accurate, culturally authentic information. "
                            "Always output valid JSON format."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # JSON 파싱
            content_json = json.loads(response.choices[0].message.content)

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
            print(f"  ✅ 완료 ({self.enriched_count}개)")

            return result

        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")
            self.failed_count += 1
            return None

    def _build_prompt(self, menu: Dict[str, Any]) -> str:
        """GPT-4o-mini 프롬프트 생성"""
        ingredients_str = ", ".join(menu.get("primary_ingredients", []))
        existing_desc_ko = menu.get("description_ko", "")
        existing_desc_en = menu.get("description_en", "")
        spice_level = menu.get("spice_level", 0)

        prompt = f"""
Generate comprehensive content for this Korean menu item.

**Menu Information:**
- Korean Name: {menu["name_ko"]}
- English Name: {menu["name_en"]}
- Concept: {menu.get("concept", "N/A")}
- Main Ingredients: {ingredients_str}
- Spice Level: {spice_level}/5
- Existing Description (KO): {existing_desc_ko}
- Existing Description (EN): {existing_desc_en}

**Required Output (JSON format):**

{{
  "description_ko": "150-200자 상세 설명 (한국어)",
  "description_en": "150-200 chars detailed description (English)",

  "regional_variants": [
    {{"name": "지역명", "difference": "차이점"}},
    // 3-5 variations
  ],

  "preparation_steps": [
    "1단계 설명",
    "2단계 설명",
    // 5-7 steps
  ],

  "nutrition": {{
    "calories": 500,
    "protein_g": 20,
    "fat_g": 15,
    "carbs_g": 60,
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
    "ordering": "주문 팁",
    "eating": "먹는 법",
    "pairing": "함께 먹으면 좋은 음식"
  }},

  "similar_dishes": [
    {{"name": "유사 메뉴명", "similarity": "유사점"}},
    // 3-5 recommendations
  ],

  "cultural_background": {{
    "history": "역사적 배경 (2-3문장)",
    "origin": "기원/지역",
    "cultural_notes": "문화적 특징 (2-3문장)"
  }}
}}

**Rules:**
1. All Korean text must be culturally authentic
2. Nutrition values should be realistic
3. Flavor profile: 1-5 scale
4. Output MUST be valid JSON
"""
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
            return False
        if len(content.get("preparation_steps", [])) < 5:
            return False
        if len(content.get("similar_dishes", [])) < 3:
            return False

        return True

    async def enrich_all_menus(self, menus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """전체 메뉴 배치 처리"""
        print(f"\n총 {len(menus)}개 메뉴 처리 시작...")
        print(f"모델: {self.model} (temperature={self.temperature})")
        print("="*60)

        # 배치 처리 (동시성 5개)
        batch_size = 5
        for i in range(0, len(menus), batch_size):
            batch = menus[i:i + batch_size]
            tasks = [self.enrich_menu(menu) for menu in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 성공한 결과만 저장
            for result in results:
                if isinstance(result, dict) and result is not None:
                    self.results.append(result)

            # 진행도
            progress = min((i + batch_size) / len(menus) * 100, 100)
            print(f"\n진행도: {progress:.1f}% ({self.enriched_count}/{len(menus)})")

            # Rate limit 방지
            await asyncio.sleep(1)

        print("\n" + "="*60)
        print(f"✅ 완료: {self.enriched_count}개")
        print(f"❌ 실패: {self.failed_count}개")
        success_rate = (self.enriched_count / len(menus) * 100) if len(menus) > 0 else 0
        print(f"성공률: {success_rate:.1f}%")

        return self.results

    def save_results(self, output_path: Path):
        """결과 저장"""
        output_data = {
            "enriched_count": self.enriched_count,
            "failed_count": self.failed_count,
            "success_rate": (self.enriched_count / (self.enriched_count + self.failed_count)) if (self.enriched_count + self.failed_count) > 0 else 0,
            "enriched_at": datetime.now().isoformat(),
            "model": self.model,
            "temperature": self.temperature,
            "menus": self.results
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n결과 저장: {output_path}")
        print(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")


async def main():
    """메인 함수"""
    print("="*60)
    print("Standalone 콘텐츠 강화 (Option C)")
    print("="*60)

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    # 시드 데이터 로드
    print("\n시드 데이터 로드 중...")
    menus = get_canonical_menu_seeds()
    print(f"  ✅ {len(menus)}개 메뉴 로드 완료")

    # Enricher 생성
    enricher = ContentEnricher()

    # 전체 메뉴 처리
    await enricher.enrich_all_menus(menus)

    # 결과 저장
    output_path = BASE_DIR / "data" / "enriched_menus.json"
    enricher.save_results(output_path)

    # 통계 출력
    total_cost = (enricher.enriched_count * 1500 * 0.15 / 1_000_000) + \
                 (enricher.enriched_count * 1000 * 0.60 / 1_000_000)
    print(f"\n예상 비용: ${total_cost:.2f}")
    print("\n✅ 모든 작업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
