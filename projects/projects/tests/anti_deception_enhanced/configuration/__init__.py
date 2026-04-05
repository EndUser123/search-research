"""
Configuration Testing Package

This package provides comprehensive testing infrastructure for configuration validation,
migration, and profile management. It validates the configuration system's ability
to handle various configuration scenarios, ensure data integrity, and support
smooth migrations between versions.

Package Structure:
- test_configuration_validation.py: Configuration file validation, schema validation, and security validation
- test_configuration_migration.py: Version migration, data transformation, backward compatibility, and import/export
- config_utils.py: Utility classes and helpers for configuration testing
"""

import asyncio
import base64
import hashlib
import json
import os
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from anti_deception_enhanced.utils.configuration import (
    ConfigManager,
    ConfigMigrator,
    ConfigProfile,
    ConfigSchema,
    ConfigurationError,
    ConfigValidator,
)


@dataclass
class ConfigurationTestScenario:
    """Test scenario configuration for configuration validation"""

    name: str
    config_data: dict[str, Any]
    expected_valid: bool
    expected_errors: list[str] = field(default_factory=list)
    config_format: str = "json"
    config_version: str = "1.0"


@dataclass
class MigrationTestScenario:
    """Test scenario configuration for configuration migration"""

    name: str
    source_config: dict[str, Any]
    target_version: str
    expected_migrated: dict[str, Any]
    migration_errors: list[str] = field(default_factory=list)


