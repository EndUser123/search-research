import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test the integration module
from dnld_telegram.config.integration import ConfigurationBridge

# Create a bridge instance and check what config directory it's using
bridge = ConfigurationBridge()
print(f"Config manager config directory: {bridge._config_manager.config_dir}")

# Try to load channels
channels = bridge.get_channels_dict()
print(f"Loaded channels: {len(channels)}")
