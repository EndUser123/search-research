"""
Anti-Lazy Diff Nudge - Enforces visibility for template file updates.

Detects Write/Edit operations on arch/ template files and nudges for:
- Unified diff of changes
- Explanation of what recurring mistake this change prevents

Purpose: Template updates must be visible and explain the "why" behind them.
"""

import json
import re
import sys


def main():
    """PostToolUse hook entry point."""
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    # Only process Write and Edit tools
    if tool_name not in ("Write", "Edit"):
        print("{}")
        sys.exit(0)

    # Normalize path for cross-platform comparison
    path = (tool_input.get("path") or "").replace("\\", "/")

    # Check if this is an arch/ file edit
    if not _is_arch_file(path):
        print("{}")
        sys.exit(0)

    # Generate nudge message
    nudge = _generate_nudge(path)

    # Output as additionalContext (advisory only, no blocking)
    output = {"hookSpecificOutput": {"additionalContext": nudge}}
    print(json.dumps(output))
    sys.exit(0)


def _is_arch_file(path: str) -> bool:
    """Check if path is an architecture template file."""
    if not path:
        return False

    # Normalize Windows paths for consistent matching
    path = path.replace("\\", "/")

    # Direct arch/ directory match
    if path.startswith("arch/") or path.startswith(".claude/arch/") or "/arch/" in path:
        return True

    # SKILL.md files (often contain behavior templates)
    if re.search(r"/SKILL\.md$", path, re.IGNORECASE):
        return True

    # Template files in known locations
    template_patterns = [
        r"packages/arch/skill/",
        r"\.claude/skills/arch/",
    ]
    for pattern in template_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            return True

    return False


def _generate_nudge(path: str) -> str:
    """Generate the nudge message for template visibility."""
    return f"""
📋 **TEMPLATE UPDATE VISIBILITY REQUIRED**

You just updated a template-like file: `{path}`

For visibility and learning, please show:
1. **Unified diff** of the changes you made
2. **Explanation** (1–2 sentences): What recurring mistake or failure mode does this change prevent?

Example format:
```diff
- old pattern
+ new pattern (prevents: describe the mistake)
```

If this change was triggered by user complaints about repeated behavior, explicitly connect your explanation to that complaint.

**Why this matters**: Template updates encode learning. Without visible diffs and clear rationale, the "why" behind the change is lost.
"""
