"""
Shared git destructive operation definitions.

Used by:
- PreToolUse_destructive_git_guard.py (hooks) — gates Claude Code Bash tool
- sync.py (skills/git) — gates skill-internal subprocess calls

Keeping config in one place prevents divergence if one location is updated
without the other.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DangerOp:
    """Immutable description of a dangerous git operation."""
    danger_flags: tuple[str, ...] | None = None
    danger_subcommands: tuple[str, ...] | None = None
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM
    description: str = ""  # Human-readable description for block messages
    category: str = "destructive"  # "destructive" or "creative"


# Maps git subcommand -> DangerOp configuration
DESTRUCTIVE_GIT_OPS: dict[str, DangerOp] = {
    "reset": DangerOp(
        danger_flags=("--hard",),
        severity="CRITICAL",
        description="Discard all uncommitted changes in working directory",
        category="destructive",
    ),
    "clean": DangerOp(
        danger_flags=("-f", "-fd", "-fXd", "-fxd"),
        severity="HIGH",
        description="Delete untracked files",
        category="destructive",
    ),
    "stash": DangerOp(
        danger_subcommands=("drop", "clear"),
        severity="HIGH",
        description="Permanently delete stash entries",
        category="destructive",
    ),
}
