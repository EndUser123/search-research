#!/usr/bin/env python3
"""
Tests for TDD DISCOVER gate enforcement.

DISABLED: pretooluse_tdd_gate module was removed/renamed.
This test file is preserved for reference but tests are skipped.
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))


@pytest.mark.skip(reason="pretooluse_tdd_gate module removed - test needs update for current TDD architecture (tdd95)")
class TestDiscoverGate:
    """
    Test suite for DISCOVER phase enforcement - DISABLED.

    NOTE: pretooluse_tdd_gate module was removed during TDD-95 migration.
    To re-enable: Update tests to use current TDD architecture (tdd95_core.py).
    """
    pass
