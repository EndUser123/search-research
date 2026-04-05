#!/usr/bin/env python3
from __future__ import annotations

# Import auto-logging decorator
from __lib.hook_base import hook_main

"""
Automatic CKS Storage Hook - Session Accumulation
================================================

Accumulates work during session and stores to CKS at session end.
Filters for significant work only (not trivial edits).

HOOK TYPE: PostToolUse (accumulates) + SessionEnd (stores)

Design:
- Accumulates Edit/Write/Task results in memory
- Filters by: edit size, file type, success
- Stores to CKS when session ends (detect via timeout or manual trigger)

Author: CSF v2.4
Version: 1.1.0
"""

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent
from typing import Any

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "__csf" / "src" / "lib"))

try:
    from core_utils.agent_factory.cks_integration import store_to_cks
    CKS_INTEGRATION_AVAILABLE = True
except ImportError:
    CKS_INTEGRATION_AVAILABLE = False
    store_to_cks = None

# Session state file
STATE_FILE = hooks_dir / "session_data/auto_cks_state.json"

# Minimum edit size to store (characters)
MIN_EDIT_SIZE = 100

# File types to track (production code)
TRACKED_PATTERNS = [
    "src/**/*.py",
    "src/**/*.ts",
    "src/**/*.js",
    "lib/**/*.py",
    "__csf/**/*.py",
    ".claude/hooks/**/*.py",
]

# File types to ignore (tests, configs, docs)
IGNORE_PATTERNS = [
    "**/test*.py",
    "**/*test*.py",
    "**/tests/**",
    "**/*.md",
    "**/*.txt",
    "**/*.json",
    "**/.git/**",
]


def should_track_file(file_path: str) -> bool:
    """Check if file should be tracked."""
    path_lower = file_path.lower()

    # Check ignore patterns first
    for pattern in IGNORE_PATTERNS:
        pattern_lower = pattern.lower().replace("**", "")
        if pattern_lower in path_lower:
            return False

    # Check tracked patterns (substring matching)
    tracked_dirs = ["src/", "lib/", "__csf/", ".claude/hooks/"]
    for pattern in TRACKED_PATTERNS:
        pattern_lower = pattern.lower().replace("**", "")
        if pattern_lower in path_lower:
            return True

    # Fallback: check if path contains key directories
    return any(d in path_lower for d in tracked_dirs)


def _load_intent_state() -> dict | None:
    """Load intent from session state if available."""
    try:
        intent_state_file = hooks_dir / "session_data/intent_state.json"
        if intent_state_file.exists():
            with open(intent_state_file) as f:
                state = json.load(f)
                return state.get("current_intent")
    except Exception:
        pass
    return None


def _store_work_item_immediate(work_item: dict) -> None:
    """Store a single work item immediately to CKS with intent context."""
    if not CKS_INTEGRATION_AVAILABLE or store_to_cks is None:
        return

    try:
        # Load intent to add context
        intent = _load_intent_state()

        # Format as CKS entry with intent context
        work_type = intent.get("work_type", "unknown") if intent else "unknown"
        target = intent.get("target", "unspecified") if intent else "unspecified"
        problem = intent.get("problem", "Not specified") if intent else "Not specified"

        # Build question with work type and target
        if work_type != "unknown":
            question = f"{work_type}: {target}"
        else:
            question = f"{work_item['tool']}: {work_item.get('file_path', 'unknown')}"

        # Build answer with problem context
        answer_parts = []
        if intent and problem != "Not specified":
            answer_parts.append(f"Problem: {problem}")
            answer_parts.append(f"User intent: {intent.get('user_prompt', '')[:100]}")
            answer_parts.append("")

        answer_parts.append("Changes made:")
        answer_parts.append(f"  Modified: {work_item.get('file_path', 'unknown')}")
        answer_parts.append(f"  Size: {work_item.get('size', 0)} characters")

        if work_item.get('content_preview'):
            preview = work_item['content_preview'][:300]
            answer_parts.append("")
            answer_parts.append("Code preview:")
            answer_parts.append(f"  {preview}")

        answer_parts.append("")
        answer_parts.append(f"Timestamp: {work_item.get('timestamp', '')}")

        answer = "\n".join(answer_parts)

        # Build metadata with intent information
        metadata = {
            "source": "claude_code_auto_immediate",
            "tool": work_item.get("tool"),
            "file_path": work_item.get("file_path"),
            "size": work_item.get("size", 0),
            "stored_at": datetime.now(UTC).isoformat(),
        }

        # Add intent context if available
        if intent:
            metadata.update({
                "work_type": work_type,
                "target": target,
                "problem": problem[:200],  # Truncate for metadata
                "user_intent": intent.get("user_prompt", "")[:200],
            })

        # Store immediately (fail silently if CKS unavailable)
        store_to_cks(question, answer, metadata=metadata)

    except Exception:
        # Fail silently - immediate storage is best-effort
        pass


