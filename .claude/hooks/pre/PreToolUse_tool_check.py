#!/usr/bin/env python3
"""
PreToolUse Hook: Tool Parameter Validation

Purpose: Validate tool parameters BEFORE execution to prevent common errors.
Enforces Tool Usage Checklist from MEMORY.md.

Triggers: Before any tool use

Common Errors Prevented:
- Edit tool: replace_all="false" (string) instead of replace_all=False (boolean)
- Edit tool: old_string not unique in file
- Agent tool: Using Task tool for subagent spawning
- Bash tool: Windows path separators, invasive operations without detection

Enforced Protocols (from MEMORY.md):
- Tool Usage Checklist: Read docs, identify parameters, check types, look for examples
"""

import json
import sys

import logging as _li
_logger = _li.getLogger(__name__)

from pathlib import Path

# Tool parameter validation rules
TOOL_VALIDATION_RULES = {
    "Edit": {
        "replace_all": {
            "allowed_types": [bool],
            "error_message": "replace_all must be boolean (True/False or omit), not string 'false'",
            "prohibited_values": ["false", "true", "False", "True"],
            "fix": "Use replace_all=False or omit entirely (defaults to False)"
        },
        "old_string": {
            "requires": "unique_in_file",
            "error_message": "old_string must be unique in file - Edit tool will fail if pattern matches multiple locations",
            "fix": "Include more context to make old_string unique"
        }
    },
    "Agent": {
        "subagent_type": {
            "required": True,
            "error_message": "Agent tool requires subagent_type parameter (model is optional)",
            "fix": "Specify subagent_type (e.g., 'general-purpose', 'Explore')"
        },
        "model": {
            "allowed_values": ["sonnet", "opus", "haiku"],
            "optional": True,
            "error_message": "model must be 'sonnet', 'opus', or 'haiku'",
            "fix": "Omit model parameter (defaults to parent model) or use valid value"
        }
    },
    "Bash": {
        "command": {
            "forbidden_patterns": [
                ("\\\\", "Use forward slashes / in paths even on Windows"),
                ("rm -rf /", "Destructive operation - require user confirmation"),
                ("git push --force", "Force push - require user confirmation"),
                (":(?![/])", "Use forward slashes in file paths"),
            ],
            "requires_detection": ["rm", "delete", "drop", "force"],
            "error_message": "Invasive operations require detection commands first",
            "fix": "Run detection commands (ls, find, grep) before invasive operations"
        }
    },
    "Write": {
        "file_path": {
            "requires": "file_exists_check",
            "error_message": "Write tool requires Read first if file exists",
            "fix": "Read existing file before Write to prevent accidental overwrite"
        }
    },
    "TaskUpdate": {
        "taskId": {
            "required": True,
            "allowed_types": [str],
            "error_message": "TaskUpdate requires 'taskId' (camelCase), not 'task_id' (snake_case)",
            "prohibited_values": [],
            "fix": "Use taskId=<number> — the numeric task ID, not a parameter name"
        }
    }
}

