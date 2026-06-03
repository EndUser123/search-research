"""Shared import-health check for top-level hook dispatchers.

Single source of truth for *which* files are the hot-path dispatchers and
*how* to verify they still import. Imported by both:
  - tests/test_hook_import_health.py  (pytest-level coverage)
  - PostToolUse_hook_import_health.py  (in-session advisory gate)

Keeping the list in one place prevents the drift class of bug this whole
check exists to catch: a dispatcher silently dropping out of coverage
because two copies of the list disagreed.

Background (2026-06): breadcrumb_tracker_hook.py hardcoded a path to a
plugin that moved during the marketplace migration, so `import skill_guard`
failed and PostToolUse logged the same traceback 350 times across a day —
a non-blocking error on *every* tool call. Importing a dispatcher
transitively loads its sub-hook package, so an import check on the four
dispatchers catches that entire class.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

# P:/.claude/hooks — this module lives in __lib/ one level down.
HOOKS_DIR = Path(__file__).resolve().parent.parent

# Top-level dispatchers. Every tool call / prompt / stop routes through one
# of these, so a broken import here fires a non-blocking hook error on EVERY
# such event until a human notices. Importing each transitively loads its
# sub-hook package (e.g. PostToolUse.py -> posttooluse package ->
# breadcrumb_tracker_hook -> skill_guard), which is what surfaces drift in
# any hook that package wires in. All four guard main() behind
# `if __name__ == "__main__"`, so importing them is side-effect-free
# (stdin is read only inside main()).
DISPATCHER_HOOKS: list[str] = [
    "PreToolUse.py",
    "PostToolUse.py",
    "Stop.py",
    "UserPromptSubmit.py",
]


def try_load(name_or_path: str) -> tuple[bool, str]:
    """Import a hook module by filename (resolved under HOOKS_DIR) or by path.

    Returns (ok, error_message). A throwaway module name is used and the
    module object is discarded, so import side effects do not persist in the
    calling process beyond what the import itself does.
    """
    path = Path(name_or_path)
    hook_path = path if path.is_absolute() else (HOOKS_DIR / name_or_path)
    if not hook_path.exists():
        return False, "file does not exist"
    spec = importlib.util.spec_from_file_location(hook_path.stem, hook_path)
    if spec is None or spec.loader is None:
        return False, "no spec/loader"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except SystemExit as e:
        # Some hooks call sys.exit() at import time (self-check scripts).
        return False, f"SystemExit code={e.code} at import time"
    except BaseException as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    return True, ""


def check_dispatchers() -> list[tuple[str, str]]:
    """Import every dispatcher. Return list of (name, error) for failures."""
    failures: list[tuple[str, str]] = []
    for name in DISPATCHER_HOOKS:
        ok, err = try_load(name)
        if not ok:
            failures.append((name, err))
    return failures
