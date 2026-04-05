#!/usr/bin/env python3
"""GTO Verification Stop Hook - Platform-aware wrapper with scope guard.

This script:
1. Checks if GTO was actually used (scope guard)
2. Detects the platform and runs the appropriate verification script
3. Returns appropriate exit codes

Exit codes:
- 0: Verification passed (or skipped - GTO not used)
- 2: Verification failed, must retry
"""

import os
import sys
from pathlib import Path


# Add hooks to path for shared utilities
# Search upward for hooks directory instead of hardcoded parent levels
def _find_hooks_dir(start_path: Path) -> Path:
    """Find hooks directory by searching upward from start_path."""
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        hooks_dir = parent / "hooks"
        if hooks_dir.exists() and (hooks_dir / "__lib" / "hook_base.py").exists():
            return hooks_dir
    raise FileNotFoundError("Could not find hooks directory with __lib/hook_base.py")


sys.path.insert(0, str(_find_hooks_dir(Path(__file__))))

from __lib.hook_base import get_terminal_id
from __lib.hook_platform import run_platform_hook, scope_guard_check


def main() -> int:
    """Main entry point."""
    # Get terminal ID using centralized function with fallbacks
    # For skill-based hooks, CLAUDE_TERMINAL_ID is not available
    # Use get_terminal_id() which derives from console/PID+timestamp
    terminal_id = get_terminal_id()
    if not terminal_id:
        print(
            '{"decision": "block", "reason": "Unable to determine terminal ID for multi-terminal isolation."}'
        )
        return 2

    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    # Scope guard: Check if GTO was actually used
    should_skip, reason = scope_guard_check(project_root, "gto-state-{terminal_id}", terminal_id)

    if should_skip:
        print(f"GTO scope guard: {reason}")
        return 0  # Skip (pass) - GTO was not used

    # Run platform-specific verification hook
    script_dir = Path(__file__).parent

    try:
        exit_code, stdout, stderr = run_platform_hook(
            script_dir=script_dir,
            script_name="gto_verify",
            env={
                "TERMINAL_ID": terminal_id,
                "CLAUDE_PROJECT_DIR": str(project_root),
            },
            timeout=30,
        )

        # Output the verification result
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, file=sys.stderr)

        return exit_code

    except FileNotFoundError as e:
        print(f"GTO verification error: {e}")
        return 2  # Block if script not found


if __name__ == "__main__":
    sys.exit(main())