def validate_tool_use(tool_name: str, tool_params: dict) -> dict:
    """
    Validate tool parameters against validation rules.

    Returns dict with:
    - valid: bool
    - errors: list of error messages
    - warnings: list of warning messages
    - fixes: list of suggested fixes
    """
    if tool_name not in TOOL_VALIDATION_RULES:
        return {"valid": True, "errors": [], "warnings": [], "fixes": []}

    rules = TOOL_VALIDATION_RULES[tool_name]
    errors = []
    warnings = []
    fixes = []

    for param_name, param_rules in rules.items():
        param_value = tool_params.get(param_name)

        # Check required parameters
        if param_rules.get("required") and param_value is None:
            errors.append(f"Missing required parameter: {param_name}")
            fixes.append(param_rules.get("fix", f"Provide {param_name} parameter"))
            continue

        # Skip validation if parameter not provided and optional
        if param_value is None and param_rules.get("optional", False):
            continue

        # Type validation for Edit.replace_all
        if tool_name == "Edit" and param_name == "replace_all":
            if isinstance(param_value, str):
                errors.append(f"{param_name}: {param_rules['error_message']}")
                fixes.append(param_rules['fix'])

        # Value validation for Agent.model
        if tool_name == "Agent" and param_name == "model":
            if param_value and param_value not in param_rules.get("allowed_values", []):
                errors.append(f"{param_name}: {param_rules['error_message']}")
                fixes.append(param_rules['fix'])

        # Type validation for TaskUpdate.taskId (must be str, not int or other)
        if tool_name == "TaskUpdate" and param_name == "taskId":
            allowed = param_rules.get("allowed_types", [])
            if param_value is not None and allowed and not any(isinstance(param_value, t) for t in allowed):
                type_names = ", ".join(t.__name__ for t in allowed)
                errors.append(f"{param_name}: must be {type_names}, got {type(param_value).__name__}")
                fixes.append(param_rules.get("fix", "Use taskId=<number>"))

        # Forbidden pattern detection for Bash
        if tool_name == "Bash" and param_name == "command":
            for pattern, message in param_rules.get("forbidden_patterns", []):
                if pattern in str(param_value):
                    errors.append(f"Command contains forbidden pattern: {pattern}")
                    fixes.append(message)

            # Check for invasive operations
            cmd_lower = str(param_value).lower()
            for invasive_op in param_rules.get("requires_detection", []):
                if invasive_op in cmd_lower:
                    # Check if detection command preceded this (would need context)
                    warnings.append(f"Invasive operation '{invasive_op}' detected")
                    fixes.append("Run detection commands first (ls, find, grep)")

        # File existence check for Write
        if tool_name == "Write" and param_name == "file_path":
            if Path(param_value).exists():
                warnings.append(f"File exists: {param_value}")
                fixes.append("Read existing file first to prevent accidental overwrite")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "fixes": fixes
    }

def main():
    """
    PreToolUse hook entry point.

    Read stdin for tool invocation JSON, validate parameters, exit with error code if invalid.
    """
    # Read tool invocation from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not JSON - skip validation (might be called during skill load)
        sys.exit(0)

    # Extract tool name and parameters
    tool_name = input_data.get("tool", "")
    tool_params = input_data.get("parameters", {})

    if not tool_name:
        sys.exit(0)

    # Validate tool use
    result = validate_tool_use(tool_name, tool_params)

    if not result["valid"]:
        # Validation failed - block the tool use
        _logger.error("## TOOL VALIDATION FAILED")
        print(f"\nTool: {tool_name}", file=sys.stderr)
        _logger.error(f"Parameters: {json.dumps(tool_params, indent=2)}")

        print(f"\nErrors Found: {len(result['errors'])}", file=sys.stderr)
        for i, error in enumerate(result["errors"], 1):
            _logger.error(f"  {i}. {error}")

        if result["warnings"]:
            print(f"\nWarnings: {len(result['warnings'])}", file=sys.stderr)
            for i, warning in enumerate(result["warnings"], 1):
                _logger.warning(f"  {i}. {warning}")

        print("\nSuggested Fixes:", file=sys.stderr)
        for i, fix in enumerate(result["fixes"], 1):
            _logger.info(f"  {i}. {fix}")

        print("\n📚 See MEMORY.md - Tool Usage Checklist", file=sys.stderr)

        sys.exit(1)

    elif result["warnings"]:
        # Validation passed with warnings - allow but notify
        _logger.warning("## TOOL VALIDATION WARNING")
        print(f"\nTool: {tool_name}", file=sys.stderr)
        print(f"\nWarnings: {len(result['warnings'])}", file=sys.stderr)
        for i, warning in enumerate(result["warnings"], 1):
            _logger.warning(f"  {i}. {warning}")
        print("\nProceeding with tool use...", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
