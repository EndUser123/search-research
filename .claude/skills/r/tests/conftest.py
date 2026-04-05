"""Pytest configuration for /r skill tests."""

import sys
from pathlib import Path

# Add the skills directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
