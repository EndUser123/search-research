"""Plugin bootstrap -- call bootstrap(__file__) from any hook to set up sys.path.

Replaces per-hook path boilerplate. Single point of change for path resolution logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_LIB = PLUGIN_ROOT / "__lib"


def bootstrap(hook_file: str | Path) -> Path:
    """Set up sys.path for a plugin hook. Returns the resolved hooks dir."""
    # Plugin's own __lib/
    if str(PLUGIN_LIB) not in sys.path:
        sys.path.insert(0, str(PLUGIN_LIB))

    # Global hooks dir for shared __lib__ access
    from hooks_resolver import get_hooks_dir
    hooks_dir = get_hooks_dir()
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    hooks_lib = hooks_dir / "__lib"
    if str(hooks_lib) not in sys.path:
        sys.path.insert(0, str(hooks_lib))

    return hooks_dir


def state_root() -> Path:
    """External state dir for this plugin; never inside source/cache."""
    import os
    base = os.environ.get("CSF_STATE_DIR") or str(Path("P:/") / ".claude" / "state")
    return Path(base) / "cc-aca-investigation"
