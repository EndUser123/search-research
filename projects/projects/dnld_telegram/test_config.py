import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dnld_telegram.config.manager import get_config_manager

# Test the config manager
config_dir = Path(__file__).parent / "config"
print(f"Config directory: {config_dir}")
print(f"Config directory exists: {config_dir.exists()}")

if config_dir.exists():
    config_manager = get_config_manager(config_dir)
    channels_config = config_manager.get_channels_config()
    print(f"Channels config: {channels_config}")
    enabled_channels = channels_config.get_enabled_channels()
    print(f"Enabled channels: {enabled_channels}")
