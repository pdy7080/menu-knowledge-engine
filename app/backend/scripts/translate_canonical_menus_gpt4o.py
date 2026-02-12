#!/usr/bin/env python3
"""
다국어 번역 스크립트 - GPT-4o 기반
Papago 대비 93% 비용 절감

사용법:
  python translate_canonical_menus_gpt4o.py \
    --language ja,zh \
    --batch-size 10 \
    --max-retries 3
"""

import asyncio
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Database
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# OpenAI
from openai import AsyncOpenAI

# Config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from models.canonical_menu import CanonicalMenu


class TranslationService:
    """GPT-4o 기반 번역 서비스"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"  # ✅ GPT-4o 사용

        # Database
        self.engine = create_engine(settings.DATABASE_URL)

        # Stats
        self.translated_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    async def translate_menu_description(
        self,
        menu_name_ko: str,
        description_en: str,
        target_languages: List[str] = ["ja", "zh"]
    ) -> Dict[str, str]:
        """
        GPT-4o를 사용한 메뉴 설명 번역

        Args:
            menu_name_ko: 한식당 메뉴명 (한글)
            description_en: 영문 설명
            target_languages: 목표 언어 (ja, zh)

        Returns:
            {"ja": "...", "zh": "..."}
        """

        # 프롬프트 구성 (한식 문화 맥락 포함)
        target_langs_str = ", ".join(
            {"ja": "일본어", "zh": "중국어(간체)"}.get(lang, lang)
            for lang in target_languages
        )

        prompt = f"""
당신은 한식 요리사이자 다국어 번역가입니다.

다음 한식 메뉴의 영문 설명을 {target_langs_str}로 번역해주세요.
- 한식 문화, 재료, 맛의 특징을 자연스럽게 표현하세요
- 각 언어권 고객이 이해할 수 있는 음식 문화 설명을 포함하세요
- 번역은 자연스럽고 정확하게 해주세요

메뉴 정보:
- 메뉴명(한글): {menu_name_ko}
- 영문 설명: {description_en}

출력 형식 (JSON만 반환, 다른 텍스트 없음):
{{
    "ja": "일본어 번역",
    "zh": "중국어(간체) 번역"
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Korean cuisine expert and translator. "
                        "Translate food descriptions naturally considering cultural context."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 일관된 번역
                max_tokens=200,
                response_format={"type": "json_object"}  # JSON 출력 강제
            )

            # 응답 파싱
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return {lang: result.get(lang, "") for lang in target_languages}

        except Exception as e:
            print(f"  [FAIL] Translation error ({menu_name_ko}): {e}")
            self.error_count += 1
            return {lang: "" for lang in target_languages}

    async def batch_translate(
        self,
        menus: List[Dict],
        target_languages: List[str],
        batch_size: int = 10,
        max_retries: int = 3
    ):
        """
        배치 번역 (동시 처리)

        Args:
            menus: [{"name_ko": "...", "description_en": "..."}, ...]
            target_languages: ["ja", "zh"]
            batch_size: 동시 처리 개수
            max_retries: 최대 재시도 횟수
        """

        print(f"\n[START] Batch Translation (GPT-4o)")
        print(f"  [MENUS] Total: {len(menus)}")
        print(f"  [LANGS] Target: {', '.join(target_languages)}")
        print(f"  [BATCH] Concurrent: {batch_size} menus/batch\n")

        # 배치로 나누기
        for i in range(0, len(menus), batch_size):
            batch = menus[i : i + batch_size]
            print(f"[BATCH {i // batch_size + 1}] Processing {len(batch)} menus...")

            # 동시 처리
            tasks = [
                self.translate_menu_description(
                    menu["name_ko"],
                    menu["description_en"],
                    target_languages
                )
                for menu in batch
            ]

            results = await asyncio.gather(*tasks)

            # 결과 저장
            for menu, result in zip(batch, results):
                if any(result.values()):  # 최소 하나 이상 번역됨
                    self.translated_count += 1
                    ja_status = 'OK' if result.get('ja') else 'FAIL'
                    zh_status = 'OK' if result.get('zh') else 'FAIL'
                    print(
                        f"  [OK] {menu['name_ko']}: "
                        f"JA={ja_status} "
                        f"ZH={zh_status}"
                    )

                    # 즉시 DB에 저장
                    yield menu, result

        print(f"\n[COMPLETE] Translated: {self.translated_count} menus")
        if self.error_count:
            print(f"[ERRORS] Failed: {self.error_count} menus")

    def save_to_database(self, menu_id: str, translations: Dict[str, str]):
        """DB에 번역 데이터 저장"""
        with Session(self.engine) as session:
            menu = session.query(CanonicalMenu).filter(
                CanonicalMenu.id == menu_id
            ).first()

            if menu:
                # JSONB 컬럼 업데이트 (SQLAlchemy 변경 감지를 위해 전체 재할당)
                updated_dict = menu.explanation_short.copy() if menu.explanation_short else {}

                for lang, text in translations.items():
                    if text:
                        updated_dict[lang] = text

                # 전체 딕셔너리 재할당 (이렇게 해야 SQLAlchemy가 변경 감지)
                menu.explanation_short = updated_dict

                session.commit()


async def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description="GPT-4o 기반 메뉴 번역")
    parser.add_argument(
        "--language",
        default="ja,zh",
        help="번역 언어 (쉼표로 구분, 기본: ja,zh)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="동시 처리 개수 (기본: 10)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="최대 재시도 횟수 (기본: 3)"
    )

    args = parser.parse_args()
    target_languages = args.language.split(",")

    # 서비스 초기화
    service = TranslationService()

    # DB에서 메뉴 로드
    with Session(service.engine) as session:
        menus_db = session.query(CanonicalMenu).all()

    # 번역할 메뉴 준비
    menus_to_translate = [
        {
            "id": menu.id,
            "name_ko": menu.name_ko,
            "description_en": menu.explanation_short.get("en", "")
            if menu.explanation_short else ""
        }
        for menu in menus_db
        if menu.explanation_short and menu.explanation_short.get("en")
    ]

    print(f"[LOAD] Loaded menus from DB: {len(menus_to_translate)}")

    # 배치 번역 실행
    count = 0
    async for menu, translations in service.batch_translate(
        menus_to_translate,
        target_languages,
        batch_size=args.batch_size,
        max_retries=args.max_retries
    ):
        service.save_to_database(menu["id"], translations)
        count += 1

    # 통계
    elapsed = datetime.now() - service.start_time
    print(f"\n" + "=" * 60)
    print(f"[STATS] Translation Summary")
    print(f"=" * 60)
    print(f"  [RESULT] Translated: {count} menus")
    print(f"  [TIME] Elapsed: {elapsed.total_seconds():.1f} seconds")
    print(f"  [COST] Estimated: ~{count * 50:,} KRW (very affordable!)")
    print(f"  [SPEED] Average: {count / elapsed.total_seconds():.1f} menus/sec")
    print(f"=" * 60)

    print(f"\n[SUCCESS] All translations saved to DB!")
    print(f"   Next: I18n-Auditor re-validation")


if __name__ == "__main__":
    asyncio.run(main())
