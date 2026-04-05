"""
Constitutional Compliance Check Hook

Validates that code changes comply with project constitutional constraints
before allowing edits to proceed.

Reads CLAUDE.md for constraints and validates against them.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


def check_constitutional_compliance(
    tool_name: str,
    tool_input: Dict[str, Any],
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Check if tool use complies with project constitutional constraints.

    Args:
        tool_name: Name of the tool being used (e.g., "Edit", "Write")
        tool_input: Input parameters for the tool
        project_root: Project root directory (defaults to current working directory)

    Returns:
        Dict with:
        - allowed (bool): Whether the tool use should proceed
        - reason (str): Explanation if not allowed
        - warnings (List[str]): Compliance warnings (non-blocking)
    """
    result = {
        "allowed": True,
        "reason": "",
        "warnings": []
    }

    # Only check code-editing tools
    if tool_name not in ["Edit", "Write"]:
        return result

    # Find project root
    if project_root is None:
        project_root = Path.cwd()
        # Search up for CLAUDE.md
        for _ in range(5):  # Max 5 levels up
            if (project_root / "CLAUDE.md").exists():
                break
            if project_root.parent == project_root:  # Reached filesystem root
                break
            project_root = project_root.parent

    # Load constitutional constraints
    claude_md_path = project_root / "CLAUDE.md"
    if not claude_md_path.exists():
        # No CLAUDE.md = no constraints
        return result

    try:
        constraints = read_constitutional_constraints(claude_md_path)
    except Exception:
        # If we can't read constraints, don't block
        return result

    # Extract file path and content from tool input
    file_path = tool_input.get("file_path", "")
    new_content = tool_input.get("new_string", "") or tool_input.get("content", "")

    if not file_path or not new_content:
        return result

    # Check constraints
    violations, warnings = check_constraints(
        file_path=file_path,
        content=new_content,
        constraints=constraints
    )

    if violations:
        result["allowed"] = False
        result["reason"] = "; ".join(violations)

    if warnings:
        result["warnings"] = warnings

    return result


def read_constitutional_constraints(claude_md_path: Path) -> Dict[str, List[str]]:
    """
    Read constitutional constraints from CLAUDE.md.

    Returns dict with constraint categories and their rules.
    """
    constraints = {
        "prohibited": [],
        "required": [],
        "solo_dev": []
    }

    content = claude_md_path.read_text()

    # Parse common constraint patterns
    lines = content.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Detect constraint sections
        if "prohibited" in line.lower() or "forbidden" in line.lower() or "don't" in line.lower():
            current_section = "prohibited"
        elif "required" in line.lower() or "must" in line.lower():
            current_section = "required"
        elif "solo-dev" in line.lower() or "solo dev" in line.lower():
            current_section = "solo_dev"

        # Extract bullet points as constraints
        if line.startswith("-") and current_section:
            constraint = line[1:].strip()
            if constraint:
                constraints[current_section].append(constraint)

    return constraints


def check_constraints(
    file_path: str,
    content: str,
    constraints: Dict[str, List[str]]
) -> tuple[List[str], List[str]]:
    """
    Check content against constraints.

    Returns (violations, warnings) where violations block the action
    and warnings are non-blocking compliance issues.
    """
    violations = []
    warnings = []

    # Check prohibited patterns
    for prohibition in constraints.get("prohibited", []):
        if prohibition.lower() in content.lower():
            violations.append(f"Prohibited pattern detected: {prohibition}")

    # Check solo-dev constraints (warn about enterprise patterns)
    solo_dev_patterns = [
        "abstract factory",
        "dependency injection",
        "service mesh",
        "microservice",
        "enterprise",
        "framework",
        "container"
    ]

    for pattern in solo_dev_patterns:
        if pattern.lower() in content.lower():
            warnings.append(f"Enterprise pattern detected: {pattern} (verify solo-dev compliance)")

    return violations, warnings


def pre_tool_use(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    PreToolUse hook entry point.

    Called before tool execution to validate constitutional compliance.
    """
    # Allow by default, only block if violation found
    result = check_constitutional_compliance(tool_name, tool_input)

    if not result["allowed"]:
        # Block the tool use
        print("\n❌ CONSTITUTIONAL COMPLIANCE CHECK FAILED")
        print(f"Reason: {result['reason']}")
        print("\nThis change violates project constitutional constraints.")
        print("Please review CLAUDE.md for project constraints.\n")

    if result["warnings"]:
        # Show warnings but allow
        for warning in result["warnings"]:
            print(f"⚠️  {warning}")

    return result


# Hook entry point
if __name__ == "__main__":
    # For testing
    tool_input = {
        "file_path": "test.py",
        "new_string": "print('hello')"
    }
    result = pre_tool_use("Edit", tool_input)
    print(f"Allowed: {result['allowed']}")
    print(f"Reason: {result.get('reason', '')}")
    print(f"Warnings: {result.get('warnings', [])}")
