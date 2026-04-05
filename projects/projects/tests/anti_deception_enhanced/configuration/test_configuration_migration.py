"""
Configuration Migration Testing

This module implements comprehensive testing for configuration migration
functionality, including version migration, data transformation, and
backward compatibility validation.

Test Categories:
1. Version Migration Tests
2. Data Transformation Tests
3. Backward Compatibility Tests
4. Migration Path Validation
5. Migration Error Handling
6. Configuration Import/Export
7. Migration Performance
8. Migration Security
"""

import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import pytest
import yaml

from anti_deception_enhanced.utils.configuration import (
    ConfigMigrator,
    ConfigurationError,
)


@dataclass
class MigrationTestCase:
    """Test case for configuration migration"""

    name: str
    source_version: str
    target_version: str
    source_config: dict[str, Any]
    expected_config: dict[str, Any]
    expected_errors: list[str] = field(default_factory=list)
    migration_strategy: str = "auto"


@dataclass
class TransformationTest:
    """Test case for data transformation"""

    name: str
    source_data: Any
    transformation_rules: dict[str, Any]
    expected_data: Any
    transform_type: str = "mapping"


@dataclass
class CompatibilityTest:
    """Test case for backward compatibility"""

    name: str
    old_version_config: dict[str, Any]
    new_version_config: dict[str, Any]
    is_compatible: bool
    compatibility_issues: list[str] = field(default_factory=list)


