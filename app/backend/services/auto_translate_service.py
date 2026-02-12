#!/usr/bin/env python3
"""
자동 번역 서비스 - 새 메뉴 자동 번역

기능:
- 새 canonical_menu 생성 시 자동 번역 트리거
- 일본어/중국어 자동 생성
- 백그라운드 비동기 처리
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

# Logging
import logging

logger = logging.getLogger(__name__)

# Database
from sqlalchemy.orm import Session

# OpenAI
from openai import AsyncOpenAI

# Models
from models.canonical_menu import CanonicalMenu

# Config
from config import settings


class AutoTranslateService:
    """새 메뉴 자동 번역 서비스"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    async def auto_translate_new_menu(
        self,
        menu_id: UUID,
        menu_name_ko: str,
        description_en: str,
        db: Session
    ) -> Dict[str, str]:
        """
        새 메뉴 자동 번역

        호출 위치:
        1. CanonicalMenu 모델의 after_insert 이벤트
        2. Admin API에서 새 메뉴 등록 시
        3. 수동 번역 필요 시

        Args:
            menu_id: 메뉴 ID
            menu_name_ko: 한글 메뉴명
            description_en: 영문 설명
            db: Database session

        Returns:
            {"ja": "...", "zh": "..."}
        """

        try:
            logger.info(f"🔄 자동 번역 시작: {menu_name_ko}")

            # GPT-4o로 번역
            translations = await self._translate_with_gpt4o(
                menu_name_ko,
                description_en
            )

            # DB 업데이트
            if translations and any(translations.values()):
                menu = db.query(CanonicalMenu).filter(
                    CanonicalMenu.id == menu_id
                ).first()

                if menu:
                    if not menu.explanation_short:
                        menu.explanation_short = {}

                    # 기존 영문 보존
                    menu.explanation_short["en"] = description_en

                    # 번역 추가
                    for lang, text in translations.items():
                        if text:
                            menu.explanation_short[lang] = text

                    db.commit()
                    logger.info(f"✅ 자동 번역 완료: {menu_name_ko}")
                    return translations

        except Exception as e:
            logger.error(f"❌ 자동 번역 실패: {menu_name_ko} - {e}")
            return {}

        return {}

    async def _translate_with_gpt4o(
        self,
        menu_name_ko: str,
        description_en: str
    ) -> Dict[str, str]:
        """GPT-4o로 번역"""

        prompt = f"""
당신은 한식 요리사이자 다국어 번역가입니다.

다음 한식 메뉴의 영문 설명을 일본어와 중국어(간체)로 번역해주세요.
- 한식 문화, 재료, 맛의 특징을 자연스럽게 표현하세요
- 각 언어권 고객이 이해할 수 있도록 설명하세요

메뉴 정보:
- 메뉴명(한글): {menu_name_ko}
- 영문 설명: {description_en}

출력 형식 (JSON만 반환):
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
                        "content": "You are a Korean cuisine expert translator. "
                        "Translate food descriptions naturally with cultural context."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return {
                "ja": result.get("ja", ""),
                "zh": result.get("zh", "")
            }

        except Exception as e:
            logger.error(f"GPT-4o 번역 오류: {e}")
            return {}


# 싱글톤 인스턴스
auto_translate_service = AutoTranslateService()


# ============================================================
# 사용 예시 (API에서)
# ============================================================

"""
# app/backend/api/admin.py에서

@router.post("/api/v1/admin/canonical-menus")
async def create_canonical_menu(
    menu_data: CanonicalMenuCreate,
    db: Session = Depends(get_db)
):
    '''새 canonical 메뉴 생성 → 자동 번역'''

    # 1. 메뉴 생성 (영문만)
    menu = CanonicalMenu(
        name_ko=menu_data.name_ko,
        name_en=menu_data.name_en,
        explanation_short={
            "en": menu_data.explanation_short_en
        }
    )
    db.add(menu)
    db.commit()

    # 2. 자동 번역 트리거 (백그라운드)
    asyncio.create_task(
        auto_translate_service.auto_translate_new_menu(
            menu_id=menu.id,
            menu_name_ko=menu_data.name_ko,
            description_en=menu_data.explanation_short_en,
            db=db
        )
    )

    return {
        "id": menu.id,
        "message": "메뉴 생성 완료. 자동 번역 진행 중..."
    }
"""
