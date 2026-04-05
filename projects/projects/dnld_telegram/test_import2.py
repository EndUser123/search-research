import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("Python path:")
for p in sys.path:
    print(f"  {p}")

try:
    from dnld_telegram.config.config_manager import ConfigManager

    print("Successfully imported ConfigManager")

    # Test the config manager without explicit path
    cm = ConfigManager()
    api_id = cm.get("telegram.api_id")
    api_hash = cm.get("telegram.api_hash")
    session_string = cm.get("telegram.session_string")

    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash}")
    print(f"Session String length: {len(session_string) if session_string else 0}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