class TestVersionMigration:
    """Test version migration functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.migrator = ConfigMigrator()
        self.test_cases = [
            MigrationTestCase(
                name="v1_0_to_v2_0_migration",
                source_version="1.0",
                target_version="2.0",
                source_config={
                    "version": "1.0",
                    "security": {"enable_validation": True, "cost_budget": 0.10},
                    "performance": {
                        "max_response_time": 2.0,
                        "max_concurrent_requests": 3,
                    },
                },
                expected_config={
                    "version": "2.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                        "enhanced_validation": True,
                    },
                    "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
                },
            ),
            MigrationTestCase(
                name="v2_0_to_v3_0_migration",
                source_version="2.0",
                target_version="3.0",
                source_config={
                    "version": "2.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                    "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
                },
                expected_config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                        "advanced_validation": True,
                        "risk_assessment": True,
                        "ml_optimization": True,
                    },
                    "performance": {
                        "max_response_time": 0.5,
                        "concurrent_requests": 10,
                        "memory_optimization": True,
                        "caching_enabled": True,
                    },
                },
            ),
            MigrationTestCase(
                name="v3_0_to_v4_0_migration",
                source_version="3.0",
                target_version="4.0",
                source_config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                        "advanced_validation": True,
                        "risk_assessment": True,
                    },
                    "performance": {
                        "max_response_time": 0.5,
                        "concurrent_requests": 10,
                        "memory_optimization": True,
                    },
                },
                expected_config={
                    "version": "4.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.85,
                        "cost_budget": 0.10,
                        "advanced_validation": True,
                        "risk_assessment": True,
                        "adaptive_security": True,
                        "real_time_monitoring": True,
                    },
                    "performance": {
                        "max_response_time": 0.3,
                        "concurrent_requests": 20,
                        "memory_optimization": True,
                        "distributed_processing": True,
                    },
                    "features": {
                        "auto_scaling": True,
                        "load_balancing": True,
                        "health_checks": True,
                    },
                },
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_version_migration_execution(self):
        """Test version migration execution"""
        for test_case in self.test_cases:
            # Perform migration
            migrated_config = self.migrator.migrate_config(
                test_case.source_config, test_case.target_version
            )

            # Validate migration
            assert migrated_config is not None
            assert migrated_config["version"] == test_case.target_version

            # Compare with expected configuration
            self._compare_configurations(migrated_config, test_case.expected_config)

    def test_migration_error_handling(self):
        """Test migration error handling"""
        error_cases = [
            {
                "name": "invalid_source_version",
                "source_config": {"version": "invalid"},
                "target_version": "2.0",
                "expected_error": "Invalid source version",
            },
            {
                "name": "unsupported_migration",
                "source_config": {"version": "1.0"},
                "target_version": "5.0",
                "expected_error": "Migration not supported",
            },
            {
                "name": "configuration_corrupted",
                "source_config": {"version": "1.0", "corrupted": None},
                "target_version": "2.0",
                "expected_error": "Configuration corrupted",
            },
        ]

        for case in error_cases:
            with pytest.raises(ConfigurationError) as exc_info:
                self.migrator.migrate_config(
                    case["source_config"], case["target_version"]
                )

            assert case["expected_error"] in str(exc_info.value)

    def test_migration_path_validation(self):
        """Test migration path validation"""
        valid_paths = [
            ("1.0", "2.0"),
            ("2.0", "3.0"),
            ("1.0", "3.0"),
            ("2.0", "4.0"),
            ("3.0", "4.0"),
        ]

        invalid_paths = [
            ("1.0", "1.0"),  # Same version
            ("2.0", "1.0"),  # Backward migration
            ("1.0", "0.9"),  # Backward migration
            ("1.0", "3.1"),  # Invalid target version
            ("invalid", "2.0"),  # Invalid source
            ("1.0", "invalid"),  # Invalid target
        ]

        for source_version, target_version in valid_paths:
            is_valid = self.migrator.validate_migration_path(
                source_version, target_version
            )
            assert is_valid is True

        for source_version, target_version in invalid_paths:
            is_valid = self.migrator.validate_migration_path(
                source_version, target_version
            )
            assert is_valid is False

    def _compare_configurations(self, actual: dict[str, Any], expected: dict[str, Any]):
        """Helper method to compare configurations"""
        for key, expected_value in expected.items():
            assert key in actual, f"Missing key: {key}"

            if isinstance(expected_value, dict):
                assert isinstance(actual[key], dict), f"Expected dict for key {key}"
                self._compare_configurations(actual[key], expected_value)
            else:
                assert (
                    actual[key] == expected_value
                ), f"Value mismatch for key {key}: expected {expected_value}, got {actual[key]}"


class TestDataTransformation:
    """Test data transformation functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.migrator = ConfigMigrator()
        self.test_transformations = [
            TransformationTest(
                name="field_renaming",
                source_data={"old_field": "old_value", "another_old": "another_value"},
                transformation_rules={
                    "old_field": "new_field",
                    "another_old": "another_new",
                },
                expected_data={
                    "new_field": "old_value",
                    "another_new": "another_value",
                },
                transform_type="renaming",
            ),
            TransformationTest(
                name="data_type_conversion",
                source_data={"string_field": "123", "float_field": "45.67"},
                transformation_rules={"string_field": "int", "float_field": "float"},
                expected_data={"string_field": 123, "float_field": 45.67},
                transform_type="conversion",
            ),
            TransformationTest(
                name="value_mapping",
                source_data={"status": "old_status", "level": "old_level"},
                transformation_rules={
                    "status": {"old_status": "new_status"},
                    "level": {"old_level": "new_level"},
                },
                expected_data={"status": "new_status", "level": "new_level"},
                transform_type="mapping",
            ),
            TransformationTest(
                name="field_addition",
                source_data={"existing_field": "value"},
                transformation_rules={
                    "add_field": "default_value",
                    "conditional_field": "conditional_value",
                },
                expected_data={
                    "existing_field": "value",
                    "add_field": "default_value",
                    "conditional_field": "conditional_value",
                },
                transform_type="addition",
            ),
        ]

    def test_data_transformation(self):
        """Test data transformation"""
        for transform_test in self.test_transformations:
            # Apply transformation
            transformed_data = self.migrator.apply_transformation(
                transform_test.source_data,
                transform_test.transformation_rules,
                transform_test.transform_type,
            )

            # Validate transformation
            self._compare_transformed_data(
                transformed_data, transform_test.expected_data
            )

    def test_transformation_error_handling(self):
        """Test transformation error handling"""
        error_cases = [
            {
                "name": "invalid_transform_type",
                "source_data": {"test": "value"},
                "rules": {"test": "mapped"},
                "transform_type": "invalid_type",
            },
            {
                "name": "invalid_mapping",
                "source_data": {"status": "unknown"},
                "rules": {"status": {"invalid": "mapped"}},
                "transform_type": "mapping",
            },
            {
                "name": "type_conversion_error",
                "source_data": {"number": "not_a_number"},
                "rules": {"number": "int"},
                "transform_type": "conversion",
            },
        ]

        for case in error_cases:
            with pytest.raises(ConfigurationError):
                self.migrator.apply_transformation(
                    case["source_data"], case["rules"], case["transform_type"]
                )

    def _compare_transformed_data(self, actual: Any, expected: Any):
        """Helper method to compare transformed data"""
        if isinstance(expected, dict):
            assert isinstance(actual, dict)
            for key, expected_value in expected.items():
                assert key in actual
                self._compare_transformed_data(actual[key], expected_value)
        else:
            assert actual == expected


class TestBackwardCompatibility:
    """Test backward compatibility functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.migrator = ConfigMigrator()
        self.compatibility_tests = [
            CompatibilityTest(
                name="v1_to_v2_compatible",
                old_version_config={
                    "version": "1.0",
                    "security": {"enable_validation": True, "cost_budget": 0.10},
                },
                new_version_config={
                    "version": "2.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                is_compatible=True,
            ),
            CompatibilityTest(
                name="v2_to_v3_compatible",
                old_version_config={
                    "version": "2.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                new_version_config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                        "advanced_validation": True,
                    },
                },
                is_compatible=True,
            ),
            CompatibilityTest(
                name="breaking_changes_incompatible",
                old_version_config={
                    "version": "1.0",
                    "security": {"enable_validation": True, "cost_budget": 0.10},
                    "removed_field": "will_be_removed",
                },
                new_version_config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                is_compatible=False,
                compatibility_issues=["removed_field_removed"],
            ),
        ]

    def test_backward_compatibility_check(self):
        """Test backward compatibility checking"""
        for test_case in self.compatibility_tests:
            # Check compatibility
            compatibility_result = self.migrator.check_backward_compatibility(
                test_case.old_version_config, test_case.new_version_config
            )

            # Validate result
            assert compatibility_result["is_compatible"] == test_case.is_compatible
            assert len(compatibility_result["issues"]) == len(
                test_case.compatibility_issues
            )

            if not test_case.is_compatible:
                for issue in test_case.compatibility_issues:
                    assert issue in compatibility_result["issues"]

    def test_migration_recommendations(self):
        """Test migration recommendations"""
        test_config = {
            "version": "1.0",
            "security": {"enable_validation": True, "cost_budget": 0.10},
        }

        # Get migration recommendations
        recommendations = self.migrator.get_migration_recommendations(test_config)

        # Validate recommendations
        assert "recommended_path" in recommendations
        assert "migration_steps" in recommendations
        assert "estimated_time" in recommendations
        assert "risk_level" in recommendations

        assert recommendations["recommended_path"] == ["2.0", "3.0", "4.0"]
        assert recommendations["risk_level"] in ["low", "medium", "high"]

    def test_version_comparison(self):
        """Test version comparison"""
        version_tests = [
            (("1.0", "1.1"), "older"),
            (("1.0", "1.0"), "same"),
            (("1.1", "1.0"), "newer"),
            (("1.9", "2.0"), "older"),
            (("2.0", "1.9"), "newer"),
            (("1.0.0", "1.0"), "same"),
            (("1.0.1", "1.0.0"), "newer"),
        ]

        for (version1, version2), expected_result in version_tests:
            result = self.migrator.compare_versions(version1, version2)
            assert result == expected_result

    def test_feature_flag_migration(self):
        """Test feature flag migration"""
        # Test feature flag handling during migration
        config_with_flags = {
            "version": "2.0",
            "security": {"enable_validation": True, "validation_threshold": 0.8},
            "feature_flags": {"legacy_feature": True, "new_feature": False},
        }

        # Migrate config
        migrated_config = self.migrator.migrate_config(config_with_flags, "3.0")

        # Validate feature flags
        assert (
            "feature_flags" not in migrated_config
        )  # Should be integrated into main config
        assert (
            "advanced_validation" in migrated_config["security"]
        )  # Flag became real config


class TestConfigurationImportExport:
    """Test configuration import/export functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.migrator = ConfigMigrator()
        self.test_configs = [
            {
                "name": "production_config",
                "config": {
                    "version": "4.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.85,
                        "cost_budget": 0.10,
                    },
                    "performance": {
                        "max_response_time": 0.3,
                        "concurrent_requests": 20,
                    },
                },
            },
            {
                "name": "development_config",
                "config": {
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.6,
                        "cost_budget": 0.20,
                    },
                    "performance": {"max_response_time": 2.0, "concurrent_requests": 5},
                },
            },
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_configuration(self):
        """Test configuration export"""
        for config_info in self.test_configs:
            # Export configuration
            export_path = os.path.join(self.temp_dir, f"{config_info['name']}.json")
            export_success = self.migrator.export_configuration(
                config_info["config"], export_path
            )

            assert export_success is True
            assert os.path.exists(export_path)

            # Verify exported content
            with open(export_path) as f:
                exported_config = json.load(f)
            assert exported_config == config_info["config"]

    def test_import_configuration(self):
        """Test configuration import"""
        for config_info in self.test_configs:
            # Export configuration first
            export_path = os.path.join(self.temp_dir, f"{config_info['name']}.json")
            self.migrator.export_configuration(config_info["config"], export_path)

            # Import configuration
            imported_config = self.migrator.import_configuration(export_path)

            # Verify imported content
            assert imported_config == config_info["config"]

    def test_import_with_migration(self):
        """Test configuration import with migration"""
        # Create old version configuration
        old_config = {
            "version": "1.0",
            "security": {"enable_validation": True, "cost_budget": 0.10},
        }

        # Export old configuration
        export_path = os.path.join(self.temp_dir, "old_config.json")
        self.migrator.export_configuration(old_config, export_path)

        # Import with automatic migration
        imported_config = self.migrator.import_configuration(
            export_path, target_version="4.0"
        )

        # Verify migration occurred
        assert imported_config["version"] == "4.0"
        assert "validation_threshold" in imported_config["security"]
        assert imported_config["security"]["validation_threshold"] == 0.85

    def test_export_multiple_formats(self):
        """Test configuration export in multiple formats"""
        test_config = {
            "version": "4.0",
            "security": {"enable_validation": True, "validation_threshold": 0.85},
        }

        formats = ["json", "yaml", "xml"]
        for format_type in formats:
            export_path = os.path.join(self.temp_dir, f"config.{format_type}")
            export_success = self.migrator.export_configuration(
                test_config, export_path, format_type
            )

            assert export_success is True
            assert os.path.exists(export_path)

            # Verify content
            if format_type == "json":
                with open(export_path) as f:
                    loaded_config = json.load(f)
            elif format_type == "yaml":
                with open(export_path) as f:
                    loaded_config = yaml.safe_load(f)
            elif format_type == "xml":
                tree = ET.parse(export_path)
                loaded_config = self._xml_to_dict(tree.getroot())

            assert loaded_config == test_config

    def _xml_to_dict(self, element):
        """Helper method to convert XML to dictionary"""
        result = {}
        for child in element:
            if len(child) > 0:
                result[child.tag] = self._xml_to_dict(child)
            else:
                result[child.tag] = child.text
        return result

    def test_import_export_error_handling(self):
        """Test import/export error handling"""
        error_cases = [
            {"name": "invalid_file_path", "file_path": "/nonexistent/path/config.json"},
            {
                "name": "invalid_file_format",
                "file_path": os.path.join(self.temp_dir, "config.txt"),
            },
            {"name": "corrupted_file", "file_path": self._create_corrupted_file()},
            {"name": "invalid_json", "file_path": self._create_invalid_json()},
        ]

        for case in error_cases:
            with pytest.raises(ConfigurationError):
                self.migrator.import_configuration(case["file_path"])

    def _create_corrupted_file(self):
        """Create a corrupted file for testing"""
        corrupted_path = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_path, "w") as f:
            f.write("corrupted content")
        return corrupted_path

    def _create_invalid_json(self):
        """Create an invalid JSON file for testing"""
        invalid_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_path, "w") as f:
            f.write("{invalid: json")
        return invalid_path


class TestMigrationPerformance:
    """Test migration performance"""

    def setup_method(self):
        """Setup test environment"""
        self.migrator = ConfigMigrator()

    def test_migration_performance_benchmark(self):
        """Test migration performance benchmark"""
        # Create test configurations of different sizes
        small_config = self._create_test_config(10)
        medium_config = self._create_test_config(100)
        large_config = self._create_test_config(1000)

        test_configs = [
            ("small", small_config),
            ("medium", medium_config),
            ("large", large_config),
        ]

        performance_results = []

        for config_name, config in test_configs:
            # Measure migration performance
            start_time = time.time()

            # Perform multiple migrations
            for _ in range(10):
                self.migrator.migrate_config(config, "4.0")

            end_time = time.time()
            avg_time = (end_time - start_time) / 10

            performance_results.append(
                {
                    "config_size": config_name,
                    "avg_time_ms": avg_time * 1000,
                    "config_elements": len(json.dumps(config)),
                }
            )

        # Validate performance requirements
        for result in performance_results:
            assert (
                result["avg_time_ms"] < 1000
            ), f"Migration too slow: {result['avg_time_ms']}ms"

    def _create_test_config(self, size):
        """Create a test configuration of specified size"""
        config = {
            "version": "1.0",
            "security": {"enable_validation": True, "cost_budget": 0.10},
        }

        # Add nested elements to reach desired size
        for i in range(size):
            config[f"field_{i}"] = f"value_{i}"
            config[f"nested_{i}"] = {
                "subfield_1": f"subvalue_{i}_1",
                "subfield_2": f"subvalue_{i}_2",
            }

        return config

    def test_concurrent_migration(self):
        """Test concurrent migration performance"""
        test_configs = [self._create_test_config(50) for _ in range(10)]

        # Perform concurrent migrations
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.migrator.migrate_config, config, "4.0")
                for config in test_configs
            ]

            results = []
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Concurrent migration failed: {e}")

        end_time = time.time()
        total_time = end_time - start_time

        # Validate concurrent performance
        assert len(results) == len(test_configs)
        assert total_time < 30.0, f"Concurrent migration too slow: {total_time}s"

    def test_memory_usage_during_migration(self):
        """Test memory usage during migration"""
        import psutil

        process = psutil.Process()

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large configuration
        large_config = self._create_test_config(1000)

        # Perform migration
        start_time = time.time()
        for _ in range(5):
            migrated_config = self.migrator.migrate_config(large_config, "4.0")
        end_time = time.time()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Validate memory usage
        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
        assert (
            end_time - start_time
        ) < 5.0, f"Migration too slow: {end_time - start_time}s"


class TestMigrationSecurity:
    """Test migration security"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.migrator = ConfigMigrator()
        self.sensitive_config = {
            "version": "1.0",
            "security": {
                "enable_validation": True,
                "cost_budget": 0.10,
                "encryption_key": "super_secret_key_123",
                "api_key": "sk_test_123456789",
            },
            "database": {
                "password": "db_password_123",
                "connection_string": "postgres://user:pass@localhost/db",
            },
        }

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sensitive_data_detection(self):
        """Test sensitive data detection during migration"""
        # Detect sensitive fields
        sensitive_fields = self.migrator.detect_sensitive_fields(self.sensitive_config)

        # Validate detection
        expected_fields = ["encryption_key", "api_key", "password"]
        for field in expected_fields:
            assert field in sensitive_fields

    def test_sensitive_data_protection(self):
        """Test sensitive data protection during migration"""
        # Migrate configuration with sensitive data
        migrated_config = self.migrator.migrate_config(self.sensitive_config, "4.0")

        # Verify sensitive data is still protected
        assert "encryption_key" in migrated_config["security"]
        assert "api_key" in migrated_config["security"]
        assert "password" in migrated_config["database"]

        # Verify sensitive data is properly encrypted/obfuscated
        assert (
            migrated_config["security"]["encryption_key"]
            != self.sensitive_config["security"]["encryption_key"]
        )

    def test_integrity_verification(self):
        """Test integrity verification during migration"""
        # Migrate configuration
        migrated_config = self.migrator.migrate_config(self.sensitive_config, "4.0")

        # Verify integrity
        integrity_check = self.migrator.verify_migration_integrity(
            self.sensitive_config, migrated_config
        )

        assert integrity_check["is_valid"] is True
        assert integrity_check["checksum"] is not None

    def test_secure_export(self):
        """Test secure export functionality"""
        # Export configuration securely
        export_path = os.path.join(self.temp_dir, "secure_config.json")
        export_success = self.migrator.export_configuration(
            self.sensitive_config, export_path, encrypt_sensitive=True
        )

        assert export_success is True
        assert os.path.exists(export_path)

        # Verify file is encrypted
        with open(export_path) as f:
            content = f.read()
            assert "encryption_key" not in content  # Sensitive data should be encrypted
            assert "api_key" not in content  # Sensitive data should be encrypted

    def test_secure_import(self):
        """Test secure import functionality"""
        # Create encrypted configuration
        export_path = os.path.join(self.temp_dir, "encrypted_config.json")
        self.migrator.export_configuration(
            self.sensitive_config, export_path, encrypt_sensitive=True
        )

        # Import securely
        imported_config = self.migrator.import_configuration(
            export_path, decrypt_sensitive=True
        )

        # Verify sensitive data is restored
        assert (
            imported_config["security"]["encryption_key"]
            == self.sensitive_config["security"]["encryption_key"]
        )
        assert (
            imported_config["security"]["api_key"]
            == self.sensitive_config["security"]["api_key"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
