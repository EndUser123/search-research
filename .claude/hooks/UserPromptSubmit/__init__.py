"""Compatibility package for legacy ``UserPromptSubmit.*`` imports.

The active implementation lives under ``UserPromptSubmit_modules``. Some tests
and older hook code still import from ``UserPromptSubmit`` as if it were a real
package, so expose the same package path and module object semantics here.
"""

from __future__ import annotations

import importlib
import sys

import UserPromptSubmit_modules as _modules

__path__ = list(getattr(_modules, "__path__", []))
__all__ = getattr(_modules, "__all__", [])

# Ensure both package names resolve to the same root module object when possible.
sys.modules.setdefault("UserPromptSubmit_modules", _modules)

# Keep legacy submodule imports bound to the active implementation modules so
# patching/imports through either package name hit the same module object.
for _name in __all__:
    try:
        _module = importlib.import_module(f"UserPromptSubmit_modules.{_name}")
    except Exception:
        continue
    sys.modules[f"UserPromptSubmit.{_name}"] = _module