class ExtendedConfigMigrator(ConfigMigrator):
    """Extended config migrator for testing"""

    def __init__(self):
        super().__init__()
        self.migration_history = []
        self.performance_metrics = {}

    def track_migration(
        self,
        source_version: str,
        target_version: str,
        config: dict[str, Any],
        duration: float,
    ):
        """Track migration history and performance"""
        migration_record = {
            "source_version": source_version,
            "target_version": target_version,
            "config_hash": self._calculate_config_hash(config),
            "duration": duration,
            "timestamp": datetime.now(),
            "success": True,
        }
        self.migration_history.append(migration_record)

        # Update performance metrics
        if target_version not in self.performance_metrics:
            self.performance_metrics[target_version] = []

        self.performance_metrics[target_version].append(duration)

    def get_migration_statistics(self) -> dict[str, Any]:
        """Get migration statistics"""
        if not self.migration_history:
            return {"total_migrations": 0}

        total_migrations = len(self.migration_history)
        avg_duration = (
            sum(m["duration"] for m in self.migration_history) / total_migrations
        )

        # Calculate success rate
        successful_migrations = sum(1 for m in self.migration_history if m["success"])
        success_rate = successful_migrations / total_migrations

        return {
            "total_migrations": total_migrations,
            "average_duration": avg_duration,
            "success_rate": success_rate,
            "version_migrations": {},
        }

    def _calculate_config_hash(self, config: dict[str, Any]) -> str:
        """Calculate hash of configuration"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

    def simulate_migration_failure(
        self, source_config: dict[str, Any], target_version: str
    ) -> dict[str, Any]:
        """Simulate migration failure for testing"""
        try:
            # Simulate failure scenario
            if target_version == "5.0":
                raise ConfigurationError("Target version not supported")

            return self.migrate_config(source_config, target_version)
        except ConfigurationError as e:
            return {
                "error": str(e),
                "source_version": source_config.get("version", "unknown"),
                "target_version": target_version,
                "success": False,
            }


class ConfigurationTestingUtilities:
    """Utilities for configuration system testing"""

    @staticmethod
    def create_test_validator() -> ConfigValidator:
        """Create test configuration validator"""
        return ConfigValidator()

    @staticmethod
    def create_test_migrator() -> ExtendedConfigMigrator:
        """Create test configuration migrator"""
        return ExtendedConfigMigrator()

    @staticmethod
    def create_test_manager(temp_dir: str) -> ConfigManager:
        """Create test configuration manager"""
        return ConfigManager(temp_dir)

    @staticmethod
    def generate_test_config(version: str = "1.0") -> dict[str, Any]:
        """Generate test configuration"""
        return {
            "version": version,
            "security": {
                "enable_validation": True,
                "validation_threshold": 0.8,
                "cost_budget": 0.10,
            },
            "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
            "logging": {"level": "INFO", "file_path": "/var/log/anti_deception.log"},
        }

    @staticmethod
    def generate_invalid_config() -> dict[str, Any]:
        """Generate invalid configuration for testing"""
        return {
            "version": "invalid",
            "security": {
                "enable_validation": "yes",  # Should be boolean
                "validation_threshold": 1.5,  # Should be <= 1.0
                "cost_budget": -0.1,  # Should be >= 0.0
            },
            "missing_required_field": None,
        }

    @staticmethod
    def create_test_profile(name: str, config: dict[str, Any]) -> ConfigProfile:
        """Create test configuration profile"""
        return ConfigProfile(
            name=name,
            description=f"Test profile: {name}",
            config=config,
            is_active=True,
        )

    @staticmethod
    def validate_configuration_integrity(config: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration integrity"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "score": 100,
        }

        # Check required fields
        required_fields = ["version", "security"]
        for field in required_fields:
            if field not in config:
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False
                validation_result["score"] -= 20

        # Check version format
        if "version" in config and not isinstance(config["version"], str):
            validation_result["issues"].append("Version must be a string")
            validation_result["is_valid"] = False
            validation_result["score"] -= 10

        # Check security configuration
        if "security" in config and isinstance(config["security"], dict):
            security = config["security"]
            if "enable_validation" in security and not isinstance(
                security["enable_validation"], bool
            ):
                validation_result["issues"].append(
                    "enable_validation must be a boolean"
                )
                validation_result["is_valid"] = False
                validation_result["score"] -= 10

            if (
                "validation_threshold" in security
                and security["validation_threshold"] > 1.0
            ):
                validation_result["warnings"].append(
                    "validation_threshold > 1.0 may cause issues"
                )
                validation_result["score"] -= 5

        return validation_result

    @staticmethod
    def benchmark_configuration_performance(
        config: dict[str, Any], operations: int = 1000
    ) -> dict[str, float]:
        """Benchmark configuration performance"""
        import time

        results = {}

        # Validation benchmark
        validator = ConfigurationTestingUtilities.create_test_validator()
        start_time = time.time()
        for _ in range(operations):
            validator.validate_configuration(config)
        validation_time = (time.time() - start_time) / operations

        # Migration benchmark
        migrator = ConfigurationTestingUtilities.create_test_migrator()
        start_time = time.time()
        for _ in range(operations):
            migrator.migrate_config(config, "4.0")
        migration_time = (time.time() - start_time) / operations

        # Storage benchmark
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigurationTestingUtilities.create_test_manager(temp_dir)
            start_time = time.time()
            for _ in range(operations):
                manager.store_configuration(config)
            storage_time = (time.time() - start_time) / operations

        results = {
            "validation_time": validation_time,
            "migration_time": migration_time,
            "storage_time": storage_time,
            "total_time": validation_time + migration_time + storage_time,
        }

        return results

    @staticmethod
    def test_configuration_scenarios(temp_dir: str) -> dict[str, Any]:
        """Test various configuration scenarios"""
        results = {
            "validation_tests": [],
            "migration_tests": [],
            "profile_tests": [],
            "performance_tests": [],
            "error_handling_tests": [],
        }

        # Test configuration validation
        validator = ConfigurationTestingUtilities.create_test_validator()
        test_configs = [
            (
                "valid_config",
                ConfigurationTestingUtilities.generate_test_config(),
                True,
            ),
            (
                "invalid_config",
                ConfigurationTestingUtilities.generate_invalid_config(),
                False,
            ),
        ]

        for config_name, config, expected_valid in test_configs:
            validation_result = validator.validate_configuration(config)
            results["validation_tests"].append(
                {
                    "name": config_name,
                    "expected_valid": expected_valid,
                    "actual_valid": validation_result["is_valid"],
                    "passed": expected_valid == validation_result["is_valid"],
                }
            )

        # Test configuration migration
        migrator = ConfigurationTestingUtilities.create_test_migrator()
        migration_test_cases = [
            (
                "v1_to_v2",
                ConfigurationTestingUtilities.generate_test_config("1.0"),
                "2.0",
            ),
            (
                "v2_to_v3",
                ConfigurationTestingUtilities.generate_test_config("2.0"),
                "3.0",
            ),
            (
                "v3_to_v4",
                ConfigurationTestingUtilities.generate_test_config("3.0"),
                "4.0",
            ),
        ]

        for case_name, source_config, target_version in migration_test_cases:
            try:
                start_time = time.time()
                migrated_config = migrator.migrate_config(source_config, target_version)
                duration = time.time() - start_time

                migrator.track_migration(
                    source_config["version"], target_version, migrated_config, duration
                )

                results["migration_tests"].append(
                    {
                        "name": case_name,
                        "success": True,
                        "duration": duration,
                        "target_version": target_version,
                    }
                )
            except Exception as e:
                results["migration_tests"].append(
                    {"name": case_name, "success": False, "error": str(e)}
                )

        # Test profile management
        manager = ConfigurationTestingUtilities.create_test_manager(temp_dir)
        profiles = [
            ("production", ConfigurationTestingUtilities.generate_test_config("4.0")),
            ("development", ConfigurationTestingUtilities.generate_test_config("3.0")),
            ("testing", ConfigurationTestingUtilities.generate_test_config("2.0")),
        ]

        for profile_name, config in profiles:
            try:
                profile = ConfigurationTestingUtilities.create_test_profile(
                    profile_name, config
                )
                profile_id = manager.create_profile(profile)
                results["profile_tests"].append(
                    {"name": profile_name, "success": True, "profile_id": profile_id}
                )
            except Exception as e:
                results["profile_tests"].append(
                    {"name": profile_name, "success": False, "error": str(e)}
                )

        # Test performance
        test_config = ConfigurationTestingUtilities.generate_test_config()
        performance_results = (
            ConfigurationTestingUtilities.benchmark_configuration_performance(
                test_config
            )
        )
        results["performance_tests"] = performance_results

        # Test error handling
        error_test_cases = [
            ("invalid_config", {"invalid": "data"}),
            ("missing_version", {}),
            ("none_config", None),
        ]

        for case_name, config_data in error_test_cases:
            try:
                validator.validate_configuration(config_data)
                results["error_handling_tests"].append(
                    {
                        "name": case_name,
                        "expected_error": True,
                        "actual_error": False,
                        "passed": False,
                    }
                )
            except Exception:
                results["error_handling_tests"].append(
                    {
                        "name": case_name,
                        "expected_error": True,
                        "actual_error": True,
                        "passed": True,
                    }
                )

        return results

    @staticmethod
    def generate_migration_report(temp_dir: str) -> dict[str, Any]:
        """Generate comprehensive migration report"""
        migrator = ConfigurationTestingUtilities.create_test_migrator()
        manager = ConfigurationTestingUtilities.create_test_manager(temp_dir)

        report = {
            "timestamp": datetime.now().isoformat(),
            "migration_statistics": migrator.get_migration_statistics(),
            "system_health": {
                "configuration_count": len(manager.list_profiles()),
                "active_profiles": len(
                    [p for p in manager.list_profiles() if p.is_active]
                ),
                "average_validation_score": 0,
                "migration_success_rate": 0,
            },
            "recommendations": [],
        }

        # Calculate system health metrics
        profiles = manager.list_profiles()
        if profiles:
            validation_scores = []
            for profile in profiles:
                integrity = (
                    ConfigurationTestingUtilities.validate_configuration_integrity(
                        profile.config
                    )
                )
                validation_scores.append(integrity["score"])

            report["system_health"]["average_validation_score"] = sum(
                validation_scores
            ) / len(validation_scores)

        # Generate recommendations
        stats = report["migration_statistics"]
        if stats.get("success_rate", 0) < 0.9:
            report["recommendations"].append(
                "Consider improving migration success rate"
            )

        if stats.get("average_duration", 0) > 2.0:
            report["recommendations"].append("Migration performance could be improved")

        return report


# Pytest fixtures
@pytest.fixture
def temp_config_directory():
    """Fixture for temporary configuration directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_validator():
    """Fixture for test configuration validator"""
    return ConfigurationTestingUtilities.create_test_validator()


