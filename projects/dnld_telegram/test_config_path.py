import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test the ConfigManager
from dnld_telegram.config.config_manager import ConfigManager

# Create a ConfigManager instance and check what config file it's looking for
config = ConfigManager()
print(f"Config file path that would be used: {config._config_path}")

# Try to manually calculate the expected path
current_file = Path(__file__).resolve()
print(f"Current file: {current_file}")

# The ConfigManager is in src/dnld_telegram/config/config_manager.py
# We want to get to the project root to find config.toml
config_manager_path = (
    Path(__file__).parent / "src" / "dnld_telegram" / "config" / "config_manager.py"
)
print(f"ConfigManager path: {config_manager_path}")

# Calculate the path resolution as done in the ConfigManager
project_root_from_config = os.path.join(
    os.path.dirname(str(config_manager_path)), "..", "..", ".."
)
resolved_path = os.path.join(project_root_from_config, "config.toml")
print(f"ConfigManager resolution path: {resolved_path}")
print(f"ConfigManager resolution path exists: {os.path.exists(resolved_path)}")

# The actual config.toml path
actual_config_path = Path(__file__).parent / "config.toml"
print(f"Actual config.toml path: {actual_config_path}")
print(f"Actual config.toml exists: {actual_config_path.exists()}")

# Try to resolve the path
resolved_path_obj = Path(resolved_path).resolve()
actual_path_obj = actual_config_path.resolve()
print(f"Resolved path object: {resolved_path_obj}")
print(f"Actual path object: {actual_path_obj}")
print(f"Paths are equal: {resolved_path_obj == actual_path_obj}")
