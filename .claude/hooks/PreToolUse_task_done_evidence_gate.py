#!/usr/bin/env python3
"""
PreToolUse task done evidence gate.

Blocks TaskUpdate(status="completed") unless:
  - commit_hash argument is present, OR
  - evidence_file argument is present, OR
  - skip_evidence=true argument is present (logged, not blocked)

Exit codes:
  0 = allow
  2 = block (missing evidence)

Env vars:
  TASK_DONE_EVIDENCE_ENABLED=true (default: true)
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_ENABLED = os.environ.get("TASK_DONE_EVIDENCE_ENABLED", "true").lower() == "true"
_EVIDENCE_LOG = Path(os.path.expanduser("~/.claude/state/task_tracker/evidence_skips.jsonl"))


def _log_skip(task_id: str, reason: str) -> None:
    _EVIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "task_id": task_id,
        "reason": reason,
    }
    with open(_EVIDENCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check(tool_input: dict) -> tuple[bool, str]:
    """Return (allowed, reason)."""
    status = tool_input.get("status", "")
    if status != "completed":
        return True, ""

    if not _ENABLED:
        return True, "gate disabled"

    task_id = tool_input.get("taskId") or tool_input.get("task_id", "?")

    skip = tool_input.get("skip_evidence", "")
    if str(skip).lower() in ("true", "1", "yes"):
        _log_skip(task_id, "skip_evidence=true")
        return True, ""

    commit = tool_input.get("commit_hash", "")
    if commit and len(commit.strip()) >= 8:
        return True, ""

    evidence = tool_input.get("evidence_file", "")
    if evidence and os.path.exists(evidence):
        return True, ""

    return (
        False,
        f"BLOCKED: Provide commit_hash or evidence_file when marking task #{task_id} completed.\n"
        f"Examples:\n"
        f"  TaskUpdate(taskId=\"{task_id}\", status=\"completed\", "
        f"commit_hash=\"abc12345\", description=\"...\")\n"
        f"  TaskUpdate(taskId=\"{task_id}\", status=\"completed\", "
        f"evidence_file=\"P:/tmp/evidence.txt\", description=\"...\")\n"
        f"Or pass skip_evidence=true for intentional non-evidence completions (logged)."
    )


def main():
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data)
    except json.JSONDecodeError:
        return  # malformed input, don't block
    tool_input = data.get("tool_input", {})
    allowed, reason = check(tool_input)
    if not allowed:
        print(reason, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
