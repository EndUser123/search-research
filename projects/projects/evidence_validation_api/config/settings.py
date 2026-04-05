"""
Configuration settings for the Evidence Validation API.

This module provides comprehensive configuration management using Pydantic
Settings with environment variable support and validation.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # Connection settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/evidence_validation",
        description="PostgreSQL database connection URL",
    )

    # Connection pool settings
    pool_size: int = Field(
        default=20, ge=1, le=100, description="Database connection pool size"
    )

    max_overflow: int = Field(
        default=0, ge=0, le=20, description="Maximum overflow connections"
    )

    pool_timeout: int = Field(
        default=30, ge=1, le=300, description="Connection pool timeout in seconds"
    )

    pool_recycle: int = Field(
        default=300, ge=60, le=3600, description="Connection recycle time in seconds"
    )

    # Query settings
    query_timeout: int = Field(
        default=30, ge=1, le=300, description="Default query timeout in seconds"
    )

    echo_sql: bool = Field(default=False, description="Enable SQLAlchemy query logging")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    # Connection settings
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # Connection pool settings
    max_connections: int = Field(
        default=20, ge=1, le=100, description="Maximum Redis connections"
    )

    socket_timeout: int = Field(
        default=5, ge=1, le=30, description="Redis socket timeout in seconds"
    )

    socket_connect_timeout: int = Field(
        default=5, ge=1, le=30, description="Redis connection timeout in seconds"
    )

    # Retry settings
    retry_on_timeout: bool = Field(
        default=True, description="Retry operations on timeout"
    )

    max_retry_attempts: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts"
    )

    # Health check
    health_check_interval: int = Field(
        default=30, ge=1, le=300, description="Health check interval in seconds"
    )


class ValidationSettings(BaseSettings):
    """Validation service configuration settings."""

    # Performance settings
    default_timeout: int = Field(
        default=30, ge=1, le=300, description="Default validation timeout in seconds"
    )

    max_concurrent_validations: int = Field(
        default=100, ge=1, le=1000, description="Maximum concurrent validations"
    )

    max_queue_size: int = Field(
        default=1000, ge=10, le=10000, description="Maximum validation queue size"
    )

    # Caching settings
    default_cache_strategy: str = Field(
        default="medium_term", description="Default caching strategy"
    )

    cache_ttl_short: int = Field(
        default=300, ge=60, le=3600, description="Short-term cache TTL in seconds"
    )

    cache_ttl_medium: int = Field(
        default=3600, ge=300, le=86400, description="Medium-term cache TTL in seconds"
    )

    cache_ttl_long: int = Field(
        default=86400, ge=3600, le=604800, description="Long-term cache TTL in seconds"
    )

    cache_ttl_persistent: int = Field(
        default=604800,
        ge=86400,
        le=2592000,
        description="Persistent cache TTL in seconds",
    )

    # Content limits
    max_content_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        ge=1024,
        le=1024 * 1024 * 1024,  # 1GB
        description="Maximum evidence content size in bytes",
    )

    max_validation_rules: int = Field(
        default=50, ge=1, le=100, description="Maximum validation rules per request"
    )

    # Async validation settings
    async_validation_enabled: bool = Field(
        default=True, description="Enable async validation"
    )

    webhook_timeout: int = Field(
        default=10, ge=1, le=60, description="Webhook timeout in seconds"
    )

    @field_validator("default_cache_strategy")
    @classmethod
    def validate_cache_strategy(cls, v: str) -> str:
        """Validate cache strategy."""
        allowed_strategies = [
            "no_cache",
            "short_term",
            "medium_term",
            "long_term",
            "persistent",
        ]
        if v not in allowed_strategies:
            raise ValueError(f"Cache strategy must be one of: {allowed_strategies}")
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    # JWT settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing",
    )

    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")

    jwt_expire_minutes: int = Field(
        default=60, ge=5, le=1440, description="JWT token expiration time in minutes"
    )

    # API key settings
    api_key_header: str = Field(default="X-API-Key", description="API key header name")

    # CORS settings
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    cors_methods: list[str] = Field(default=["*"], description="CORS allowed methods")

    cors_headers: list[str] = Field(default=["*"], description="CORS allowed headers")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")

    rate_limit_requests: int = Field(
        default=100, ge=1, le=10000, description="Rate limit requests per window"
    )

    rate_limit_window: int = Field(
        default=60, ge=1, le=3600, description="Rate limit time window in seconds"
    )


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""

    # Metrics settings
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")

    metrics_port: int = Field(
        default=9090, ge=1024, le=65535, description="Metrics server port"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")

    log_format: str = Field(default="json", description="Log format (json or text)")

    # Health check settings
    health_check_interval: int = Field(
        default=30, ge=1, le=300, description="Health check interval in seconds"
    )

    health_check_timeout: int = Field(
        default=10, ge=1, le=60, description="Health check timeout in seconds"
    )

    # Sentry settings
    sentry_dsn: str | None = Field(
        default=None, description="Sentry DSN for error tracking"
    )

    sentry_environment: str = Field(
        default="development", description="Sentry environment"
    )

    sentry_traces_sample_rate: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Sentry traces sample rate"
    )


class APISettings(BaseSettings):
    """General API configuration settings."""

    # Basic settings
    api_title: str = Field(default="Evidence Validation API", description="API title")

    api_description: str = Field(
        default="Standardized Evidence Validation API", description="API description"
    )

    api_version: str = Field(default="1.0.0", description="API version")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")

    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")

    workers: int = Field(
        default=1, ge=1, le=10, description="Number of worker processes"
    )

    # Request settings
    max_request_size: int = Field(
        default=16 * 1024 * 1024,  # 16MB
        ge=1024,
        le=100 * 1024 * 1024,  # 100MB
        description="Maximum request size in bytes",
    )

    request_timeout: int = Field(
        default=60, ge=1, le=300, description="Request timeout in seconds"
    )

    # WebSocket settings
    websocket_enabled: bool = Field(
        default=True, description="Enable WebSocket support"
    )

    websocket_max_connections: int = Field(
        default=1000, ge=1, le=10000, description="Maximum WebSocket connections"
    )

    websocket_ping_interval: int = Field(
        default=20, ge=5, le=60, description="WebSocket ping interval in seconds"
    )

    # Documentation settings
    docs_enabled: bool = Field(default=True, description="Enable API documentation")

    docs_url: str = Field(default="/docs", description="API documentation URL")

    redoc_url: str = Field(default="/redoc", description="ReDoc documentation URL")

    # Environment
    environment: str = Field(
        default="development", description="Application environment"
    )

    debug: bool = Field(default=False, description="Enable debug mode")


class Settings(BaseSettings):
    """Main application settings combining all configuration groups."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    api: APISettings = Field(default_factory=APISettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.api.environment.lower() in ["development", "dev", "local"]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.api.environment.lower() in ["production", "prod"]

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.api.environment.lower() in ["testing", "test"]

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return self.database.database_url

    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return self.redis.redis_url


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Environment-specific overrides
def get_environment_overrides() -> dict[str, Any]:
    """Get environment-specific configuration overrides."""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    overrides = {}

    if environment == "production":
        overrides.update(
            {
                "database__echo_sql": False,
                "validation__async_validation_enabled": True,
                "security__cors_origins": [],  # Empty list, configure explicitly
                "monitoring__log_level": "WARNING",
                "api__debug": False,
                "api__docs_enabled": False,
            }
        )
    elif environment == "testing":
        overrides.update(
            {
                "database__database_url": "sqlite+aiosqlite:///./test.db",
                "redis__redis_url": "redis://localhost:6379/15",  # Separate database
                "validation__max_concurrent_validations": 10,
                "validation__default_timeout": 5,
                "monitoring__log_level": "DEBUG",
                "api__debug": True,
            }
        )

    return overrides


# Settings instance
settings = get_settings()

# Apply environment overrides
environment_overrides = get_environment_overrides()
for key, value in environment_overrides.items():
    if hasattr(settings, key):
        setattr(settings, key, value)
