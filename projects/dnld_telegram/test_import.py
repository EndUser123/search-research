import sys
from pathlib import Path

# Add the project root and src directory to the Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print("Python path:")
for p in sys.path:
    print(f"  {p}")

try:
    from dnld_telegram.download.__main__ import main as download_main

    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")

try:
    # Alternative import approach
    import dnld_telegram.download.__main__ as download_module

    print("Alternative import successful!")
except ImportError as e:
    print(f"Alternative import failed: {e}")
