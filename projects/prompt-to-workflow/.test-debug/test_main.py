import pytest
from main import main

def test_solution():
    result = main()
    assert result is not None
