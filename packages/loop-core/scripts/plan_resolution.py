"""Plan path resolution logic for /ralph-loop skill.

This module implements the plan path resolution logic for the /ralph-loop skill,
which needs to locate plan files using a priority-based resolution strategy.

Resolution Priority:
-------------------
1. Explicit plan path argument (highest priority)
2. .claude/loop/plan.md (default location)
3. plan.{terminal_id}.md (per-terminal plan)
4. plan.md in project root (fallback)

This resolution strategy enables flexible plan organization:
- Users can explicitly specify any plan path
- Default plans live in a centralized location (.claude/loop/)
- Per-terminal plans enable multi-terminal isolation
- Root plan.md provides backward compatibility

Example Usage:
-------------
    >>> from scripts.plan_resolution import resolve_plan_path
    >>> # Explicit path
    >>> resolve_plan_path(explicit_arg="custom.md", terminal_id="term_1", project_root=Path("/project"))
    'custom.md'

    >>> # Default resolution
    >>> resolve_plan_path(explicit_arg=None, terminal_id="term_1", project_root=Path("/project"))
    '.claude/loop/plan.md'  # if exists

    >>> # Per-terminal plan
    >>> resolve_plan_path(explicit_arg=None, terminal_id="console_abc", project_root=Path("/project"))
    'plan.console_abc.md'  # if exists

    >>> # Fallback to root
    >>> resolve_plan_path(explicit_arg=None, terminal_id="term_1", project_root=Path("/project"))
    'plan.md'  # if exists

    >>> # No plan found
    >>> resolve_plan_path(explicit_arg=None, terminal_id="term_1", project_root=Path("/empty"))
    None
"""

from pathlib import Path
from typing import Optional


def resolve_plan_path(
    explicit_arg: Optional[str],
    terminal_id: str,
    project_root: Path,
) -> Optional[str]:
    """Resolve plan file path using priority-based resolution strategy.

    Implements 4-tier priority resolution:
    1. Explicit path argument (always returned if provided and non-empty)
    2. .claude/loop/plan.md (default location)
    3. plan.{terminal_id}.md (per-terminal isolation)
    4. plan.md (root fallback)

    Args:
        explicit_arg: Explicit plan path from user argument. If provided and
            non-empty, this takes absolute priority over all other resolution
            methods. The path is returned as-is even if the file doesn't exist
            (validation happens later in the workflow).
        terminal_id: Terminal identifier for per-terminal plan resolution.
            Used to construct plan.{terminal_id}.md filename.
        project_root: Project root directory for path resolution. All relative
            paths are resolved from this directory.

    Returns:
        Resolved plan path as string, or None if no plan file found.
        Returns explicit_arg if provided (even if file doesn't exist).

    Raises:
        TypeError: If project_root is not a Path object or terminal_id is not a string.

    Examples:
        >>> # Explicit path (highest priority)
        >>> resolve_plan_path("custom.md", "term_1", Path("/project"))
        'custom.md'

        >>> # Default .claude/loop/plan.md
        >>> resolve_plan_path(None, "term_1", Path("/project"))
        '.claude/loop/plan.md'

        >>> # Per-terminal plan
        >>> resolve_plan_path(None, "console_abc", Path("/project"))
        'plan.console_abc.md'

        >>> # No plan found
        >>> resolve_plan_path(None, "term_1", Path("/empty"))
        None

    Implementation Notes:
        - Explicit path is always returned if provided (no existence check)
        - Empty string explicit_arg is treated as None (auto-resolution)
        - Terminal ID is sanitized before use in filename construction
        - All paths are returned as strings (not Path objects)
    """
    # Type validation
    if not isinstance(project_root, Path):
        raise TypeError(f"project_root must be Path, got {type(project_root).__name__}")

    if not isinstance(terminal_id, str):
        raise TypeError(f"terminal_id must be str, got {type(terminal_id).__name__}")

    # Priority 1: Explicit path argument (highest priority)
    # Return as-is if provided and non-empty, even if file doesn't exist
    if explicit_arg and explicit_arg.strip():
        return explicit_arg

    # Priority 2: .claude/loop/plan.md (default location)
    default_plan = project_root / ".claude" / "loop" / "plan.md"
    if default_plan.exists():
        return str(default_plan)

    # Priority 3: plan.{terminal_id}.md (per-terminal plan)
    # Terminal ID may contain special characters, sanitize for filename
    safe_terminal_id = _sanitize_terminal_id(terminal_id)
    terminal_plan = project_root / f"plan.{safe_terminal_id}.md"
    if terminal_plan.exists():
        return str(terminal_plan)

    # Priority 4: plan.md (project root fallback)
    root_plan = project_root / "plan.md"
    if root_plan.exists():
        return str(root_plan)

    # No plan found
    return None


