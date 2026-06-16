"""DEPRECATED — skill_guard path utilities.

Historically provided centralized skill_guard src path resolution and sys.path
injection. As of 2026-06-01 (RCA Option C), the in-process fast path that consumed
this helper has been removed from PreToolUse.py. The subprocess path
(skill_guard/__lib/router.py PreToolUse, wired in user settings.json) is now the
sole contract gate.

The historical hardcoded path `P:/packages/.claude-marketplace/plugins/skill-guard/src` no longer exists;
skill-guard now lives at
P:/packages/.claude-marketplace/plugins/skill-guard. Keeping this file for
backward compatibility with any external importer that still uses the function
names.
"""

from pathlib import Path
import sys

_SKILL_GUARD_SRC = Path(
    "P:/packages/.claude-marketplace/plugins/skill-guard/src"
).resolve()


def get_skill_guard_src() -> Path:
    """Return the resolved skill_guard src path.

    DEPRECATED: Prefer the subprocess path (skill_guard/__lib/router.py)
    for active enforcement. This helper remains for legacy importers.
    """
    return _SKILL_GUARD_SRC


def ensure_skill_guard_in_syspath() -> None:
    """DEPRECATED no-op stub.

    Returns silently. The in-process fast path that consumed this helper has
    been removed. Use the subprocess entry point at skill_guard/__lib/router.py
    for skill-guard enforcement.
    """
    # Intentionally a no-op. The subprocess path doesn't need sys.path
    # injection because it resolves relative to its own __file__.
    pass
