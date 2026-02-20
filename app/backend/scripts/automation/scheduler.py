"""
Automation Scheduler - APScheduler 기반 일일 자동화
사무실 PC에서 24시간 구동하는 자동 DB 확충 스케줄러

Schedule:
- 02:00 — 새 메뉴 수집 (Module 2) + 품질 필터
- 04:00 — 콘텐츠 생성 with Gemini 2.5 Flash (Module 1)
- 06:00 — 이미지 수집 (Module 3) — enriched name_en 기반
- 08:00 — 프로덕션 DB 동기화 (Module 5)

Author: terminal-developer
Date: 2026-02-20
Cost: $0/day (Gemini 2.5 Flash-Lite 무료 tier, 18 menus/day, RPD=20)
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from .config_auto import auto_settings, BACKEND_DIR
from .logging_config import setup_logging
from .metrics import DailyMetrics
from .state_manager import StateManager

logger = logging.getLogger("automation.scheduler")


async def run_menu_collection():
    """02:00 — 새 메뉴 수집"""
    logger.info("=" * 60)
    logger.info("JOB: Menu Collection Started")
    logger.info("=" * 60)

    metrics = DailyMetrics()
    started_at = datetime.now().isoformat()

    try:
        from .menu_discovery import MenuDiscovery
        discovery = MenuDiscovery()
        await discovery.load_existing_names_from_file()
        result = await discovery.discover_daily()

        metrics.record_collection(
            discovered=result.get("total_discovered", 0),
            inserted=result.get("total_new", 0),
            sources=result.get("sources", {}),
            errors=0,
            started_at=started_at,
        )
        logger.info(f"Collection complete: {result.get('total_new', 0)} new menus")

    except Exception as e:
        logger.error(f"Collection job failed: {e}", exc_info=True)
        metrics.record_collection(
            discovered=0, inserted=0, sources={}, errors=1,
            started_at=started_at,
        )


async def run_content_enrichment():
    """04:00 — Gemini 2.5 Flash로 콘텐츠 생성 (무료)"""
    logger.info("=" * 60)
    logger.info("JOB: Content Enrichment Started (Gemini Free Tier)")
    logger.info("=" * 60)

    metrics = DailyMetrics()
    started_at = datetime.now().isoformat()

    try:
        from .content_generator import ContentGenerator
        from .gemini_client import GeminiClient

        client = GeminiClient()
        generator = ContentGenerator(client)

        # Gemini 확인
        if not await generator.check_llm():
            logger.warning("Gemini not available, skipping enrichment")
            return

        # 일일 사용량 확인
        usage = client.get_daily_usage()
        logger.info(f"Daily RPD: {usage['used']}/{usage['limit']} ({usage['remaining']} remaining)")

        # 스테이징에서 미enriched 메뉴 로드
        staging_dir = Path(auto_settings.AUTOMATION_STAGING_DIR) / "new_menus"
        menus_to_enrich = []

        if staging_dir.exists():
            for json_file in sorted(staging_dir.glob("discovery_*.json")):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for menu in data.get("menus", []):
                        menus_to_enrich.append(menu)
                except Exception:
                    continue

        if not menus_to_enrich:
            logger.info("No menus to enrich")
            return

        # 일일 최대 18개 (Gemini 무료 tier: RPD 20, is_available 1 + 여유 1)
        batch = menus_to_enrich[:18]
        results = await generator.enrich_batch(batch, checkpoint_interval=10)

        metrics.record_enrichment(
            enriched=len(results),
            failed=len(batch) - len(results),
            avg_time_sec=0,
            model=client.model,
            started_at=started_at,
        )
        logger.info(f"Enrichment complete: {len(results)} menus enriched")
        logger.info(f"Daily RPD remaining: {client.get_daily_usage()['remaining']}")

    except Exception as e:
        logger.error(f"Enrichment job failed: {e}", exc_info=True)


async def run_image_collection():
    """06:00 — 이미지 수집 (enriched name_en 기반)"""
    logger.info("=" * 60)
    logger.info("JOB: Image Collection Started (name_en based)")
    logger.info("=" * 60)

    metrics = DailyMetrics()
    started_at = datetime.now().isoformat()

    try:
        from .image_matcher import ImageMatcher

        matcher = ImageMatcher()

        # enriched JSON에서 name_en이 있는 메뉴 로드 (정확한 이미지 검색)
        staging_dir = Path(auto_settings.AUTOMATION_STAGING_DIR)
        menus_without_images = []

        for json_file in sorted(staging_dir.glob("enrichment_batch_*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for menu in data.get("menus", []):
                    name_en = menu.get("name_en", "")
                    if name_en:  # name_en이 있는 메뉴만
                        menus_without_images.append({
                            "name_ko": menu.get("name_ko", ""),
                            "name_en": name_en,
                        })
            except Exception:
                continue

        if not menus_without_images:
            logger.info("No enriched menus with name_en for image search")
            return

        # 일일 최대 30개
        batch = menus_without_images[:30]
        result = await matcher.batch_collect(batch)

        metrics.record_images(
            found=result.get("images_found", 0),
            downloaded=result.get("images_downloaded", 0),
            sources=result.get("sources", {}),
            started_at=started_at,
        )

    except Exception as e:
        logger.error(f"Image collection job failed: {e}", exc_info=True)


async def run_production_sync():
    """08:00 — 프로덕션 DB 동기화"""
    logger.info("=" * 60)
    logger.info("JOB: Production DB Sync Started")
    logger.info("=" * 60)

    metrics = DailyMetrics()
    started_at = datetime.now().isoformat()

    try:
        from .db_sync import ProductionSync

        sync = ProductionSync()
        result = await sync.sync_all()

        metrics.record_sync(
            menus_synced=result.get("menus_synced", 0),
            content_synced=result.get("content_synced", 0),
            images_synced=result.get("images_synced", 0),
            started_at=started_at,
        )

    except Exception as e:
        logger.error(f"Sync job failed: {e}", exc_info=True)


async def run_all_jobs():
    """전체 파이프라인 순차 실행 (수동 테스트용)"""
    setup_logging()
    logger.info("Running all automation jobs sequentially...")

    await run_menu_collection()
    await run_content_enrichment()
    await run_image_collection()
    await run_production_sync()

    logger.info("All jobs completed!")
