"""
GPT-4o 콘텐츠 자동 확장 스크립트 (Sprint 2 Phase 1)
300개 메뉴에 대해 8가지 콘텐츠 유형 자동 생성

Content Types:
1. Detailed descriptions (Korean/English, 150-200 chars each)
2. Regional variants (3-5 variations)
3. Preparation steps (5-7 steps)
4. Nutrition info (calories, protein, fat, carbs)
5. Flavor profile (spiciness, sweetness, saltiness, umami, sourness)
6. Visitor tips (ordering, eating, pairing)
7. Similar dishes (3-5 recommendations)
8. Cultural background (history, origin)

Author: content-engineer (Agent Teams)
Date: 2026-02-19
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai

# Path 설정
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings
from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from sqlalchemy import select


# OpenAI 클라이언트 초기화
client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class ContentEnricher:
    """메뉴 콘텐츠 확장 엔진"""

    def __init__(self):
        self.model = "gpt-4o-mini"  # 비용 효율성
        self.temperature = 0.3  # 사실성 중시
        self.enriched_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []

    async def enrich_menu(self, menu: CanonicalMenu) -> Optional[Dict[str, Any]]:
        """단일 메뉴에 대해 8가지 콘텐츠 생성"""
        print(f"\n[{self.enriched_count + 1}] {menu.name_ko} ({menu.name_en}) 처리 중...")

        try:
            # GPT-4o-mini 프롬프트 생성
            prompt = self._build_prompt(menu)

            # API 호출
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Korean food expert specializing in menu content creation. "
                            "Provide accurate, culturally authentic information about Korean dishes. "
                            "Always output valid JSON format with all requested fields."
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
                print(f"  ❌ 검증 실패: {menu.name_ko}")
                self.failed_count += 1
                return None

            # 결과 저장
            result = {
                "menu_id": str(menu.id),
                "name_ko": menu.name_ko,
                "name_en": menu.name_en,
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

    def _build_prompt(self, menu: CanonicalMenu) -> str:
        """GPT-4o-mini 프롬프트 생성"""
        main_ingredients_str = ", ".join([
            ing.get("ko", "") for ing in menu.main_ingredients
        ]) if menu.main_ingredients else "정보 없음"

        # 기존 설명 활용 (있는 경우)
        existing_desc_ko = menu.explanation_short.get("ko", "") if isinstance(menu.explanation_short, dict) else ""
        existing_desc_en = menu.explanation_short.get("en", "") if isinstance(menu.explanation_short, dict) else ""

        prompt = f"""
Generate comprehensive content for the Korean menu item below.

**Menu Information:**
- Korean Name: {menu.name_ko}
- English Name: {menu.name_en}
- Main Ingredients: {main_ingredients_str}
- Spice Level: {menu.spice_level}/5
- Existing Description (KO): {existing_desc_ko or "없음"}
- Existing Description (EN): {existing_desc_en or "없음"}

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
    "spiciness": 3,
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

**Important Rules:**
1. All Korean text must be accurate and culturally authentic
2. Nutrition values should be realistic (research if unsure)
3. Flavor profile: 1-5 scale (1=very low, 5=very high)
4. Regional variants: focus on actual regional differences in Korea
5. Preparation steps: concise, actionable steps
6. Similar dishes: recommend actual Korean dishes
7. Output MUST be valid JSON
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

        # 필수 키 확인
        for key in required_keys:
            if key not in content:
                print(f"  ⚠️  누락된 필드: {key}")
                return False

        # 타입 검증
        if not isinstance(content["regional_variants"], list):
            return False
        if not isinstance(content["preparation_steps"], list):
            return False
        if not isinstance(content["similar_dishes"], list):
            return False

        # 필드 개수 검증
        if len(content["regional_variants"]) < 3:
            print(f"  ⚠️  regional_variants 부족: {len(content['regional_variants'])}개")
            return False
        if len(content["preparation_steps"]) < 5:
            print(f"  ⚠️  preparation_steps 부족: {len(content['preparation_steps'])}개")
            return False
        if len(content["similar_dishes"]) < 3:
            print(f"  ⚠️  similar_dishes 부족: {len(content['similar_dishes'])}개")
            return False

        return True

    async def enrich_all_menus(self, limit: int = 300) -> List[Dict[str, Any]]:
        """전체 메뉴 처리 (배치)"""
        async with AsyncSessionLocal() as session:
            # DB에서 메뉴 로드
            stmt = select(CanonicalMenu).where(
                CanonicalMenu.status == "active"
            ).limit(limit)
            result = await session.execute(stmt)
            menus = result.scalars().all()

            print(f"\n총 {len(menus)}개 메뉴 처리 시작...")
            print(f"모델: {self.model} (temperature={self.temperature})")
            print("="*60)

            # 배치 처리 (동시성 제한: 5개씩)
            batch_size = 5
            for i in range(0, len(menus), batch_size):
                batch = menus[i:i + batch_size]
                tasks = [self.enrich_menu(menu) for menu in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 성공한 결과만 저장
                for result in results:
                    if isinstance(result, dict) and result is not None:
                        self.results.append(result)

                # 진행도 출력
                progress = min((i + batch_size) / len(menus) * 100, 100)
                print(f"\n진행도: {progress:.1f}% ({self.enriched_count}/{len(menus)})")

                # Rate limit 방지 (1초 대기)
                await asyncio.sleep(1)

            print("\n" + "="*60)
            print(f"✅ 완료: {self.enriched_count}개")
            print(f"❌ 실패: {self.failed_count}개")
            print(f"성공률: {self.enriched_count / len(menus) * 100:.1f}%")

            return self.results

    def save_results(self, output_path: Path):
        """결과 저장 (JSON)"""
        output_data = {
            "enriched_count": self.enriched_count,
            "failed_count": self.failed_count,
            "success_rate": self.enriched_count / (self.enriched_count + self.failed_count) if (self.enriched_count + self.failed_count) > 0 else 0,
            "enriched_at": datetime.now().isoformat(),
            "model": self.model,
            "temperature": self.temperature,
            "menus": self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n결과 저장: {output_path}")
        print(f"파일 크기: {output_path.stat().st_size / 1024:.1f} KB")


async def main():
    """메인 함수"""
    print("="*60)
    print("GPT-4o 콘텐츠 자동 확장 (Sprint 2 Phase 1)")
    print("="*60)

    # 환경변수 확인
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("  .env 파일에 OPENAI_API_KEY를 추가하세요.")
        sys.exit(1)

    # Enricher 생성
    enricher = ContentEnricher()

    # 전체 메뉴 처리
    await enricher.enrich_all_menus(limit=300)

    # 결과 저장
    # BASE_DIR = app/backend, parent.parent = project root
    output_path = BASE_DIR.parent.parent / "data" / "enriched_menus.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enricher.save_results(output_path)

    print("\n✅ 모든 작업 완료!")
    print(f"다음 단계: 품질 검증 (data/enriched_menus.json 확인)")


if __name__ == "__main__":
    asyncio.run(main())
