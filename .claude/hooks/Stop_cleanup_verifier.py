#!/usr/bin/env python3
"""
Stop hook: Cleanup verification gate - checks for missing cleanup steps based on work type.

This hook detects work type from accumulated tool history and warns if cleanup steps are incomplete.
Non-blocking by design - shows warnings via systemMessage.

Environment variables:
- CLEANUP_VERIFIER_ENABLED: Enable/disable (default: true)
- CLEANUP_VERIFIER_MODE: "warn" (default) or "block"
- CLEANUP_TRACKER_DIR: Directory for history files (default: P:/.claude/state)
"""
from __future__ import annotations

import json
import logging as _li
import os
import re
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)


def run(data: dict) -> dict | None:
    """Main entry point for cleanup verification."""
    try:
        # Check if enabled
        if os.environ.get("CLEANUP_VERIFIER_ENABLED", "true").lower() == "false":
            return None

        response = data.get("response", "")
        if not response:
            return None

        # Load tool history from accumulated file
        tool_history = _load_tool_history(data)
        if not tool_history:
            return None

        # Detect work type from tool history
        work_type = detect_work_type(tool_history)
        if not work_type:
            return None

        # Check cleanup requirements for work type
        cleanup_issues = check_cleanup_requirements(work_type, tool_history, response, data)
        if not cleanup_issues:
            return None

        # Build warning message
        warning_parts = [
            "⚠️ CLEANUP VERIFICATION WARNING",
            "",
            f"Work type detected: {work_type}",
            "",
            "Missing cleanup steps:",
        ]

        for issue in cleanup_issues:
            warning_parts.append(f"  • {issue}")

        warning_parts.extend([
            "",
            "Reference: .serena/memories/cleanup_patterns.md",
            "",
            "To disable: export CLEANUP_VERIFIER_ENABLED=false",
        ])

        warning_message = "\n".join(warning_parts)

        # Check mode (warn vs block)
        mode = os.environ.get("CLEANUP_VERIFIER_MODE", "warn").lower()

        if mode == "block":
            return {
                "decision": "block",
                "reason": warning_message,
                "blocking_hook": "Stop.py:cleanup_verifier",
            }
        else:
            # Warn mode - print to stdout (not stderr, to avoid "hook error" false positive)
            print(f"[systemMessage]{warning_message}[/systemMessage]")
            return None

    except Exception as e:
        # Fail open - cleanup verifier should never break sessions
        _logger.error(f"[Stop] cleanup_verifier error: {e}")
        return None


def _load_tool_history(data: dict) -> list | None:
    """Load accumulated tool history from session file.

    Args:
        data: Stop hook input data (may contain session_id)

    Returns:
        List of tool entries or None if file missing/unreadable
    """
    try:
        # Extract session_id from Stop hook data
        session_id = (
            data.get("session_id")
            or data.get("sessionId")
            or data.get("conversation_id")
            or data.get("conversationId")
            or os.environ.get("CLAUDE_SESSION_ID", "")
        ).strip()

        if not session_id:
            # No session_id, cannot locate history file
            return None

        # Sanitize session_id for filename
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)

        # Determine history file path
        state_dir = Path(os.environ.get(
            "CLEANUP_TRACKER_DIR",
            "P:/.claude/state"
        ))
        history_file = state_dir / f"cleanup_history_{safe_session}.json"

        # Check if file exists
        if not history_file.exists():
            return None

        # Load and parse history
        content = history_file.read_text(encoding="utf-8")
        history: dict[str, list[dict[str, object]]] = json.loads(content)

        # Extract tool list
        return history.get("tools", [])

    except (json.JSONDecodeError, OSError, KeyError):
        # File unreadable or corrupted
        return None


def detect_work_type(tool_history: list) -> str | None:
    """Detect work type from tool history.

    Returns: work_type string or None if undetectable
    """
    if not tool_history:
        return None

    # Count tool usage patterns
    tools_used = [tool.get("name", "") for tool in tool_history]

    # Bug fix pattern: Edit files + (Read/Grep for investigation)
    if "Edit" in tools_used or "Write" in tools_used:
        # Check for investigation tools (Read, Grep, Glob)
        investigation_tools = sum(1 for t in tools_used if t in ("Read", "Grep", "Glob", "Find"))
        # Check for hook-related files
        hook_files = any("hook" in str(tool.get("input", {})).lower() for tool in tool_history)

        if hook_files:
            return "hook_dev"
        elif investigation_tools > 0:
            return "bug_fix"
        else:
            # Check for documentation patterns before defaulting to feature_dev
            doc_patterns = ["claude.md", "readme.md", "skill.md", "documentation"]
            all_inputs = " ".join(str(tool.get("input", {})) for tool in tool_history)
            if any(pattern in all_inputs.lower() for pattern in doc_patterns):
                return "documentation"
            else:
                return "feature_dev"

    # Test development
    if any(t in tools_used for t in ("Bash", "Task")):
        # Check if bash commands include pytest/python test runs
        bash_commands = [
            str(tool.get("input", {})).lower()
            for tool in tool_history
            if tool.get("name") == "Bash"
        ]
        test_keywords = ["pytest", "python -m pytest", "test_", "unittest"]
        if any(kw in " ".join(bash_commands) for kw in test_keywords):
            return "testing"

    # Architecture work
    if "Skill" in tools_used:
        skills_invoked = [
            str(tool.get("input", {})).lower()
            for tool in tool_history
            if tool.get("name") == "Skill"
        ]
        if any("arch" in s for s in skills_invoked):
            return "architecture"

    return None


