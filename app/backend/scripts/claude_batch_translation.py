#!/usr/bin/env python3
"""
Claude CLI 배치 번역 스크립트 (주말 일괄 작업)

목적: 260개 미번역 메뉴를 Claude Pro Max로 일괄 번역
실행: python scripts/claude_batch_translation.py
소요: 1-2시간 (260개)
"""

import asyncio
import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path

# Path setup
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.canonical_menu import CanonicalMenu
from config import settings

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude_batch_translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def translate_with_claude_cli(menu_name_ko: str, description_en: str) -> Optional[Dict[str, str]]:
    """Claude CLI로 번역 (headless mode)"""

    prompt = f"""한국 음식 '{menu_name_ko}'의 영문 설명을 일본어와 중국어(간체)로 번역하세요.

영문 설명: {description_en}

다음 규칙을 따르세요:
- 한식 문화, 재료, 맛의 특징을 자연스럽게 표현
- 각 언어권 고객이 이해할 수 있도록 설명
- 음식 이름은 정확히 번역 (예: 삼치=Spanish mackerel, NOT salmon)

JSON 형식으로만 반환 (다른 텍스트 없이):
{{"ja": "일본어 번역", "zh": "중국어(간체) 번역"}}"""

    try:
        # Claude CLI 실행
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--output-format", "json",
                "--allowedTools", "none"  # 도구 사용 금지 (빠른 응답)
            ],
            capture_output=True,
            text=True,
            timeout=60  # 60초 타임아웃
        )

        if result.returncode != 0:
            logger.error(f"Claude CLI error (exit {result.returncode}): {result.stderr}")
            return None

        # JSON 파싱
        output = result.stdout.strip()

        # 마크다운 코드블록 제거
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()

        data = json.loads(output)

        # 검증
        if not data.get("ja") or not data.get("zh"):
            logger.warning(f"Incomplete translation: {data}")
            return None

        return {
            "ja": data.get("ja", ""),
            "zh": data.get("zh", "")
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timeout for {menu_name_ko}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {menu_name_ko}: {e}\nOutput: {result.stdout}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {menu_name_ko}: {e}")
        return None


async def get_untranslated_menus(db: AsyncSession) -> list:
    """미번역 메뉴 전체 조회"""
    query = select(CanonicalMenu).where(
        CanonicalMenu.name_ja == None
    )

    result = await db.execute(query)
    return result.scalars().all()


async def translate_menu(menu: CanonicalMenu, db: AsyncSession) -> Dict:
    """단일 메뉴 번역 및 DB 업데이트"""

    # English description 확인
    description_en = ""
    if menu.explanation_short and isinstance(menu.explanation_short, dict):
        description_en = menu.explanation_short.get("en", "")

    if not description_en:
        logger.warning(f"⚠️ {menu.name_ko}: No English description")
        return {"status": "skipped", "reason": "no_description"}

    # Claude 번역
    translations = await translate_with_claude_cli(menu.name_ko, description_en)

    if not translations:
        logger.error(f"❌ {menu.name_ko}: Translation failed")
        return {"status": "failed"}

    # DB 업데이트
    try:
        menu.name_ja = translations["ja"]
        menu.name_zh_cn = translations["zh"]

        if menu.explanation_short is None:
            menu.explanation_short = {}

        menu.explanation_short["ja"] = translations["ja"]
        menu.explanation_short["zh"] = translations["zh"]

        await db.commit()

        logger.info(f"✅ {menu.name_ko}")
        logger.info(f"   JA: {translations['ja'][:50]}...")
        logger.info(f"   ZH: {translations['zh'][:50]}...")

        return {
            "status": "success",
            "menu_ko": menu.name_ko,
            "ja": translations["ja"],
            "zh": translations["zh"]
        }

    except Exception as e:
        logger.error(f"❌ DB update failed for {menu.name_ko}: {e}")
        await db.rollback()
        return {"status": "db_error", "error": str(e)}


async def main():
    logger.info("=" * 80)
    logger.info("Claude Batch Translation Started (Weekend Marathon)")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # Database
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 미번역 메뉴 조회
        menus = await get_untranslated_menus(db)

        if not menus:
            logger.info("✅ All menus already translated!")
            return

        total = len(menus)
        logger.info(f"📋 Found {total} untranslated menus")
        logger.info(f"⏱️ Estimated time: {total * 5 // 60} minutes")
        logger.info("")

        # 번역 실행
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "db_error": 0
        }

        start_time = datetime.now()

        for i, menu in enumerate(menus, 1):
            logger.info(f"\n[{i}/{total}] {menu.name_ko}")

            result = await translate_menu(menu, db)
            results[result["status"]] += 1

            # 진행률 표시
            if i % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / i
                remaining = (total - i) * avg_time
                logger.info(f"\n📊 Progress: {i}/{total} ({i/total*100:.1f}%)")
                logger.info(f"⏱️ Elapsed: {elapsed//60:.0f}m {elapsed%60:.0f}s")
                logger.info(f"⏱️ Remaining: {remaining//60:.0f}m {remaining%60:.0f}s")

        # 최종 요약
        elapsed_total = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("Translation Complete!")
        logger.info("=" * 80)
        logger.info(f"✅ Success: {results['success']}")
        logger.info(f"❌ Failed: {results['failed']}")
        logger.info(f"⚠️ Skipped: {results['skipped']}")
        logger.info(f"💥 DB Error: {results['db_error']}")
        logger.info(f"Total: {sum(results.values())}")
        logger.info(f"Time: {elapsed_total//60:.0f}m {elapsed_total%60:.0f}s")
        logger.info(f"Avg: {elapsed_total/total:.1f}s per menu")
        logger.info(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