@pytest.fixture
def test_migrator():
    """Fixture for test configuration migrator"""
    return ConfigurationTestingUtilities.create_test_migrator()


@pytest.fixture
def test_manager(temp_config_directory):
    """Fixture for test configuration manager"""
    return ConfigurationTestingUtilities.create_test_manager(temp_config_directory)


@pytest.fixture
def test_config():
    """Fixture for test configuration"""
    return ConfigurationTestingUtilities.generate_test_config()


@pytest.fixture
def test_profile():
    """Fixture for test configuration profile"""
    config = ConfigurationTestingUtilities.generate_test_config()
    return ConfigurationTestingUtilities.create_test_profile("test", config)


# Test markers
pytest.mark.config_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.migration_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.performance_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)
pytest.mark.integration_testing = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)


# Test helpers
def validate_config_result(result: dict[str, Any], expected_valid: bool) -> bool:
    """Validate configuration test result"""
    return result["is_valid"] == expected_valid


def validate_migration_result(result: dict[str, Any], expected_success: bool) -> bool:
    """Validate migration test result"""
    return result.get("success", False) == expected_success


def validate_performance_results(
    results: dict[str, float], thresholds: dict[str, float]
) -> bool:
    """Validate performance test results"""
    for metric, threshold in thresholds.items():
        if metric in results:
            if results[metric] > threshold:
                return False
    return True


