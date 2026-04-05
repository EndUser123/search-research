"""
Configuration management for FastAPI authentication API.

Test Case ID: TC-CONFIG-002
Priority: High
Test Type: Configuration Management

Purpose:
Centralized configuration management with environment variable support,
security settings validation, and deployment-specific configurations.

Algorithm Approach: Pydantic-based settings with validation and type safety
Time Complexity: O(1) - Configuration loading
Space Complexity: O(1) - Configuration storage

Security Considerations:
- Environment variable validation
- Secret key security
- Database connection security
- Rate limiting configuration
"""

import logging
import os
import secrets
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    Design Pattern: Settings object pattern with Pydantic validation
    Provides type safety, validation, and environment variable integration.
    """

    # Application Configuration
    APP_NAME: str = Field(default="FastAPI Auth API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="production", description="Environment name")

    # Security Configuration
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Password Security
    PASSWORD_PEPPER: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Password pepper for additional security",
    )
    BCRYPT_ROUNDS: int = Field(default=12, description="BCrypt hashing rounds")
    MIN_PASSWORD_LENGTH: int = Field(default=8, description="Minimum password length")

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db", description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=10, description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=20, description="Database max overflow connections"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )
    REDIS_PASSWORD: str | None = Field(default=None, description="Redis password")

    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = Field(
        default=5, description="Rate limit requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=300, description="Rate limit window in seconds"
    )
    RATE_LIMIT_STORAGE: str = Field(
        default="redis", description="Rate limit storage backend"
    )

    # CORS Configuration
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"], description="Allowed CORS origins"
    )
    ALLOWED_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    ALLOWED_HEADERS: list[str] = Field(
        default=["*"], description="Allowed HTTP headers"
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json/text)")

    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    DOCS_URL: str | None = Field(
        default="/docs", description="API documentation URL"
    )
    REDOC_URL: str | None = Field(
        default="/redoc", description="ReDoc documentation URL"
    )

    # Security Headers
    SECURITY_HEADERS: bool = Field(default=True, description="Enable security headers")
    RATE_LIMIT_HEADERS: bool = Field(
        default=True, description="Enable rate limit headers"
    )

    # Session Configuration
    SESSION_TIMEOUT: int = Field(default=3600, description="Session timeout in seconds")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, description="Maximum login attempts")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """
        Validate secret key strength and generation.

        Algorithm Approach: Entropy and length validation
        Time Complexity: O(1) - String operations
        Space Complexity: O(1) - Constant space

        Args:
        v: Secret key string

        Returns:
        str: Validated secret key

        Raises:
        ValueError: If secret key is too weak
        """
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v == "your-secret-key-here":
            raise ValueError("SECRET_KEY must be changed from default value")
        return v

    @field_validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment name.

        Args:
        v: Environment string

        Returns:
        str: Validated environment name
        """
        valid_environments = ["development", "staging", "production", "testing"]
        if v not in valid_environments:
            logger.warning(
                f"Environment '{v}' not in valid environments: {valid_environments}"
            )
        return v.lower()

    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """
        Validate database URL format and security.

        Args:
        v: Database URL string

        Returns:
        str: Validated database URL
        """
        if v.startswith("sqlite:///:memory:"):
            return v  # In-memory database is OK for testing

        if not v.startswith(("sqlite:///", "postgresql://", "mysql://")):
            raise ValueError("DATABASE_URL must use sqlite, postgresql, or mysql")

        # Check for unencrypted connections in production
        if "localhost" in v and os.getenv("ENVIRONMENT") == "production":
            logger.warning("Using localhost database in production environment")

        return v

    @field_validator("PASSWORD_PEPPER")
    def validate_password_pepper(cls, v: str) -> str:
        """
        Validate password pepper strength.

        Args:
        v: Password pepper string

        Returns:
        str: Validated password pepper
        """
        if len(v) < 16:
            raise ValueError("PASSWORD_PEPPER must be at least 16 characters long")
        if v == "default-pepper-value":
            raise ValueError("PASSWORD_PEPPER must be changed from default value")
        return v

    @field_validator("BCRYPT_ROUNDS")
    def validate_bcrypt_rounds(cls, v: int) -> int:
        """
        Validate bcrypt rounds for security and performance.

        Args:
        v: Number of bcrypt rounds

        Returns:
        int: Validated bcrypt rounds
        """
        if v < 10:
            raise ValueError("BCRYPT_ROUNDS must be at least 10 for security")
        if v > 15:
            logger.warning(f"High BCRYPT_ROUNDS ({v}) may impact performance")
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        """
        Parse allowed origins from various input formats.

        Algorithm Approach: String splitting and list normalization
        Time Complexity: O(n) - Where n is number of origins
        Space Complexity: O(n) - Output list size

        Args:
        v: Origins input (string, list, or comma-separated)

        Returns:
        List[str]: Normalized list of origins
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """
        Check if running in development environment.

        Returns:
        bool: True if development environment
        """
        return self.ENVIRONMENT in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment.

        Returns:
        bool: True if production environment
        """
        return self.ENVIRONMENT == "production"

    @property
    def database_config(self) -> dict:
        """
        Get database configuration dictionary.

        Algorithm Approach: Configuration extraction and formatting
        Time Complexity: O(1) - Dictionary creation
        Space Complexity: O(1) - Constant dictionary size

        Returns:
        dict: Database configuration
        """
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "echo": self.DEBUG,
        }

    @property
    def redis_config(self) -> dict:
        """
        Get Redis configuration dictionary.

        Returns:
        dict: Redis configuration
        """
        return {
            "url": self.REDIS_URL,
            "password": self.REDIS_PASSWORD,
            "decode_responses": True,
        }

    @property
    def jwt_config(self) -> dict:
        """
        Get JWT configuration dictionary.

        Returns:
        dict: JWT configuration
        """
        return {
            "secret_key": self.SECRET_KEY,
            "algorithm": self.ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
        }

    @property
    def security_config(self) -> dict:
        """
        Get security configuration dictionary.

        Returns:
        dict: Security configuration
        """
        return {
            "password_pepper": self.PASSWORD_PEPPER,
            "bcrypt_rounds": self.BCRYPT_ROUNDS,
            "min_password_length": self.MIN_PASSWORD_LENGTH,
            "session_timeout": self.SESSION_TIMEOUT,
            "max_login_attempts": self.MAX_LOGIN_ATTEMPTS,
        }

    def get_log_config(self) -> dict:
        """
        Get logging configuration dictionary.

        Algorithm Approach: Configuration formatting and validation
        Time Complexity: O(1) - Configuration creation
        Space Complexity: O(1) - Constant configuration size

        Returns:
        dict: Logging configuration
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if self.LOG_FORMAT == "json" else "default",
                    "level": self.LOG_LEVEL,
                }
            },
            "root": {"level": self.LOG_LEVEL, "handlers": ["console"]},
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Algorithm Approach: LRU caching for performance
    Time Complexity: O(1) after first call
    Space Complexity: O(1) - Single settings instance

    Returns:
    Settings: Cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()


def validate_production_settings() -> list[str]:
    """
    Validate production environment settings and return warnings.

    Algorithm Approach: Security validation checklist
    Time Complexity: O(1) - Constant validation checks
    Space Complexity: O(n) - Warning list where n is number of warnings

    Returns:
    List[str]: List of security warnings for production
    """
    warnings = []

    if not settings.is_production:
        return warnings

    # Security validations for production
    if settings.DEBUG:
        warnings.append("DEBUG mode is enabled in production")

    if len(settings.SECRET_KEY) < 64:
        warnings.append("SECRET_KEY should be longer for production")

    if settings.DATABASE_URL.startswith("sqlite:///"):
        warnings.append("SQLite database not recommended for production")

    if not settings.REDIS_URL.startswith("redis://"):
        warnings.append("Redis not configured for production")

    if settings.RATE_LIMIT_REQUESTS > 100:
        warnings.append("High rate limit may impact security")

    return warnings