def _sanitize_terminal_id(terminal_id: str) -> str:
    """Sanitize terminal ID for safe use in filename construction.

    Removes or replaces characters that are problematic in filenames:
    - Path separators (/, \\)
    - Special characters (: *, ?, ", <, >, |)
    - Control characters

    Args:
        terminal_id: Raw terminal identifier string.

    Returns:
        Sanitized terminal ID safe for filename use.

    Examples:
        >>> _sanitize_terminal_id("console_abc123")
        'console_abc123'

        >>> _sanitize_terminal_id("term:with:special")
        'term_with_special'

        >>> _sanitize_terminal_id("term/with/slash")
        'term_with_slash'
    """
    # Replace path separators and problematic characters
    replacements = {
        "/": "_",
        "\\": "_",
        ":": "_",
        "*": "_",
        "?": "_",
        '"': "_",
        "<": "_",
        ">": "_",
        "|": "_",
    }

    safe_id = terminal_id
    for old, new in replacements.items():
        safe_id = safe_id.replace(old, new)

    # Remove any remaining control characters
    safe_id = "".join(char for char in safe_id if ord(char) >= 32)

    return safe_id


def resolve_plan_path_with_validation(
    explicit_arg: Optional[str],
    terminal_id: str,
    project_root: Path,
) -> tuple[Optional[str], bool, str]:
    """Resolve plan path with additional validation and diagnostics.

    Extended version of resolve_plan_path that returns validation status
    and diagnostic messages for error handling.

    Args:
        explicit_arg: Explicit plan path from user argument.
        terminal_id: Terminal identifier for per-terminal plan resolution.
        project_root: Project root directory for path resolution.

    Returns:
        Tuple of (resolved_path, is_valid, diagnostic_message):
        - resolved_path: Resolved plan path string or None
        - is_valid: True if path exists and is readable, False otherwise
        - diagnostic_message: Human-readable diagnostic message

    Examples:
        >>> # Valid plan found
        >>> resolve_plan_path_with_validation(None, "term_1", Path("/project"))
        ('.claude/loop/plan.md', True, 'Using default plan')

        >>> # Explicit path doesn't exist
        >>> resolve_plan_path_with_validation("missing.md", "term_1", Path("/project"))
        ('missing.md', False, 'Explicit path provided but file does not exist')

        >>> # No plan found
        >>> resolve_plan_path_with_validation(None, "term_1", Path("/empty"))
        (None, False, 'No plan file found in project')
    """
    # Resolve plan path
    resolved = resolve_plan_path(explicit_arg, terminal_id, project_root)

    # No plan found
    if resolved is None:
        diagnostic = (
            "No plan file found in project. "
            "Searched: .claude/loop/plan.md, plan.{terminal_id}.md, plan.md"
        )
        return (None, False, diagnostic)

    # Check if explicit path exists
    if explicit_arg and explicit_arg.strip():
        plan_path = Path(resolved)
        if not plan_path.exists():
            diagnostic = f"Explicit path provided but file does not exist: {resolved}"
            return (resolved, False, diagnostic)

    # Plan exists and is valid
    source = "explicit" if explicit_arg else "resolved"
    diagnostic = f"Using {source} plan: {resolved}"
    return (resolved, True, diagnostic)


class PlanResolutionError(Exception):
    """Exception raised when plan resolution fails critically.

    This exception is raised for critical errors during plan resolution,
    such as invalid project root or terminal ID.
    """

    pass
