from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop_router  # type: ignore


def test_active_runtime_hooks_resolve_to_real_files() -> None:
    missing: list[str] = []
    for hook_name in Stop_router.ACTIVE_RUNTIME_HOOKS:
        hook_path = Stop_router._resolve_hook_path(hook_name)
        if not hook_path.exists():
            missing.append(f"{hook_name} -> {hook_path}")

    assert missing == []
