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
    GOOGLE_API_KEY: str = ""
    PAPAGO_CLIENT_ID: str = ""
    PAPAGO_CLIENT_SECRET: str = ""
    PUBLIC_DATA_API_KEY: str = ""  # data.go.kr 공공데이터 포털 API 키

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
