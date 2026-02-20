"""
Daily metrics tracking
일일 자동화 실행 결과를 JSON으로 기록
"""
import json
import logging
from pathlib import Path
from datetime import date, datetime
from typing import Dict, Any

from .config_auto import auto_settings

logger = logging.getLogger("automation.metrics")


class DailyMetrics:
    """일일 메트릭 추적"""

    def __init__(self):
        self.metrics_dir = Path(auto_settings.AUTOMATION_METRICS_DIR)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.today = date.today().strftime('%Y%m%d')
        self.metrics_file = self.metrics_dir / f"metrics_{self.today}.json"
        self._metrics = self._load_or_create()

    def _load_or_create(self) -> dict:
        """오늘 메트릭 로드 또는 생성"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "date": date.today().isoformat(),
            "collection": {},
            "enrichment": {},
            "images": {},
            "sync": {},
            "totals": {},
        }

    def save(self):
        """메트릭 저장"""
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self._metrics, f, ensure_ascii=False, indent=2)

    def record_collection(self, discovered: int, inserted: int,
                          sources: Dict[str, int], errors: int = 0,
                          started_at: str = "", completed_at: str = ""):
        """메뉴 수집 결과 기록"""
        self._metrics["collection"] = {
            "started_at": started_at,
            "completed_at": completed_at or datetime.now().isoformat(),
            "menus_discovered": discovered,
            "menus_inserted": inserted,
            "sources": sources,
            "errors": errors,
        }
        self.save()

    def record_enrichment(self, enriched: int, failed: int,
                          avg_time_sec: float = 0, model: str = "",
                          started_at: str = "", completed_at: str = ""):
        """콘텐츠 생성 결과 기록"""
        self._metrics["enrichment"] = {
            "started_at": started_at,
            "completed_at": completed_at or datetime.now().isoformat(),
            "menus_enriched": enriched,
            "menus_failed": failed,
            "avg_generation_time_sec": round(avg_time_sec, 1),
            "ollama_model": model,
        }
        self.save()

    def record_images(self, found: int, downloaded: int,
                      sources: Dict[str, int],
                      started_at: str = "", completed_at: str = ""):
        """이미지 수집 결과 기록"""
        self._metrics["images"] = {
            "started_at": started_at,
            "completed_at": completed_at or datetime.now().isoformat(),
            "images_found": found,
            "images_downloaded": downloaded,
            "sources": sources,
        }
        self.save()

    def record_sync(self, menus_synced: int, content_synced: int,
                    images_synced: int,
                    started_at: str = "", completed_at: str = ""):
        """DB 동기화 결과 기록"""
        self._metrics["sync"] = {
            "started_at": started_at,
            "completed_at": completed_at or datetime.now().isoformat(),
            "menus_synced": menus_synced,
            "content_synced": content_synced,
            "images_synced": images_synced,
        }
        self.save()

    def record_totals(self, total_menus: int, enriched_count: int,
                      images_count: int):
        """전체 DB 현황 기록"""
        self._metrics["totals"] = {
            "canonical_menus": total_menus,
            "enriched_count": enriched_count,
            "images_count": images_count,
            "enriched_pct": round(enriched_count / max(total_menus, 1) * 100, 1),
            "images_pct": round(images_count / max(total_menus, 1) * 100, 1),
        }
        self.save()

    def get_summary(self) -> Dict[str, Any]:
        """오늘 요약"""
        return self._metrics
