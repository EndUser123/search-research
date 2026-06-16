"""DEPRECATED — skill_guard path utilities.

Historically provided centralized skill_guard src path resolution and sys.path
injection. As of 2026-06-01 (RCA Option C), the in-process fast path that consumed
this helper has been removed from PreToolUse.py. The subprocess path
(skill_guard/__lib/router.py PreToolUse, wired in user settings.json) is now the
sole contract gate.

The hardcoded path `_SKILL_GUARD_SRC = P:/packages/skill-guard/src` no longer
exists — skill-guard plugin was migrated to
P:/packages/.claude-marketplace/plugins/skill-guard. Keeping this file for backward
compatibility (any external importer that still uses the function names) but
documenting it as dead.

If you need to revive the in-process fast path, compute the path dynamically:
walk up from __file__ looking for a `plugins/skill-guard/src` directory, or
use the marketplace convention at `plugins/skill-guard/src` directly.
"""

from pathlib import Path
import sys

# Deprecated hardcoded path kept for backward compatibility only.
# Returns a non-existent path; callers MUST check `.exists()` before use.
_SKILL_GUARD_SRC = Path("P:/packages/skill-guard/src").resolve()


def get_skill_guard_src() -> Path:
    """Return the resolved (likely non-existent) skill_guard src path.

    DEPRECATED: This returns a hardcoded path that no longer exists after
    the skill-guard plugin migration. Callers should use the subprocess
    path (skill_guard/__lib/router.py) instead.
    """
    return _SKILL_GUARD_SRC


def ensure_skill_guard_in_syspath() -> None:
    """DEPRECATED no-op stub.

    Returns silently when the hardcoded path is missing. The in-process
    fast path that consumed this helper has been removed. Use the subprocess
    entry point at skill_guard/__lib/router.py for skill-guard enforcement.
    """
    # Intentionally a no-op. The hardcoded path is dead; the subprocess
    # path doesn't need sys.path injection because it resolves relative
    # to its own __file__.
    pass
