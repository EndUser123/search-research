#!/usr/bin/env python3
"""
PreToolUse_task_self_doc_gate.py - Task self-documentation gate

Blocks TaskCreate/TaskUpdate operations when tasks lack proper self-documentation.
Validates that tasks explain the problem, situation, and symptoms.

TaskCreate: subject + description required
TaskUpdate: description required when status=completed (to explain why the task was closed)

Exit codes:
    0 = allow (valid documentation or bypass)
    2 = block (invalid documentation)

Environment variables:
    TASK_SELF_DOC_GATE_ENABLED: Enable the gate (default: true)
    TASK_SELF_DOC_GATE_BLOCKING: Use blocking mode (default: true)
        true = exit 2 to block, false = exit 0 with warning in stderr
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Add hooks directory to path for __lib imports
_HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(_HOOKS_DIR))

# Module logger — advisory-mode warnings go here (NOT stderr, which CC treats as
# hook error). Previously referenced but never defined → NameError on the advisory
# path (the "_logger failure in the self-documentation gate").
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

from __lib.task_self_doc_validator import (
    DEFAULT_MIN_DESC_LEN,
    DEFAULT_MIN_SUBJECT_LEN,
    self_documentation_check,
)


def _get_bypass() -> bool:
    """Check if bypass flag is present in environment."""
    return os.environ.get("TASK_SELF_DOC_BYPASS", "").lower() in ("1", "true", "yes")


def _is_task_gate_eligible(data: dict) -> tuple[bool, dict | None]:
    """
    Check if this is a TaskCreate or TaskUpdate operation.

    Returns (is_eligible, tool_input).
    """
    tool_name = data.get("tool_name", "")
    if tool_name not in ("TaskCreate", "TaskUpdate"):
        return False, None

    tool_input = data.get("tool_input", {})
    return True, tool_input


def _validate_task_doc(tool_input: dict, tool_name: str = "TaskCreate") -> tuple[bool, str]:
    """
    Validate task self-documentation.

    TaskCreate: subject + description required
    TaskUpdate: description required only when status=completed

    Returns (is_valid, reason).
    """
    subject = tool_input.get("subject", "")
    description = tool_input.get("description", "")

    if tool_name == "TaskUpdate":
        # For TaskUpdate, the description field is optional — only set on
        # completion if the caller wants to add closing notes. Block the
        # task close with a self-doc advisory only if the caller
        # explicitly provides a description AND it's too thin. Don't
        # require a description just to close a task: the description
        # was provided at TaskCreate time and is already on the record.
        status = tool_input.get("status", "")
        if status != "completed":
            return True, "Valid"
        if not description.strip():
            # No closing notes provided; allow close (description already
            # exists from TaskCreate).
            return True, "Valid"
        # If the caller DID add a description, validate it as a real
        # completion note (Problem + at least one of Situation/Symptom).
        desc_result = self_documentation_check(
            "TaskUpdate completion", description,
            require_all=False,
            require_problem=True,
        )
        if desc_result.is_valid:
            return True, "Valid"

        missing = ", ".join(desc_result.missing_categories) if desc_result.missing_categories else "unknown"
        warnings = "; ".join(desc_result.warnings) if desc_result.warnings else ""

        reason = f"TaskUpdate self-documentation incomplete. Missing: {missing}."
        if warnings:
            reason += f" {warnings}"
        reason += (
            f"\n\nSchema: Problem (what issue?) + Situation (when/where?) + Symptom (what observable?)."
            f"\nDescription: {len(description)}/{DEFAULT_MIN_DESC_LEN} chars."
        )
        return False, reason

    # TaskCreate: Problem mandatory + at least one of Situation/Symptom for context
    result = self_documentation_check(subject, description, require_all=False, require_problem=True)

    if result.is_valid:
        return True, "Valid"

    missing = ", ".join(result.missing_categories) if result.missing_categories else "unknown"
    warnings = "; ".join(result.warnings) if result.warnings else ""

    reason = f"Task self-documentation incomplete. Missing: {missing}."
    if warnings:
        reason += f" {warnings}"
    reason += (
        f"\n\nSchema: Problem (what issue?) + Situation (when/where?) + Symptom (what observable?)."
        f"\nSubject: {len(subject)}/{DEFAULT_MIN_SUBJECT_LEN} chars."
        f"\nDescription: {len(description)}/{DEFAULT_MIN_DESC_LEN} chars."
    )

    return False, reason


def _auto_correct_params(tool_input: dict, tool_name: str = "TaskCreate") -> dict | None:
    """
    Auto-correct common wrong parameter names.

    TaskCreate: name, title -> subject
    TaskUpdate: task_id -> taskId (camelCase is correct for built-in TaskUpdate)

    Returns corrected tool_input dict with corrections applied, or None if no corrections needed.
    """
    corrections: dict[str, str] = {}

    if tool_name == "TaskCreate":
        if "name" in tool_input and "subject" not in tool_input:
            corrections["name"] = "subject"
        elif "title" in tool_input and "subject" not in tool_input:
            corrections["title"] = "subject"
    elif tool_name == "TaskUpdate":
        if "task_id" in tool_input and "taskId" not in tool_input:
            corrections["task_id"] = "taskId"
        # Collision (both task_id and taskId present): keep taskId, remove task_id — handled below

    if not corrections:
        return None

    # Apply corrections
    corrected = dict(tool_input)
    for wrong_param, correct_param in corrections.items():
        corrected[correct_param] = corrected.pop(wrong_param)

    # Handle collision case: when both taskId and task_id were present,
    # we kept taskId (correct) and auto-corrected task_id -> taskId.
    # Now remove the leftover task_id key if it still exists.
    if tool_name == "TaskUpdate" and "task_id" in corrected and "taskId" in corrected:
        corrected.pop("task_id")

    print(
        f"Auto-corrected {tool_name} params: {list(corrections.keys())} -> {list(corrections.values())}",
        file=sys.stderr,
    )
    return corrected


def run(data: dict) -> dict | None:
    """
    Run the task self-documentation gate.

    Returns None to allow, or dict with decision/reason to block.
    """
    enabled = os.environ.get("TASK_SELF_DOC_GATE_ENABLED", "true").lower()
    if enabled not in ("1", "true", "yes"):
        return None

    is_eligible, tool_input = _is_task_gate_eligible(data)
    if not is_eligible or tool_input is None:
        return None

    tool_name = data.get("tool_name", "TaskCreate")

    # Check bypass
    if _get_bypass():
        return None

    # Auto-correct wrong parameter names before validation
    corrected = _auto_correct_params(tool_input, tool_name)
    if corrected is None and tool_name == "TaskUpdate":
        # Collision case: both taskId (correct) and task_id (wrong) present.
        # Resolve by removing task_id, keeping taskId.
        if "taskId" in tool_input and "task_id" in tool_input:
            corrected = dict(tool_input)
            corrected.pop("task_id")
    if corrected is not None:
        # For TaskUpdate without status=completed, skip self-doc validation since
        # no description requirement exists for non-completion updates.
        # Note: Auto-correct still runs (e.g. task_id -> taskId) but validation
        # is intentionally bypassed for non-completion status. This is safe because
        # the built-in TaskUpdate tool validates params; we only add guidance.
        status = corrected.get("status", "")
        if tool_name == "TaskUpdate" and status != "completed":
            return {"decision": "modify", "tool_input": corrected}
        # Validate self-doc on corrected input (not just for TaskUpdate with status=completed)
        is_valid, reason = _validate_task_doc(corrected, tool_name)
        if is_valid:
            # Input is valid after correction - allow with modifications
            return {"decision": "modify", "tool_input": corrected}

        # Still invalid after correction
        blocking = os.environ.get("TASK_SELF_DOC_GATE_BLOCKING", "true").lower()
        if blocking in ("1", "true", "yes"):
            return {"decision": "block", "reason": reason}
        # Advisory mode: warn but allow
        _logger.warning("%s", reason)
        return {"decision": "modify", "tool_input": corrected}

    is_valid, reason = _validate_task_doc(tool_input, tool_name)

    if is_valid:
        return None

    blocking = os.environ.get("TASK_SELF_DOC_GATE_BLOCKING", "true").lower()
    if blocking in ("1", "true", "yes"):
        return {"decision": "block", "reason": reason}
    else:
        # Advisory mode: write warning to stderr and allow
        _logger.warning("%s", reason)
        return None


def main() -> int:
    """Command-line entry point for standalone hook execution.

    Emits stdout JSON so PreToolUse.run_hook can propagate block/modify decisions
    (and surface the block reason to the model). Malformed input fails OPEN — this
    is a quality gate, not a security gate; a malformed payload must not block
    legitimate task operations or crash with a traceback.
    """
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Fail-open: cannot validate a payload we cannot parse. No traceback.
        _logger.warning("task_self_doc_gate: malformed JSON input, failing open")
        return 0
    if not isinstance(data, dict):
        _logger.warning("task_self_doc_gate: non-dict input, failing open")
        return 0

    try:
        result = run(data)
    except Exception as exc:  # never crash the tool call
        _logger.warning("task_self_doc_gate: run() raised %s, failing open", exc)
        return 0

    if result is None:
        return 0  # Allow

    # Propagate decision as stdout JSON (run_hook parses stdout first).
    if result.get("decision") in ("block", "modify"):
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
