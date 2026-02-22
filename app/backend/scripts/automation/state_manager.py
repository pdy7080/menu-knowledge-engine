"""
State Manager - 체크포인트/재개 상태 관리
기존 enrichment 스크립트의 checkpoint 패턴을 따름
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Set

from .config_auto import auto_settings

logger = logging.getLogger("automation.state")


class StateManager:
    """
    자동화 파이프라인 상태 관리
    - 처리 완료된 항목 추적
    - 체크포인트 저장/복원
    - 일일 메트릭 기록
    """

    def __init__(self, task_name: str):
        """
        Args:
            task_name: 작업 이름 (collection, enrichment, images, sync)
        """
        self.task_name = task_name
        self.state_dir = Path(auto_settings.AUTOMATION_STATE_DIR)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / f"{task_name}_state.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        """기존 상태 로드"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"State file corrupt, starting fresh: {e}")
        return {
            "task_name": self.task_name,
            "processed_ids": [],
            "last_run": None,
            "total_processed": 0,
            "total_failed": 0,
            "history": [],
        }

    def save_state(self):
        """상태 저장 (체크포인트)"""
        self._state["last_saved"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
        logger.debug(f"State saved: {self.task_name}")

    @property
    def processed_ids(self) -> Set[str]:
        """이미 처리된 항목 ID 세트"""
        return set(self._state.get("processed_ids", []))

    def mark_processed(self, item_id: str):
        """항목을 처리 완료로 표시"""
        if item_id not in self._state["processed_ids"]:
            self._state["processed_ids"].append(item_id)
            self._state["total_processed"] = len(self._state["processed_ids"])

    def mark_failed(self, item_id: str, error: str = ""):
        """항목 처리 실패 기록"""
        self._state["total_failed"] = self._state.get("total_failed", 0) + 1
        if "failed_items" not in self._state:
            self._state["failed_items"] = []
        self._state["failed_items"].append(
            {
                "id": item_id,
                "error": error,
                "at": datetime.now().isoformat(),
            }
        )

    def is_processed(self, item_id: str) -> bool:
        """이미 처리된 항목인지 확인"""
        return item_id in self.processed_ids

    def start_run(self):
        """새 실행 시작 기록"""
        self._state["last_run"] = datetime.now().isoformat()
        self._state["current_run_start"] = datetime.now().isoformat()

    def end_run(self, success_count: int = 0, fail_count: int = 0):
        """실행 종료 기록"""
        run_info = {
            "started": self._state.get("current_run_start"),
            "ended": datetime.now().isoformat(),
            "success": success_count,
            "failed": fail_count,
        }
        if "history" not in self._state:
            self._state["history"] = []
        self._state["history"].append(run_info)
        # 최근 30일만 유지
        self._state["history"] = self._state["history"][-30:]
        self.save_state()

    def get_last_run(self) -> Optional[str]:
        """마지막 실행 시간"""
        return self._state.get("last_run")

    def save_checkpoint(self, data: Any, checkpoint_name: str = ""):
        """
        중간 결과 체크포인트 저장 (기존 enrich 패턴)

        Args:
            data: 저장할 데이터
            checkpoint_name: 체크포인트 이름 (기본: task_name_checkpoint)
        """
        name = checkpoint_name or f"{self.task_name}_checkpoint"
        staging_dir = Path(auto_settings.AUTOMATION_STAGING_DIR)
        staging_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = staging_dir / f"{name}.json"

        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint saved: {checkpoint_file}")

    def load_checkpoint(self, checkpoint_name: str = "") -> Optional[Any]:
        """체크포인트 데이터 로드"""
        name = checkpoint_name or f"{self.task_name}_checkpoint"
        checkpoint_file = Path(auto_settings.AUTOMATION_STAGING_DIR) / f"{name}.json"

        if checkpoint_file.exists():
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
