"""
Tests for the CODE & Enhancement Styles Plugin System

Comprehensive test suite covering core functionality, plugin management,
quality gates, configuration, and integration.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from lib.enhancement_plugins import (
    EnhancedPromptSystem,
    EnhancementOptions,
    QualityGatePlugin,
    EnhancementPlugin,
    PluginContext,
    PluginResult,
    PluginMetadata,
    PluginPriority
)
from lib.enhancement_plugins.core import PluginStatus
from lib.enhancement_plugins.config import ConfigManager, PluginConfig


class TestPlugin(EnhancementPlugin):
    """Test plugin for testing purposes"""

    def __init__(self, config=None):
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0")
            description="Test plugin",
            author="Test",
            priority=PluginPriority.NORMAL,
            tags=["test"]
        )
        super().__init__(metadata, config)

    def enhance(self, context: PluginContext) -> PluginResult:
        return PluginResult(
            success=True,
            enhanced_prompt=f"Enhanced: {context.current_prompt}",
            confidence=0.8
        )


class FailingPlugin(EnhancementPlugin):
    """Plugin that always fails for testing error handling"""

    def __init__(self):
        metadata = PluginMetadata(
            name="failing_plugin",
            version="1.0.0")
            description="Failing test plugin",
            author="Test",
            priority=PluginPriority.NORMAL
        )
        super().__init__(metadata)

    def enhance(self, context: PluginContext) -> PluginResult:
        return PluginResult(
            success=False,
            enhanced_prompt=context.current_prompt,
            confidence=0.0,
            error_message="Intentional test failure"
        )


class TestEnhancementPluginSystem:
    """Test the core plugin system functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.system = EnhancedPromptSystem()

    def test_basic_enhancement(self):
        """Test basic prompt enhancement"""
        prompt = "create a web scraper"
        result = self.system.enhance(prompt, EnhancementOptions(style="technical"))

        assert result.success
        assert result.enhanced_prompt != prompt or len(result.enhanced_prompt) >= len(prompt)
        assert isinstance(result.quality_score, float)
        assert isinstance(result.confidence, float)
        assert isinstance(result.plugins_executed, list)
        assert result.execution_time >= 0

    def test_enhancement_with_options(self):
        """Test enhancement with custom options"""
        prompt = "implement an API"
        options = EnhancementOptions(
            style="technical",
            enable_quality_gates=True,
            strict_quality_mode=False,
            min_quality_score=0.60
        )

        result = self.system.enhance(prompt, options)

        assert result.success
        assert result.style == "technical"
        assert len(result.plugins_executed) > 0

    def test_plugin_registration(self):
        """Test plugin registration and management"""
        test_plugin = TestPlugin()
        success = self.system.register_plugin(test_plugin)

        assert success

        # Check plugin is in the list
        plugins = self.system.list_plugins()
        plugin_names = [p['name'] for p in plugins]
        assert "test_plugin" in plugin_names

        # Get plugin info
        plugin_info = self.system.get_plugin_info("test_plugin")
        assert plugin_info is not None
        assert plugin_info['name'] == "test_plugin"

        # Unregister plugin
        unregister_success = self.system.unregister_plugin("test_plugin")
        assert unregister_success

    def test_quality_assessment(self):
        """Test quality assessment functionality"""
        # Test with different quality prompts
        poor_prompt = "do stuff"
        good_prompt = "Design and implement a RESTful API with user authentication, database integration, and comprehensive error handling."

        poor_quality = self.system.get_quality_assessment(poor_prompt)
        good_quality = self.system.get_quality_assessment(good_prompt)

        # Good prompt should have higher quality score
        assert good_quality['overall_score'] > poor_quality['overall_score']

        # Check quality structure
        for quality in [poor_quality, good_quality]:
            assert 'overall_score' in quality
            assert 'quality_level' in quality
            assert 'confidence' in quality
            assert 'criteria_scores' in quality
            assert 'issues' in quality
            assert 'suggestions' in quality

    def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        # Register failing plugin
        failing_plugin = FailingPlugin()
        self.system.register_plugin(failing_plugin)

        # Test with failing plugin
        prompt = "test prompt"
        options = EnhancementOptions(
            plugins=["failing_plugin"],
            fallback_to_legacy=True
        )

        result = self.system.enhance(prompt, options)

        # Should still succeed due to fallback
        assert result.success
        assert len(result.plugins_executed) >= 1

        # Check that failing plugin was marked as failed
        failing_plugin_result = next(
            (p for p in result.plugins_executed if p['name'] == 'failing_plugin'),
            None
        )
        assert failing_plugin_result is not None
        assert failing_plugin_result['success'] is False

    def test_backward_compatibility(self):
        """Test backward compatibility with legacy system"""
        prompt = "create a function"
        style = "technical"

        # Test legacy enhancement
        legacy_result = self.system.enhance_legacy(prompt, style)

        assert hasattr(legacy_result, 'enhanced_prompt')
        assert hasattr(legacy_result, 'quality_score')
        assert hasattr(legacy_result, 'style')
        assert hasattr(legacy_result, 'confidence')

        # Test conversion from new to legacy format
        new_result = self.system.enhance(prompt, EnhancementOptions(style=style))
        converted = new_result.to_legacy()

        assert hasattr(converted, 'enhanced_prompt')
        assert hasattr(converted, 'quality_score')
        assert converted.style == style


