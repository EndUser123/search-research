"""Compatibility loader for cc-aca-epistemic plugin wrapper delegation.

Wrappers in P:/.claude/hooks/ delegate to plugin hooks via this module.
Two delegation styles share one path resolver (resolve_plugin_hook):

- delegate():    subprocess style — runpy the plugin hook as __main__ (reads stdin).
                 Used by the ~22 stub wrappers.
- load_module(): in-process style — import the plugin hook and return the module so
                 a wrapper can re-export symbols, e.g.
                     run = load_module(__file__).run
                 Used by StopHook_cross_validator.py, which Stop.py imports directly
                 (`from StopHook_cross_validator import run`). Does NOT run __main__.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

# Wrapper filename prefix -> plugin hooks/<dir>/ subdirectory.
_EVENT_DIRS: dict[str, str] = {
    "StopHook_": "stop",
    "PreToolUse_": "pretool",
    "PostToolUse_": "posttool",
    "UserPromptSubmit_": "userpromptsubmit",
}


def resolve_plugin_hook(wrapper_path: str) -> Path:
    """Map a wrapper filename to its plugin hook path.

    StopHook_cross_validator.py -> <plugin>/hooks/stop/StopHook_cross_validator.py

    The path is *derived* from the wrapper filename and this module's location, so a
    plugin move/rename updates one place — not a hardcoded absolute path per wrapper.
    """
    wrapper_name = Path(wrapper_path).name
    plugin_root = Path(__file__).resolve().parent.parent

    for prefix, event_dir in _EVENT_DIRS.items():
        if wrapper_name.startswith(prefix):
            hook_path = plugin_root / "hooks" / event_dir / wrapper_name
            if not hook_path.exists():
                raise ImportError(
                    f"Plugin hook not found: {hook_path} (wrapper: {wrapper_path})"
                )
            return hook_path

    raise ImportError(f"Unknown wrapper type: {wrapper_name}")


def load_module(wrapper_path: str) -> ModuleType:
    """Import the corresponding plugin hook in-process and return the module.

    Use when a wrapper must re-export symbols for in-process callers. Loads the hook
    as a normal module (not __main__), so its `if __name__ == "__main__":` stdin path
    does not run at import time.
    """
    hook_path = resolve_plugin_hook(wrapper_path)
    mod_name = f"cc_aca_epistemic_{hook_path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, hook_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to build import spec for {hook_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def delegate(wrapper_path: str) -> None:
    """Load and execute the corresponding plugin hook as a script (__main__)."""
    import runpy

    hook_path = resolve_plugin_hook(wrapper_path)
    runpy.run_path(str(hook_path), run_name="__main__")
