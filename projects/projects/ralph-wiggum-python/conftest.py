# TDD Guard Pytest Reporter integration
# Registers the tdd_guard_reporter plugin with pytest

try:
    from tdd_guard_reporter import pytest_configure, pytest_addoption
    # Export the hooks
    __all__ = ['pytest_configure', 'pytest_addoption']
except ImportError:
    # If not found, that's okay - it's optional
    pass
