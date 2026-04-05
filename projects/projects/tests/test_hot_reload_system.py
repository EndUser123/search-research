"""
Test Suite for CSF NIP Hot-Reload System
==========================================

Comprehensive tests for the configuration hot-reload system including:
- File watching and debouncing
- Configuration validation
- Environment overrides
- Backward compatibility
- Impact analysis
- Change logging
- Integration tests

Author: CSF NIP Backend Architect
"""

import json
import logging
import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from src.csf_nip.config.backward_compatibility import (
    ClaudeSettingsMigrationV1ToV2,
    ConfigVersionDetection,
    LegacyConfigWrapper,
)
from src.csf_nip.config.ecosystem_hot_reload_manager import EcosystemHotReloadManager

# Import the hot-reload system components
from src.csf_nip.config.hot_reload_system import (
    ChangeSeverity,
    ConfigChangeEvent,
    ConfigChangeLogger,
    ConfigImpactAnalyzer,
    ConfigValidator,
    EnvironmentOverrideLoader,
    HotReloadSystem,
)


class TestConfigValidator(unittest.TestCase):
    """Test configuration validation functionality."""

    def setUp(self):
        self.validator = ConfigValidator()

    def test_claude_settings_validation_valid(self):
        """Test validation of valid Claude settings."""
        config = {
            "permissions": {
                "allow": ["Bash(git status)", "Bash(ls)"],
                "deny": ["Bash(rm -rf /)"],
            },
            "env": {"VERIFICATION_WORKFLOW_ENABLED": "true"},
            "verification_workflow": {"enabled": True, "evidence_window_minutes": 30},
            "anti_deception": {"enabled": True, "strict_mode": False},
            "hooks": {"SessionStart": [], "UserPromptSubmit": []},
        }

        result = self.validator.validate("claude/settings.json", config)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_claude_settings_validation_missing_required(self):
        """Test validation with missing required fields."""
        config = {"env": {"VERIFICATION_WORKFLOW_ENABLED": "true"}}

        result = self.validator.validate("claude/settings.json", config)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("permissions" in error for error in result.errors))

    def test_security_validation_dangerous_patterns(self):
        """Test security validation for dangerous patterns."""
        config = {"permissions": {"allow": ["Bash(rm -rf /)"], "deny": []}}

        result = self.validator.validate("claude/settings.json", config)
        # Should still be valid but with warnings
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.warnings) > 0)
        self.assertTrue(
            any("dangerous" in warning.lower() for warning in result.warnings)
        )

    def test_speckit_config_validation(self):
        """Test Speckit configuration validation."""
        config = {
            "task_management": {
                "global_counter": {"current_id": 1, "format": "TSK-%03d"},
                "task_storage": {"active_tasks": "cache/active_tasks.json"},
            },
            "speckit_framework": {"version": "2.0.0", "enhanced_templates": True},
            "paths": {"templates": "templates/", "memory": "memory/"},
        }

        result = self.validator.validate("speckit_config.json", config)
        self.assertTrue(result.is_valid)

    def test_custom_validation_rule(self):
        """Test custom validation rule functionality."""

        def custom_rule(config, result):
            if "test_field" in config and config["test_field"] == "invalid":
                result.errors.append("Custom validation failed")

        self.validator.add_validation_rule("test_config", custom_rule)

        config = {"test_field": "invalid"}
        result = self.validator.validate("test_config", config)
        self.assertFalse(result.is_valid)
        self.assertIn("Custom validation failed", result.errors)


