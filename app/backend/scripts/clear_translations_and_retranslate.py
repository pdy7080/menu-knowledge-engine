#!/usr/bin/env python3
"""
1. 모든 번역 데이터(ja, zh) 완전 삭제
2. 새로운 실제 GPT-4o 번역 저장
"""

import asyncio
import json
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


class TranslationCleaner:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def clear_all_translations(self):
        """Step 1: 모든 ja/zh 번역 삭제"""
        with Session(self.engine) as session:
            menus = session.query(CanonicalMenu).all()

            for menu in menus:
                if menu.explanation_short:
                    # ja, zh만 삭제 (en은 보존)
                    if 'ja' in menu.explanation_short:
                        del menu.explanation_short['ja']
                    if 'zh' in menu.explanation_short:
                        del menu.explanation_short['zh']

            session.commit()

        print(f"[DONE] All ja/zh translations cleared")

    async def translate_one(self, name_ko: str, desc_en: str) -> Dict[str, str]:
        """실제 GPT-4o 번역"""
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
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Korean cuisine expert. Translate naturally without any prefix like [JA] or [ZH]."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=250,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            return {"ja": result.get("ja", ""), "zh": result.get("zh", "")}

        except Exception as e:
            print(f"    [ERROR] Translation failed: {e}")
            return {}

    async def retranslate_all(self, batch_size: int = 10):
        """Step 2: 새로운 실제 번역 저장"""

        print(f"\n[START] Retranslating all menus with real GPT-4o...")

        with Session(self.engine) as session:
            menus_db = session.query(CanonicalMenu).all()

        menus_to_translate = [
            {"id": m.id, "name_ko": m.name_ko, "desc_en": m.explanation_short.get("en", "")}
            for m in menus_db
            if m.explanation_short and m.explanation_short.get("en")
        ]

        # 배치 처리
        success = 0
        for i in range(0, len(menus_to_translate), batch_size):
            batch = menus_to_translate[i:i+batch_size]
            print(f"[BATCH {i//batch_size + 1}] Processing {len(batch)} menus...")

            # 동시 번역
            tasks = [self.translate_one(m["name_ko"], m["desc_en"]) for m in batch]
            results = await asyncio.gather(*tasks)

            # DB 저장 (매우 주의깊게)
            with Session(self.engine) as session:
                for menu_data, translation in zip(batch, results):
                    if translation.get("ja") or translation.get("zh"):
                        menu = session.query(CanonicalMenu).filter(
                            CanonicalMenu.id == menu_data["id"]
                        ).first()

                        if menu:
                            if not menu.explanation_short:
                                menu.explanation_short = {}

                            # 새로운 번역 추가 (이전 데이터는 이미 삭제됨)
                            if translation.get("ja"):
                                menu.explanation_short["ja"] = translation["ja"]
                            if translation.get("zh"):
                                menu.explanation_short["zh"] = translation["zh"]

                            session.commit()
                            success += 1
                            print(f"    [OK] {menu_data['name_ko']}")

        print(f"\n[COMPLETE] Retranslated: {success} menus")

async def main():
    cleaner = TranslationCleaner()

    print("="*70)
    print("[STEP 1] Clearing all previous translations (ja, zh)")
    print("="*70)
    cleaner.clear_all_translations()

    print("\n" + "="*70)
    print("[STEP 2] Retranslating with real GPT-4o")
    print("="*70)
    await cleaner.retranslate_all(batch_size=10)

    print("\n[SUCCESS] Complete!")

if __name__ == "__main__":
    asyncio.run(main())
