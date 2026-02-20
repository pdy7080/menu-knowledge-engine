"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:5500,http://localhost:8080,http://127.0.0.1:5500,http://127.0.0.1:8080"

    # API Keys
    CLOVA_OCR_API_KEY: str = ""
    CLOVA_OCR_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""  # Deprecated: Use GOOGLE_API_KEY_1 instead
    GOOGLE_API_KEY_1: str = ""  # Primary Gemini API key (20 RPD)
    GOOGLE_API_KEY_2: str = ""  # Secondary Gemini API key (20 RPD)
    GOOGLE_API_KEY_3: str = ""  # Tertiary Gemini API key (20 RPD)
    PAPAGO_CLIENT_ID: str = ""
    PAPAGO_CLIENT_SECRET: str = ""
    PUBLIC_DATA_API_KEY: str = ""  # data.ex.co.kr 한국도로공사 API 키
    DATA_GO_KR_API_KEY: str = ""  # data.go.kr 공공데이터포털 API 키 (별도 발급)

    # Storage
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "menu-knowledge-bucket"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    CACHE_ENABLED: bool = True

    # CloudFlare R2 Storage
    STORAGE_PROVIDER: str = "local"  # "local" or "r2"
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TIMEOUT: int = 120

    # Automation
    AUTOMATION_ENABLED: bool = False
    DAILY_MENU_TARGET: int = 50
    UNSPLASH_ACCESS_KEY: str = ""
    PIXABAY_API_KEY: str = ""
    PRODUCTION_DATABASE_URL: str = ""

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def redis_url(self) -> str:
        """Build Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
