#!/usr/bin/env python3
"""SessionEnd hook - Background archive sessions after they close.

Runs asynchronously (non-blocking) after a session ends. Uses claude-vault
to archive sessions for redundancy. If PreCompact somehow fails, this hook
ensures sessions are still archived when the session closes.

This hook uses timeout=0 in hooks.json, meaning it runs in the background
without blocking Claude Code cleanup.
"""

import subprocess
import sys
import os


def main():
    """Archive sessions to vault in the background."""
    try:
        # Call claude-vault import to archive all sessions from ~/.claude/projects/
        # This runs in the background (non-blocking) after session close
        subprocess.run(
            ["claude-vault", "import"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Always return 0 for background hooks - don't log anything
        return 0

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Silent failure - this is a background hook, don't spam logs
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(0)  # Always exit 0 for background hooks
