#!/usr/bin/env python3
"""
Test for the checkpoint helper function.
"""


def test_create_checkpoint_function_exists():
    """Test that the create_checkpoint function can be imported."""
    try:
        from src.utils.checkpoint_helper import create_checkpoint

        assert create_checkpoint is not None
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False


if __name__ == "__main__":
    result = test_create_checkpoint_function_exists()
    if result:
        print("Test passed!")
    else:
        print("Test failed!")
