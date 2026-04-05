import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test the ConfigManager
from dnld_telegram.config.config_manager import ConfigManager

# Create a ConfigManager instance and check what config file it's looking for
config = ConfigManager()
print(f"Config file path: {config._config_path}")
print(
    f"Config file exists: {os.path.exists(config._config_path) if config._config_path else 'No path set'}"
)

# Try to get API credentials
api_id = config.get("telegram.api_id")
api_hash = config.get("telegram.api_hash")
session_string = config.get("telegram.session_string")

print(f"API ID: {api_id}")
print(f"API Hash: {api_hash}")
print(f"Session String: {session_string}")