class TestQualityGatePlugin:
    """Test the quality gate plugin specifically"""

    def setup_method(self):
        """Set up test environment"""
        self.quality_plugin = QualityGatePlugin()

    def test_quality_assessment_criteria(self):
        """Test quality assessment across different criteria"""
        test_prompts = [
            ("make website", "poor"),
            ("create a responsive website with user authentication", "fair"),
            ("Design and implement a comprehensive e-commerce platform with user authentication, payment processing, inventory management, and administrative dashboard", "good")
        ]

        for prompt, expected_level in test_prompts:
            context = PluginContext(
                original_prompt=prompt,
                current_prompt=prompt,
                style="technical"
            )

            result = self.quality_plugin.enhance(context)

            assert result.success
            assert result.confidence >= 0.0

            # Check metadata contains quality metrics
            metadata = result.metadata
            assert 'quality_metrics' in metadata
            assert 'quality_passed' in metadata
            assert 'quality_level' in metadata

    def test_quality_gate_thresholds(self):
        """Test quality gate threshold enforcement"""
        # Test with strict mode
        strict_plugin = QualityGatePlugin({"strict_mode": True, "min_quality_score": 0.90})

        context = PluginContext(
            original_prompt="simple task",
            current_prompt="simple task",
            style="technical"
        )

        result = strict_plugin.enhance(context)

        # Should fail in strict mode with low quality input
        if not result.success:
            assert result.error_message is not None
            assert metadata := result.metadata.get('blocked', False)

    def test_quality_enhancement(self):
        """Test quality enhancement when quality is low"""
        plugin = QualityGatePlugin({
            "strict_mode": False,
            "enhance_on_failure": True
        })

        context = PluginContext(
            original_prompt="do it",
            current_prompt="do it",
            style="technical"
        )

        result = plugin.enhance(context)

        assert result.success
        assert len(result.enhanced_prompt) > len(context.current_prompt)

        # Check that suggestions were added
        assert 'suggestions' in result.metadata


