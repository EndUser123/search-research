#!/usr/bin/env python3
"""Compatibility wrapper — delegates to cc-aca-session plugin.
Source of truth: P:/packages/cc-aca-session/hooks/precompact/aca_session_precompact.py
"""
import sys
from pathlib import Path

_PLUGIN_ROOT = Path("P:/packages/cc-aca-session")
sys.path.insert(0, str(_PLUGIN_ROOT))

from hooks.precompact.aca_session_precompact import main

if __name__ == "__main__":
    main()
