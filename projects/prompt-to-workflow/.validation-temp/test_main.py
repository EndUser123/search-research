import pytest
from main import main

def test_main_exists():
    """Test that main function exists and is callable."""
    assert callable(main), "main should be a callable function"