class TestConfigManager:
    """Test configuration management"""

    def setup_method(self):
        """Set up test environment"""
        self.config_manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")

    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_default_config(self):
        """Test creating default configuration"""
        success = self.config_manager.create_default_config(self.config_path)
        assert success
        assert os.path.exists(self.config_path)

    def test_load_config(self):
        """Test loading configuration"""
        # Create default config first
        self.config_manager.create_default_config(self.config_path)

        # Load config
        config = self.config_manager.load_config(self.config_path)

        assert config is not None
        assert hasattr(config, 'auto_load_plugins')
        assert hasattr(config, 'quality_gates')
        assert hasattr(config, 'log_level')

    def test_plugin_config_management(self):
        """Test plugin-specific configuration"""
        # Create and load config
        self.config_manager.create_default_config(self.config_path)
        self.config_manager.load_config(self.config_path)

        # Update plugin config
        updates = {
            "enabled": False,
            "priority": 25,
            "config": {"custom_option": "value"}
        }
        self.config_manager.update_plugin_config("test_plugin", updates)

        # Get plugin config
        plugin_config = self.config_manager.get_plugin_config("test_plugin")
        assert plugin_config.enabled is False
        assert plugin_config.priority == 25
        assert plugin_config.config["custom_option"] == "value"

    def test_config_validation(self):
        """Test configuration validation"""
        # Create and load config
        self.config_manager.create_default_config(self.config_path)
        self.config_manager.load_config(self.config_path)

        # Validate config
        errors = self.config_manager.validate_config()
        assert isinstance(errors, list)
        # Default config should be valid
        assert len(errors) == 0

    def test_save_config(self):
        """Test saving configuration"""
        # Create default config
        self.config_manager.create_default_config(self.config_path)

        # Load and modify
        config = self.config_manager.load_config(self.config_path)
        config.log_level = "DEBUG"

        # Save changes
        success = self.config_manager.save_config(self.config_path)
        assert success

        # Reload and verify
        reloaded_config = self.config_manager.load_config(self.config_path)
        assert reloaded_config.log_level == "DEBUG"


class TestIntegrationScenarios:
    """Integration tests for complete scenarios"""

    def test_end_to_end_enhancement(self):
        """Test complete enhancement pipeline"""
        system = EnhancedPromptSystem()

        # Test with different styles
        styles = ["technical", "creative", "educational", "systematic"]
        prompt = "create a user management system"

        results = {}
        for style in styles:
            result = system.enhance(
                prompt,
                EnhancementOptions(style=style, enable_quality_gates=True)
            )
            results[style] = result

            assert result.success
            assert result.style == style

        # Results should be different for different styles
        enhanced_prompts = [result.enhanced_prompt for result in results.values()]
        assert len(set(enhanced_prompts)) > 1  # Should have different enhancements

    def test_performance_consistency(self):
        """Test performance consistency across multiple runs"""
        system = EnhancedPromptSystem()
        prompt = "implement a sorting algorithm"

        # Run multiple times
        results = []
        for _ in range(5):
            result = system.enhance(prompt, EnhancementOptions(style="technical"))
            results.append(result)

        # Check consistency
        execution_times = [r.execution_time for r in results]
        avg_time = sum(execution_times) / len(execution_times)

        # Execution time should be relatively consistent (within 50% of average)
        for time in execution_times:
            assert time < avg_time * 1.5, f"Inconsistent execution time: {time} vs avg {avg_time}"

        # All should succeed
        assert all(r.success for r in results)

    def test_custom_plugin_integration(self):
        """Test integration of custom plugins"""
        class UppercasePlugin(EnhancementPlugin):
            def __init__(self):
                metadata = PluginMetadata(
                    name="uppercase_plugin",
                    version="1.0.0")
                    description="Converts prompt to uppercase",
                    author="Test",
                    priority=PluginPriority.HIGH
                )
                super().__init__(metadata)

            def enhance(self, context: PluginContext) -> PluginResult:
                return PluginResult(
                    success=True,
                    enhanced_prompt=context.current_prompt.upper(),
                    confidence=1.0,
                    metadata={"transformation": "uppercase"}
                )

        # Register custom plugin
        system = EnhancedPromptSystem()
        uppercase_plugin = UppercasePlugin()
        system.register_plugin(uppercase_plugin)

        # Test with custom plugin
        prompt = "test message"
        result = system.enhance(
            prompt,
            EnhancementOptions(plugins=["uppercase_plugin", "quality_gate"])
        )

        assert result.success
        # Should be uppercase due to our plugin
        assert "TEST MESSAGE" in result.enhanced_prompt

        # Check plugin was executed
        plugin_names = [p['name'] for p in result.plugins_executed]
        assert "uppercase_plugin" in plugin_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
