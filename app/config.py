"""
Configuration management for Integration Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/integrations")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Webhook
    webhook_timeout: int = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
    
    # Sync
    sync_batch_size: int = int(os.getenv("SYNC_BATCH_SIZE", "100"))
    sync_retry_attempts: int = int(os.getenv("SYNC_RETRY_ATTEMPTS", "3"))
    
    # Application
    app_name: str = "Integration Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    global_state_manager_url: str = os.getenv("GLOBAL_STATE_MANAGER_URL", "http://localhost:8035")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # tolerate env vars owned by other libs (e.g. unkey-auth's UNKEY_*)


settings = Settings()
