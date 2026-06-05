#!/usr/bin/env python3
"""Compatibility wrapper -- delegates to cc-lazy-closure-debt Stop hook."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _find_hook() -> Path:
    paths = [
        Path("P:/packages/.claude-marketplace/plugins/cc-lazy-closure-debt/hooks/stop/cc_lazy_closure_debt_Stop.py"),
    ]
    for p in paths:
        if p.exists():
            return p
    raise ImportError("cc_lazy_closure_debt_Stop.py not found in cc-lazy-closure-debt plugin")


_plugin_hook = _find_hook()
_lib = str(_plugin_hook.parent.parent.parent / "__lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("cc_lazy_closure_debt_Stop", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_mod)

# Re-export module-level names for direct callers.
for _k, _v in vars(_mod).items():
    if _k not in ("__name__", "__file__", "__package__", "__loader__", "__spec__", "__doc__"):
        globals()[_k] = _v

# Local alias used by Stop.py.
record_at_stop = _mod.run
