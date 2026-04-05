"""
Pytest configuration for all tests.

This ensures the module can be imported during testing.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
