#!/usr/bin/env python3
"""
SessionStart Repo Map Regen

Regenerates the structural repo map on session start, but only if stale
(generator or any plugin manifest changed since the last regen). Otherwise
skips — keeps session startup cheap.

Outputs (written by regen_repo_map.py):
    .claude/state/shared/repo_map.generated.{md,json}
    .claude/state/shared/canonical_paths.generated.md

Configuration:
    REPO_MAP_REGEN_ENABLED: Enable/disable (default: true)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

ENABLED = os.environ.get("REPO_MAP_REGEN_ENABLED", "true").lower() in ("1", "true", "yes")

GENERATOR = HOOKS_DIR / "regen_repo_map.py"
PLUGIN_ROOT = Path("P:/packages/.claude-marketplace/plugins")
OUTPUTS = [
    Path("P:/.claude/state/shared/repo_map.generated.md"),
    Path("P:/.claude/state/shared/repo_map.generated.json"),
    Path("P:/.claude/state/shared/canonical_paths.generated.md"),
]


def _needs_regen() -> bool:
    """True if any output is missing or older than the generator / newest manifest."""
    if not all(p.exists() for p in OUTPUTS):
        return True
    try:
        out_mtime = min(p.stat().st_mtime for p in OUTPUTS)
    except OSError:
        return True
    if not GENERATOR.exists():
        return False  # ponytail: nothing to regen with; skip silently
    if GENERATOR.stat().st_mtime > out_mtime:
        return True
    # Check newest plugin.json mtime — cheap (26 small files).
    if PLUGIN_ROOT.exists():
        try:
            newest_manifest = max(
                (p.stat().st_mtime for p in PLUGIN_ROOT.rglob("plugin.json")),
                default=0.0,
            )
            if newest_manifest > out_mtime:
                return True
        except OSError:
            pass
    return False


def main() -> None:
    if not ENABLED:
        return
    if not _needs_regen():
        return
    try:
        import regen_repo_map as gen

        gen.main()
    except Exception as exc:  # never disrupt session start
        print(f"SessionStart_repo_map: regen failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