def run_configuration_tests(temp_dir: str) -> dict[str, Any]:
    """Run comprehensive configuration tests"""
    return ConfigurationTestingUtilities.test_configuration_scenarios(temp_dir)


def generate_migration_report_summary(temp_dir: str) -> str:
    """Generate migration report summary"""
    report = ConfigurationTestingUtilities.generate_migration_report(temp_dir)

    summary = f"""
    Configuration Migration Report
    ==============================
    Timestamp: {report['timestamp']}

    Migration Statistics:
    - Total Migrations: {report['migration_statistics']['total_migrations']}
    - Average Duration: {report['migration_statistics']['average_duration']:.2f}s
    - Success Rate: {report['migration_statistics']['success_rate']:.1%}

    System Health:
    - Configuration Count: {report['system_health']['configuration_count']}
    - Active Profiles: {report['system_health']['active_profiles']}
    - Average Validation Score: {report['system_health']['average_validation_score']:.1f}

    Recommendations:
    """

    for i, recommendation in enumerate(report["recommendations"], 1):
        summary += f"\n    {i}. {recommendation}"

    return summary


# Test configuration
CONFIG_TEST_CONFIG = {
    "max_config_size": 10000,
    "max_validation_time": 1.0,
    "max_migration_time": 5.0,
    "min_compatibility_score": 0.8,
    "performance_thresholds": {
        "validation_time": 0.01,
        "migration_time": 0.5,
        "storage_time": 0.01,
    },
}


# Integration test helpers
def test_configuration_integration(temp_config_directory, test_manager):
    """Test configuration system integration"""
    # Create test configuration
    test_config = ConfigurationTestingUtilities.generate_test_config()

    # Store configuration
    config_id = test_manager.store_configuration(test_config)
    assert config_id is not None

    # Retrieve configuration
    retrieved_config = test_manager.get_configuration(config_id)
    assert retrieved_config == test_config

    # Create profile
    test_profile = ConfigurationTestingUtilities.create_test_profile(
        "integration_test", test_config
    )
    profile_id = test_manager.create_profile(test_profile)
    assert profile_id is not None

    # Validate profile
    retrieved_profile = test_manager.get_profile(profile_id)
    assert retrieved_profile is not None
    assert retrieved_profile.config == test_config


def test_migration_integration(test_migrator, test_config):
    """Test migration system integration"""
    # Test version migrations
    versions = ["2.0", "3.0", "4.0"]
    migrated_configs = []

    for version in versions:
        start_time = time.time()
        migrated_config = test_migrator.migrate_config(test_config, version)
        duration = time.time() - start_time

        test_migrator.track_migration(
            test_config["version"], version, migrated_config, duration
        )

        migrated_configs.append(migrated_config)
        assert migrated_config["version"] == version

    # Test migration statistics
    stats = test_migrator.get_migration_statistics()
    assert stats["total_migrations"] == len(versions)
    assert stats["success_rate"] == 1.0


def test_error_handling_integration(test_validator, test_migrator):
    """Test error handling integration"""
    # Test invalid configuration validation
    invalid_config = ConfigurationTestingUtilities.generate_invalid_config()
    validation_result = test_validator.validate_configuration(invalid_config)
    assert validation_result["is_valid"] is False

    # Test invalid migration
    with pytest.raises(ConfigurationError):
        test_migrator.migrate_config(invalid_config, "5.0")


def test_performance_integration(temp_config_directory, test_config):
    """Test performance integration"""
    # Test configuration performance
    performance_results = (
        ConfigurationTestingUtilities.benchmark_configuration_performance(test_config)
    )

    thresholds = CONFIG_TEST_CONFIG["performance_thresholds"]
    assert validate_performance_results(performance_results, thresholds)

    # Test concurrent operations
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(test_validator.validate_configuration, test_config)
            for _ in range(10)
        ]

        results = concurrent.futures.wait(futures, timeout=10)
        assert len(results.done) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
