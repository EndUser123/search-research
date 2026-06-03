"""
Regression test: hooks under P:/.claude/hooks/ must be loadable.

Background: 2026-06-02 RCA found that SessionStart_task_identity.py has
a broken import (ModuleNotFoundError: No module named 'knowledge'). The
file is currently commented out in SessionStart.SETUP_SEQUENCE, but it
still exists on disk and any direct invocation (manual test, importer
probe, future re-enable) crashes with a non-blocking status code.

Scope: this test loads ONLY the files that SessionStart could plausibly
execute (the SETUP_SEQUENCE list and the top-level dispatchers
SessionStart.py, UserPromptSubmit.py, PostToolUse.py, Stop.py). The
broader directory has files that are tools, tests-as-scripts, or
legacy artifacts, and asserting they all import cleanly is out of scope
for this regression test (and would be a Tier 3 change of its own).

Why: prevents the "import path points to a module that doesn't exist"
class of bug from re-occurring in the hot path. The previous
investigation required manually running each hook and reading stderr;
this test catches the same class automatically for the hot-path hooks.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
if str(HOOKS_DIR / "__lib") not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR / "__lib"))

# Single source of truth for the dispatcher list and the loader, shared with
# the in-session gate (PostToolUse_hook_import_health.py) so the two cannot
# drift apart.
from hook_import_health import DISPATCHER_HOOKS, try_load as _try_load  # noqa: E402


# Hooks intentionally disabled (commented out in SessionStart.SETUP_SEQUENCE
# or otherwise known-unused) but still on disk. Listed here so we do not
# silently regress by re-enabling them with a broken import. If you add
# an entry here, add a one-line reason.
KNOWN_BROKEN_BUT_DISABLED: dict[str, str] = {
    "SessionStart_task_identity.py": (
        "DISABLED in SessionStart.SETUP_SEQUENCE:53 (output not consumed by "
        "PreCompact). Import path knowledge.systems... does not exist on disk; "
        "fix is item #1 of the 2026-06-02 RCA Tier 3 list. Re-enable only after "
        "the import is repaired."
    ),
    "SessionStart_folder_context.py": (
        "DISABLED: Missing features.lib_folder_context module per "
        "SessionStart.SETUP_SEQUENCE:37 comment."
    ),
    "SessionStart_hook_health_check.py": (
        "DISABLED: 319ms avg, never caught a failure in 17 runs per "
        "SessionStart.SETUP_SEQUENCE:39 comment."
    ),
    "SessionStart_search_daemon.py": (
        "DISABLED: spawns dreaming daemon --daemon-type search (identical to "
        "dreaming daemon, no differentiation) per "
        "SessionStart.SETUP_SEQUENCE:49 comment."
    ),
}


# Hot-path hooks. The first entry is the SessionStart orchestrator itself;
# the rest are the SETUP_SEQUENCE sub-hooks. Other top-level hooks
# (UserPromptSubmit, PostToolUse, Stop) are covered by DISPATCHER_HOOKS above.
HOT_PATH_HOOKS: list[str] = [
    "SessionStart.py",
    "SessionStart_symlink_check.py",
    "SessionStart_terminal_id.py",
    "SessionStart_contract_health.py",
    "SessionStart_log_rotation.py",
    "SessionStart_semantic_daemon.py",
    "SessionStart_dreaming_daemon.py",
    "SessionStart_memory_cks_auto.py",
    "SessionStart_timeline.py",
    "SessionStart_constraint_display.py",
    "SessionStart_commitment_tracker.py",
    "SessionStart_characterization_check.py",
]


def test_no_orphan_disabled_hooks() -> None:
    """KNOWN_BROKEN_BUT_DISABLED must only list files that actually exist."""
    for name in KNOWN_BROKEN_BUT_DISABLED:
        path = HOOKS_DIR / name
        assert path.exists(), (
            f"KNOWN_BROKEN_BUT_DISABLED references {name} but the file "
            f"does not exist. Remove the entry."
        )


def test_hot_path_hooks_load() -> None:
    """Each hot-path hook must be importable.

    A load failure indicates a broken import path, syntax error, or
    missing module. The previous SessionStart_task_identity incident
    was this class of bug — same file lives one directory above the
    SETUP_SEQUENCE list and was caught only after a non-blocking
    hook error in the user's terminal.
    """
    failures: list[tuple[str, str]] = []
    for name in HOT_PATH_HOOKS:
        if name in KNOWN_BROKEN_BUT_DISABLED:
            continue
        ok, err = _try_load(name)
        if not ok:
            failures.append((name, err))

    assert not failures, (
        "The following hot-path hooks failed to load. Each one is a class "
        "of bug that causes a non-blocking hook error in the user's "
        "terminal. Fix the import path or add to KNOWN_BROKEN_BUT_DISABLED "
        "with a one-line reason:\n  "
        + "\n  ".join(f"{name}: {reason}" for name, reason in failures)
    )


def test_dispatcher_hooks_load() -> None:
    """Each top-level dispatcher must be importable.

    A dispatcher import failure is the highest-impact class of hook bug: it
    fires a non-blocking error on every tool call (PostToolUse), every prompt
    (UserPromptSubmit), or every stop (Stop) until a human notices. Importing
    the dispatcher transitively loads its sub-hook package, so this catches
    import-path drift in any hook that package wires in (the 2026-06
    skill_guard regression that spammed 350 identical tracebacks).
    """
    failures: list[tuple[str, str]] = []
    for name in DISPATCHER_HOOKS:
        ok, err = _try_load(name)
        if not ok:
            failures.append((name, err))

    assert not failures, (
        "The following top-level dispatchers failed to load. Each one fires a "
        "non-blocking hook error on EVERY tool call/prompt/stop until fixed. A "
        "failure here usually means a sub-hook in the dispatcher's package has "
        "an import-path that drifted (e.g. a hardcoded path to a moved plugin). "
        "Fix the import before committing:\n  "
        + "\n  ".join(f"{name}: {reason}" for name, reason in failures)
    )


def test_hot_path_hooks_have_main() -> None:
    """Each loadable hot-path hook must define a main() function.

    HookImporter calls hook.main() to execute the hook. A missing main()
    causes AttributeError at execution time, which Claude Code surfaces as
    a non-blocking error.
    """
    missing: list[str] = []
    for name in HOT_PATH_HOOKS:
        if name in KNOWN_BROKEN_BUT_DISABLED:
            continue
        ok, _ = _try_load(name)
        if not ok:
            continue
        # Re-import to check for main attribute
        hook_path = HOOKS_DIR / name
        spec = importlib.util.spec_from_file_location(hook_path.stem, hook_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except BaseException:  # noqa: BLE001
            continue
        if not hasattr(module, "main"):
            missing.append(name)

    assert not missing, (
        "The following hooks load successfully but lack a main() function, "
        "so HookImporter.execute_hook() will raise AttributeError at runtime:\n  "
        + "\n  ".join(missing)
    )