class TestConfigImpactAnalyzer(unittest.TestCase):
    """Test configuration change impact analysis."""

    def setUp(self):
        self.analyzer = ConfigImpactAnalyzer()

    def test_initial_load_analysis(self):
        """Test impact analysis for initial configuration load."""
        config = {
            "permissions": {"allow": ["test"]},
            "anti_deception": {"enabled": True},
        }

        severity, components, description = self.analyzer.analyze_change(None, config)

        self.assertEqual(severity, ChangeSeverity.LOW)
        self.assertIn("permissions", components)
        self.assertIn("command_execution", components)
        self.assertIn("Initial configuration load", description)

    def test_low_severity_changes(self):
        """Test impact analysis for low severity changes."""
        old_config = {"permissions": {"allow": ["old_permission"]}}
        new_config = {"permissions": {"allow": ["new_permission"]}}

        severity, components, description = self.analyzer.analyze_change(
            old_config, new_config
        )

        self.assertEqual(severity, ChangeSeverity.LOW)
        self.assertEqual(len(components), 2)  # permissions and command_execution

    def test_high_severity_changes(self):
        """Test impact analysis for high severity changes."""
        old_config = {"permissions": {"allow": ["test"]}}
        new_config = {"permissions": {"allow": ["test"], "deny": ["dangerous"]}}

        severity, components, description = self.analyzer.analyze_change(
            old_config, new_config
        )

        self.assertEqual(severity, ChangeSeverity.HIGH)
        self.assertIn("command_execution", components)

    def test_critical_severity_changes(self):
        """Test impact analysis for critical severity changes."""
        old_config = {"permissions": {"allow": ["test"]}}
        new_config = {"permissions": {"allow": ["test"], "deny": ["rm -rf /"]}}

        severity, components, description = self.analyzer.analyze_change(
            old_config, new_config
        )

        self.assertEqual(severity, ChangeSeverity.CRITICAL)

    def test_added_removed_keys(self):
        """Test impact analysis for added and removed keys."""
        old_config = {"section1": {"key1": "value1"}}
        new_config = {
            "section1": {"key1": "value1", "key2": "value2"},
            "section2": {"key3": "value3"},
        }

        severity, components, description = self.analyzer.analyze_change(
            old_config, new_config
        )

        self.assertEqual(severity, ChangeSeverity.MEDIUM)
        self.assertIn("Added", description)
        self.assertIn("Removed", description)


class TestEnvironmentOverrideLoader(unittest.TestCase):
    """Test environment-specific configuration overrides."""

    def setUp(self):
        self.env_loader = EnvironmentOverrideLoader()

    @patch.dict(os.environ, {"CSF_NIP_ENV": "staging"})
    def test_environment_detection(self):
        """Test environment detection from environment variables."""
        self.assertEqual(self.env_loader.current_env, "staging")

    def test_override_file_path_generation(self):
        """Test override file path generation."""
        config_path = "/path/to/config.json"
        override_path = self.env_loader._get_override_file_path(config_path)
        self.assertEqual(override_path, "/path/to/config.development.json")

    def test_config_merging(self):
        """Test configuration merging with overrides."""
        base_config = {"key1": "value1", "nested": {"subkey1": "subvalue1"}}
        override_config = {
            "key1": "overridden_value",
            "key2": "value2",
            "nested": {"subkey2": "subvalue2"},
        }

        merged = self.env_loader._merge_configs(base_config, override_config)

        self.assertEqual(merged["key1"], "overridden_value")
        self.assertEqual(merged["key2"], "value2")
        self.assertEqual(merged["nested"]["subkey1"], "subvalue1")
        self.assertEqual(merged["nested"]["subkey2"], "subvalue2")

    @patch.dict(os.environ, {"CSF_VERIFICATION_ENABLED": "true"})
    def test_env_var_overrides(self):
        """Test environment variable overrides."""
        config = {"verification_workflow": {"enabled": False}}
        config_path = "settings.json"

        overridden = self.env_loader._apply_env_var_overrides(config, config_path)

        self.assertTrue(overridden["verification_workflow"]["enabled"])

    def test_env_value_conversion(self):
        """Test environment variable value conversion."""
        # Boolean conversion
        self.assertTrue(self.env_loader._convert_env_value("true"))
        self.assertFalse(self.env_loader._convert_env_value("false"))

        # Number conversion
        self.assertEqual(self.env_loader._convert_env_value("42"), 42)
        self.assertEqual(self.env_loader._convert_env_value("3.14"), 3.14)

        # JSON conversion
        json_value = '{"key": "value"}'
        self.assertEqual(
            self.env_loader._convert_env_value(json_value), {"key": "value"}
        )

        # String fallback
        self.assertEqual(
            self.env_loader._convert_env_value("plain_string"), "plain_string"
        )


