"""Shared skill_guard path utilities.

Provides centralized skill_guard src path resolution and sys.path injection
with proper .resolve() + .exists() validation. Eliminates scattered inline
patterns across hook files that drift independently.

Usage:
    from __lib.skill_guard_path import ensure_skill_guard_in_syspath
    ensure_skill_guard_in_syspath()
    from skill_guard.breadcrumb.tracker import ...
"""

from pathlib import Path
import sys

# Canonical path — P:/packages/skill-guard/src is the fixed skill_guard package root
_SKILL_GUARD_SRC = Path("P:/packages/skill-guard/src").resolve()


def get_skill_guard_src() -> Path:
    """Return the resolved skill_guard src path.

    Does NOT check existence — use get_skill_guard_src().exists() to verify.
    """
    return _SKILL_GUARD_SRC


def ensure_skill_guard_in_syspath() -> None:
    """Add skill_guard src to sys.path if not already present.

    Uses .resolve() to canonicalize path and detect junctions/symlinks.
    Uses .exists() to avoid inserting non-existent paths.
    Safe to call multiple times — guard prevents duplicate insertion.
    """
    if _SKILL_GUARD_SRC.exists() and str(_SKILL_GUARD_SRC) not in sys.path:
        sys.path.insert(0, str(_SKILL_GUARD_SRC))
