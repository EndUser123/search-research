#!/usr/bin/env python3
"""
Stage 1.5: Naming & Standards Compliance

Validates:
- File naming conventions (verbose naming standard)
- Python 2025 compliance (anti-pattern detection)
- Logical grouping (files in correct directories)

Usage:
    python stage1_5_naming.py file1.py file2.py ...

Exit codes:
    0 - Pass (or warnings only, non-blocking)
    1 - Never exits 1 (non-blocking stage)
"""

import re
import sys
from pathlib import Path


# File naming patterns from code_standards_guides.md
PATTERNS = {
    "library": re.compile(r"^[a-z_]+_[a-z_]+\.py$"),  # {system}_{component}.py
    "hook": re.compile(
        r"^(SessionStart|UserPromptSubmit|PreToolUse|PostToolUse|PreCompact|PostCompact|StopHook)_[a-z]+_[a-z_]+\.py$"
    ),
    "router": re.compile(
        r"^(SessionStart|UserPromptSubmit|PreToolUse|PostToolUse)_router\.py$"
    ),
    "gate": re.compile(r"^(PreToolUse)_[a-z_]+_gate\.py$"),
    "test": re.compile(r"^test_[a-z_]+_[a-z_]+\.py$"),  # test_{component}_{scenario}.py
}

# Anti-patterns from Python 2025 standards
ANTI_PATTERNS = {
    "requirements.txt": "Use pyproject.toml + uv",
    "setup.py": "Use pyproject.toml",
    "black": "Use ruff",
    "isort": "Use ruff",
    "flake8": "Use ruff",
}


def check_naming(path: Path, findings: list) -> bool:
    """Check file naming conventions."""
    name = path.name
    parent = path.parent.name if path.parent else ""
    all_pass = True

    if path.suffix == ".py":
        if parent == "__lib__":
            if not PATTERNS["library"].match(name):
                findings.append(
                    f"  ⚠️  Library file should follow {{system}}_{{component}}.py pattern: {name}"
                )
                all_pass = False
        elif parent == "hooks":
            if not (
                PATTERNS["hook"].match(name)
                or PATTERNS["router"].match(name)
                or PATTERNS["gate"].match(name)
            ):
                findings.append(
                    f"  ⚠️  Hook file should follow {{Event}}_{{action}}_{{noun}}.py pattern: {name}"
                )
                all_pass = False
        elif "test" in parent:
            if not PATTERNS["test"].match(name):
                findings.append(
                    f"  ⚠️  Test file should follow test_{{component}}_{{scenario}}.py pattern: {name}"
                )
                all_pass = False

        # Check for verbose naming (no short cryptic names)
        if len(name) < 10 and name not in ["__init__.py", "conftest.py"]:
            findings.append(f"  ⚠️  File name too short - use verbose naming: {name}")
            all_pass = False

    return all_pass


def check_anti_patterns(path: Path, findings: list) -> bool:
    """Check for Python 2025 anti-patterns."""
    name = path.name
    all_pass = True

    if name in ANTI_PATTERNS:
        findings.append(f"  ❌ {name}: {ANTI_PATTERNS[name]}")
        all_pass = False

    return all_pass


def check_logical_grouping(path: Path, findings: list) -> bool:
    """Check files are in correct directories."""
    parent = path.parent.name if path.parent else ""
    all_pass = True

    if parent == "hooks" and path.suffix != ".py":
        findings.append(f"  ⚠️  Non-Python file in hooks/ directory: {path.name}")
        all_pass = False

    return all_pass


def check_content_patterns(path: Path, findings: list) -> None:
    """Check file content for Python 2025 violations."""
    if path.suffix != ".py" or not path.exists():
        return

    try:
        content = path.read_text()
    except Exception:
        return

    if "os.getenv(" in content and "pydantic_settings" not in content:
        findings.append(f"  ⚠️  Using os.getenv() - use pydantic-settings instead")
    if "import requests" in content and "asyncio" in content:
        findings.append(f"  ⚠️  Using requests in async context - use httpx instead")
    if "asyncio.create_task(" in content and "TaskGroup" not in content:
        findings.append(f"  ⚠️  Using create_task() - use asyncio.TaskGroup() instead")


def main():
    if len(sys.argv) < 2:
        print("Usage: python stage1_5_naming.py <target1> [target2] ...")
        sys.exit(0)

    # Handle comma-separated input
    targets = []
    for arg in sys.argv[1:]:
        targets.extend(arg.split(","))
    targets = [t.strip() for t in targets if t.strip()]

    all_pass = True
    findings = []

    for target in targets:
        path = Path(target)
        print(f"\n📄 Checking: {target}")

        if not path.exists():
            print(f"  ⚠️  File not found")
            continue

        # Run all checks
        if not check_naming(path, findings):
            all_pass = False
        if not check_anti_patterns(path, findings):
            all_pass = False
        if not check_logical_grouping(path, findings):
            all_pass = False
        check_content_patterns(path, findings)

    # Output findings
    if findings:
        for f in findings:
            print(f)
        if not all_pass:
            print("\n⚠️  Stage 1.5 WARN - Naming/standards issues found")
        else:
            print("\n✅ Stage 1.5 PASS - All naming checks passed")
    else:
        print("\n✅ Stage 1.5 PASS - No naming/standards issues")

    # Always exit 0 - non-blocking stage
    sys.exit(0)


if __name__ == "__main__":
    main()
