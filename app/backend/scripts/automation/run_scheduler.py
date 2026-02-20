"""
Automation Scheduler Entry Point
사무실 PC에서 24시간 구동하는 메인 프로세스

실행 방법:
1. 직접 실행: python -m app.backend.scripts.automation.run_scheduler
2. Windows Task Scheduler: 부팅 시 자동 시작
3. NSSM 서비스: nssm install MenuAutomation python run_scheduler.py

Author: terminal-developer
Date: 2026-02-20
"""
import asyncio
import sys
import signal
import logging
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
from automation.scheduler import (
    run_menu_collection,
    run_content_enrichment,
    run_image_collection,
    run_production_sync,
)

logger = logging.getLogger("automation.main")


async def start_scheduler():
    """APScheduler로 일일 스케줄 구동"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("APScheduler not installed. Run: pip install apscheduler")
        logger.info("Falling back to simple loop mode...")
        await simple_loop()
        return

    scheduler = AsyncIOScheduler(
        job_defaults={
            'coalesce': True,       # 누적된 미실행 작업 병합
            'max_instances': 1,     # 동시 실행 방지
            'misfire_grace_time': 3600,  # 1시간 유예
        }
    )

    # 일일 스케줄
    scheduler.add_job(
        run_menu_collection,
        CronTrigger(hour=2, minute=0),
        id='daily_menu_collection',
        name='Menu Collection (02:00)',
        replace_existing=True,
    )

    scheduler.add_job(
        run_content_enrichment,
        CronTrigger(hour=4, minute=0),
        id='daily_content_enrichment',
        name='Content Enrichment (04:00)',
        replace_existing=True,
    )

    scheduler.add_job(
        run_image_collection,
        CronTrigger(hour=6, minute=0),
        id='daily_image_collection',
        name='Image Collection (06:00)',
        replace_existing=True,
    )

    scheduler.add_job(
        run_production_sync,
        CronTrigger(hour=8, minute=0),
        id='daily_production_sync',
        name='Production Sync (08:00)',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started!")
    logger.info("Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: next run at {job.next_run_time}")

    # Health check endpoint (optional)
    try:
        await start_health_server()
    except Exception:
        logger.info("Health server not started (port may be in use)")

    # 무한 대기 (스케줄러가 백그라운드에서 실행)
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


async def simple_loop():
    """APScheduler 없이 단순 루프 (fallback)"""
    import time
    from datetime import datetime

    logger.info("Running in simple loop mode (no APScheduler)")

    while True:
        now = datetime.now()

        # 02:00 - Menu Collection
        if now.hour == 2 and now.minute == 0:
            await run_menu_collection()

        # 04:00 - Content Enrichment
        elif now.hour == 4 and now.minute == 0:
            await run_content_enrichment()

        # 06:00 - Image Collection
        elif now.hour == 6 and now.minute == 0:
            await run_image_collection()

        # 08:00 - Production Sync
        elif now.hour == 8 and now.minute == 0:
            await run_production_sync()

        # 1분 대기
        await asyncio.sleep(60)


async def start_health_server():
    """Health check HTTP 서버 (포트 8099)"""
    from .health import create_health_app
    import uvicorn

    app = create_health_app()
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=auto_settings.AUTOMATION_HEALTH_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    logger.info(f"Health server: http://localhost:{auto_settings.AUTOMATION_HEALTH_PORT}/health")


def main():
    """메인 진입점"""
    setup_logging()

    logger.info("=" * 60)
    logger.info("Menu Knowledge Engine - Automation Scheduler")
    logger.info(f"Model: {auto_settings.OLLAMA_MODEL}")
    logger.info(f"Daily target: {auto_settings.DAILY_MENU_TARGET} menus")
    logger.info(f"Cost: $0")
    logger.info("=" * 60)

    if not auto_settings.AUTOMATION_ENABLED:
        logger.info("Automation is disabled (AUTOMATION_ENABLED=false)")
        return

    # Graceful shutdown
    def shutdown_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 실행
    asyncio.run(start_scheduler())


if __name__ == "__main__":
    main()
