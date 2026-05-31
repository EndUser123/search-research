#!/usr/bin/env python3
"""Compatibility wrapper -- delegates to cc-aca-reasoning plugin."""
import sys, json as _json
from pathlib import Path

def _plugin_root(plugin_name):
    installed = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    data = _json.loads(installed.read_text(encoding="utf-8"))
    entries = data.get("plugins", data).get(plugin_name + "@local", [])
    if not entries:
        raise RuntimeError(f"Plugin " + plugin_name + " not found in installed_plugins.json")
    return Path(entries[0]["installPath"])

_PLUGIN_ROOT = _plugin_root("cc-aca-reasoning")
sys.path.insert(0, str(_PLUGIN_ROOT / "__lib"))

from _bootstrap import bootstrap; _hd = bootstrap(__file__)

_hook = _PLUGIN_ROOT / "hooks" / "userpromptsubmit" / "sequential_thinking_semantic_client.py"

import importlib.util
_spec = importlib.util.spec_from_file_location("sequential_thinking_semantic_client", _hook)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})

if hasattr(_mod, "main"):
    _mod.main()
