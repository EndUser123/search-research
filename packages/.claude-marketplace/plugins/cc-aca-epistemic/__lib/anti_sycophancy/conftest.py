"""conftest.py — sys.path setup for anti_sycophancy test suite.

lazy_closure_detector imports from __lib.anti_lazy_policy, which lives in
P:/.claude/hooks/__lib/. That path must appear BEFORE the plugin root so
`from __lib.anti_lazy_policy` resolves to the global hooks __lib/, not the
plugin's own __lib/ package (which doesn't contain anti_lazy_policy).

Insert order (last insert = position 0 = highest priority):
  1. plugin root (so bare module names like lazy_closure_detector resolve)
  2. global hooks dir (so __lib.anti_lazy_policy resolves; ends up at pos 0)

Do NOT guard the global-hooks insert with `if p not in sys.path` — if it is
already somewhere further back in the path (put there by pytest.ini), it must
still be moved to position 0 to win over the plugin root.
"""
import sys
from pathlib import Path

# Plugin root — so bare `from lazy_closure_detector import ...` resolves.
_plugin_root = str(Path(__file__).resolve().parent.parent.parent)
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

# Global hooks dir — inserted at 0 unconditionally so __lib from hooks
# always wins over the plugin's own __lib/ package.
_global_hooks = "P:/.claude/hooks"
if _global_hooks in sys.path:
    sys.path.remove(_global_hooks)
sys.path.insert(0, _global_hooks)
# Evict any stale __lib cached from the plugin root.
sys.modules.pop("__lib", None)
