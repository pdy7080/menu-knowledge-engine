"""
Automation-specific settings
기존 config.py (Pydantic Settings) 패턴을 따름
"""
import sys
from pathlib import Path
from pydantic_settings import BaseSettings

# Backend root for imports
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))


class AutomationSettings(BaseSettings):
    """자동화 시스템 전용 설정 (.env에서 로드)"""

    # Database (기존 설정 재사용)
    DATABASE_URL: str = "sqlite:///data/automation/local.db"

    # Ollama (Local LLM — fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TIMEOUT: int = 120

    # Google Gemini (Primary LLM — 무료 tier)
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"  # 무료: flash=20 RPD, flash-lite=20 RPD
    GEMINI_RPM_LIMIT: int = 15       # flash-lite 무료: 15 req/min
    GEMINI_RPD_LIMIT: int = 20       # 실측 RPD=20 (2026-02-20 확인, 모든 모델 동일)

    # Image APIs (무료 tier)
    UNSPLASH_ACCESS_KEY: str = ""
    PIXABAY_API_KEY: str = ""

    # Public Data APIs (기존 키 재사용)
    PUBLIC_DATA_API_KEY: str = ""
    DATA_GO_KR_API_KEY: str = ""

    # Production Sync
    PRODUCTION_DATABASE_URL: str = ""

    # Scheduler
    AUTOMATION_ENABLED: bool = True
    DAILY_MENU_TARGET: int = 18  # Gemini RPD=20 기준 (여유 2건 확보)
    AUTOMATION_HEALTH_PORT: int = 8099

    # Paths
    AUTOMATION_LOG_DIR: str = str(BACKEND_DIR / "data" / "automation" / "logs")
    AUTOMATION_STATE_DIR: str = str(BACKEND_DIR / "data" / "automation" / "state")
    AUTOMATION_STAGING_DIR: str = str(BACKEND_DIR / "data" / "automation" / "staging")
    AUTOMATION_METRICS_DIR: str = str(BACKEND_DIR / "data" / "automation" / "metrics")

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = True
        extra = "ignore"


# Singleton instance
auto_settings = AutomationSettings()
