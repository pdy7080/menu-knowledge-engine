"""
Gemini API Client — 멀티키 라운드 로빈
Google Gemini 2.5 Flash-Lite 기반 비동기 LLM 클라이언트

멀티키 전략 (3키 × 20 RPD = 60 RPD/일):
- 키마다 독립 RPD 카운터 추적
- 요청 시 가장 여유 있는 키 자동 선택
- 429 에러 시 해당 키만 소진 처리 → 다음 키로 즉시 전환
- 모든 키 소진 시 즉시 중단 (무의미한 재시도 없음)

google.genai SDK 사용 (google.generativeai는 deprecated)
OllamaClient와 동일한 인터페이스 제공

Author: terminal-developer
Date: 2026-02-20
Updated: 2026-02-21 (멀티키 라운드 로빈, 429 조기 중단)
Cost: $0 (무료 tier)
"""
import asyncio
import json
import logging
import re
import time
from datetime import date
from typing import Optional, Dict, Any, List

from .config_auto import auto_settings

logger = logging.getLogger("automation.gemini")


class _KeyState:
    """단일 API 키의 상태 추적"""

    def __init__(self, key: str, index: int, rpd_limit: int):
        self.key = key
        self.index = index
        self.rpd_limit = rpd_limit
        self.daily_count: int = 0
        self.daily_date: str = ""
        self.exhausted: bool = False
        self.client = None  # lazy init

    def reset_if_new_day(self):
        today = date.today().isoformat()
        if self.daily_date != today:
            self.daily_date = today
            self.daily_count = 0
            self.exhausted = False

    @property
    def remaining(self) -> int:
        self.reset_if_new_day()
        if self.exhausted:
            return 0
        return max(0, self.rpd_limit - self.daily_count)

    def mark_used(self):
        self.reset_if_new_day()
        self.daily_count += 1

    def mark_exhausted(self):
        """429 에러 시 이 키를 소진 처리"""
        self.exhausted = True
        self.daily_count = self.rpd_limit
        logger.warning(f"Key #{self.index + 1} exhausted (RPD limit reached)")


