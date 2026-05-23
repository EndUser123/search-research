#!/usr/bin/env python3
"""Compatibility wrapper — delegates to cc-aca-session plugin.
Source of truth: P:/packages/cc-aca-session/hooks/sessionend/aca_session_tdd_cleanup.py
"""
import sys
from pathlib import Path

_PLUGIN_ROOT = Path("P:/packages/cc-aca-session")
sys.path.insert(0, str(_PLUGIN_ROOT))

from hooks.sessionend.aca_session_tdd_cleanup import main

if __name__ == "__main__":
    main()
