#!/usr/bin/env python3
"""Delegates error_investigation_gate to cc-aca-investigation plugin."""
import importlib.util
import sys
from pathlib import Path

_plugin_hook = Path("P:/packages/cc-aca-investigation/hooks/userpromptsubmit/error_investigation_gate.py")
if not _plugin_hook.exists():
    raise ImportError(f"Plugin hook not found: {_plugin_hook}")

_lib = str(Path("P:/packages/cc-aca-investigation/__lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("error_investigation_gate", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export the register_hook decorator so UPS framework finds it
register_hook = _mod.register_hook
