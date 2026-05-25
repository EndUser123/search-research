#!/usr/bin/env python3
"""Compatibility wrapper -- delegates to cc-aca-authority UPS module."""
import importlib.util
import sys
from pathlib import Path

_plugin_hook = Path("P:/packages/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py")
if not _plugin_hook.exists():
    raise ImportError(f"Plugin hook not found: {_plugin_hook}")

_lib = str(Path("P:/packages/cc-aca-authority/__lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("delegation_prospector", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export module-level names for UPS framework
_g = {}
for _k, _v in vars(_mod).items():
    if not _k.startswith("_"):
        _g[_k] = _v
globals().update(_g)
