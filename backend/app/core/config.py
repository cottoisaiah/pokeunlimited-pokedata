"""
🔧 Core Configuration Settings
Production-ready configuration management with environment-based settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    APP_NAME: str = "PokeUnlimited-PokeData"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Security Settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Settings (using existing tradingcards database)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://trading:trading@localhost:5432/tradingcards", 
        env="DATABASE_URL"
    )
    ASYNC_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://trading:trading@localhost:5432/tradingcards",
        env="ASYNC_DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Cache Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_PRICING: int = 30   # 30 seconds for live pricing
    CACHE_TTL_ANALYTICS: int = 600  # 10 minutes for analytics
    
    # TCGdex API Settings (replaces discontinued TCGPlayer API)
    TCGDEX_BASE_URL: str = Field(
        default="https://api.tcgdx.net/v2",
        env="TCGDEX_BASE_URL"
    )
    TCGDEX_GRAPHQL_URL: str = Field(
        default="https://api.tcgdx.net/graphql",
        env="TCGDEX_GRAPHQL_URL"
    )
    TCGDEX_LANGUAGE: str = Field(
        default="en",
        env="TCGDEX_LANGUAGE"
    )
    
    # Legacy TCGPlayer placeholders (for compatibility)
    TCGPLAYER_PUBLIC_KEY: str = Field(
        default="tcgdex-replacement",
        env="TCGPLAYER_PUBLIC_KEY"
    )
    TCGPLAYER_PRIVATE_KEY: str = Field(
        default="tcgdex-replacement", 
        env="TCGPLAYER_PRIVATE_KEY"
    )
    TCGPLAYER_BASE_URL: str = "https://api.tcgdex.net/v2"
    
    # eBay API Settings (using environment variables)
    EBAY_APP_ID: str = Field(
        default="", 
        env="EBAY_APP_ID"
    )
    EBAY_DEV_ID: str = Field(
        default="",
        env="EBAY_DEV_ID"
    )
    EBAY_CERT_ID: str = Field(
        default="",
        env="EBAY_CERT_ID"
    )
    EBAY_CLIENT_ID: str = Field(
        default="",
        env="EBAY_CLIENT_ID"
    )
    EBAY_CLIENT_SECRET: str = Field(
        default="",
        env="EBAY_CLIENT_SECRET"
    )
    EBAY_USER_TOKEN: Optional[str] = Field(default=None, env="EBAY_USER_TOKEN")
    EBAY_SANDBOX: bool = Field(default=False, env="EBAY_SANDBOX")
    EBAY_REDIRECT_URI: str = Field(
        default="https://poketrade.redexct.xyz/admin/oauth/callback",
        env="EBAY_REDIRECT_URI"
    )
    
    # Rate Limiting Settings
    RATE_LIMIT_FREE_TIER: int = 100      # requests per day
    RATE_LIMIT_GOLD_TIER: int = 1000     # requests per day
    RATE_LIMIT_PLATINUM_TIER: int = 10000 # requests per day
    RATE_LIMIT_WINDOW: int = 86400       # 24 hours in seconds
    
    # API Performance Settings
    API_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 50
    REQUEST_DELAY_MS: int = 100  # Delay between API requests
    
    # Background Tasks
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    PRICING_UPDATE_INTERVAL: int = 300   # 5 minutes
    ANALYTICS_UPDATE_INTERVAL: int = 1800 # 30 minutes
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="ALLOWED_ORIGINS"
    )
    
    # Monitoring & Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Email Settings (for alerts and notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    
    # WebSocket Settings
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting"""
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Environment-specific configurations
if settings.ENVIRONMENT == "production":
    # Production optimizations
    settings.DEBUG = False
    settings.DATABASE_POOL_SIZE = 50
    settings.CACHE_TTL_PRICING = 15  # More aggressive caching in production
    
elif settings.ENVIRONMENT == "staging":
    # Staging configurations
    settings.DEBUG = False
    settings.DATABASE_POOL_SIZE = 20
    
else:  # development
    # Development configurations
    settings.DEBUG = True
    settings.DATABASE_POOL_SIZE = 10
    settings.CACHE_TTL_PRICING = 60  # Longer cache in development