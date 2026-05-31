#!/usr/bin/env python3
"""Compatibility wrapper -- delegates to cc-aca-authority UPS module."""
import importlib.util
import sys
from pathlib import Path

def _find_hook():
    paths = [
        Path("P:/packages/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py"),
        Path("P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py")
    ]
    for p in paths:
        if p.exists():
            return p
    raise ImportError("delegation_prospector.py not found in cc-aca-authority plugin")

_plugin_hook = _find_hook()
_lib = str(_plugin_hook.parent.parent.parent / "__lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("delegation_prospector", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export module-level names for UPS framework and tests
for _k, _v in vars(_mod).items():
    if _k not in ("__name__", "__file__", "__package__", "__loader__", "__spec__", "__doc__"):
        globals()[_k] = _v