class GeminiClient:
    """Google Gemini API 클라이언트 — 멀티키 라운드 로빈"""

    def __init__(
        self,
        api_keys: List[str] = None,
        model: str = "",
        rpm_limit: int = 0,
        rpd_limit: int = 0,
    ):
        self.model = model or auto_settings.GEMINI_MODEL
        self.rpm_limit = rpm_limit or auto_settings.GEMINI_RPM_LIMIT
        self.rpd_limit = rpd_limit or auto_settings.GEMINI_RPD_LIMIT

        # 키 수집: 명시적 전달 > .env 멀티키 > .env 단일키
        if api_keys:
            raw_keys = api_keys
        else:
            raw_keys = [
                auto_settings.GOOGLE_API_KEY_1,
                auto_settings.GOOGLE_API_KEY_2,
                auto_settings.GOOGLE_API_KEY_3,
                auto_settings.GOOGLE_API_KEY,  # 하위호환 (단일키)
            ]
        # 빈 값, 중복 제거
        seen = set()
        unique_keys = []
        for k in raw_keys:
            k = k.strip()
            if k and k not in seen:
                seen.add(k)
                unique_keys.append(k)

        self._key_states: List[_KeyState] = [
            _KeyState(key=k, index=i, rpd_limit=self.rpd_limit)
            for i, k in enumerate(unique_keys)
        ]

        # Rate limiting (키 무관, 전체 RPM 공유)
        self._last_request_time: float = 0.0
        self._sdk_imported: bool = False

    @property
    def total_keys(self) -> int:
        return len(self._key_states)

    @property
    def total_rpd(self) -> int:
        """전체 일일 RPD 합계"""
        return self.total_keys * self.rpd_limit

    def _pick_best_key(self) -> Optional[_KeyState]:
        """가장 여유 있는 키 선택"""
        best = None
        for ks in self._key_states:
            ks.reset_if_new_day()
            if ks.exhausted or ks.remaining <= 0:
                continue
            if best is None or ks.remaining > best.remaining:
                best = ks
        return best

    def _get_client_for_key(self, ks: _KeyState):
        """키별 genai.Client 초기화 (lazy)"""
        if ks.client is not None:
            return ks.client

        from google import genai
        ks.client = genai.Client(api_key=ks.key)
        logger.info(f"Gemini SDK initialized for key #{ks.index + 1}: {self.model}")
        return ks.client

    def _ensure_sdk(self):
        if self._sdk_imported:
            return
        try:
            from google import genai  # noqa: F401
            self._sdk_imported = True
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )

    def is_all_exhausted(self) -> bool:
        """모든 키가 소진되었는지 확인"""
        for ks in self._key_states:
            ks.reset_if_new_day()
            if not ks.exhausted and ks.remaining > 0:
                return False
        return True

    async def is_available(self) -> bool:
        """사용 가능 여부 확인 (API 호출 없이)"""
        if not self._key_states:
            logger.warning("No Gemini API keys configured")
            return False

        if self.is_all_exhausted():
            logger.warning("All Gemini keys exhausted for today")
            return False

        try:
            self._ensure_sdk()
            return True
        except Exception as e:
            logger.error(f"Gemini SDK init failed: {e}")
            return False

    async def has_model(self, model_name: str = "") -> bool:
        """하위호환 인터페이스"""
        return await self.is_available()

    async def _rate_limit(self):
        """RPM rate limit (키 무관, 전체 공유)"""
        min_interval = 60.0 / self.rpm_limit
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
        텍스트 생성 — 자동으로 최적 키 선택

        Returns:
            생성된 텍스트 또는 None (모든 키 소진 시)
        """
        ks = self._pick_best_key()
        if ks is None:
            logger.warning("All keys exhausted — cannot generate")
            return None

        self._ensure_sdk()
        await self._rate_limit()

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            client = self._get_client_for_key(ks)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )

            ks.mark_used()
            total_usage = self.get_daily_usage()
            logger.debug(
                f"Key #{ks.index + 1} used ({ks.daily_count}/{self.rpd_limit}) | "
                f"Total: {total_usage['used']}/{total_usage['limit']}"
            )

            if response.text:
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                ks.mark_exhausted()
                # 다른 키로 즉시 재시도
                next_ks = self._pick_best_key()
                if next_ks:
                    logger.info(
                        f"Key #{ks.index + 1} hit 429 → switching to key #{next_ks.index + 1} "
                        f"({next_ks.remaining} remaining)"
                    )
                    return await self._generate_with_key(
                        next_ks, full_prompt, temperature, max_tokens
                    )
                else:
                    logger.error("All keys exhausted after 429")
                    return None
            else:
                logger.error(f"Gemini generate error: {e}")
                return None

    async def _generate_with_key(
        self,
        ks: _KeyState,
        full_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """특정 키로 생성 (429 fallback용, 내부 전용)"""
        await self._rate_limit()

        try:
            client = self._get_client_for_key(ks)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )

            ks.mark_used()

            if response.text:
                return response.text
            return None

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                ks.mark_exhausted()
            else:
                logger.error(f"Gemini generate error (key #{ks.index + 1}): {e}")
            return None

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_retries: int = 2,
    ) -> Optional[dict]:
        """
        JSON 출력 생성 — 429 조기 중단 포함

        모든 키 소진 시 즉시 None 반환 (무의미한 재시도 없음)
        """
        if self.is_all_exhausted():
            logger.warning("All keys exhausted — skipping generate_json")
            return None

        json_system = (
            (system or "")
            + "\nIMPORTANT: Output ONLY valid JSON. "
            "No markdown, no code blocks, no extra text."
        )

        for attempt in range(max_retries):
            # 매 시도 전 키 잔여량 재확인
            if self.is_all_exhausted():
                logger.warning(
                    f"All keys exhausted at attempt {attempt + 1} — stopping retries"
                )
                return None

            response_text = await self.generate(
                prompt=prompt,
                system=json_system.strip(),
                temperature=temperature,
            )

            if not response_text:
                if self.is_all_exhausted():
                    logger.warning("All keys exhausted — stopping retries")
                    return None
                logger.warning(
                    f"Empty response (attempt {attempt + 1}/{max_retries})"
                )
                continue

            # JSON 추출
            cleaned = response_text.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

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
        """전체 키의 합산 사용량"""
        total_used = 0
        total_limit = 0
        key_details = []

        for ks in self._key_states:
            ks.reset_if_new_day()
            total_used += ks.daily_count
            total_limit += self.rpd_limit
            key_details.append({
                "key_index": ks.index + 1,
                "used": ks.daily_count,
                "remaining": ks.remaining,
                "exhausted": ks.exhausted,
            })

        return {
            "date": date.today().isoformat(),
            "used": total_used,
            "limit": total_limit,
            "remaining": total_limit - total_used,
            "keys": key_details,
            "total_keys": self.total_keys,
        }
