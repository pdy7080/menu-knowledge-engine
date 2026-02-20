#!/usr/bin/env python3
"""
일일 자동 번역 스크립트

목적: 미번역 메뉴 58개를 자동으로 번역 (Gemini 60 RPD - 2 버퍼)
실행: python scripts/daily_translation.py --limit 58
스케줄: cron으로 매일 09:00 KST 자동 실행
"""

import asyncio
import sys
import argparse
from datetime import datetime
from typing import List, Dict
import logging

# Path setup
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.canonical_menu import CanonicalMenu
from services.auto_translate_service import auto_translate_service
from config import settings

# Logging 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_daily.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def get_untranslated_menus(db: AsyncSession, limit: int) -> List[CanonicalMenu]:
    """미번역 메뉴 조회 (name_ja IS NULL)"""
    query = select(CanonicalMenu).where(
        CanonicalMenu.name_ja == None
    ).limit(limit)

    result = await db.execute(query)
    menus = result.scalars().all()

    return menus


async def translate_menu(menu: CanonicalMenu, db: AsyncSession) -> Dict:
    """단일 메뉴 번역"""
    try:
        # English description 확인
        description_en = ""
        if menu.explanation_short and isinstance(menu.explanation_short, dict):
            description_en = menu.explanation_short.get("en", "")

        if not description_en:
            logger.warning(f"⚠️ {menu.name_ko}: No English description, skipping")
            return {"status": "skipped", "reason": "no_english_description"}

        # 번역 실행
        translations = await auto_translate_service._translate_with_gemini(
            menu.name_ko,
            description_en
        )

        if not translations or not translations.get("ja"):
            logger.error(f"❌ {menu.name_ko}: Translation failed")
            return {"status": "failed", "reason": "empty_result"}

        # DB 업데이트
        menu.name_ja = translations.get("ja", "")
        menu.name_zh_cn = translations.get("zh", "")

        # explanation_short도 업데이트
        if menu.explanation_short is None:
            menu.explanation_short = {}

        menu.explanation_short["ja"] = translations.get("ja", "")
        menu.explanation_short["zh"] = translations.get("zh", "")

        await db.commit()

        logger.info(f"✅ {menu.name_ko} → JA: {translations['ja'][:30]}...")

        return {
            "status": "success",
            "menu_ko": menu.name_ko,
            "ja": translations.get("ja", ""),
            "zh": translations.get("zh", "")
        }

    except Exception as e:
        logger.error(f"❌ {menu.name_ko}: {e}")
        return {"status": "error", "reason": str(e)}


async def main():
    parser = argparse.ArgumentParser(description='Daily auto-translation')
    parser.add_argument('--limit', type=int, default=58, help='Number of menus to translate (default: 58)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without translation')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info(f"Daily Auto-Translation Started")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Limit: {args.limit}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info("=" * 80)

    # Database connection (async)
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 미번역 메뉴 조회
        menus = await get_untranslated_menus(db, args.limit)

        if not menus:
            logger.info("✅ All menus already translated!")
            return

        logger.info(f"📋 Found {len(menus)} untranslated menus")

        if args.dry_run:
            logger.info("\n[Dry Run Mode - Preview Only]")
            for i, menu in enumerate(menus[:10], 1):
                logger.info(f"  {i}. {menu.name_ko}")
            if len(menus) > 10:
                logger.info(f"  ... and {len(menus) - 10} more")
            return

        # 번역 실행
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0
        }

        for i, menu in enumerate(menus, 1):
            logger.info(f"\n[{i}/{len(menus)}] {menu.name_ko}")

            result = await translate_menu(menu, db)
            results[result["status"]] += 1

            # API 키 사용량 출력
            logger.info(f"  Key Usage: {auto_translate_service.daily_usage}")

            # RPD 소진 체크
            all_keys_exhausted = all(
                usage >= auto_translate_service.max_rpd
                for usage in auto_translate_service.daily_usage.values()
            )

            if all_keys_exhausted:
                logger.warning("⚠️ All API keys exhausted (60 RPD). Stopping for today.")
                break

        # 최종 요약
        logger.info("\n" + "=" * 80)
        logger.info("Translation Summary")
        logger.info("=" * 80)
        logger.info(f"✅ Success: {results['success']}")
        logger.info(f"❌ Failed: {results['failed']}")
        logger.info(f"⚠️ Skipped: {results['skipped']}")
        logger.info(f"💥 Error: {results['error']}")
        logger.info(f"Total Processed: {sum(results.values())}")
        logger.info(f"Final Key Usage: {auto_translate_service.daily_usage}")
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
