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
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # API Keys
    CLOVA_OCR_API_KEY: str = ""
    CLOVA_OCR_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    PAPAGO_CLIENT_ID: str = ""
    PAPAGO_CLIENT_SECRET: str = ""

    # Storage
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "menu-knowledge-bucket"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
