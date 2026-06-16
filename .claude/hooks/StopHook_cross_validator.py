#!/usr/bin/env python3
"""Delegates to cc-aca-epistemic plugin. Exposes run() for in-process callers.

Loaded by Stop.py via `from StopHook_cross_validator import run as cross_validate`.
The shim is also a registered in Stop.py's in-process gate pipeline; standalone
script invocation (the old hook_runner.py path) is no longer wired in settings.
"""
import importlib.util
import sys
from pathlib import Path

_PLUGIN_HOOK = Path(
    "P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py"
)
_spec = importlib.util.spec_from_file_location(
    "cc_aca_epistemic_cross_validator", _PLUGIN_HOOK
)
assert _spec is not None and _spec.loader is not None, (
    f"Failed to build import spec for {_PLUGIN_HOOK}"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

run = _mod.run  # re-export for `from StopHook_cross_validator import run`
