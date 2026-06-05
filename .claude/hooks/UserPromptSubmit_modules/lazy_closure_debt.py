#!/usr/bin/env python3
"""Compatibility wrapper -- delegates to cc-lazy-closure-debt UserPromptSubmit hook."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook


def _find_hook() -> Path:
    paths = [
        Path("P:/packages/.claude-marketplace/plugins/cc-lazy-closure-debt/hooks/userpromptsubmit/cc_lazy_closure_debt_UserPromptSubmit.py"),
    ]
    for p in paths:
        if p.exists():
            return p
    raise ImportError("cc_lazy_closure_debt_UserPromptSubmit.py not found in cc-lazy-closure-debt plugin")


_plugin_hook = _find_hook()
_lib = str(_plugin_hook.parent.parent.parent / "__lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("cc_lazy_closure_debt_UserPromptSubmit", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_mod)

# Re-export module-level names for direct callers and tests.
for _k, _v in vars(_mod).items():
    if _k not in ("__name__", "__file__", "__package__", "__loader__", "__spec__", "__doc__"):
        globals()[_k] = _v


@register_hook("lazy_closure_debt", priority=4.9)
def lazy_closure_debt(context: HookContext) -> HookResult:
    """Inject deduped debt context from the marketplace plugin."""
    result = _mod.run(context.data)
    hook_output = result.get("hookSpecificOutput") if isinstance(result, dict) else None
    additional = ""
    if isinstance(hook_output, dict):
        additional = str(hook_output.get("additionalContext", "") or "")
    if additional:
        return HookResult(context=additional, tokens=len(additional.split()), priority=4.9)
    return HookResult.empty()
