"""
Health Check HTTP Endpoint
스케줄러 상태 확인용 경량 서버

GET http://localhost:8099/health

Author: terminal-developer
Date: 2026-02-20
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path

from .config_auto import auto_settings

logger = logging.getLogger("automation.health")


def create_health_app():
    """FastAPI health check app 생성"""
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.warning("FastAPI not available for health endpoint")
        return None

    app = FastAPI(title="Menu Automation Health", docs_url=None, redoc_url=None)

    @app.get("/health")
    async def health_check():
        """스케줄러 상태 확인"""
        # 오늘 메트릭 로드
        metrics_file = (
            Path(auto_settings.AUTOMATION_METRICS_DIR)
            / f"metrics_{date.today().strftime('%Y%m%d')}.json"
        )
        today_metrics = {}
        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    today_metrics = json.load(f)
            except Exception:
                pass

        # 상태 정보
        status = {
            "status": "running",
            "automation_enabled": auto_settings.AUTOMATION_ENABLED,
            "ollama_model": auto_settings.OLLAMA_MODEL,
            "daily_target": auto_settings.DAILY_MENU_TARGET,
            "today": date.today().isoformat(),
            "today_collection": today_metrics.get("collection", {}),
            "today_enrichment": today_metrics.get("enrichment", {}),
            "today_images": today_metrics.get("images", {}),
            "today_sync": today_metrics.get("sync", {}),
            "totals": today_metrics.get("totals", {}),
            "checked_at": datetime.now().isoformat(),
        }

        return JSONResponse(content=status)

    @app.get("/")
    async def root():
        return {"service": "Menu Automation Scheduler", "health": "/health"}

    return app
