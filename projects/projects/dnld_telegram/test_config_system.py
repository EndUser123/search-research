#!/usr/bin/env python3
"""
Test script for the optimal configuration system.

This script tests:
1. Configuration loading and validation
2. Hot reloading functionality
3. Environment variable overrides
4. Integration with legacy systems
"""

import asyncio
import time
from pathlib import Path


def test_basic_config_loading():
    """Test basic configuration loading."""
    print("🧪 Testing basic configuration loading...")

    try:
        from config.manager import get_config_manager

        config_manager = get_config_manager()
        app_config = config_manager.get_app_config()
        channels_config = config_manager.get_channels_config()

        print(f"✅ App config loaded: {app_config.name} v{app_config.version}")
        print(f"✅ Environment: {app_config.environment.value}")
        print(f"✅ Channels base: {app_config.paths.channels_base}")
        print(f"✅ Max concurrent: {app_config.download.max_concurrent}")
        print(f"✅ UI mode: {app_config.ui.default_mode.value}")

        enabled_channels = channels_config.get_enabled_channels()
        print(f"✅ Channels loaded: {len(enabled_channels)} enabled")
        for name, config in list(enabled_channels.items())[:3]:  # Show first 3
            print(f"   - {name}: {config.chat_id}")

        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False


def test_integration_layer():
    """Test the integration layer compatibility."""
    print("\n🧪 Testing integration layer...")

    try:
        from config.integration import get_channels, get_config_bridge

        # Test bridge
        bridge = get_config_bridge()
        channels_dict = bridge.get_channels_dict()
        base_path = bridge.get_channels_base_path()
        download_config = bridge.get_download_config()

        print(f"✅ Bridge working: {len(channels_dict)} channels")
        print(f"✅ Base path: {base_path}")
        print(f"✅ Max concurrent from bridge: {download_config['max_concurrent']}")

        # Test legacy compatibility functions
        legacy_channels = get_channels()
        print(f"✅ Legacy function: {len(legacy_channels)} channels")

        return True
    except Exception as e:
        print(f"❌ Integration layer failed: {e}")
        return False


def test_environment_overrides():
    """Test environment variable overrides."""
    print("\n🧪 Testing environment variable overrides...")

    import os

    # Set test environment variables
    os.environ["TELEGRAM_DOWNLOAD_MAX_CONCURRENT"] = "8"
    os.environ["TELEGRAM_UI_DEFAULT_MODE"] = "rich"
    os.environ["TELEGRAM_LOGGING_CONSOLE_LEVEL"] = "DEBUG"

    try:
        from config.manager import get_config_manager, reload_config

        # Reload to pick up environment changes
        reload_config()

        config_manager = get_config_manager()
        app_config = config_manager.get_app_config()

        max_concurrent = app_config.download.max_concurrent
        ui_mode = app_config.ui.default_mode.value
        log_level = app_config.logging.console_level.value

        print(f"✅ Max concurrent override: {max_concurrent} (should be 8)")
        print(f"✅ UI mode override: {ui_mode} (should be rich)")
        print(f"✅ Log level override: {log_level} (should be DEBUG)")

        # Clean up
        del os.environ["TELEGRAM_DOWNLOAD_MAX_CONCURRENT"]
        del os.environ["TELEGRAM_UI_DEFAULT_MODE"]
        del os.environ["TELEGRAM_LOGGING_CONSOLE_LEVEL"]

        return max_concurrent == 8 and ui_mode == "rich" and log_level == "DEBUG"
    except Exception as e:
        print(f"❌ Environment overrides failed: {e}")
        return False


def test_hot_reloading():
    """Test hot reloading functionality."""
    print("\n🧪 Testing hot reloading...")

    try:
        from config.manager import get_config_manager

        config_manager = get_config_manager()

        # Get initial config
        initial_config = config_manager.get_app_config()
        initial_max_concurrent = initial_config.download.max_concurrent

        print(f"Initial max_concurrent: {initial_max_concurrent}")

        # Modify config file
        app_config_file = Path("config/app.toml")
        if app_config_file.exists():
            # Read current content
            content = app_config_file.read_text()

            # Replace max_concurrent value
            new_value = 99 if initial_max_concurrent != 99 else 88
            modified_content = content.replace(
                f"max_concurrent = {initial_max_concurrent}",
                f"max_concurrent = {new_value}",
            )

            if modified_content != content:
                # Write modified content
                app_config_file.write_text(modified_content)

                print(f"Modified config file: max_concurrent -> {new_value}")

                # Wait for file watcher to trigger reload
                print("Waiting for hot reload...")
                time.sleep(2)

                # Check if config reloaded
                reloaded_config = config_manager.get_app_config()
                reloaded_max_concurrent = reloaded_config.download.max_concurrent

                print(f"After hot reload: {reloaded_max_concurrent}")

                # Restore original content
                app_config_file.write_text(content)
                time.sleep(1)  # Wait for restore to complete

                if reloaded_max_concurrent == new_value:
                    print("✅ Hot reloading works!")
                    return True
                else:
                    print("❌ Hot reloading failed - config not updated")
                    return False
            else:
                print("❌ Could not modify config file for hot reload test")
                return False
        else:
            print("❌ Config file not found for hot reload test")
            return False

    except Exception as e:
        print(f"❌ Hot reloading test failed: {e}")
        return False


def test_legacy_compatibility():
    """Test compatibility with legacy configuration systems."""
    print("\n🧪 Testing legacy compatibility...")

    try:
        # Test legacy path functions
        from src.download.config.paths import (
            get_channel_media_path,
            get_channel_path,
            get_channels_base_path,
            validate_channels_base_path,
        )

        base_path = get_channels_base_path()
        channel_path = get_channel_path("test_channel")
        media_path = get_channel_media_path("test_channel")
        is_valid = validate_channels_base_path()

        print(f"✅ Legacy paths work: base={base_path}")
        print(f"✅ Channel path: {channel_path}")
        print(f"✅ Media path: {media_path}")
        print(f"✅ Path validation: {is_valid}")

        # Test legacy settings functions
        from src.download.config.settings import get_channels

        channels = get_channels()
        print(f"✅ Legacy settings: {len(channels)} channels")

        return True
    except Exception as e:
        print(f"❌ Legacy compatibility failed: {e}")
        return False


async def test_configuration_summary():
    """Test configuration summary display."""
    print("\n🧪 Testing configuration summary...")

    try:
        from config.manager import get_config_manager

        config_manager = get_config_manager()
        summary = config_manager.get_effective_config_summary()

        print("Configuration Summary:")
        print(summary)
        print("✅ Configuration summary works!")

        return True
    except Exception as e:
        print(f"❌ Configuration summary failed: {e}")
        return False


async def run_all_tests():
    """Run all configuration system tests."""
    print("🚀 Starting optimal configuration system tests...\n")

    tests = [
        ("Basic Config Loading", test_basic_config_loading),
        ("Integration Layer", test_integration_layer),
        ("Environment Overrides", test_environment_overrides),
        ("Hot Reloading", test_hot_reloading),
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Configuration Summary", test_configuration_summary),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    print("\n📊 Test Results:")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print("=" * 50)
    print(f"Passed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("🎉 All tests passed! Optimal configuration system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

    return passed == len(results)


if __name__ == "__main__":
    # Change to project directory
    import os

    project_root = Path(__file__).parent
    os.chdir(project_root)

    asyncio.run(run_all_tests())
