"""
Content Generator - Ollama Local LLM 기반 콘텐츠 생성기
enrich_content_gemini_v2.py의 패턴을 재사용하되 Ollama로 대체

Features:
- 메뉴 콘텐츠 생성 (9개 필드)
- 번역 생성 (EN/JA/ZH)
- 카테고리 분류
- 체크포인트 저장/복원 (10개마다)
- 일일 배치 처리

Author: terminal-developer
Date: 2026-02-20
Cost: $0 (Local LLM)
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .ollama_client import OllamaClient
from .prompt_templates import (
    SYSTEM_PROMPT,
    build_enrichment_prompt,
    build_translation_prompt,
    build_categorization_prompt,
    detect_category,
    validate_enrichment,
)
from .state_manager import StateManager
from .config_auto import auto_settings

logger = logging.getLogger("automation.content")


class ContentGenerator:
    """Ollama 기반 메뉴 콘텐츠 생성기"""

    def __init__(self, ollama: OllamaClient = None):
        self.ollama = ollama or OllamaClient()
        self.state = StateManager("enrichment")
        self.results: List[Dict[str, Any]] = []
        self.success_count = 0
        self.fail_count = 0
        self.start_time = 0.0

    async def check_ollama(self) -> bool:
        """Ollama 사용 가능 여부 확인"""
        if not await self.ollama.is_available():
            logger.error("Ollama server is not running. Start with: ollama serve")
            return False

        if not await self.ollama.has_model():
            logger.error(
                f"Model '{self.ollama.model}' not found. "
                f"Install with: ollama pull {self.ollama.model}"
            )
            return False

        logger.info(f"Ollama ready: {self.ollama.model}")
        return True

    async def enrich_menu(self, menu_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        단일 메뉴 콘텐츠 생성 (enrich_content_gemini_v2.py 패턴)

        Args:
            menu_data: {"name_ko": str, "name_en": str, ...}

        Returns:
            생성된 콘텐츠 dict 또는 None
        """
        name_ko = menu_data.get("name_ko", "")
        name_en = menu_data.get("name_en", "")
        menu_id = menu_data.get("id", name_ko)

        # 이미 처리된 항목 건너뛰기
        if self.state.is_processed(str(menu_id)):
            logger.info(f"  Skip (already processed): {name_ko}")
            return None

        logger.info(f"[{self.success_count + 1}] {name_ko} ({name_en}) processing...")

        # 프롬프트 생성
        prompt = build_enrichment_prompt(
            name_ko=name_ko,
            name_en=name_en,
            concept=menu_data.get("concept", ""),
            ingredients=", ".join(menu_data.get("primary_ingredients", [])),
            spice_level=menu_data.get("spice_level", 0),
            description_ko=menu_data.get("description_ko", ""),
            description_en=menu_data.get("description_en", ""),
        )

        # Ollama JSON 생성
        start = time.time()
        content_json = await self.ollama.generate_json(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.3,
        )
        gen_time = time.time() - start

        if not content_json:
            logger.warning(f"  Failed to generate content for {name_ko}")
            self.fail_count += 1
            self.state.mark_failed(str(menu_id), "Empty response")
            return None

        # 검증
        if not validate_enrichment(content_json):
            logger.warning(f"  Content validation failed for {name_ko}")
            self.fail_count += 1
            self.state.mark_failed(str(menu_id), "Validation failed")
            return None

        # 결과 조합
        result = {
            "id": str(menu_id),
            "name_ko": name_ko,
            "name_en": name_en,
            "category": detect_category(name_ko),
            "content": content_json,
            "enriched_at": datetime.now().isoformat(),
            "model": self.ollama.model,
            "generation_time_sec": round(gen_time, 1),
        }

        self.success_count += 1
        self.state.mark_processed(str(menu_id))
        logger.info(f"  Done ({self.success_count}) - {gen_time:.1f}s")

        return result

    async def translate_menu(
        self,
        name_ko: str,
        description_ko: str,
        languages: list = None,
    ) -> Optional[Dict[str, str]]:
        """
        메뉴 번역 생성

        Args:
            name_ko: 한국어 메뉴명
            description_ko: 한국어 설명
            languages: 대상 언어 (기본: ["en", "ja", "zh_cn"])

        Returns:
            번역 결과 dict
        """
        prompt = build_translation_prompt(name_ko, description_ko, languages)

        result = await self.ollama.generate_json(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.2,
        )

        return result

    async def categorize_menu(self, name_ko: str) -> Optional[Dict[str, Any]]:
        """
        메뉴 분류

        Args:
            name_ko: 한국어 메뉴명

        Returns:
            분류 결과 dict
        """
        prompt = build_categorization_prompt(name_ko)

        result = await self.ollama.generate_json(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.1,
        )

        return result

    async def enrich_batch(
        self,
        menus: List[Dict[str, Any]],
        checkpoint_interval: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        배치 콘텐츠 생성 (체크포인트 포함)

        Args:
            menus: 메뉴 데이터 리스트
            checkpoint_interval: 체크포인트 저장 간격

        Returns:
            생성된 결과 리스트
        """
        self.start_time = time.time()
        self.state.start_run()

        logger.info(f"Batch enrichment: {len(menus)} menus")
        logger.info(f"Model: {self.ollama.model} (Local LLM)")
        logger.info(f"Cost: $0")
        logger.info("=" * 60)

        for i, menu in enumerate(menus):
            result = await self.enrich_menu(menu)

            if result:
                self.results.append(result)

            # 진행도
            progress = (i + 1) / len(menus) * 100
            elapsed = time.time() - self.start_time
            if self.success_count > 0:
                avg_time = elapsed / self.success_count
                remaining = (len(menus) - i - 1) * avg_time
                logger.info(
                    f"Progress: {progress:.1f}% "
                    f"({self.success_count}/{len(menus)}) "
                    f"ETA: {remaining / 60:.1f}min"
                )

            # 체크포인트 저장
            if (i + 1) % checkpoint_interval == 0:
                self._save_checkpoint()

            # Rate limit (Ollama는 제한 없지만 GPU 과부하 방지)
            await asyncio.sleep(0.5)

        # 최종 저장
        self._save_checkpoint()
        self.state.end_run(self.success_count, self.fail_count)

        total_time = time.time() - self.start_time
        logger.info("=" * 60)
        logger.info(f"Completed: {self.success_count}/{len(menus)}")
        logger.info(f"Failed: {self.fail_count}")
        logger.info(f"Total time: {total_time / 60:.1f} min")
        logger.info(f"Cost: $0 (Local LLM)")

        return self.results

    def _save_checkpoint(self):
        """체크포인트 저장 (enrich_content_gemini_v2.py 패턴)"""
        checkpoint_data = {
            "enriched_count": self.success_count,
            "failed_count": self.fail_count,
            "model": self.ollama.model,
            "saved_at": datetime.now().isoformat(),
            "menus": self.results,
        }
        self.state.save_checkpoint(
            checkpoint_data,
            f"enrichment_batch_{self.success_count}",
        )
        self.state.save_state()


async def main():
    """단독 실행용 메인 함수"""
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    from .logging_config import setup_logging
    setup_logging()

    print("=" * 60)
    print("Content Generator (Ollama Local LLM)")
    print("=" * 60)

    generator = ContentGenerator()

    # Ollama 확인
    if not await generator.check_ollama():
        return

    # 테스트: 단일 메뉴 생성
    test_menu = {
        "name_ko": "김치찌개",
        "name_en": "Kimchi-jjigae",
        "concept": "stew",
        "primary_ingredients": ["김치", "돼지고기", "두부"],
        "spice_level": 3,
    }

    print("\nTest: Single menu enrichment")
    result = await generator.enrich_menu(test_menu)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
        print("\nTest passed!")
    else:
        print("Test failed!")


if __name__ == "__main__":
    asyncio.run(main())