class TestConfigChangeLogger(unittest.TestCase):
    """Test configuration change logging."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".log"
        )
        self.logger = ConfigChangeLogger(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_change_logging(self):
        """Test logging of configuration changes."""
        event = ConfigChangeEvent(
            file_path="/test/config.json",
            old_content={"key": "old_value"},
            new_content={"key": "new_value"},
            change_time=datetime.now(),
            severity=ChangeSeverity.MEDIUM,
            description="Test change",
        )

        self.logger.log_change(event)

        # Read log file
        self.temp_file.seek(0)
        log_content = self.temp_file.read()
        self.assertIn("config.json", log_content)
        self.assertIn("medium", log_content)
        self.assertIn("Test change", log_content)

    def test_change_history_retrieval(self):
        """Test retrieval of change history."""
        # Create some test events
        events = [
            ConfigChangeEvent(
                file_path="/test/config1.json",
                old_content=None,
                new_content={"key": "value1"},
                change_time=datetime.now(),
                severity=ChangeSeverity.LOW,
                description="Initial load",
            ),
            ConfigChangeEvent(
                file_path="/test/config2.json",
                old_content={"key": "old"},
                new_content={"key": "new"},
                change_time=datetime.now(),
                severity=ChangeSeverity.HIGH,
                description="Updated config",
            ),
        ]

        for event in events:
            self.logger.log_change(event)

        # Retrieve history
        history = self.logger.get_change_history(limit=10)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["file_path"], "/test/config1.json")
        self.assertEqual(history[1]["file_path"], "/test/config2.json")


class TestHotReloadSystem(unittest.TestCase):
    """Test the main hot-reload system."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.hot_reload_system = HotReloadSystem([self.temp_dir], debounce_delay=0.1)

    def tearDown(self):
        self.hot_reload_system.stop()
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test hot-reload system initialization."""
        self.assertFalse(self.hot_reload_system.is_running)
        self.assertEqual(len(self.hot_reload_system.config_directories), 1)
        self.assertEqual(self.hot_reload_system.config_directories[0], self.temp_dir)

    def test_start_stop(self):
        """Test starting and stopping the hot-reload system."""
        self.hot_reload_system.start()
        self.assertTrue(self.hot_reload_system.is_running)

        self.hot_reload_system.stop()
        self.assertFalse(self.hot_reload_system.is_running)

    def test_config_loading(self):
        """Test configuration loading."""
        # Create a test config file
        test_config = {"test_key": "test_value"}
        config_file = os.path.join(self.temp_dir, "test_config.json")
        with open(config_file, "w") as f:
            json.dump(test_config, f)

        # Load configuration
        loaded_config = self.hot_reload_system.get_config(config_file)
        self.assertEqual(loaded_config, test_config)

    def test_config_reload(self):
        """Test configuration reloading."""
        # Create initial config
        initial_config = {"version": 1}
        config_file = os.path.join(self.temp_dir, "reload_test.json")
        with open(config_file, "w") as f:
            json.dump(initial_config, f)

        # Load initial config
        self.hot_reload_system.reload_config(config_file)
        loaded = self.hot_reload_system.get_config(config_file)
        self.assertEqual(loaded["version"], 1)

        # Update config
        updated_config = {"version": 2}
        with open(config_file, "w") as f:
            json.dump(updated_config, f)

        # Reload config
        success = self.hot_reload_system.reload_config(config_file)
        self.assertTrue(success)

        # Verify updated config
        loaded = self.hot_reload_system.get_config(config_file)
        self.assertEqual(loaded["version"], 2)

    def test_event_listeners(self):
        """Test event listener functionality."""
        events_received = []

        def test_listener(event):
            events_received.append(event)

        self.hot_reload_system.add_event_listener(test_listener)

        # Create a test event
        test_config = {"key": "value"}
        config_file = os.path.join(self.temp_dir, "listener_test.json")
        with open(config_file, "w") as f:
            json.dump(test_config, f)

        # Reload config to trigger event
        self.hot_reload_system.reload_config(config_file)

        # Give some time for async processing
        time.sleep(0.2)

        # Verify event was received
        self.assertTrue(len(events_received) > 0)
        self.assertEqual(events_received[0].file_path, os.path.abspath(config_file))

    def test_config_validation_on_reload(self):
        """Test configuration validation during reload."""
        # Create invalid config (missing required fields)
        invalid_config = {"invalid": "config"}  # Missing required permissions
        config_file = os.path.join(self.temp_dir, "invalid_test.json")
        with open(config_file, "w") as f:
            json.dump(invalid_config, f)

        # Try to reload - should fail validation
        success = self.hot_reload_system.reload_config(config_file)
        self.assertFalse(success)

    def test_rollback_functionality(self):
        """Test configuration rollback functionality."""
        # Create initial valid config
        initial_config = {"permissions": {"allow": ["test"]}}
        config_file = os.path.join(self.temp_dir, "rollback_test.json")
        with open(config_file, "w") as f:
            json.dump(initial_config, f)

        # Load initial config
        self.hot_reload_system.reload_config(config_file)

        # Create backup and update to new config
        new_config = {"permissions": {"allow": ["new_test"]}}
        with open(config_file, "w") as f:
            json.dump(new_config, f)

        self.hot_reload_system.reload_config(config_file)

        # Rollback to initial config
        success = self.hot_reload_system.rollback_config(config_file)
        self.assertTrue(success)

        # Verify rollback
        loaded = self.hot_reload_system.get_config(config_file)
        self.assertEqual(loaded["permissions"]["allow"][0], "test")


class TestEcosystemHotReloadManager(unittest.TestCase):
    """Test the ecosystem hot-reload manager."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ecosystem_file = os.path.join(self.temp_dir, "ecosystem.json")

        # Create ecosystem config
        ecosystem_config = {
            "ecosystem": {
                "name": "Test Ecosystem",
                "version": "1.0.0",
                "environment": "development",
            },
            "hot_reload": {"enabled": True, "config_directories": [self.temp_dir]},
            "components": {
                "test_component": {
                    "enabled": True,
                    "config_file": "test_config.json",
                    "hot_reload_enabled": True,
                    "restart_required": False,
                }
            },
        }

        with open(self.ecosystem_file, "w") as f:
            json.dump(ecosystem_config, f)

        self.manager = EcosystemHotReloadManager(self.ecosystem_file)

    def tearDown(self):
        self.manager.stop()
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_ecosystem_initialization(self):
        """Test ecosystem manager initialization."""
        self.assertFalse(self.manager.is_running)
        self.assertEqual(self.manager.ecosystem_file, self.ecosystem_file)

    def test_ecosystem_start_stop(self):
        """Test starting and stopping ecosystem manager."""
        self.manager.start()
        self.assertTrue(self.manager.is_running)

        self.manager.stop()
        self.assertFalse(self.manager.is_running)

    def test_ecosystem_config_loading(self):
        """Test ecosystem configuration loading."""
        self.manager.start()

        state = self.manager.get_ecosystem_state()
        self.assertIsNotNone(state)
        self.assertEqual(state.ecosystem_config["ecosystem"]["name"], "Test Ecosystem")
        self.assertIn("test_component", state.components)

    def test_component_config_access(self):
        """Test access to component configurations."""
        # Create component config file
        component_config = {"component_setting": "value"}
        component_file = os.path.join(self.temp_dir, "test_config.json")
        with open(component_file, "w") as f:
            json.dump(component_config, f)

        self.manager.start()

        # Get component config
        loaded = self.manager.get_component_config("test_component")
        self.assertIsNotNone(loaded)

    def test_ecosystem_listeners(self):
        """Test ecosystem state change listeners."""
        events_received = []

        def ecosystem_listener(state):
            events_received.append(state)

        self.manager.add_ecosystem_listener(ecosystem_listener)

        # Start manager to trigger initial state load
        self.manager.start()

        # Verify listener was called
        self.assertTrue(len(events_received) > 0)

    def test_health_status(self):
        """Test health status reporting."""
        self.manager.start()

        health = self.manager.get_health_status()
        self.assertTrue(health["is_running"])
        self.assertIn("ecosystem_healthy", health)
        self.assertIn("components", health)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_version_detection(self):
        """Test configuration version detection."""
        # Test v1 Claude settings
        v1_config = {"permissions": {"allow": ["test"]}}
        version = ConfigVersionDetection.detect_version(v1_config, "settings.json")
        self.assertEqual(version, "1.0.0")

        # Test v2 Claude settings
        v2_config = {
            "permissions": {"allow": ["test"]},
            "hooks": {"SessionStart": []},
            "verification_workflow": {"enabled": True},
        }
        version = ConfigVersionDetection.detect_version(v2_config, "settings.json")
        self.assertEqual(version, "2.0.0")

        # Test explicit version
        explicit_config = {"version": "3.1.0", "permissions": {"allow": ["test"]}}
        version = ConfigVersionDetection.detect_version(
            explicit_config, "settings.json"
        )
        self.assertEqual(version, "3.1.0")

    def test_format_detection(self):
        """Test configuration format detection."""
        self.assertEqual(ConfigVersionDetection.detect_format("config.json"), "json")
        self.assertEqual(ConfigVersionDetection.detect_format("config.yaml"), "yaml")
        self.assertEqual(ConfigVersionDetection.detect_format("config.yml"), "yaml")
        self.assertEqual(ConfigVersionDetection.detect_format("config.toml"), "toml")
        self.assertEqual(
            ConfigVersionDetection.detect_format("config.unknown"), "unknown"
        )

    def test_claude_settings_migration(self):
        """Test Claude settings migration from v1 to v2."""
        migration = ClaudeSettingsMigrationV1ToV2()

        v1_config = {
            "permissions": {"allow": ["test"]},
            "env": {"VERIFICATION_WORKFLOW_ENABLED": "true"},
        }

        self.assertTrue(migration.can_migrate(v1_config))

        migrated = migration.migrate(v1_config)

        # Check for new sections
        self.assertIn("verification_workflow", migrated)
        self.assertIn("hooks", migrated)
        self.assertIn("anti_deception", migrated)

        # Check migration logic
        self.assertTrue(migrated["verification_workflow"]["enabled"])

    def test_legacy_config_wrapper(self):
        """Test legacy configuration wrapper."""
        # Create test config file
        test_config = {"legacy_key": "legacy_value"}
        config_file = os.path.join(self.temp_dir, "legacy_config.json")
        with open(config_file, "w") as f:
            json.dump(test_config, f)

        # Create wrapper
        def legacy_loader():
            with open(config_file) as f:
                return json.load(f)

        wrapper = LegacyConfigWrapper(config_file, legacy_loader)

        # Test loading
        loaded = wrapper.load()
        self.assertEqual(loaded, test_config)

    def test_compatibility_transformations(self):
        """Test backward compatibility transformations."""
        from src.csf_nip.config.backward_compatibility import LegacyConfigurationLoader

        # Mock hot-reload system
        mock_hot_reload = Mock()
        mock_hot_reload.config_cache = {}

        loader = LegacyConfigurationLoader(mock_hot_reload)

        # Test Claude settings compatibility
        v1_config = {"permissions": {"allow": ["test"]}}
        compatible = loader._ensure_claude_settings_compatibility(v1_config, "1.0.0")

        self.assertIn("verification_workflow", compatible)
        self.assertIn("hooks", compatible)
        self.assertIn("anti_deception", compatible)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete hot-reload system."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_full_hot_reload_workflow(self):
        """Test complete hot-reload workflow from file change to notification."""
        # Create initial config
        initial_config = {
            "permissions": {"allow": ["Bash(test)"]},
            "verification_workflow": {"enabled": False},
        }
        config_file = os.path.join(self.temp_dir, "integration_test.json")
        with open(config_file, "w") as f:
            json.dump(initial_config, f)

        # Setup hot-reload system
        events_received = []

        def event_listener(event):
            events_received.append(event)

        hot_reload = HotReloadSystem([self.temp_dir], debounce_delay=0.1)
        hot_reload.add_event_listener(event_listener)

        try:
            hot_reload.start()

            # Load initial config
            hot_reload.reload_config(config_file)

            # Modify config file
            updated_config = {
                "permissions": {"allow": ["Bash(test)", "Bash(new_test)"]},
                "verification_workflow": {"enabled": True},
            }
            with open(config_file, "w") as f:
                json.dump(updated_config, f)

            # Wait for file watching and debouncing
            time.sleep(0.5)

            # Verify change was detected and processed
            self.assertTrue(len(events_received) > 0)

            # Verify updated config is loaded
            loaded = hot_reload.get_config(config_file)
            self.assertTrue(loaded["verification_workflow"]["enabled"])
            self.assertIn("Bash(new_test)", loaded["permissions"]["allow"])

        finally:
            hot_reload.stop()

    def test_ecosystem_integration(self):
        """Test ecosystem manager integration with hot-reload system."""
        # Create ecosystem config
        ecosystem_config = {
            "ecosystem": {
                "name": "Integration Test",
                "version": "1.0.0",
                "environment": "development",
            },
            "hot_reload": {"enabled": True, "config_directories": [self.temp_dir]},
            "components": {
                "claude": {
                    "enabled": True,
                    "config_file": "claude_settings.json",
                    "hot_reload_enabled": True,
                    "restart_required": False,
                }
            },
        }

        ecosystem_file = os.path.join(self.temp_dir, "ecosystem.json")
        with open(ecosystem_file, "w") as f:
            json.dump(ecosystem_config, f)

        # Create component config
        component_config = {
            "permissions": {"allow": ["Bash(integration_test)"]},
            "verification_workflow": {"enabled": False},
        }
        component_file = os.path.join(self.temp_dir, "claude_settings.json")
        with open(component_file, "w") as f:
            json.dump(component_config, f)

        # Start ecosystem manager
        manager = EcosystemHotReloadManager(ecosystem_file)

        try:
            manager.start()

            # Verify ecosystem state
            state = manager.get_ecosystem_state()
            self.assertIsNotNone(state)
            self.assertIn("claude", state.components)

            # Test component config access
            loaded = manager.get_component_config("claude")
            self.assertIsNotNone(loaded)
            self.assertEqual(
                loaded["permissions"]["allow"][0], "Bash(integration_test)"
            )

            # Test health status
            health = manager.get_health_status()
            self.assertTrue(health["is_running"])
            self.assertTrue(health["ecosystem_healthy"])

        finally:
            manager.stop()


if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)
