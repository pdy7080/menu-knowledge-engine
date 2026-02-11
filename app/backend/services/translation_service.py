"""
Translation Service - Sprint 3 P1-2
Papago API 연동 + 자동 캐싱
"""

import os
import requests
from typing import Dict, Optional
import json


class TranslationService:
    """
    Papago API 번역 서비스

    Features:
    - 영문 → 일본어/중국어 번역
    - 캐싱 (메모리/DB JSONB)
    - 배치 번역 지원
    """

    def __init__(self):
        self.papago_client_id = os.getenv("PAPAGO_CLIENT_ID")
        self.papago_client_secret = os.getenv("PAPAGO_CLIENT_SECRET")
        self.papago_url = "https://naveropenapi.apigw.ntruss.com/nmt/v1/translation"

        # In-memory cache
        self.cache = {}

    def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "ja"
    ) -> Optional[str]:
        """
        단일 텍스트 번역

        Args:
            text: 원문
            source_lang: 원본 언어 (en, ko, ja, zh-CN, zh-TW)
            target_lang: 목표 언어 (en, ko, ja, zh-CN, zh-TW)

        Returns:
            번역된 텍스트 또는 None (실패 시)
        """
        if not self.papago_client_id or not self.papago_client_secret:
            print("Warning: Papago API credentials not configured")
            return None

        # Cache key
        cache_key = f"{source_lang}_{target_lang}_{text}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.papago_client_id,
                "X-NCP-APIGW-API-KEY": self.papago_client_secret,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            data = {
                "source": source_lang,
                "target": target_lang,
                "text": text
            }

            response = requests.post(
                self.papago_url,
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                translated_text = result["message"]["result"]["translatedText"]

                # Cache result
                self.cache[cache_key] = translated_text

                return translated_text
            else:
                print(f"Papago API error: {response.status_code} {response.text}")
                return None

        except Exception as e:
            print(f"Translation error: {e}")
            return None

    def translate_menu_description(
        self,
        description_en: str
    ) -> Dict[str, str]:
        """
        메뉴 설명을 영문 → 일본어/중국어로 번역

        Args:
            description_en: 영문 설명

        Returns:
            {
                "en": "...",
                "ja": "...",
                "zh": "..."
            }
        """
        result = {
            "en": description_en
        }

        # Translate to Japanese
        ja_text = self.translate(description_en, "en", "ja")
        if ja_text:
            result["ja"] = ja_text

        # Translate to Chinese (Simplified)
        zh_text = self.translate(description_en, "en", "zh-CN")
        if zh_text:
            result["zh"] = zh_text

        return result

    def batch_translate(
        self,
        texts: list,
        source_lang: str = "en",
        target_lang: str = "ja"
    ) -> Dict[str, str]:
        """
        여러 텍스트를 한번에 번역 (순차 처리)

        Args:
            texts: 번역할 텍스트 리스트
            source_lang: 원본 언어
            target_lang: 목표 언어

        Returns:
            {original: translated, ...}
        """
        result = {}

        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            if translated:
                result[text] = translated

        return result

    def get_supported_languages(self) -> Dict[str, str]:
        """
        지원 언어 목록 반환

        Returns:
            {code: name, ...}
        """
        return {
            "ko": "한국어",
            "en": "English",
            "ja": "日本語",
            "zh-CN": "中文(简体)",
            "zh-TW": "中文(繁體)"
        }


# Singleton instance
translation_service = TranslationService()
