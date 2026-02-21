"""
Automation Pipeline Runner - Windows Task Scheduler 연동용

Windows Task Scheduler에서 개별 작업 또는 전체 파이프라인을 실행하는 진입점.
APScheduler 불필요 — OS 레벨 스케줄링 사용.

실행 방법:
  python run_pipeline.py --job all        # 전체 파이프라인 (부팅 시)
  python run_pipeline.py --job collect    # 메뉴 수집만
  python run_pipeline.py --job enrich     # 콘텐츠 생성만
  python run_pipeline.py --job image      # 이미지 수집만
  python run_pipeline.py --job sync       # DB 동기화만
  python run_pipeline.py --job status     # 상태 확인만

Author: terminal-developer
Date: 2026-02-21
"""
import argparse
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Path setup
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))

from automation.config_auto import auto_settings
from automation.logging_config import setup_logging


def print_status():
    """현재 자동화 시스템 상태 출력"""
    import logging
    logger = logging.getLogger("automation.status")

    logger.info("=" * 60)
    logger.info("Menu Knowledge Engine - Automation Status")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Automation Enabled: {auto_settings.AUTOMATION_ENABLED}")
    logger.info(f"Daily Target: {auto_settings.DAILY_MENU_TARGET} menus")
    logger.info(f"Gemini Model: {auto_settings.GEMINI_MODEL}")
    # 멀티키 상태 표시
    keys = [
        auto_settings.GOOGLE_API_KEY_1,
        auto_settings.GOOGLE_API_KEY_2,
        auto_settings.GOOGLE_API_KEY_3,
        auto_settings.GOOGLE_API_KEY,
    ]
    active_keys = len([k for k in keys if k.strip()])
    logger.info(f"Gemini API Keys: {active_keys} active")
    logger.info(f"RPD Limit: {auto_settings.GEMINI_RPD_LIMIT}/key × {active_keys} keys = {auto_settings.GEMINI_RPD_LIMIT * active_keys} total")
    logger.info("=" * 60)

    # 스테이징 디렉토리 상태
    staging_dir = Path(auto_settings.AUTOMATION_STAGING_DIR)
    if staging_dir.exists():
        new_menus = list((staging_dir / "new_menus").glob("discovery_*.json")) if (staging_dir / "new_menus").exists() else []
        enriched = list(staging_dir.glob("enrichment_batch_*.json"))
        logger.info(f"Staging: {len(new_menus)} discovery files, {len(enriched)} enrichment files")
    else:
        logger.info("Staging directory not created yet")

    # 로그 디렉토리
    log_dir = Path(auto_settings.AUTOMATION_LOG_DIR)
    if log_dir.exists():
        logs = list(log_dir.glob("*.log"))
        logger.info(f"Logs: {len(logs)} files in {log_dir}")

    has_keys = any(k.strip() for k in keys)
    return auto_settings.AUTOMATION_ENABLED and has_keys


async def run_job(job_name: str):
    """개별 작업 실행"""
    import logging
    logger = logging.getLogger("automation.runner")

    from automation.scheduler import (
        run_menu_collection,
        run_content_enrichment,
        run_image_collection,
        run_production_sync,
        run_all_jobs,
    )

    jobs = {
        "collect": ("Menu Collection", run_menu_collection),
        "enrich": ("Content Enrichment", run_content_enrichment),
        "image": ("Image Collection", run_image_collection),
        "sync": ("DB Sync", run_production_sync),
        "all": ("Full Pipeline", run_all_jobs),
    }

    if job_name not in jobs:
        logger.error(f"Unknown job: {job_name}. Available: {list(jobs.keys())}")
        return False

    name, func = jobs[job_name]
    logger.info(f"Starting: {name}")
    start = datetime.now()

    try:
        await func()
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"Completed: {name} ({elapsed:.0f}s)")
        return True
    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        logger.error(f"Failed: {name} after {elapsed:.0f}s - {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Menu Automation Pipeline Runner")
    parser.add_argument(
        "--job",
        choices=["all", "collect", "enrich", "image", "sync", "status"],
        default="all",
        help="Job to run (default: all)",
    )
    args = parser.parse_args()

    setup_logging()

    if args.job == "status":
        ready = print_status()
        sys.exit(0 if ready else 1)

    # 사전 조건 확인
    if not auto_settings.AUTOMATION_ENABLED:
        print("Automation is disabled (AUTOMATION_ENABLED=false in .env)")
        sys.exit(1)

    if args.job in ("enrich", "all"):
        has_any_key = any(k.strip() for k in [
            auto_settings.GOOGLE_API_KEY_1,
            auto_settings.GOOGLE_API_KEY_2,
            auto_settings.GOOGLE_API_KEY_3,
            auto_settings.GOOGLE_API_KEY,
        ])
        if not has_any_key:
            print("ERROR: No Gemini API keys set in .env")
            print("Set GOOGLE_API_KEY_1, _2, _3 for round-robin (60 RPD/day)")
            print("Get free keys: https://aistudio.google.com/app/apikey")
            sys.exit(1)

    print_status()

    success = asyncio.run(run_job(args.job))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()