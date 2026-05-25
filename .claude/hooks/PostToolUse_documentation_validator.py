#!/usr/bin/env python3
"""
PostToolUse hook: Documentation Validator

Validates that documentation written to skills directories meets quality standards.
This hook runs after Write/Edit operations on .md files in any skill directory,
checking for circular references, missing files, and version conflicts.

Trigger: PostToolUse event after Write/Edit operations
Output: Warning dict with validation issues (non-blocking), or permissionDecision=deny in blocking mode

Configuration:
    Uses .claude/docs-validate.local.md for mode, severity_threshold, auto_validate settings
    Defaults: mode=suggestive, severity_threshold=medium, auto_validate=true
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict
import logging as _li
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

# Constants for file path matching
MARKDOWN_EXTENSIONS = (".md", "SKILL.md")
SKILLS_DIR_PATTERN = "/skills/"

# Constants for issue display
MAX_HIGH_ISSUES_TO_SHOW = 3
MAX_MEDIUM_ISSUES_TO_SHOW = 3

# Constants for warning deduplication
DEDUPLICATION_STATE_FILE = Path("P:/.claude/state/warning_deduplication_state.json")

# Module-level import for mocking (imported here so tests can patch it)
# Will be None if not available, which is fine for graceful degradation
DocumentationValidator = None

# Try to import DocumentationValidator at module level for testability
# This import may fail if running in a test environment without the full skill setup
try:
    # We don't import it here directly because we need to add paths dynamically
    # Instead, we'll import it in _get_validator() and cache it at module level
    pass
except ImportError:
    pass


def _generate_deduplication_key(skill_root: Path, issue: dict[str, str | int]) -> str:
    """Generate a unique key for deduplicating warnings.

    Args:
        skill_root: Path to skill root directory
        issue: Issue dictionary from DocumentationValidator

    Returns:
        Unique key string for this warning (per-skill)
    """
    # Key based on skill root, issue type, and message
    # Severity is NOT part of the key (different severity, same warning = deduplicate)
    skill_id = str(skill_root)
    issue_type = issue.get("type", "")
    issue_message = issue.get("message", "")
    return f"{skill_id}:{issue_type}:{issue_message}"


def _filter_deduplicated_warnings(skill_root: Path, issues: list[Dict], disable_deduplication: bool = False) -> list[Dict]:
    """Filter out previously seen warning issues.

    Args:
        skill_root: Path to skill root directory
        issues: List of issue dictionaries from DocumentationValidator
        disable_deduplication: If True, skip deduplication filtering (for testing)

    Returns:
        Filtered list containing only new issues
    """
    if disable_deduplication:
        # Skip deduplication during testing
        return issues

    # Load previously seen warnings
    seen_warnings = _load_seen_warnings(DEDUPLICATION_STATE_FILE)

    # Filter issues to only show new warnings
    new_issues = []
    for issue in issues:
        key = _generate_deduplication_key(skill_root, issue)
        if key not in seen_warnings:
            new_issues.append(issue)
            seen_warnings.add(key)

    # Save updated seen warnings (only if there are new issues)
    if new_issues:
        _save_seen_warnings(DEDUPLICATION_STATE_FILE, seen_warnings)

    return new_issues


def _load_seen_warnings(state_file: Path) -> set[str]:
    """Load set of previously seen warning keys from state file.

    Args:
        state_file: Path to state JSON file

    Returns:
        Set of warning keys (empty if file doesn't exist or is invalid)
    """
    if not state_file.exists():
        return set()

    try:
        content = state_file.read_text(encoding='utf-8')
        data = json.loads(content)
        return set(data.get("seen_warnings", []))
    except (json.JSONDecodeError, UnicodeDecodeError, Exception):
        # If state file is corrupt, start fresh
        return set()


def _save_seen_warnings(state_file: Path, seen_warnings: set[str]) -> None:
    """Save set of seen warning keys to state file.

    Args:
        state_file: Path to state JSON file
        seen_warnings: Set of warning keys to save
    """
    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert set to list for JSON serialization
    data = {"seen_warnings": list(seen_warnings)}
    state_file.write_text(json.dumps(data, indent=2), encoding='utf-8')


def run(data: dict) -> dict:
    """PostToolUse hook to validate documentation.

    This hook validates markdown files written to skills directories
    to ensure documentation quality and prevent aspirational documentation.

    Args:
        data: Hook input data with keys:
            - tool_name: Name of tool that was executed (Write, Edit, etc.)
            - tool_input: Input parameters passed to the tool
            - tool_response: Response/result from the tool

    Returns:
        Warning dict if issues found, empty dict otherwise.
        Format: {"warning": "⚠️ DOCUMENTATION VALIDATION: ..."}
        In blocking mode: {"decision": "deny", "reason": "..."}
    """
    try:
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Early exit: only validate Write/Edit operations
        if tool_name not in ("Write", "Edit"):
            return {}

        # Early exit: only validate .md files
        file_path = tool_input.get("file_path", "")
        if not _is_markdown_file(file_path):
            return {}

        # Locate skill root directory
        skill_root = _find_skill_root(file_path)
        if skill_root is None:
            return {}

        # Load settings (uses defaults if file doesn't exist)
        settings = _load_settings(skill_root)
        if settings is None:
            settings = _get_default_settings()

        # Get validator and run validation
        validator = _get_validator(skill_root)
        if validator is None:
            return {}

        issues = validator.validate()

        # Apply warning deduplication (prevent showing same warning multiple times)
        # Disable deduplication during testing (via environment variable)
        disable_deduplication = os.environ.get("DISABLE_WARNING_DEDUPLICATION", "false").lower() == "true"
        issues = _filter_deduplicated_warnings(skill_root, issues, disable_deduplication)

        # Early exit: no issues found
        if not issues:
            return {}

        # Intelligent mode selection (or manual mode)
        auto_validate = settings.get("auto_validate", True)

        if auto_validate:
            # Dry-run analysis: recommend mode based on findings
            recommended_mode = _recommend_mode(issues)

            # Check if we should ask user (first time or mode change)
            should_ask = _should_ask_user(recommended_mode, settings, skill_root)
            _logger.debug(f"auto_validate={auto_validate}, recommended_mode={recommended_mode}, should_ask={should_ask}")

            if should_ask:
                # Show dry-run report and wait for user to configure
                return _report_findings(issues, recommended_mode, skill_root)

            # Use recommended mode without asking (user preference established)
            mode = recommended_mode
        else:
            # Manual mode: use configured mode
            mode = settings.get("mode", "suggestive")

        # Check mode - skip validation if off
        if mode == "off":
            return {}

        # Handle validation results based on mode
        if mode == "blocking":
            # Return permissionDecision=deny JSON
            high_issues = [i for i in issues if i["severity"] == "HIGH"]
            medium_issues = [i for i in issues if i["severity"] == "MEDIUM"]
            reason = f"Documentation validation failed: {len(high_issues)} HIGH, {len(medium_issues)} MEDIUM issues. Run /docs-validate for details."
            return {"decision": "deny", "reason": reason}
        else:
            # Suggestive mode (default): return warning dict
            return _format_validation_warnings(issues)

        return {}

    except ImportError as e:
        # Graceful degradation: validator module not available
        return {"warning": f"Documentation validator unavailable: {e}"}
    except Exception as e:
        # Don't break the write operation, but report the error
        return {"warning": f"Documentation validation error: {e}"}


def _is_markdown_file(file_path: str) -> bool:
    """Check if a file path has a markdown extension.

    Args:
        file_path: Path to check

    Returns:
        True if file ends with .md or SKILL.md, False otherwise
    """
    return file_path.endswith(MARKDOWN_EXTENSIONS)


def _find_skill_root(file_path: str) -> Path | None:
    """Find the skill root directory from a file path.

    Searches for a skills/ directory pattern to identify any skill root,
    not just the /package skill.

    Args:
        file_path: Path to a file within a skill directory

    Returns:
        Path to skill root, or None if not found
    """
    try:
        path = Path(file_path).resolve()

        # Extract skill root from path like P:/.claude/skills/skill-name/
        # Note: Don't use string pattern matching - it breaks on Windows paths.
        # Use path.parts which is platform-independent.
        if "skills" in path.parts:
            skills_idx = path.parts.index("skills")
            if skills_idx + 1 < len(path.parts):
                # Return path to skill directory: .../skills/skill-name
                return Path(path.drive).joinpath(*path.parts[: skills_idx + 2])

        return None
    except Exception:
        return None


def _get_validator(skill_root: Path) -> DocumentationValidator | None:
    """Get DocumentationValidator instance for a skill.

    Args:
        skill_root: Path to skill root directory

    Returns:
        DocumentationValidator instance if available, None otherwise
    """
    global DocumentationValidator

    # If DocumentationValidator is already set (e.g., by test mock), use it directly
    # This allows tests to patch hook_module.DocumentationValidator
    if DocumentationValidator is not None:
        return DocumentationValidator(skill_root)

    # Normal path: check if skill has resources/validate_docs.py
    resources_dir = skill_root / "resources"
    if not resources_dir.exists():
        return None

    # Import validator and return instance
    # IMPORTANT: Clean up sys.path after import to prevent test interference
    resources_path = str(resources_dir)
    sys.path.insert(0, resources_path)

    try:
        from validate_docs import DocumentationValidator as DV

        # Cache at module level for potential reuse and testability
        DocumentationValidator = DV

        return DocumentationValidator(skill_root)
    finally:
        # Remove from sys.path to prevent polluting other imports
        if resources_path in sys.path:
            sys.path.remove(resources_path)


def _get_default_settings() -> dict:
    """Get default validation settings.

    Returns:
        Default settings dict with mode, severity_threshold, auto_validate
    """
    return {
        "mode": "suggestive",
        "severity_threshold": "medium",
        "auto_validate": True
    }


def _load_settings(skill_root: Path) -> dict | None:
    """Load settings from .claude/docs-validate.local.md file.

    Args:
        skill_root: Path to skill root directory

    Returns:
        Settings dict if file exists and valid, None otherwise
    """
    settings_file = skill_root / ".claude" / "docs-validate.local.md"

    # Check if settings file exists
    if not settings_file.exists():
        return None

    try:
        content = settings_file.read_text(encoding='utf-8')

        # Parse YAML frontmatter (between --- markers)
        lines = content.split('\n')
        frontmatter_lines = []
        in_frontmatter = False

        for line in lines:
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    # Found closing ---
                    break
            elif in_frontmatter:
                frontmatter_lines.append(line)

        if not frontmatter_lines:
            return None

        # Parse key-value pairs from frontmatter
        settings = {}
        for line in frontmatter_lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Parse value based on type
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                # Remove quotes if present
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                settings[key] = value

        # Validate settings
        valid_modes = ['off', 'suggestive', 'blocking']
        if 'mode' in settings and settings['mode'] not in valid_modes:
            return None  # Invalid mode

        valid_thresholds = ['low', 'medium', 'high']
        if 'severity_threshold' in settings and settings['severity_threshold'] not in valid_thresholds:
            return None  # Invalid threshold

        return settings if settings else None

    except (FileNotFoundError, UnicodeDecodeError, Exception):
        # Any error reading/parsing -> use defaults
        return None


def _format_validation_warnings(issues: list[dict[str, str | int]]) -> dict:
    """Format validation issues into a warning message.

    Args:
        issues: List of issue dictionaries from DocumentationValidator

    Returns:
        Warning dict with formatted message
    """
    high_issues = [i for i in issues if i["severity"] == "HIGH"]
    medium_issues = [i for i in issues if i["severity"] == "MEDIUM"]

    output = [f"⚠️  Documentation validation: {len(high_issues)} HIGH, {len(medium_issues)} MEDIUM"]

    # Show first N HIGH severity issues with full details
    output.extend(_format_high_issues(high_issues[:MAX_HIGH_ISSUES_TO_SHOW]))

    # Show first N MEDIUM severity issues (summary only)
    output.extend(_format_medium_issues(medium_issues[:MAX_MEDIUM_ISSUES_TO_SHOW]))

    return {"warning": "\n".join(output)}


def _format_high_issues(issues: list[dict[str, str | int]]) -> list[str]:
    """Format HIGH severity issues with full details.

    Args:
        issues: List of HIGH severity issue dictionaries

    Returns:
        List of formatted strings
    """
    formatted = []
    for issue in issues:
        formatted.append(f"\n  ❌ {issue['type']}: {issue['message']}")
        formatted.append(f"     File: {issue['file']}")
        formatted.append(f"     Fix: {issue['fix']}")
    return formatted


def _format_medium_issues(issues: list[dict[str, str | int]]) -> list[str]:
    """Format MEDIUM severity issues as summary bullets.

    Args:
        issues: List of MEDIUM severity issue dictionaries

    Returns:
        List of formatted strings
    """
    formatted = []
    for issue in issues:
        formatted.append(f"\n  • {issue['message']}")
    return formatted


def _recommend_mode(issues: list[Dict]) -> str:
    """Recommend validation mode based on issue analysis.

    Args:
        issues: List of issue dictionaries from DocumentationValidator

    Returns:
        Recommended mode: "off", "suggestive", or "blocking"
    """
    if not issues:
        return "off"  # No issues, skip validation

    # Count issues by severity
    high_issues = [i for i in issues if i["severity"] == "HIGH"]
    medium_issues = [i for i in issues if i["severity"] == "MEDIUM"]

    # Smart mode selection
    if len(high_issues) >= 3:
        # 3+ HIGH issues = blocking (serious quality problem)
        return "blocking"
    elif len(high_issues) >= 1:
        # 1-2 HIGH issues = suggestive (warn but don't block)
        return "suggestive"
    elif len(medium_issues) >= 5:
        # 5+ MEDIUM issues = suggestive (quality concern)
        return "suggestive"
    else:
        # Few issues = off (skip validation, not worth interruption)
        return "off"


def _should_ask_user(recommended_mode: str, current_settings: dict, skill_root: Path) -> bool:
    """Determine if user interaction is needed.

    Args:
        recommended_mode: Mode recommended by _recommend_mode()
        current_settings: Current settings from _load_settings()
        skill_root: Path to skill root directory

    Returns:
        True if should ask user, False otherwise
    """
    # Check if user has previously made a preference for this skill
    preference_file = skill_root / ".claude" / "docs-validate.local.md"

    if not preference_file.exists():
        # First time validating this skill - always ask
        return True

    # Load current mode from settings
    current_mode = current_settings.get("mode", "suggestive")

    # Ask if mode would change (escalation or de-escalation)
    if recommended_mode != current_mode:
        # Mode escalation (suggestive → blocking) = ask
        if current_mode == "suggestive" and recommended_mode == "blocking":
            return True
        # Mode de-escalation (blocking → suggestive) = ask
        if current_mode == "blocking" and recommended_mode == "suggestive":
            return True
        # Turning on validation (off → anything) = ask
        if current_mode == "off":
            return True

    # Don't ask otherwise (non-intrusive)
    return False


def _report_findings(issues: list[Dict], recommended_mode: str, skill_root: Path) -> dict:
    """Generate dry-run report of validation findings.

    Args:
        issues: List of issue dictionaries from DocumentationValidator
        recommended_mode: Mode recommended by _recommend_mode()
        skill_root: Path to skill root directory

    Returns:
        Warning dict with dry-run report
    """
    high_issues = [i for i in issues if i["severity"] == "HIGH"]
    medium_issues = [i for i in issues if i["severity"] == "MEDIUM"]

    output = ["🔍 DRY-RUN: Documentation validation found issues"]
    output.append(f"📊 Issues: {len(high_issues)} HIGH, {len(medium_issues)} MEDIUM")
    output.append(f"💡 Recommended mode: {recommended_mode.upper()}")
    output.append(f"📁 Skill: {skill_root.name}")

    # Show first 3 HIGH issues
    if high_issues:
        output.append("\n🔴 HIGH severity issues:")
        for issue in high_issues[:3]:
            output.append(f"  • {issue['message']}")
            output.append(f"    File: {issue.get('file', 'unknown')}")
            output.append(f"    Fix: {issue.get('fix', 'see details')}")

    # Show first 3 MEDIUM issues
    if medium_issues:
        output.append("\n🟡 MEDIUM severity issues:")
        for issue in medium_issues[:3]:
            output.append(f"  • {issue['message']}")

    # Add mode explanation
    output.append("\n📖 Mode explanations:")
    output.append("  • OFF      - Skip validation (no warnings)")
    output.append("  • SUGGESTIVE - Show warnings, don't block")
    output.append("  • BLOCKING - Block write until fixed")

    # Add action prompt
    output.append("\n💬 To apply validation, create .claude/docs-validate.local.md:")
    output.append("```yaml")
    output.append("---")
    output.append(f"mode: {recommended_mode}")
    output.append("---")
    output.append("```")
    output.append("\nThen re-run your Write/Edit operation.")

    return {"warning": "\n".join(output)}
