"""
E2E Workflow Tracker - PostToolUse Hook

Tracks actual user workflow execution (not just tool calls).
Following security fixes from SEC-001, SEC-002 and performance from PERF-002.

Key Features:
1. Track skill invocations (UserPromptSubmit → skill execution → response)
2. Track multi-step workflows (tool sequences representing user workflows)
3. Track state changes (file writes, git operations, etc.)
4. Session isolation (session_id + terminal_id)

Storage: .claude/state/e2e_executions_{session_id}.jsonl
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Configuration
SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
MAX_LOG_RECORDS = 1000  # PERF-002: Rotate after 1000 records
SESSION_TTL_HOURS = 2  # PERF-002: Cleanup sessions inactive for 2 hours

# Valid field patterns (SEC-002)
WORKFLOW_TYPE_RE = re.compile(r"^[a-zA-Z0-9_]+$")
TARGET_RE = re.compile(r"^[a-zA-Z0-9_\s\-]+$")
STAGE_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")
STAGE_STATUS_RE = re.compile(r"^(passed|failed|skipped)$")


def _validate_session_id(session_id: str) -> str:
    """
    SEC-001: Validate session_id before filename construction.

    Args:
        session_id: Session identifier to validate

    Returns:
        Validated session_id

    Raises:
        ValueError: If session_id contains malicious characters
    """
    if not session_id or not isinstance(session_id, str):
        raise ValueError("Invalid session_id format")

    # Check length
    if len(session_id) > 100:
        raise ValueError("Invalid session_id format")

    # Check for path traversal attempts
    if ".." in session_id or session_id.startswith("/") or session_id.startswith("\\"):
        raise ValueError("Invalid session_id format")

    # Check for null bytes
    if "\x00" in session_id:
        raise ValueError("Invalid session_id format")

    # Validate against pattern
    if not SESSION_ID_RE.match(session_id):
        raise ValueError("Invalid session_id format")

    return session_id


def _validate_workflow_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    SEC-002: Validate all fields before JSONL write.

    Args:
        data: Workflow data to validate

    Returns:
        Validated data

    Raises:
        ValueError: If any field contains malicious content
    """
    # Validate workflow_type
    workflow_type = data.get("workflow_type", "")
    if not isinstance(workflow_type, str) or not WORKFLOW_TYPE_RE.match(workflow_type):
        raise ValueError("Invalid workflow_type")

    # Validate target
    target = data.get("target", "")
    if not isinstance(target, str) or not TARGET_RE.match(target):
        raise ValueError("Invalid target")

    # Validate stages
    stages = data.get("stages", [])
    if not isinstance(stages, list):
        raise ValueError("Invalid stages format")

    for stage in stages:
        if not isinstance(stage, dict):
            raise ValueError("Invalid stage format")

        stage_name = stage.get("stage", "")
        if not isinstance(stage_name, str) or not STAGE_NAME_RE.match(stage_name):
            raise ValueError("Invalid stage name")

        stage_status = stage.get("status", "")
        if not isinstance(stage_status, str) or not STAGE_STATUS_RE.match(stage_status):
            raise ValueError("Invalid stage status")

        duration_ms = stage.get("duration_ms")
        if duration_ms is not None and not isinstance(duration_ms, (int, float)):
            raise ValueError("Invalid stage duration")

    # Validate overall status
    overall = data.get("overall", "")
    valid_overall = ["success", "failure", "partial"]
    if overall not in valid_overall:
        raise ValueError("Invalid overall status")

    return data


def _rotate_log_if_needed(session_id: str, state_dir: Path) -> None:
    """
    PERF-002: Implement rolling log rotation.

    Archives log to .jsonl.old when MAX_LOG_RECORDS exceeded.

    Args:
        session_id: Validated session ID
        state_dir: State directory path
    """
    log_file = state_dir / f"e2e_executions_{session_id}.jsonl"

    if not log_file.exists():
        return

    # Count records
    try:
        with open(log_file, encoding="utf-8") as f:
            record_count = sum(1 for _ in f)

        if record_count >= MAX_LOG_RECORDS:
            # Archive to .old
            archive_file = state_dir / f"e2e_executions_{session_id}.jsonl.old"
            log_file.rename(archive_file)

            # Create new empty log
            log_file.touch()
    except OSError:
        # Don't fail if rotation fails
        pass


def _cleanup_expired_sessions(state_dir: Path) -> None:
    """
    PERF-002: Session cleanup based on TTL.

    Removes session files older than SESSION_TTL_HOURS.

    Args:
        state_dir: State directory path
    """
    now = datetime.now()
    cutoff = now - timedelta(hours=SESSION_TTL_HOURS)

    for log_file in state_dir.glob("e2e_executions_*.jsonl"):
        # Skip archived files
        if log_file.suffix == ".old":
            continue

        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if mtime < cutoff:
                log_file.unlink()
        except OSError:
            # Don't fail if cleanup fails
            pass


