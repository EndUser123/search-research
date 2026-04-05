#!/usr/bin/env python3
"""
Simple test for the checkpoint helper functionality.
"""

import os
import sys

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_checkpoint_helper_import():
    """Test that we can import the checkpoint helper."""
    try:
        print("SUCCESS: checkpoint_helper imported successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import checkpoint_helper: {e}")
        return False


if __name__ == "__main__":
    success = test_checkpoint_helper_import()
    if success:
        print("Test passed!")
    else:
        print("Test failed!")
