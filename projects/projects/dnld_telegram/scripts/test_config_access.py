#!/usr/bin/env python3
"""
Quick configuration access test for dnld_telegram.
This verifies that channel configurations can be properly accessed.
"""

from pathlib import Path

import toml


def test_config_access():
    """Test that channel configurations can be accessed properly."""
    try:
        # Load the main config file
        config_path = Path("config.toml")
        if not config_path.exists():
            print("❌ config.toml not found!")
            return False

        with open(config_path) as f:
            config = toml.load(f)

        # Check required sections
        if "telegram" not in config:
            print("❌ Missing 'telegram' section in config")
            return False

        if "channels" not in config:
            print("❌ Missing 'channels' section in config")
            return False

        channels = config["channels"]
        print(f"✅ Found {len(channels)} channels in config:")

        # Show first few channels as examples
        for i, (name, telegram_id) in enumerate(list(channels.items())[:5]):
            print(f"   {i+1}. {name}: {telegram_id}")

        if len(channels) > 5:
            print(f"   ... and {len(channels) - 5} more channels")

        # Verify a specific problematic channel
        test_channels = ["jcexclusive", "koreannarchive", "leaksasian"]
        for channel in test_channels:
            if channel in channels:
                print(
                    f"✅ Channel '{channel}' found with telegram_id: {channels[channel]}"
                )
            else:
                print(f"❌ Channel '{channel}' NOT found in config!")

        return True

    except Exception as e:
        print(f"❌ Configuration access test failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Testing dnld_telegram configuration access...")
    if test_config_access():
        print("\n✅ Configuration access test PASSED")
        print("💡 You can now run the maintenance script safely")
    else:
        print("\n❌ Configuration access test FAILED")
        print("🚨 Check your config.toml file and paths")
