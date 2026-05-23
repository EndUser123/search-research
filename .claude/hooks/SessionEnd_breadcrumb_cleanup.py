#!/usr/bin/env python3
"""Compatibility wrapper — delegates to cc-aca-session plugin.
Source of truth: P:/packages/cc-aca-session/hooks/sessionend/aca_session_breadcrumb_cleanup.py
"""
import json
import sys
from pathlib import Path

_PLUGIN_ROOT = Path("P:/packages/cc-aca-session")
sys.path.insert(0, str(_PLUGIN_ROOT))

from hooks.sessionend.aca_session_breadcrumb_cleanup import run

if __name__ == "__main__":
    raw = sys.stdin.read().strip()
    data = json.loads(raw) if raw else {}
    result = run(data)
    print(json.dumps(result, indent=2))