def load_state() -> dict:
    """Load session state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass

    return {
        "session_start": time.time(),
        "last_update": time.time(),
        "accumulated_work": [],
        "total_edits": 0,
        "total_writes": 0,
        "total_tasks": 0,
    }


def save_state(state: dict) -> None:
    """Save session state."""
    state["last_update"] = time.time()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def accumulate_work(tool: str, tool_input: dict, tool_response: Any, state: dict) -> None:
    """Accumulate work for later storage."""
    # Only track Edit, Write, Task tools
    if tool not in ["Edit", "Write", "Task"]:
        return

    work_item = {
        "tool": tool,
        "timestamp": datetime.now(UTC).isoformat(),
        "file_path": None,
        "content_preview": None,
        "size": 0,
    }

    # Extract relevant info based on tool
    if tool in ["Edit", "Write"]:
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return

        # Check if we should track this file
        if not should_track_file(file_path):
            return

        # Check edit size
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        content_size = len(new_string)

        if tool == "Edit" and content_size < MIN_EDIT_SIZE:
            return

        work_item["file_path"] = file_path
        work_item["content_preview"] = new_string[:200] + "..." if len(new_string) > 200 else new_string
        work_item["size"] = content_size

        if tool == "Edit":
            state["total_edits"] += 1
        else:
            state["total_writes"] += 1

    elif tool == "Task":
        description = tool_input.get("description", "")
        agent_type = tool_input.get("agent_type", "")

        work_item["file_path"] = f"Task: {agent_type}"
        work_item["content_preview"] = description
        work_item["size"] = len(description)

        state["total_tasks"] += 1

        # IMMEDIATE STORAGE: Store tasks immediately
        _store_work_item_immediate(work_item)

    # Add to accumulated work
    state["accumulated_work"].append(work_item)
    save_state(state)


def should_store_to_cks(state: dict) -> bool:
    """Determine if accumulated work is significant enough to store."""
    # Store if:
    # - 5+ edits/writes, OR
    # - 1+ Task tool usage, OR
    # - Session active for 30+ minutes with some work

    work_count = state["total_edits"] + state["total_writes"]
    task_count = state["total_tasks"]
    session_duration = time.time() - state["session_start"]

    return (
        work_count >= 5 or
        task_count >= 1 or
        (session_duration > 1800 and work_count >= 2)  # 30 min + some work
    )


def format_question_from_state(state: dict) -> str:
    """Format a question/title from accumulated work."""
    work_items = state["accumulated_work"]

    if not work_items:
        return "Claude Code session work"

    # Get the most common file paths
    file_counts = {}
    for item in work_items:
        fp = item.get("file_path", "unknown")
        file_counts[fp] = file_counts.get(fp, 0) + 1

    # Get top file
    top_file = max(file_counts, key=file_counts.get) if file_counts else "unknown"

    # Build question
    if state["total_tasks"] > 0:
        question = f"Session with {state['total_tasks']} subagent tasks and {state['total_edits'] + state['total_writes']} edits"
    elif state["total_edits"] + state["total_writes"] > 0:
        question = f"Session with {state['total_edits'] + state['total_writes']} file modifications"
    else:
        question = "Claude Code session work"

    # Add top file context
    if top_file != "unknown" and top_file.startswith("P:/"):
        # Extract meaningful part
        try:
            top_file_short = top_file.split("P:/")[-1]
            question += f" in {top_file_short}"
        except:
            pass

    return question


def format_answer_from_state(state: dict) -> str:
    """Format answer/content from accumulated work."""
    work_items = state["accumulated_work"]

    if not work_items:
        return "No significant work accumulated."

    lines = [
        "# Session Work Summary",
        "",
        f"Total edits: {state['total_edits']}",
        f"Total writes: {state['total_writes']}",
        f"Total tasks: {state['total_tasks']}",
        "",
        "## Work Items",
        ""
    ]

    # Group by file
    by_file = {}
    for item in work_items:
        fp = item.get("file_path", "unknown")
        if fp not in by_file:
            by_file[fp] = []
        by_file[fp].append(item)

    # Format each file's work
    for fp, items in by_file.items():
        lines.append(f"### {fp}")
        lines.append(f"Operations: {len(items)}")

        for item in items[:5]:  # Limit to 5 per file
            tool = item.get("tool", "")
            preview = item.get("content_preview", "")
            size = item.get("size", 0)

            lines.append(f"- {tool}: {size} chars")
            if preview:
                lines.append(f"  {preview[:100]}...")

        lines.append("")

    return "\n".join(lines)


def store_accumulated_work(state: dict) -> bool:
    """Store accumulated work to CKS."""
    if not should_store_to_cks(state):
        return False

    if not CKS_INTEGRATION_AVAILABLE or store_to_cks is None:
        return False

    question = format_question_from_state(state)
    answer = format_answer_from_state(state)

    metadata = {
        "source": "claude_code_auto",
        "session_work_count": len(state["accumulated_work"]),
        "total_edits": state["total_edits"],
        "total_writes": state["total_writes"],
        "total_tasks": state["total_tasks"],
        "session_duration_seconds": time.time() - state["session_start"],
        "stored_at": datetime.now(UTC).isoformat(),
    }

    success = store_to_cks(question, answer, metadata=metadata)

    if success:
        # Reset state after successful storage
        state["accumulated_work"] = []
        state["total_edits"] = 0
        state["total_writes"] = 0
        state["total_tasks"] = 0
        state["session_start"] = time.time()
        save_state(state)

    return success


@hook_main
def main():
    """Main hook entry point."""
    input_data = json.load(sys.stdin)

    hook_type = os.getenv("AUTO_CKS_HOOK_TYPE", "post_tool")

    result = {
        "passed": True,
        "action": "pass",
        "metadata": {
            "hook": "auto_cks_storage",
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    }

    if hook_type == "post_tool":
        # Accumulate work
        tool = input_data.get("tool", "")
        tool_input = input_data.get("input", {})
        tool_response = input_data.get("output", "")

        state = load_state()
        accumulate_work(tool, tool_input, tool_response, state)

        result["metadata"]["accumulated_count"] = len(state["accumulated_work"])
        result["metadata"]["should_store"] = should_store_to_cks(state)

    elif hook_type == "session_end":
        # Store accumulated work
        state = load_state()
        success = store_accumulated_work(state)

        result["metadata"]["stored"] = success
        result["metadata"]["work_count"] = len(state["accumulated_work"])

        # Silent success - only log errors
        DEBUG = os.environ.get("AUTO_CKS_DEBUG", "0") == "1"
        if success and DEBUG:
            log_hook_event(
                "auto_cks_storage",
                "info",
                f"Auto-stored {state['total_edits'] + state['total_writes']} edits, {state['total_tasks']} tasks to CKS"
            )

    print(json.dumps(result, default=str))
    sys.exit(0)

if __name__ == "__main__":
    main()
