#!/usr/bin/env python3
"""
PostToolUse Hook: Wrapper Argument Forwarding Validator

Automatically validates wrapper functions when .py or .ps1 files are
created or modified to detect argument forwarding bugs before they cause issues.

Supports:
- Python (.py) - Validates *args/**kwargs forwarding
- PowerShell (.ps1) - Validates @Args/@PSBoundParameters/$Args forwarding

This hook provides automatic validation feedback without requiring manual CLI
invocation of the argument validators.

Run: PostToolUse (after Edit/Write tools)
Timeout: 5 seconds
Exit Codes:
  - 0: Allow (always - advisory mode only)

Author: Claude Code
Date: 2026-03-15
Related: plan-20260315-wrapper-validator-enhancement.md
"""

import json
import sys
from pathlib import Path

# Add hooks lib to path for imports
hooks_lib = Path(__file__).resolve().parent / "__lib"
sys.path.insert(0, str(hooks_lib))

from argument_forwarding_validator import (
    ArgumentForwardingValidator,
    PowerShellArgumentForwardingValidator,
    PythonArgumentForwardingValidator,
)


def run(data: dict) -> dict | None:
    """Validate .py and .ps1 files after Write/Edit operations.

    Args:
        data: Hook data dictionary from PostToolUse event

    Returns:
        dict with validation findings if .py or .ps1 file was modified
        None otherwise
    """
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only validate on Write or Edit operations
    if tool_name not in ("Write", "Edit"):
        return None

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Check if file exists (may not for failed Write operations)
    path = Path(file_path)
    if not path.exists():
        return None

    # Determine validator based on file extension
    validators: list[ArgumentForwardingValidator] = []
    validation_type = ""

    if file_path.endswith(".py"):
        validators.append(PythonArgumentForwardingValidator())
        validation_type = "Python argument forwarding"
    elif file_path.endswith(".ps1"):
        validators.append(PowerShellArgumentForwardingValidator())
        validation_type = "PowerShell argument forwarding"
    else:
        return None  # Not a file type we validate

    # Run validation
    all_findings = []
    all_passed = True

    for validator in validators:
        result = validator.validate_file(path)
        all_findings.extend(result.findings)
        if not result.passed:
            all_passed = False

    # Only report findings if there are any (pass or fail)
    if all_findings:
        # Build summary
        if all_passed:
            status_icon = "✅"
            status_text = "PASS"
        else:
            status_icon = "❌"
            status_text = "FAIL"

        # Format findings as JSON output
        findings_data = {
            "decision": "allow",  # Always allow - advisory only
            "validation": validation_type,
            "file": str(file_path),
            "status": status_text,
            "findings": all_findings,
        }

        # Print to stdout (not stderr - that would trigger hook error)
        print(f"\n{status_icon} Wrapper Validation: {path.name} - {status_text}", file=sys.stdout)
        for finding in all_findings:
            print(f"  {finding}", file=sys.stdout)
        print(file=sys.stdout)

        # Return data for potential downstream processing
        return findings_data

    return None


if __name__ == "__main__":
    # Read hook data from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid JSON - allow operation
        sys.exit(0)

    # Run the validation
    run(input_data)

    # Always exit with success (advisory mode)
    sys.exit(0)
