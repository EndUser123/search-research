#!/usr/bin/env python3
"""Delegates to cc-aca-epistemic plugin. Exposes run() for in-process callers.

Loaded by Stop.py via `from StopHook_cross_validator import run as cross_validate`.
Path resolution is shared with the subprocess stub wrappers
(compat_loader.resolve_plugin_hook), so a plugin move/rename updates one place
instead of a hardcoded absolute path here. Standalone script invocation (the old
hook_runner.py path) is no longer wired in settings.
"""
import sys

sys.path.insert(0, "P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib")
from compat_loader import load_module

# Re-export for `from StopHook_cross_validator import run`.
run = load_module(__file__).run
