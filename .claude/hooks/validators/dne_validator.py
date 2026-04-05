"""
DNE Validator - Validates DUF-NSE output structure
"""
import sys
from pathlib import Path

# Add validators directory to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core_validator import validate_file  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dne_validator.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    sys.exit(validate_file(filepath, "dne"))
