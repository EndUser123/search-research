import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    # Try to import and test the new configuration system first
    from dnld_telegram.config.integration import get_channels

    channels = get_channels()
    print("Loaded channels from new configuration system:")
    for name, chat_id in list(channels.items())[:5]:  # Show first 5 channels
        print(f"  {name}: {chat_id}")
    print(f"  ... and {len(channels) - 5} more channels")

except ImportError as e:
    print(f"Could not import from new configuration system: {e}")

    # Fall back to the legacy system
    try:
        from dnld_telegram.config.channels_toml_loader import load_telegram_channels

        channels = load_telegram_channels()
        print("Loaded channels from legacy TOML loader:")
        for name, chat_id in list(channels.items())[:5]:  # Show first 5 channels
            print(f"  {name}: {chat_id}")
        print(f"  ... and {len(channels) - 5} more channels")
    except Exception as e:
        print(f"Could not load channels from legacy TOML loader: {e}")

        # Final fallback to environment variables
        try:
            from dnld_telegram.download.config.settings import load_channels_from_env

            channels = load_channels_from_env()
            print("Loaded channels from environment variables:")
            for name, chat_id in list(channels.items())[:5]:  # Show first 5 channels
                print(f"  {name}: {chat_id}")
            print(f"  ... and {len(channels) - 5} more channels")
        except Exception as e:
            print(f"Could not load channels from environment variables: {e}")

print("Test completed.")