def track_workflow(
    workflow_type: str,
    target: str,
    session_id: str,
    terminal_id: str,
    stages: list[dict[str, Any]],
    overall: str,
    state_dir: Path | None = None,
) -> None:
    """
    Track end-to-end workflow execution.

    Args:
        workflow_type: Type of workflow (skill_invocation, multi_step, tool_chain)
        target: Skill name or workflow description
        session_id: Session identifier (validated for security)
        terminal_id: Terminal identifier
        stages: List of stage results with status and duration
        overall: Overall workflow status (success, failure, partial)
        state_dir: State directory (defaults to .claude/state)

    Raises:
        ValueError: If validation fails (SEC-001, SEC-002)
        IOError: If write fails
    """
    # Validate session_id (SEC-001)
    validated_session_id = _validate_session_id(session_id)

    # Prepare data
    data = {
        "ts": datetime.now().isoformat(),
        "workflow_type": workflow_type,
        "target": target,
        "session_id": validated_session_id,
        "terminal_id": terminal_id,
        "stages": stages,
        "overall": overall,
    }

    # Validate all fields (SEC-002)
    validated_data = _validate_workflow_fields(data)

    # Determine state directory
    if state_dir is None:
        # Default to P:/.claude/state (absolute path, not CWD-relative)
        # This prevents .claude/ from being created in arbitrary directories
        state_dir = Path("P:/") / ".claude" / "state"

    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)

    # PERF-002: Check log rotation
    _rotate_log_if_needed(validated_session_id, state_dir)

    # PERF-002: Cleanup expired sessions (occasionally)
    _cleanup_expired_sessions(state_dir)

    # Write to JSONL file
    log_file = state_dir / f"e2e_executions_{validated_session_id}.jsonl"

    try:
        # Serialize with ensure_ascii for security
        jsonl_line = json.dumps(validated_data, ensure_ascii=True)

        # Verify by parsing back (SEC-002)
        parsed = json.loads(jsonl_line)
        assert parsed == validated_data

        # Append to log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(jsonl_line + "\n")

    except (json.JSONDecodeError, AssertionError, OSError) as e:
        raise OSError(f"Failed to write workflow log: {e}")


def post_tool_use_hook(
    tool_name: str, tool_input: dict[str, Any], tool_output: dict[str, Any], context: dict[str, Any]
) -> None:
    """
    PostToolUse hook entry point.

    Analyzes tool usage to track workflows.

    Args:
        tool_name: Name of tool that was called
        tool_input: Input parameters to tool
        tool_output: Output from tool
        context: Execution context (session_id, terminal_id, etc.)
    """
    # Extract session and terminal IDs from context
    session_id = context.get("session_id", "unknown")
    terminal_id = context.get("terminal_id", "unknown")

    try:
        # Detect skill invocations
        if tool_name == "Skill":
            skill_name = tool_input.get("skill", "unknown")
            skill_output = tool_output.get("result", {})

            stages = []
            # Add UserPromptSubmit stage if timing available
            if "timing" in context:
                timing = context["timing"]
                if "user_prompt_submit" in timing:
                    stages.append(
                        {
                            "stage": "UserPromptSubmit",
                            "status": "passed",
                            "duration_ms": timing["user_prompt_submit"],
                        }
                    )

            # Add skill execution stage
            skill_duration = context.get("timing", {}).get("skill_execution", 0)
            stages.append(
                {
                    "stage": "skill_execution",
                    "status": "passed" if tool_output.get("success") else "failed",
                    "duration_ms": skill_duration,
                }
            )

            # Add response generation stage
            response_duration = context.get("timing", {}).get("response_generation", 0)
            stages.append(
                {
                    "stage": "response_generation",
                    "status": "passed",
                    "duration_ms": response_duration,
                }
            )

            # Track skill invocation
            track_workflow(
                workflow_type="skill_invocation",
                target=skill_name,
                session_id=session_id,
                terminal_id=terminal_id,
                stages=stages,
                overall="success" if tool_output.get("success") else "failure",
            )

        # Detect multi-step workflows (sequences of related tools)
        elif tool_name in ["Read", "Edit", "Write", "Bash"]:
            # These are often part of larger workflows
            # We track them as tool_chain stages
            tool_duration = context.get("timing", {}).get("tool_execution", 0)

            stage = {
                "stage": tool_name,
                "status": "passed" if tool_output.get("success") else "failed",
                "duration_ms": tool_duration,
            }

            # For now, track individual tool calls
            # In future, we could aggregate related calls into workflows
            track_workflow(
                workflow_type="tool_chain",
                target=f"{tool_name} operation",
                session_id=session_id,
                terminal_id=terminal_id,
                stages=[stage],
                overall="success" if tool_output.get("success") else "failure",
            )

    except (OSError, ValueError):
        # Don't fail the tool use if tracking fails
        # Just log the error (could integrate with evidence_store here)
        pass


# Export hook function
__all__ = ["post_tool_use_hook", "track_workflow"]
