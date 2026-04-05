import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("Python path:")
for p in sys.path:
    print(f"  {p}")

try:
    print("Successfully imported download module")
except Exception as e:
    print(f"Error importing download module: {e}")
    import traceback

    traceback.print_exc()
