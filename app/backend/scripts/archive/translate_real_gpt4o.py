#!/usr/bin/env python3
"""
순수 GPT-4o 번역 스크립트 (Mock 로직 제거)
실제 OpenAI API만 사용
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict

# Setup path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from config import settings
from models.canonical_menu import CanonicalMenu


class RealTranslationService:
    """순수 GPT-4o 번역"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.engine = create_engine(settings.DATABASE_URL)
        self.translated = 0
        self.failed = 0
        self.start_time = datetime.now()

    async def translate(self, name_ko: str, desc_en: str) -> Dict[str, str]:
        """
        GPT-4o로 실제 번역
        """

        prompt = f"""당신은 한식 요리사이자 다국어 번역가입니다.

다음 한식 메뉴의 영문 설명을 일본어와 중국어(간체)로 번역해주세요.
- 한식 문화, 재료, 맛의 특징을 자연스럽게 표현하세요
- 각 언어권 고객이 이해할 수 있도록 설명하세요

메뉴: {name_ko}
설명: {desc_en}

JSON 형식으로만 응답:
{{"ja": "일본어", "zh": "중국어"}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Korean cuisine expert. Translate naturally.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            return {"ja": result.get("ja", ""), "zh": result.get("zh", "")}

        except Exception as e:
            print(f"    [ERROR] {e}")
            self.failed += 1
            return {}

    async def translate_all(self, batch_size: int = 10):
        """모든 메뉴 번역"""

        with Session(self.engine) as session:
            menus = session.query(CanonicalMenu).all()

        print(f"\n[START] Translating {len(menus)} menus with GPT-4o...")

        menus_to_process = []
        for menu in menus:
            if menu.explanation_short and menu.explanation_short.get("en"):
                menus_to_process.append(
                    {
                        "id": menu.id,
                        "name_ko": menu.name_ko,
                        "desc_en": menu.explanation_short["en"],
                    }
                )

        # 배치 처리
        for i in range(0, len(menus_to_process), batch_size):
            batch = menus_to_process[i : i + batch_size]
            print(f"\n[BATCH {i//batch_size + 1}] Processing {len(batch)} menus...")

            # 동시 번역
            tasks = [self.translate(m["name_ko"], m["desc_en"]) for m in batch]

            results = await asyncio.gather(*tasks)

            # DB 저장
            with Session(self.engine) as session:
                for menu_data, translation in zip(batch, results):
                    if translation and (translation.get("ja") or translation.get("zh")):
                        menu = (
                            session.query(CanonicalMenu)
                            .filter(CanonicalMenu.id == menu_data["id"])
                            .first()
                        )

                        if menu:
                            if not menu.explanation_short:
                                menu.explanation_short = {}

                            # 영문 보존
                            menu.explanation_short["en"] = menu_data["desc_en"]

                            # 번역 추가
                            if translation.get("ja"):
                                menu.explanation_short["ja"] = translation["ja"]
                            if translation.get("zh"):
                                menu.explanation_short["zh"] = translation["zh"]

                            session.commit()
                            self.translated += 1

                            print(f"    [OK] {menu_data['name_ko']}")

        # 결과
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"[COMPLETE] Translations: {self.translated} menus")
        print(f"[FAILED] Failed: {self.failed} menus")
        print(f"[TIME] {elapsed:.1f} seconds")
        print(f"[COST] ~{self.translated * 50:,} KRW")
        print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Real GPT-4o Translation")
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    service = RealTranslationService()
    await service.translate_all(batch_size=args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