def check_cleanup_requirements(work_type: str, tool_history: list, response: str, data: dict) -> list:
    """Check cleanup requirements for work type.

    Returns: List of missing cleanup steps (empty if all complete)
    """
    issues = []
    project_root = Path(data.get("project_root", "P:/"))

    if work_type == "bug_fix":
        # Check 1: bugfixes.md updated
        bugfixes_path = Path(project_root) / ".serena" / "memories" / "bugfixes.md"
        if bugfixes_path.exists():
            content = bugfixes_path.read_text(encoding="utf-8")
            # Check if recent entry exists (today's date or recent dates)
            import datetime
            recent_dates = [
                (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
                for i in range(7)
            ]
            if not any(date in content for date in recent_dates):
                issues.append("Document bug fix in .serena/memories/bugfixes.md with date, problem, root cause, fix")

        # Check 2: Git commit
        bash_commands = [
            str(tool.get("input", ""))
            for tool in tool_history
            if tool.get("name") == "Bash"
        ]
        if not any("git commit" in cmd for cmd in bash_commands):
            if "git commit" not in response.lower():
                issues.append("Create git commit with descriptive message")

    elif work_type == "hook_dev":
        # Check 1: Hook tested
        bash_commands = [
            str(tool.get("input", {})).lower()
            for tool in tool_history
            if tool.get("name") == "Bash"
        ]
        test_commands = ["pytest", "python", "test"]
        if not any(any(kw in cmd for kw in test_commands) for cmd in bash_commands):
            if not any(kw in response.lower() for kw in test_commands):
                issues.append("Test hook changes (pytest or manual test)")

        # Check 2: Document in CLAUDE.md
        if "claude.md" not in response.lower():
            if not any("claude.md" in str(tool.get("input", "")).lower() for tool in tool_history if tool.get("name") in ("Read", "Edit", "Write")):
                issues.append("Document hook in .claude/hooks/CLAUDE.md")

    elif work_type == "architecture":
        # Check: ADR created
        arch_decisions_dir = Path(project_root) / "docs" / "adrs"
        if arch_decisions_dir.exists():
            # Check for recent ADR files
            import datetime
            adrs = list(arch_decisions_dir.glob("*.md"))
            if adrs:
                most_recent = max(adrs, key=lambda p: p.stat().st_mtime)
                mtime = datetime.datetime.fromtimestamp(most_recent.stat().st_mtime)
                if (datetime.datetime.now() - mtime).days > 1:
                    issues.append("Create ADR in docs/adrs/ (YYYY-MM-DD-{topic}.md)")
            else:
                issues.append("Create ADR in docs/adrs/ (YYYY-MM-DD-{topic}.md)")

    elif work_type == "documentation":
        # Check: References updated
        if "reference" not in response.lower() and "link" not in response.lower():
            issues.append("Check for broken references (grep for old paths/names)")

    elif work_type == "feature_dev":
        # Check 1: Update project CLAUDE.md
        project_claude_md = Path(project_root) / "CLAUDE.md"
        if project_claude_md.exists():
            # Check if CLAUDE.md was edited in this session
            claude_edited = any(
                "claude.md" in str(tool.get("input", "")).lower()
                for tool in tool_history
                if tool.get("name") in ("Read", "Edit", "Write")
            )
            if not claude_edited and "claude.md" not in response.lower():
                issues.append("Update project CLAUDE.md with new features/architecture")

    elif work_type == "testing":
        # Check 1: Tests added to test suite
        bash_commands = [
            str(tool.get("input", {})).lower()
            for tool in tool_history
            if tool.get("name") == "Bash"
        ]
        # Check if tests were created/edited
        test_files_edited = any(
            any(ext in str(tool.get("input", "")).lower() for ext in ("test_", "_test.py", "test.py", "tests/"))
            for tool in tool_history
            if tool.get("name") in ("Edit", "Write")
        )
        if not test_files_edited:
            if not any(kw in " ".join(bash_commands) for kw in ("pytest", "python -m pytest", "unittest")):
                issues.append("Add tests to test suite (pytest or unittest)")

    return issues


if __name__ == "__main__":
    # For direct execution via hook_runner.py
    import json
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    if result and result.get("decision") == "block":
        print(json.dumps(result))
        sys.exit(2)
    else:
        print("{}")
        sys.exit(0)
