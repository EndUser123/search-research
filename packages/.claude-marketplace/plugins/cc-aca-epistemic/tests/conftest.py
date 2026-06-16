"""Shared fixtures for cc-aca-epistemic plugin tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_LIB = PLUGIN_ROOT / "__lib"
GLOBAL_HOOKS_DIR = Path("P:/.claude/hooks")
GLOBAL_HOOKS_LIB = GLOBAL_HOOKS_DIR / "__lib__"

# Paths that plugin modules and hooks need on sys.path at import time.
# Added once at session start and kept for the session lifetime.
_REQUIRED_PATHS = [str(PLUGIN_LIB), str(GLOBAL_HOOKS_LIB), str(GLOBAL_HOOKS_DIR)]


def pytest_configure(config: pytest.Config) -> None:
    """Add plugin lib/ and global hooks __lib__/ to sys.path once."""
    for p in _REQUIRED_PATHS:
        if p not in sys.path:
            sys.path.insert(0, p)
