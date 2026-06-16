#!/usr/bin/env python3
"""
SessionStart_symlink_check.py - Validate hook symlinks at startup

Checks all symlinks in the hooks directory and reports broken ones.
Silent by default - only outputs warnings when symlinks are broken.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# Symlinks that should exist and point to valid targets
EXPECTED_SYMLINKS = {
    # handoff hooks were consolidated into the snapshot plugin (no longer local
    # symlinks); the former packages/handoff/ source dir no longer exists.
    "StopHook_rca_contract.py": "/p/packages/cc-skills-sdlc/skills/rca/hooks/",
    "StopHook_rca_reflector.py": "/p/packages/cc-skills-sdlc/skills/rca/hooks/",
    "StopHook_skill_execution_gate.py": "/p/packages/.claude-marketplace/plugins/skill-guard/src/skill_guard/",
    "skill_execution_state.py": "/p/packages/.claude-marketplace/plugins/skill-guard/src/skill_guard/",
}

def main():
    broken = []
    for symlink_name, expected_prefix in EXPECTED_SYMLINKS.items():
        symlink_path = HOOKS_DIR / symlink_name
        if not symlink_path.exists():
            # Not a symlink or doesn't exist
            if symlink_path.is_symlink():
                broken.append(f"BROKEN: {symlink_name} -> target does not exist")
            continue
        if not symlink_path.is_symlink():
            # Not a symlink - that's fine, just means it's a real file
            continue
        target = symlink_path.resolve()
        if not target.exists():
            broken.append(f"BROKEN: {symlink_name} -> {target}")

    if broken:
        print("WARNING: Broken symlinks detected in hooks directory:")
        for msg in broken:
            print(f"  - {msg}")
        print("Hook functionality may be degraded.")
        sys.exit(1)
    else:
        # Silent success - only log in debug mode
        if os.environ.get("CSF_HOOK_DEBUG") == "1":
            print("INFO: All hook symlinks valid")
        sys.exit(0)

if __name__ == "__main__":
    main()