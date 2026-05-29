#!/usr/bin/env python3
"""PreCompact hook - Auto-archive sessions to vault before cleanup.

Runs before Claude Code cleanup deletes old sessions. Uses claude-vault
to archive sessions from ~/.claude/projects/ to vault.db for searchable
long-term storage via /search.
"""

import subprocess
import sys


def main():
    """Archive sessions to vault before cleanup."""
    try:
        # Call claude-vault import to archive all sessions from ~/.claude/projects/
        # This is idempotent - duplicates are skipped via UUID deduplication
        result = subprocess.run(
            ["claude-vault", "import"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Always exit 0 to not block cleanup, even if claude-vault import fails
        # (e.g., claude-vault not installed, vault.db locked, etc.)
        if result.returncode != 0:
            sys.stderr.write(f"[VAULT-ARCHIVE] claude-vault import failed: {result.stderr}\n")
        else:
            # Log import results
            if result.stdout:
                sys.stderr.write(f"[VAULT-ARCHIVE] {result.stdout}")

        return 0

    except subprocess.TimeoutExpired:
        sys.stderr.write("[VAULT-ARCHIVE] claude-vault import timed out after 60s\n")
        return 0
    except FileNotFoundError:
        sys.stderr.write("[VAULT-ARCHIVE] claude-vault command not found - install from https://github.com/kuroko1t/claude-vault\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"[VAULT-ARCHIVE] Hook error: {e}\n")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(0)  # Always exit 0 to not block cleanup
