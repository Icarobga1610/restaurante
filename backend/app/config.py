"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
    )
    
    # Application
    app_name: str = "Restaurante Conta Mensal"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./restaurante.db"
    
    # Security
    secret_key: str = "***"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:8002"
    
    # Rate Limiting
    rate_limit_login_attempts: int = 5
    rate_limit_login_window_minutes: int = 15
    
    # Redis (for caching and Celery)
    redis_url: Optional[str] = None
    
    # Sentry
    sentry_dsn: Optional[str] = None
    
    # Biometric settings
    biometric_token_expire_minutes: int = 3
    webauthn_challenge_expire_minutes: int = 5


settings = Settings()