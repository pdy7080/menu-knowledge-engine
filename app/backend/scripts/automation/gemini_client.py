"""
Gemini API Client
Google Gemini 2.5 Flash-Lite 기반 비동기 LLM 클라이언트

무료 tier 제한 (2026-02-20 실측):
- gemini-2.5-flash-lite: RPM 15, RPD 20
- gemini-2.5-flash: RPM 10, RPD 20
- 모든 무료 모델 RPD=20 동일 (2025-12 Google 축소)
- TPM: 250,000

google.genai SDK 사용 (google.generativeai는 deprecated)
OllamaClient와 동일한 인터페이스를 제공하여 교체 용이

Author: terminal-developer
Date: 2026-02-20
Cost: $0 (무료 tier)
"""
import asyncio
import json
import logging
import re
import time
from datetime import date
from typing import Optional, Dict, Any

from .config_auto import auto_settings

logger = logging.getLogger("automation.gemini")


class GeminiClient:
    """Google Gemini API 클라이언트 (OllamaClient 호환 인터페이스)"""

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        rpm_limit: int = 0,
        rpd_limit: int = 0,
    ):
        self.api_key = api_key or auto_settings.GOOGLE_API_KEY
        self.model = model or auto_settings.GEMINI_MODEL
        self.rpm_limit = rpm_limit or auto_settings.GEMINI_RPM_LIMIT
        self.rpd_limit = rpd_limit or auto_settings.GEMINI_RPD_LIMIT

        # Rate limiting state
        self._last_request_time: float = 0.0
        self._daily_count: int = 0
        self._daily_date: str = ""

        # google.genai SDK (new)
        self._client = None

    def _init_sdk(self):
        """google.genai SDK 초기화 (lazy loading)"""
        if self._client is not None:
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini SDK initialized: {self.model}")
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )

    async def is_available(self) -> bool:
        """Gemini API 사용 가능 여부 확인 (RPD 절약: API 호출 없이 SDK 초기화만)"""
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not configured")
            return False

        if not self._check_daily_limit():
            return False

        try:
            self._init_sdk()
            # RPD 절약: API 호출 없이 SDK 초기화 성공만 확인
            # 실제 연결 검증은 첫 generate() 호출에서 수행됨
            return True
        except Exception as e:
            logger.error(f"Gemini SDK initialization failed: {e}")
            return False

    async def has_model(self, model_name: str = "") -> bool:
        """모델 사용 가능 여부 (Gemini는 항상 True if API key valid)"""
        return await self.is_available()

    def _check_daily_limit(self) -> bool:
        """일일 RPD 한도 확인"""
        today = date.today().isoformat()
        if self._daily_date != today:
            self._daily_date = today
            self._daily_count = 0

        if self._daily_count >= self.rpd_limit:
            logger.warning(
                f"Daily RPD limit reached: {self._daily_count}/{self.rpd_limit}"
            )
            return False
        return True

    async def _rate_limit(self):
        """RPM rate limit 적용 (flash-lite: 15 RPM = 4초 간격)"""
        min_interval = 60.0 / self.rpm_limit  # 15 RPM = 4초
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            wait = min_interval - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        self._last_request_time = time.time()

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """
        텍스트 생성 (OllamaClient.generate 호환)

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트
            temperature: 생성 온도
            max_tokens: 최대 토큰 수

        Returns:
            생성된 텍스트 또는 None
        """
        if not self._check_daily_limit():
            return None

        self._init_sdk()
        await self._rate_limit()

        # 시스템 프롬프트를 프롬프트 앞에 결합
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )

            self._daily_count += 1
            logger.debug(
                f"Gemini request #{self._daily_count}/{self.rpd_limit} today"
            )

            if response.text:
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # RPD 한도 초과 — 더 이상 호출하지 않도록 카운터 최대화
                logger.error(f"RPD limit reached (429): forcing daily limit stop")
                self._daily_count = self.rpd_limit
            else:
                logger.error(f"Gemini generate error: {e}")
            return None

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_retries: int = 2,
    ) -> Optional[dict]:
        """
        JSON 출력 생성 (OllamaClient.generate_json 호환)

        Args:
            prompt: JSON 생성 프롬프트
            system: 시스템 프롬프트
            temperature: 생성 온도
            max_retries: 최대 재시도 횟수

        Returns:
            파싱된 JSON dict 또는 None
        """
        json_system = (
            (system or "")
            + "\nIMPORTANT: Output ONLY valid JSON. "
            "No markdown, no code blocks, no extra text."
        )

        for attempt in range(max_retries):
            response_text = await self.generate(
                prompt=prompt,
                system=json_system.strip(),
                temperature=temperature,
            )

            if not response_text:
                logger.warning(
                    f"Empty response (attempt {attempt + 1}/{max_retries})"
                )
                continue

            # JSON 추출
            cleaned = response_text.strip()

            # 마크다운 코드 블록 제거
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # JSON 객체 추출 (첫 번째 { ~ 마지막 })
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)

            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"JSON parse error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                logger.debug(f"Raw response: {response_text[:300]}...")

        logger.error(f"Failed to get valid JSON after {max_retries} attempts")
        return None

    def get_daily_usage(self) -> Dict[str, Any]:
        """오늘의 API 사용량 반환"""
        today = date.today().isoformat()
        if self._daily_date != today:
            return {"date": today, "used": 0, "limit": self.rpd_limit, "remaining": self.rpd_limit}
        return {
            "date": self._daily_date,
            "used": self._daily_count,
            "limit": self.rpd_limit,
            "remaining": self.rpd_limit - self._daily_count,
        }
