"""
Logging configuration for automation system
기존 logging.getLogger(__name__) 패턴을 따름
"""

import logging
from pathlib import Path
from datetime import date

from .config_auto import auto_settings


def setup_logging(log_dir: str = "") -> logging.Logger:
    """
    자동화 시스템 로깅 설정

    Args:
        log_dir: 로그 디렉토리 (기본: auto_settings.AUTOMATION_LOG_DIR)

    Returns:
        Root logger
    """
    log_path = Path(log_dir or auto_settings.AUTOMATION_LOG_DIR)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / f"scheduler_{date.today().strftime('%Y%m%d')}.log"

    # Root logger 설정
    root_logger = logging.getLogger("automation")
    root_logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if root_logger.handlers:
        return root_logger

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger
