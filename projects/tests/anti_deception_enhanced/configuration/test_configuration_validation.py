"""
Configuration Validation Testing

This module implements comprehensive testing for configuration validation,
migration, and profile management. It validates the configuration system's
ability to handle various configuration scenarios, ensure data integrity,
and support smooth migrations between versions.

Test Categories:
1. Configuration File Validation
2. Schema Validation
3. Configuration Migration
4. Profile Management
5. Configuration Security
6. Configuration Performance
7. Configuration Error Handling
8. Configuration Backup and Recovery
"""

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Any

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
    """Test scenario for configuration validation"""

    name: str
    config_data: dict[str, Any]
    expected_valid: bool
    expected_errors: list[str] = field(default_factory=list)
    config_format: str = "json"
    config_version: str = "1.0"


@dataclass
class MigrationTestScenario:
    """Test scenario for configuration migration"""

    name: str
    source_config: dict[str, Any]
    target_version: str
    expected_migrated: dict[str, Any]
    migration_errors: list[str] = field(default_factory=list)


class TestConfigurationFileValidation:
    """Test configuration file validation"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ConfigValidator()
        self.test_scenarios = [
            ConfigurationTestScenario(
                name="valid_json_config",
                config_data={
                    "version": "1.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                    "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
                    "logging": {
                        "level": "INFO",
                        "file_path": "/var/log/anti_deception.log",
                    },
                },
                expected_valid=True,
                config_format="json",
            ),
            ConfigurationTestScenario(
                name="valid_yaml_config",
                config_data={
                    "version": "1.0",
                    "security": {"enable_validation": True, "cost_budget": 0.05},
                    "performance": {"max_response_time": 2.0},
                },
                expected_valid=True,
                config_format="yaml",
            ),
            ConfigurationTestScenario(
                name="invalid_json_config",
                config_data={
                    "version": "1.0",
                    "security": {
                        "enable_validation": "yes"  # Should be boolean
                    },
                    "missing_required_field": None,
                },
                expected_valid=False,
                expected_errors=["Invalid boolean value", "Missing required field"],
                config_format="json",
            ),
            ConfigurationTestScenario(
                name="malformed_json_config",
                config_data="{invalid_json",
                expected_valid=False,
                expected_errors=["JSON parsing error"],
                config_format="json",
            ),
            ConfigurationTestScenario(
                name="empty_config",
                config_data={},
                expected_valid=False,
                expected_errors=["Empty configuration", "Missing required fields"],
                config_format="json",
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_configuration_file_parsing(self):
        """Test configuration file parsing"""
        for scenario in self.test_scenarios:
            # Create configuration file
            config_file = os.path.join(
                self.temp_dir, f"config.{scenario.config_format}"
            )

            if scenario.config_format == "json":
                with open(config_file, "w") as f:
                    json.dump(scenario.config_data, f)
            elif scenario.config_format == "yaml":
                with open(config_file, "w") as f:
                    yaml.dump(scenario.config_data, f)

            # Parse configuration
            try:
                parsed_config = self.validator.parse_config_file(config_file)
                if scenario.expected_valid:
                    assert parsed_config is not None
                    assert parsed_config == scenario.config_data
                else:
                    assert parsed_config is None
            except Exception as e:
                if scenario.expected_valid:
                    pytest.fail(f"Failed to parse valid config: {e}")
                else:
                    # Expected to fail
                    pass

    def test_configuration_validation(self):
        """Test configuration validation"""
        for scenario in self.test_scenarios:
            # Validate configuration
            validation_result = self.validator.validate_configuration(
                scenario.config_data
            )

            assert validation_result["is_valid"] == scenario.expected_valid
            assert len(validation_result["errors"]) == len(scenario.expected_errors)

            if not scenario.expected_valid:
                for expected_error in scenario.expected_errors:
                    assert any(
                        expected_error in error for error in validation_result["errors"]
                    )

    def test_configuration_file_validation(self):
        """Test configuration file validation"""
        for scenario in self.test_scenarios:
            # Create configuration file
            config_file = os.path.join(
                self.temp_dir, f"config.{scenario.config_format}"
            )

            if scenario.config_format == "json":
                with open(config_file, "w") as f:
                    if scenario.expected_valid:
                        json.dump(scenario.config_data, f)
                    else:
                        if isinstance(scenario.config_data, str):
                            f.write(scenario.config_data)
                        else:
                            json.dump(scenario.config_data, f)
            elif scenario.config_format == "yaml":
                with open(config_file, "w") as f:
                    yaml.dump(scenario.config_data, f)

            # Validate configuration file
            validation_result = self.validator.validate_config_file(config_file)

            assert validation_result["is_valid"] == scenario.expected_valid
            assert len(validation_result["errors"]) == len(scenario.expected_errors)

    def test_configuration_format_detection(self):
        """Test configuration format detection"""
        format_test_cases = [
            ("config.json", "json"),
            ("config.yaml", "yaml"),
            ("config.yml", "yaml"),
            ("config.xml", "xml"),
            ("config.unknown", "unknown"),
        ]

        for filename, expected_format in format_test_cases:
            detected_format = self.validator.detect_config_format(filename)
            assert detected_format == expected_format

    def test_configuration_security_validation(self):
        """Test configuration security validation"""
        security_test_cases = [
            {
                "name": "secure_config",
                "config": {
                    "security": {
                        "enable_validation": True,
                        "cost_budget": 0.10,
                        "encryption_key": "secure_key_123",
                        "audit_logging": True,
                    }
                },
                "expected_valid": True,
            },
            {
                "name": "weak_security_config",
                "config": {
                    "security": {
                        "enable_validation": False,
                        "cost_budget": 0.0,
                        "encryption_key": "",
                        "audit_logging": False,
                    }
                },
                "expected_valid": True,  # Should be valid but flagged as weak
            },
            {
                "name": "insecure_config",
                "config": {
                    "security": {
                        "enable_validation": True,
                        "cost_budget": 1.0,  # Too high budget
                        "encryption_key": "weak_key",
                        "audit_logging": False,
                    }
                },
                "expected_valid": True,  # Structurally valid but insecure
            },
        ]

        for test_case in security_test_cases:
            security_result = self.validator.validate_security_config(
                test_case["config"]
            )
            assert security_result["is_valid"] == test_case["expected_valid"]
            assert "security_score" in security_result

    def test_configuration_performance_validation(self):
        """Test configuration performance validation"""
        performance_test_cases = [
            {
                "name": "optimal_performance",
                "config": {
                    "performance": {
                        "max_response_time": 1.0,
                        "concurrent_requests": 5,
                        "memory_limit": "1GB",
                        "cpu_limit": 80,
                    }
                },
                "expected_valid": True,
            },
            {
                "name": "aggressive_performance",
                "config": {
                    "performance": {
                        "max_response_time": 0.1,
                        "concurrent_requests": 100,
                        "memory_limit": "100MB",
                        "cpu_limit": 95,
                    }
                },
                "expected_valid": True,  # Valid but may cause issues
            },
            {
                "name": "invalid_performance",
                "config": {
                    "performance": {
                        "max_response_time": -1.0,  # Invalid negative value
                        "concurrent_requests": 0,  # Invalid zero value
                        "memory_limit": "invalid",  # Invalid format
                        "cpu_limit": 101,  # Invalid percentage
                    }
                },
                "expected_valid": False,
            },
        ]

        for test_case in performance_test_cases:
            performance_result = self.validator.validate_performance_config(
                test_case["config"]
            )
            assert performance_result["is_valid"] == test_case["expected_valid"]
            assert "performance_score" in performance_result


class TestConfigurationSchemaValidation:
    """Test configuration schema validation"""

    def setup_method(self):
        """Setup test environment"""
        self.validator = ConfigValidator()
        self.test_schema = ConfigSchema(
            version="1.0",
            fields={
                "version": {"type": str, "required": True, "pattern": r"^\d+\.\d+$"},
                "security": {
                    "type": dict,
                    "required": True,
                    "subfields": {
                        "enable_validation": {"type": bool, "required": True},
                        "validation_threshold": {
                            "type": float,
                            "required": True,
                            "min": 0.0,
                            "max": 1.0,
                        },
                        "cost_budget": {"type": float, "required": True, "min": 0.0},
                    },
                },
                "performance": {
                    "type": dict,
                    "required": False,
                    "subfields": {
                        "max_response_time": {
                            "type": float,
                            "required": False,
                            "min": 0.1,
                        },
                        "concurrent_requests": {
                            "type": int,
                            "required": False,
                            "min": 1,
                            "max": 100,
                        },
                    },
                },
            },
        )

    def test_schema_validation(self):
        """Test schema validation"""
        test_cases = [
            {
                "name": "valid_config",
                "config": {
                    "version": "1.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                "expected_valid": True,
            },
            {
                "name": "invalid_version",
                "config": {
                    "version": "invalid_version",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                "expected_valid": False,
            },
            {
                "name": "missing_required_field",
                "config": {
                    "version": "1.0",
                    "security": {
                        "enable_validation": True
                        # Missing validation_threshold and cost_budget
                    },
                },
                "expected_valid": False,
            },
            {
                "name": "invalid_field_type",
                "config": {
                    "version": "1.0",
                    "security": {
                        "enable_validation": "yes",  # Should be bool
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                },
                "expected_valid": False,
            },
            {
                "name": "invalid_range",
                "config": {
                    "version": "1.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 1.5,  # Should be <= 1.0
                        "cost_budget": -0.1,  # Should be >= 0.0
                    },
                },
                "expected_valid": False,
            },
        ]

        for test_case in test_cases:
            validation_result = self.validator.validate_with_schema(
                test_case["config"], self.test_schema
            )
            assert validation_result["is_valid"] == test_case["expected_valid"]

    def test_schema_field_validation(self):
        """Test individual field validation"""
        field_test_cases = [
            {
                "field_name": "version",
                "test_values": [
                    "1.0",
                    "2.1",
                    "1.0.0",
                ],  # 1.0 and 2.1 are valid, 1.0.0 is invalid
                "expected_valid": [True, True, False],
            },
            {
                "field_name": "enable_validation",
                "test_values": [True, False, "yes", 1, 0],
                "expected_valid": [True, True, False, False, False],
            },
            {
                "field_name": "validation_threshold",
                "test_values": [0.5, 0.0, 1.0, -0.1, 1.1],
                "expected_valid": [True, True, True, False, False],
            },
            {
                "field_name": "cost_budget",
                "test_values": [0.0, 10.0, -1.0, "invalid"],
                "expected_valid": [True, True, False, False],
            },
        ]

        for field_test in field_test_cases:
            field_config = self.test_schema.fields[field_test["field_name"]]
            for value, expected in zip(
                field_test["test_values"], field_test["expected_valid"], strict=False
            ):
                validation_result = self.validator.validate_field_value(
                    value, field_config
                )
                assert validation_result["is_valid"] == expected

    def test_schema_nested_validation(self):
        """Test nested schema validation"""
        nested_config = {
            "version": "1.0",
            "security": {
                "enable_validation": True,
                "validation_threshold": 0.8,
                "cost_budget": 0.10,
                "nested_field": {"deep_field": "test_value"},
            },
            "performance": {"max_response_time": 1.5, "concurrent_requests": 10},
        }

        validation_result = self.validator.validate_with_schema(
            nested_config, self.test_schema
        )
        assert validation_result["is_valid"] is True

    def test_schema_extension(self):
        """Test schema extension"""
        extended_schema = self.test_schema.extend(
            {
                "new_field": {"type": str, "required": False},
                "enhanced_security": {
                    "type": dict,
                    "required": False,
                    "subfields": {
                        "advanced_validation": {"type": bool, "required": False}
                    },
                },
            }
        )

        # Test extended schema
        extended_config = {
            "version": "1.0",
            "security": {
                "enable_validation": True,
                "validation_threshold": 0.8,
                "cost_budget": 0.10,
            },
            "new_field": "test_value",
            "enhanced_security": {"advanced_validation": True},
        }

        validation_result = self.validator.validate_with_schema(
            extended_config, extended_schema
        )
        assert validation_result["is_valid"] is True


class TestConfigurationMigration:
    """Test configuration migration"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.migrator = ConfigMigrator()
        self.migration_scenarios = [
            MigrationTestScenario(
                name="v1_to_v2_migration",
                source_config={
                    "version": "1.0",
                    "security": {"enable_validation": True, "cost_budget": 0.10},
                    "performance": {"max_response_time": 2.0},
                },
                target_version="2.0",
                expected_migrated={
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
            MigrationTestScenario(
                name="v2_to_v3_migration",
                source_config={
                    "version": "2.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                    "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
                },
                target_version="3.0",
                expected_migrated={
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
            ),
            MigrationTestScenario(
                name="invalid_migration",
                source_config={"version": "1.0", "invalid_field": "should_be_removed"},
                target_version="2.0",
                expected_migrated={
                    "version": "2.0",
                    "security": {"enable_validation": True, "cost_budget": 0.05},
                },
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_version_migration(self):
        """Test version migration"""
        for scenario in self.migration_scenarios:
            # Perform migration
            migrated_config = self.migrator.migrate_config(
                scenario.source_config, scenario.target_version
            )

            # Validate migration
            assert migrated_config is not None
            assert migrated_config["version"] == scenario.target_version

            # Compare with expected result
            for key, value in scenario.expected_migrated.items():
                assert key in migrated_config
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        assert sub_key in migrated_config[key]
                        assert migrated_config[key][sub_key] == sub_value
                else:
                    assert migrated_config[key] == value

    def test_migration_path_validation(self):
        """Test migration path validation"""
        valid_paths = [("1.0", "1.1"), ("1.0", "2.0"), ("2.0", "2.1"), ("2.0", "3.0")]

        invalid_paths = [
            ("1.0", "0.9"),  # Backward migration not supported
            ("3.0", "2.0"),  # Backward migration not supported
            ("1.0", "2.5"),  # Skip version not supported
            ("invalid", "2.0"),  # Invalid source version
            ("1.0", "invalid"),  # Invalid target version
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

    def test_migration_error_handling(self):
        """Test migration error handling"""
        error_cases = [
            {
                "name": "missing_source_version",
                "source_config": {"invalid": "config"},
                "target_version": "2.0",
                "expected_error": "Source configuration missing version",
            },
            {
                "name": "unsupported_migration",
                "source_config": {"version": "1.0"},
                "target_version": "5.0",  # Too far ahead
                "expected_error": "Migration not supported",
            },
            {
                "name": "corrupted_config",
                "source_config": {"version": "1.0", "corrupted": None},
                "target_version": "2.0",
                "expected_error": "Configuration corrupted",
            },
        ]

        for case in error_cases:
            try:
                migrated_config = self.migrator.migrate_config(
                    case["source_config"], case["target_version"]
                )
                pytest.fail(
                    f"Expected error for {case['name']}: {case['expected_error']}"
                )
            except ConfigurationError as e:
                assert case["expected_error"] in str(e)

    def test_migration_backup(self):
        """Test migration backup functionality"""
        # Create source config
        source_config = {
            "version": "1.0",
            "security": {"enable_validation": True, "cost_budget": 0.10},
        }

        # Create backup
        backup_path = os.path.join(self.temp_dir, "migration_backup.json")
        backup_success = self.migrator.create_migration_backup(
            source_config, backup_path
        )
        assert backup_success is True
        assert os.path.exists(backup_path)

        # Verify backup content
        with open(backup_path) as f:
            backup_content = json.load(f)
        assert backup_content == source_config

        # Test backup restoration
        restored_config = self.migrator.restore_from_backup(backup_path)
        assert restored_config == source_config

    def test_migration_rollback(self):
        """Test migration rollback functionality"""
        # Create source config
        source_config = {
            "version": "1.0",
            "security": {"enable_validation": True, "cost_budget": 0.10},
        }

        # Perform migration
        migrated_config = self.migrator.migrate_config(source_config, "2.0")

        # Create backup before rollback
        backup_path = os.path.join(self.temp_dir, "pre_rollback_backup.json")
        backup_success = self.migrator.create_migration_backup(
            migrated_config, backup_path
        )
        assert backup_success is True

        # Test rollback
        rollback_success = self.migrator.rollback_migration(backup_path)
        assert rollback_success is True

        # Verify rollback result
        restored_config = self.migrator.restore_from_backup(backup_path)
        assert restored_config == migrated_config


class TestConfigurationProfileManagement:
    """Test configuration profile management"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.profile_manager = ConfigManager(self.temp_dir)
        self.test_profiles = [
            ConfigProfile(
                name="production",
                description="Production environment configuration",
                config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.9,
                        "cost_budget": 0.05,
                    },
                    "performance": {
                        "max_response_time": 0.5,
                        "concurrent_requests": 10,
                    },
                },
                is_active=True,
            ),
            ConfigProfile(
                name="development",
                description="Development environment configuration",
                config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.6,
                        "cost_budget": 0.20,
                    },
                    "performance": {"max_response_time": 2.0, "concurrent_requests": 5},
                },
                is_active=False,
            ),
            ConfigProfile(
                name="testing",
                description="Testing environment configuration",
                config={
                    "version": "3.0",
                    "security": {
                        "enable_validation": True,
                        "validation_threshold": 0.8,
                        "cost_budget": 0.10,
                    },
                    "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
                },
                is_active=False,
            ),
        ]

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_profile_creation(self):
        """Test profile creation"""
        for profile in self.test_profiles:
            # Create profile
            profile_id = self.profile_manager.create_profile(profile)
            assert profile_id is not None

            # Verify profile creation
            retrieved_profile = self.profile_manager.get_profile(profile_id)
            assert retrieved_profile is not None
            assert retrieved_profile.name == profile.name
            assert retrieved_profile.description == profile.description
            assert retrieved_profile.config == profile.config

    def test_profile_retrieval(self):
        """Test profile retrieval"""
        # Create all profiles
        profile_ids = []
        for profile in self.test_profiles:
            profile_id = self.profile_manager.create_profile(profile)
            profile_ids.append(profile_id)

        # Test individual retrieval
        for i, profile_id in enumerate(profile_ids):
            retrieved_profile = self.profile_manager.get_profile(profile_id)
            assert retrieved_profile.name == self.test_profiles[i].name

        # Test list retrieval
        all_profiles = self.profile_manager.list_profiles()
        assert len(all_profiles) == len(self.test_profiles)

        # Test active profile retrieval
        active_profile = self.profile_manager.get_active_profile()
        assert active_profile is not None
        assert active_profile.name == "production"

    def test_profile_update(self):
        """Test profile update"""
        # Create profile
        profile = self.test_profiles[0]
        profile_id = self.profile_manager.create_profile(profile)

        # Update profile
        updated_config = profile.config.copy()
        updated_config["security"]["cost_budget"] = 0.08
        updated_description = "Updated production configuration"

        update_success = self.profile_manager.update_profile(
            profile_id, config=updated_config, description=updated_description
        )
        assert update_success is True

        # Verify update
        retrieved_profile = self.profile_manager.get_profile(profile_id)
        assert retrieved_profile.config["security"]["cost_budget"] == 0.08
        assert retrieved_profile.description == updated_description

    def test_profile_deletion(self):
        """Test profile deletion"""
        # Create profile
        profile = self.test_profiles[0]
        profile_id = self.profile_manager.create_profile(profile)

        # Verify creation
        assert self.profile_manager.get_profile(profile_id) is not None

        # Delete profile
        deletion_success = self.profile_manager.delete_profile(profile_id)
        assert deletion_success is True

        # Verify deletion
        retrieved_profile = self.profile_manager.get_profile(profile_id)
        assert retrieved_profile is None

    def test_profile_activation(self):
        """Test profile activation"""
        # Create all profiles
        profile_ids = []
        for profile in self.test_profiles:
            profile_id = self.profile_manager.create_profile(profile)
            profile_ids.append(profile_id)

        # Test activation
        activation_success = self.profile_manager.activate_profile(
            profile_ids[1]
        )  # Development
        assert activation_success is True

        # Verify activation
        active_profile = self.profile_manager.get_active_profile()
        assert active_profile.name == "development"

        # Test that previous active profile is deactivated
        production_profile = self.profile_manager.get_profile(profile_ids[0])
        assert production_profile.is_active is False

    def test_profile_validation(self):
        """Test profile validation"""
        # Create valid profile
        valid_profile = self.test_profiles[0]
        profile_id = self.profile_manager.create_profile(valid_profile)
        assert profile_id is not None

        # Test invalid profile
        invalid_profile = ConfigProfile(
            name="",  # Empty name
            description="Invalid profile",
            config={
                "version": "3.0",
                "security": {
                    "enable_validation": "yes"  # Invalid boolean
                },
            },
        )

        with pytest.raises(ConfigurationError):
            self.profile_manager.create_profile(invalid_profile)

    def test_profile_export_import(self):
        """Test profile export and import"""
        # Create profile
        profile = self.test_profiles[0]
        profile_id = self.profile_manager.create_profile(profile)

        # Export profile
        export_path = os.path.join(self.temp_dir, "profile_export.json")
        export_success = self.profile_manager.export_profile(profile_id, export_path)
        assert export_success is True
        assert os.path.exists(export_path)

        # Verify exported content
        with open(export_path) as f:
            exported_data = json.load(f)
        assert exported_data["name"] == profile.name
        assert exported_data["config"] == profile.config

        # Import profile
        import_success = self.profile_manager.import_profile(export_path)
        assert import_success is True

        # Verify import
        imported_profile = self.profile_manager.get_active_profile()
        assert imported_profile.name == profile.name


class TestConfigurationSecurity:
    """Test configuration security"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        self.test_config = {
            "version": "3.0",
            "security": {
                "enable_validation": True,
                "validation_threshold": 0.8,
                "cost_budget": 0.10,
                "encryption_key": "secret_key_123",
                "api_key": "sk_test_123456789",
            },
            "performance": {"max_response_time": 1.0, "concurrent_requests": 5},
        }

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_configuration_encryption(self):
        """Test configuration encryption"""
        # Create encrypted configuration
        encrypted_config = self.config_manager.encrypt_configuration(self.test_config)
        assert encrypted_config is not None
        assert encrypted_config != self.test_config

        # Decrypt configuration
        decrypted_config = self.config_manager.decrypt_configuration(encrypted_config)
        assert decrypted_config == self.test_config

    def test_sensitive_data_detection(self):
        """Test sensitive data detection"""
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "api_key",
            "credential",
            "auth",
        ]

        detected_fields = self.config_manager.detect_sensitive_fields(self.test_config)
        assert len(detected_fields) > 0
        assert "encryption_key" in detected_fields
        assert "api_key" in detected_fields

    def test_configuration_integrity_check(self):
        """Test configuration integrity check"""
        # Store configuration
        config_id = self.config_manager.store_configuration(self.test_config)
        assert config_id is not None

        # Check integrity
        integrity_check = self.config_manager.check_configuration_integrity(config_id)
        assert integrity_check["is_valid"] is True
        assert integrity_check["checksum"] is not None

        # Modify configuration to break integrity
        with open(f"{self.temp_dir}/{config_id}.json", "w") as f:
            json.dump({"modified": True}, f)

        # Check integrity again
        integrity_check = self.config_manager.check_configuration_integrity(config_id)
        assert integrity_check["is_valid"] is False

    def test_configuration_access_control(self):
        """Test configuration access control"""
        # Store configuration
        config_id = self.config_manager.store_configuration(self.test_config)

        # Test access control
        access_granted = self.config_manager.check_access_permission(config_id, "read")
        assert access_granted is True

        access_denied = self.config_manager.check_access_permission(config_id, "admin")
        assert access_denied is False

    def test_configuration_audit_logging(self):
        """Test configuration audit logging"""
        # Store configuration
        config_id = self.config_manager.store_configuration(self.test_config)

        # Get audit log
        audit_log = self.config_manager.get_configuration_audit_log(config_id)
        assert len(audit_log) > 0

        # Verify audit log entries
        for entry in audit_log:
            assert "timestamp" in entry
            assert "action" in entry
            assert "user" in entry
            assert "configuration_id" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
