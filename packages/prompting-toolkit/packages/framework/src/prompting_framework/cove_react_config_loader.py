from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .cove_react_integration import VerificationMode

"""CoVe-ReAct Configuration Loader.

This module provides configuration management for the CoVe-ReAct integration system,
including loading, validation, and dynamic configuration updates.

Key Features:
- JSON-based configuration loading and validation
- Environment-specific configuration overrides
- Runtime configuration updates
- Configuration validation and error handling
- Performance-optimized configuration access

Algorithm Approach:
1. Load base configuration from JSON file
2. Apply environment-specific overrides
3. Validate configuration structure and values
4. Provide optimized access methods
5. Support runtime updates and caching

Time Complexity: O(1) for configuration access after loading
Space Complexity: O(n) where n is the size of configuration data
Performance: Cached access with <1ms lookup time
"""





class EnvironmentType(Enum):
    """Environment types for configuration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class VerificationConfig:
    """Configuration for verification settings."""

    default_mode: VerificationMode
    max_verification_time: float
    parallel_verification: bool
    confidence_threshold: float
    enable_caching: bool
    cache_ttl: int


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""

    optimization_mode: str
    enable_parallel_processing: bool
    max_worker_threads: int
    memory_limit_mb: int
    enable_profiling: bool
    performance_tracking: bool


@dataclass
class DomainConfig:
    """Domain-specific configuration."""

    verification_required: bool
    confidence_threshold: float
    verification_mode: VerificationMode
    evidence_sources: list[str]
    max_verification_time: float


@dataclass
class CoVeReActConfig:
    """Complete CoVe-ReAct configuration."""

    enabled: bool
    verification: VerificationConfig
    performance: PerformanceConfig
    domain_settings: dict[str, DomainConfig]
    source_credibility: dict[str, Any]
    react_integration: dict[str, Any]
    coordination: dict[str, Any]
    monitoring: dict[str, Any]
    fallback: dict[str, Any]
    experimental: dict[str, Any]

    # Configuration metadata
    version: str
    environment: EnvironmentType
    loaded_at: float
    config_path: str | None = None


class CoVeReActConfigLoader:
    """
    Configuration loader for CoVe-ReAct integration system.

    This class provides comprehensive configuration management with validation,
    environment-specific overrides, and performance-optimized access.
    """

    def __init__(self, config_path: str | None = None, environment: EnvironmentType | None = None):
        """
        Initialize configuration loader.

        Args:
        ----
            config_path: Path to configuration file (optional, uses default)
            environment: Environment type for overrides (optional, auto-detected)

        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.environment = environment or self._detect_environment()

        # Configuration cache
        self._config_cache: CoVeReActConfig | None = None
        self._cache_timestamp: float = 0
        self._cache_ttl: int = 300  # 5 minutes

        # Configuration validation schema
        self._validation_schema = self._initialize_validation_schema()

    async def load_config(self, force_reload: bool = False) -> CoVeReActConfig:
        """
        Load configuration with caching and validation.

        Args:
        ----
            force_reload: Force reload even if cached config exists

        Returns:
        -------
            Validated configuration object

        """
        current_time = time.time()

        # Check cache first
        if not force_reload and self._config_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
            self.logger.debug("Using cached configuration")
            return self._config_cache

        try:
            # Load base configuration
            raw_config = await self._load_raw_config()

            # Apply environment-specific overrides
            overridden_config = await self._apply_environment_overrides(raw_config)

            # Validate configuration
            validated_config = await self._validate_configuration(overridden_config)

            # Create configuration object
            config = await self._create_config_object(validated_config)

            # Cache the configuration
            self._config_cache = config
            self._cache_timestamp = current_time

            self.logger.info(f"Configuration loaded successfully for environment: {self.environment.value}")
            return config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e!s}")
            # Return fallback configuration
            return await self._create_fallback_config()

    async def _load_raw_config(self) -> dict[str, Any]:
        """Load raw configuration from file."""
        config_file_path = Path(self.config_path)

        if not config_file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(config_file_path, encoding="utf-8") as f:
                config_data = json.load(f)

            # Extract cove_react_integration section
            if "cove_react_integration" in config_data:
                return config_data["cove_react_integration"]
            return config_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e!s}")

    async def _apply_environment_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply environment-specific configuration overrides."""
        overridden_config = config.copy()

        # Environment-specific override files
        env_override_file = Path(self.config_path).parent / f"overrides.{self.environment.value}.json"

        if env_override_file.exists():
            try:
                with open(env_override_file, encoding="utf-8") as f:
                    overrides = json.load(f)

                # Deep merge overrides
                overridden_config = self._deep_merge(overridden_config, overrides)
                self.logger.info(f"Applied environment overrides for: {self.environment.value}")

            except Exception as e:
                self.logger.warning(f"Failed to apply environment overrides: {e!s}")

        # Environment variable overrides
        env_overrides = self._get_environment_variable_overrides()
        if env_overrides:
            overridden_config = self._deep_merge(overridden_config, env_overrides)

        return overridden_config

    async def _validate_configuration(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration structure and values."""
        # Basic structure validation
        required_keys = [
            "verification_settings",
            "performance_settings",
            "domain_specific_settings",
        ]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")

        # Value validation
        validation_errors = []

        # Validate verification settings
        verification = config.get("verification_settings", {})
        if "max_verification_time" in verification:
            if not isinstance(verification["max_verification_time"], (int, float)):
                validation_errors.append("max_verification_time must be numeric")
            elif verification["max_verification_time"] <= 0 or verification["max_verification_time"] > 60:
                validation_errors.append("max_verification_time must be between 0 and 60 seconds")

        if "confidence_threshold" in verification:
            threshold = verification["confidence_threshold"]
            if not isinstance(threshold, (int, float)):
                validation_errors.append("confidence_threshold must be numeric")
            elif threshold < 0 or threshold > 1:
                validation_errors.append("confidence_threshold must be between 0 and 1")

        # Validate performance settings
        performance = config.get("performance_settings", {})
        if "max_worker_threads" in performance:
            threads = performance["max_worker_threads"]
            if not isinstance(threads, int) or threads < 1 or threads > 32:
                validation_errors.append("max_worker_threads must be integer between 1 and 32")

        if validation_errors:
            raise ValueError(f"Configuration validation failed: {', '.join(validation_errors)}")

        return config

    async def _create_config_object(self, config: dict[str, Any]) -> CoVeReActConfig:
        """Create configuration object from validated dictionary."""
        # Verification config
        verification_settings = config.get("verification_settings", {})
        verification_config = VerificationConfig(
            default_mode=VerificationMode(verification_settings.get("default_mode", "enhanced_react")),
            max_verification_time=verification_settings.get("max_verification_time", 3.0),
            parallel_verification=verification_settings.get("parallel_verification", True),
            confidence_threshold=verification_settings.get("confidence_threshold", 0.7),
            enable_caching=verification_settings.get("enable_caching", True),
            cache_ttl=verification_settings.get("cache_ttl", 3600),
        )

        # Performance config
        performance_settings = config.get("performance_settings", {})
        performance_config = PerformanceConfig(
            optimization_mode=performance_settings.get("optimization_mode", "balanced"),
            enable_parallel_processing=performance_settings.get("enable_parallel_processing", True),
            max_worker_threads=performance_settings.get("max_worker_threads", 4),
            memory_limit_mb=performance_settings.get("memory_limit_mb", 512),
            enable_profiling=performance_settings.get("enable_profiling", False),
            performance_tracking=performance_settings.get("performance_tracking", True),
        )

        # Domain configs
        domain_settings = {}
        domain_specific = config.get("domain_specific_settings", {})
        for domain, settings in domain_specific.items():
            domain_settings[domain] = DomainConfig(
                verification_required=settings.get("verification_required", False),
                confidence_threshold=settings.get("confidence_threshold", 0.7),
                verification_mode=VerificationMode(settings.get("verification_mode", "enhanced_react")),
                evidence_sources=settings.get("evidence_sources", []),
                max_verification_time=settings.get("max_verification_time", 3.0),
            )

        return CoVeReActConfig(
            enabled=config.get("enabled", True),
            verification=verification_config,
            performance=performance_config,
            domain_settings=domain_settings,
            source_credibility=config.get("source_credibility", {}),
            react_integration=config.get("react_integration", {}),
            coordination=config.get("coordination_settings", {}),
            monitoring=config.get("monitoring_and_logging", {}),
            fallback=config.get("fallback_behavior", {}),
            experimental=config.get("experimental_features", {}),
            version=config.get("version", "1.0.0"),
            environment=self.environment,
            loaded_at=time.time(),
            config_path=self.config_path,
        )

    async def _create_fallback_config(self) -> CoVeReActConfig:
        """Create fallback configuration when loading fails."""
        self.logger.warning("Creating fallback configuration")

        return CoVeReActConfig(
            enabled=True,
            verification=VerificationConfig(
                default_mode=VerificationMode.ENHANCED_REACT,
                max_verification_time=3.0,
                parallel_verification=True,
                confidence_threshold=0.7,
                enable_caching=False,
                cache_ttl=3600,
            ),
            performance=PerformanceConfig(
                optimization_mode="balanced",
                enable_parallel_processing=True,
                max_worker_threads=2,
                memory_limit_mb=256,
                enable_profiling=False,
                performance_tracking=True,
            ),
            domain_settings={
                "general": DomainConfig(
                    verification_required=False,
                    confidence_threshold=0.6,
                    verification_mode=VerificationMode.ENHANCED_REACT,
                    evidence_sources=["general_sources"],
                    max_verification_time=3.0,
                ),
            },
            source_credibility={},
            react_integration={},
            coordination={},
            monitoring={},
            fallback={},
            experimental={},
            version="1.0.0-fallback",
            environment=self.environment,
            loaded_at=time.time(),
        )

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        config_dir = current_dir / "config"
        return str(config_dir / "cove_react_config.json")

    def _detect_environment(self) -> EnvironmentType:
        """Auto-detect environment type."""
        # Check environment variable first
        env_var = os.getenv("COVE_REACT_ENV", "").lower()
        if env_var:
            try:
                return EnvironmentType(env_var)
            except ValueError:
                pass

        # Auto-detect based on common indicators
        if os.getenv("PYTHONPATH") and "production" in os.getenv("PYTHONPATH", ""):
            return EnvironmentType.PRODUCTION
        if os.getenv("TESTING") or "test" in os.getenv("PYTHONPATH", ""):
            return EnvironmentType.TESTING
        if os.getenv("STAGING") or "staging" in os.getenv("PYTHONPATH", ""):
            return EnvironmentType.STAGING
        return EnvironmentType.DEVELOPMENT

    def _get_environment_variable_overrides(self) -> dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}

        # Map environment variables to config paths
        env_mappings = {
            "COVE_REACT_ENABLED": ("enabled", lambda x: x.lower() == "true"),
            "COVE_REACT_MAX_VERIFICATION_TIME": ("verification_settings.max_verification_time", float),
            "COVE_REACT_PARALLEL_VERIFICATION": (
                "verification_settings.parallel_verification",
                lambda x: x.lower() == "true",
            ),
            "COVE_REACT_CONFIDENCE_THRESHOLD": ("verification_settings.confidence_threshold", float),
            "COVE_REACT_MAX_WORKER_THREADS": ("performance_settings.max_worker_threads", int),
            "COVE_REACT_MEMORY_LIMIT": ("performance_settings.memory_limit_mb", int),
        }

        for env_var, (config_path, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    self._set_nested_value(overrides, config_path, converted_value)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid environment variable {env_var}: {value}")

        return overrides

    def _set_nested_value(self, data: dict[str, Any], path: str, value: Any) -> None:
        """Set nested value in dictionary using dot notation path."""
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _initialize_validation_schema(self) -> dict[str, Any]:
        """Initialize configuration validation schema."""
        return {
            "required_keys": [
                "verification_settings",
                "performance_settings",
                "domain_specific_settings",
            ],
            "value_constraints": {
                "max_verification_time": {"type": "number", "min": 0.1, "max": 60.0},
                "confidence_threshold": {"type": "number", "min": 0.0, "max": 1.0},
                "max_worker_threads": {"type": "integer", "min": 1, "max": 32},
                "memory_limit_mb": {"type": "integer", "min": 64, "max": 8192},
            },
        }

    # Convenience methods for common configuration access

    async def is_enabled(self) -> bool:
        """Check if CoVe-ReAct integration is enabled."""
        config = await self.load_config()
        return config.enabled

    async def get_domain_config(self, domain: str) -> DomainConfig | None:
        """Get domain-specific configuration."""
        config = await self.load_config()
        return config.domain_settings.get(domain)

    async def get_verification_mode(self, domain: str | None = None) -> VerificationMode:
        """Get verification mode for domain or default."""
        config = await self.load_config()

        if domain and domain in config.domain_settings:
            return config.domain_settings[domain].verification_mode

        return config.verification.default_mode

    async def should_verify_domain(self, domain: str) -> bool:
        """Check if verification is required for domain."""
        domain_config = await self.get_domain_config(domain)
        return domain_config.verification_required if domain_config else False

    async def reload_config(self) -> CoVeReActConfig:
        """Force reload configuration."""
        return await self.load_config(force_reload=True)

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache = None
        self._cache_timestamp = 0


# Global configuration instance
_global_config_loader: CoVeReActConfigLoader | None = None


def get_config_loader(
    config_path: str | None = None,
    environment: EnvironmentType | None = None,
) -> CoVeReActConfigLoader:
    """Get global configuration loader instance."""
    global _global_config_loader

    if _global_config_loader is None:
        _global_config_loader = CoVeReActConfigLoader(config_path, environment)

    return _global_config_loader


async def get_config(
    config_path: str | None = None,
    environment: EnvironmentType | None = None,
) -> CoVeReActConfig:
    """Get loaded configuration."""
    loader = get_config_loader(config_path, environment)
    return await loader.load_config()


# Factory functions for easy integration
async def create_cove_react_integrator_from_config(
    config_path: str | None = None,
    environment: EnvironmentType | None = None,
) -> tuple:
    """Create CoVe-ReAct integrator and coordination system from configuration."""
    from .cove_react_integration import create_cove_react_integrator
    from .technique_coordination_system import TechniqueCoordinationSystem

    config = await get_config(config_path, environment)

    cove_integrator = create_cove_react_integrator(
        verification_mode=config.verification.default_mode,
        max_verification_time=config.verification.max_verification_time,
        parallel_verification=config.verification.parallel_verification,
    )

    coordination_system = TechniqueCoordinationSystem(
        enable_cove_react_integration=config.enabled,
        cove_react_config={
            "verification_mode": config.verification.default_mode.value,
            "max_verification_time": config.verification.max_verification_time,
            "parallel_verification": config.verification.parallel_verification,
        },
    )

    return cove_integrator, coordination_system, config
