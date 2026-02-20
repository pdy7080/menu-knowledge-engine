"""
Ollama REST API Client
Local LLM 호출을 위한 비동기 HTTP 클라이언트

Ollama API: http://localhost:11434
- POST /api/generate — 텍스트 생성
- POST /api/chat — 대화형 생성
- GET /api/tags — 설치된 모델 목록
- POST /api/pull — 모델 다운로드

패턴: public_data_client.py의 httpx async 패턴을 따름

Author: terminal-developer
Date: 2026-02-20
"""
import json
import logging
import re
import httpx
from typing import Optional, Dict, Any

from .config_auto import auto_settings

logger = logging.getLogger("automation.ollama")


class OllamaClient:
    """Ollama Local LLM REST API 클라이언트"""

    def __init__(
        self,
        base_url: str = "",
        model: str = "",
        timeout: int = 0,
    ):
        self.base_url = (base_url or auto_settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or auto_settings.OLLAMA_MODEL
        self.timeout = timeout or auto_settings.OLLAMA_TIMEOUT

    async def is_available(self) -> bool:
        """Ollama 서버 실행 여부 확인"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.warning("Ollama server not available")
            return False

    async def list_models(self) -> list:
        """설치된 모델 목록 조회"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    async def has_model(self, model_name: str = "") -> bool:
        """특정 모델 설치 여부 확인"""
        target = model_name or self.model
        models = await self.list_models()
        # "qwen2.5:7b" 형태로 비교 (태그 포함/미포함 모두 처리)
        return any(
            target in m or m.startswith(target.split(":")[0])
            for m in models
        )

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Optional[str]:
        """
        텍스트 생성 (POST /api/generate)

        Args:
            prompt: 사용자 프롬프트
            system: 시스템 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수

        Returns:
            생성된 텍스트 또는 None
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text[:200]}")
                    return None

                data = response.json()
                return data.get("response", "")

        except httpx.TimeoutException:
            logger.error(f"Ollama timeout ({self.timeout}s)")
            return None
        except httpx.ConnectError:
            logger.error("Ollama server not running")
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> Optional[dict]:
        """
        JSON 출력 생성 (enrich_content_gemini.py의 JSON 추출 패턴)

        Args:
            prompt: JSON 생성 프롬프트
            system: 시스템 프롬프트
            temperature: 생성 온도
            max_retries: 최대 재시도 횟수

        Returns:
            파싱된 JSON dict 또는 None
        """
        # JSON 포맷 지시를 시스템 프롬프트에 추가
        json_system = (system or "") + "\nIMPORTANT: Output ONLY valid JSON. No markdown, no code blocks, no extra text."

        for attempt in range(max_retries):
            response_text = await self.generate(
                prompt=prompt,
                system=json_system.strip(),
                temperature=temperature,
            )

            if not response_text:
                logger.warning(f"Empty response (attempt {attempt + 1}/{max_retries})")
                continue

            # JSON 추출 (enrich_content_gemini_v2.py 라인 94-101 패턴)
            cleaned = response_text.strip()

            # 마크다운 코드 블록 제거
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # JSON 객체 추출 (첫 번째 { ~ 마지막 } 사이)
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

    async def generate_chat(
        self,
        messages: list,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        대화형 생성 (POST /api/chat)

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
            temperature: 생성 온도

        Returns:
            생성된 텍스트 또는 None
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                if response.status_code != 200:
                    logger.error(f"Chat API error: {response.status_code}")
                    return None

                data = response.json()
                return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return None
