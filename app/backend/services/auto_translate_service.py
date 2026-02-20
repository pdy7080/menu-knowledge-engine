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
from sqlalchemy.ext.asyncio import AsyncSession

# Google Gemini
import google.generativeai as genai

# Models
from models.canonical_menu import CanonicalMenu

# Config
from config import settings

# Retry utility
from utils.retry import async_retry


class AutoTranslateService:
    """새 메뉴 자동 번역 서비스 (Multi-Key Round Robin)"""

    def __init__(self):
        # 다중 API 키 설정 (라운드 로빈)
        self.api_keys = []

        # 키 수집 (빈 문자열 제외)
        for key_name in ['GOOGLE_API_KEY_1', 'GOOGLE_API_KEY_2', 'GOOGLE_API_KEY_3']:
            key_value = getattr(settings, key_name, "")
            if key_value:
                self.api_keys.append(key_value)

        # Fallback: 기존 GOOGLE_API_KEY 사용
        if not self.api_keys and settings.GOOGLE_API_KEY:
            self.api_keys.append(settings.GOOGLE_API_KEY)

        if not self.api_keys:
            raise ValueError("❌ No Google API keys configured")

        # 라운드 로빈 상태
        self.current_key_index = 0
        self.daily_usage = {i: 0 for i in range(len(self.api_keys))}  # 키별 사용량
        self.max_rpd = 20  # Requests Per Day per key

        logger.info(f"✅ Google Gemini API 초기화 완료 ({len(self.api_keys)}개 키, 총 {len(self.api_keys) * self.max_rpd} RPD)")

    def _get_next_available_key(self) -> Optional[str]:
        """사용 가능한 다음 키 반환 (라운드 로빈)"""
        # 모든 키를 순회하며 사용 가능한 키 찾기
        for attempt in range(len(self.api_keys)):
            key_index = (self.current_key_index + attempt) % len(self.api_keys)

            # RPD 한도 확인
            if self.daily_usage[key_index] < self.max_rpd:
                self.current_key_index = key_index
                return self.api_keys[key_index]

        # 모든 키가 소진됨
        logger.warning("⚠️ All API keys exhausted (60 RPD limit reached)")
        return None

    def _mark_key_used(self):
        """현재 키 사용량 증가"""
        self.daily_usage[self.current_key_index] += 1
        logger.debug(f"Key {self.current_key_index + 1} used: {self.daily_usage[self.current_key_index]}/{self.max_rpd}")

    async def auto_translate_new_menu(
        self,
        menu_id: UUID,
        menu_name_ko: str,
        description_en: str,
        db: AsyncSession
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

            # Google Gemini로 번역
            translations = await self._translate_with_gemini(
                menu_name_ko,
                description_en
            )

            # DB 업데이트 (async)
            if translations and any(translations.values()):
                from sqlalchemy import select
                result = await db.execute(
                    select(CanonicalMenu).where(CanonicalMenu.id == menu_id)
                )
                menu = result.scalar_one_or_none()

                if menu:
                    if not menu.explanation_short:
                        menu.explanation_short = {}

                    # 기존 영문 보존
                    menu.explanation_short["en"] = description_en

                    # 번역 추가
                    for lang, text in translations.items():
                        if text:
                            menu.explanation_short[lang] = text

                    await db.commit()
                    logger.info(f"✅ 자동 번역 완료: {menu_name_ko}")
                    return translations

        except Exception as e:
            logger.error(f"❌ 자동 번역 실패: {menu_name_ko} - {e}")
            return {}

        return {}

    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def _translate_with_gemini(
        self,
        menu_name_ko: str,
        description_en: str
    ) -> Dict[str, str]:
        """
        Google Gemini로 번역 (Multi-Key Round Robin)

        Retry policy:
        - Attempt 1: immediate
        - Attempt 2: after 1.0 seconds (다음 키로 자동 전환)
        - Attempt 3: after 2.0 seconds (다음 키로 자동 전환)
        """

        # 사용 가능한 키 확인
        api_key = self._get_next_available_key()
        if not api_key:
            logger.error("❌ All API keys exhausted (60 RPD)")
            return {}

        # 해당 키로 Gemini 설정
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
당신은 한식 요리사이자 다국어 번역가입니다.

다음 한식 메뉴의 영문 설명을 일본어와 중국어(간체)로 번역해주세요.
- 한식 문화, 재료, 맛의 특징을 자연스럽게 표현하세요
- 각 언어권 고객이 이해할 수 있도록 설명하세요

메뉴 정보:
- 메뉴명(한글): {menu_name_ko}
- 영문 설명: {description_en}

출력 형식 (JSON만 반환, 다른 텍스트 없이):
{{
    "ja": "일본어 번역",
    "zh": "중국어(간체) 번역"
}}
"""

        try:
            # Gemini API 호출
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200,
                )
            )

            result_text = response.text.strip()

            # JSON 파싱 (마크다운 코드블록 제거)
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # 성공 시 사용량 증가
            self._mark_key_used()

            return {
                "ja": result.get("ja", ""),
                "zh": result.get("zh", "")
            }

        except Exception as e:
            error_msg = str(e)

            # 429 에러 시 현재 키 소진 처리
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"⚠️ Key {self.current_key_index + 1} quota exhausted, switching to next key")
                self.daily_usage[self.current_key_index] = self.max_rpd  # 강제 소진
                # Retry 시 자동으로 다음 키 사용

            logger.error(f"Google Gemini 번역 오류 (Key {self.current_key_index + 1}): {e}")
            raise  # Retry decorator가 처리


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
