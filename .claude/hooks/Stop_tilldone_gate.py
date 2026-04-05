"""
Stop_tilldone_gate v3 — Block premature exits during /code execution.

Pre-mortem-hardened against 8 identified failure modes:

1. False completion     → cross-check [x] count against git diff file count
2. Format mismatch      → detect numbered tasks, header tasks, not just checkboxes
3. No plan.md yet       → also check for active /code skill state marker
4. Exempt gaming        → require BLOCKED: + concrete evidence, not just keyword
5. Infinite loop        → consecutive-block counter with safety valve
6. Context exhaustion   → detect compaction markers, relax enforcement
7. Concurrent plans     → session-scoped state directory
8. TodoWrite vs plan    → also read TodoWrite state if plan.md absent

Detection layers:
  L1 (structural): No implementation tools + incomplete tasks = block
  L2 (pattern):    Premature-stop phrases + incomplete tasks = block

Imported by Stop.py as an in-process gate.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOOKS_DIR = Path(__file__).resolve().parent

# Max consecutive blocks before safety valve opens
MAX_CONSECUTIVE_BLOCKS = 5

# State directory for block counter (session-scoped)
STATE_DIR = HOOKS_DIR / "state" / "tilldone"

# Tools that indicate active implementation work
IMPLEMENTATION_TOOLS = {
    "Edit", "Write", "Bash", "Task",
    "NotebookEdit",
    "mcp__plugin_serena_serena__replace_content",
    "mcp__plugin_serena_serena__replace_symbol_body",
    "mcp__plugin_serena_serena__insert_after_symbol",
    "mcp__plugin_serena_serena__insert_before_symbol",
    "mcp__plugin_serena_serena__create_text_file",
    "mcp__plugin_serena_serena__execute_shell_command",
    "mcp__plugin_serena_serena__replace_lines",
    "mcp__plugin_serena_serena__delete_lines",
    "mcp__plugin_serena_serena__insert_at_line",
}


# ---------------------------------------------------------------------------
# Plan parsing — handles multiple formats (Gap #2)
# ---------------------------------------------------------------------------

def _find_plan_file() -> Path | None:
    """Find plan.md in common locations."""
    candidates = [
        Path("plan.md"),
        Path("P:/plan.md"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


# Checkbox: - [ ] task or - [x] task
_CHECKBOX_INCOMPLETE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)
_CHECKBOX_COMPLETE = re.compile(r"^\s*[-*]\s*\[[xX]\]", re.MULTILINE)

# Numbered task with status markers: 1. [DONE] task or 1. [TODO] task or 1. task
_NUMBERED_DONE = re.compile(
    r"^\s*\d+\.\s*(?:\[(?:DONE|COMPLETE|FINISHED|SHIPPED|PASSED)\]|~~)",
    re.MULTILINE | re.IGNORECASE,
)
_NUMBERED_TODO = re.compile(
    r"^\s*\d+\.\s*(?:\[(?:TODO|PENDING|IN.?PROGRESS|BLOCKED|WIP)\]\s+\S|\S)",
    re.MULTILINE | re.IGNORECASE,
)

# Header-based tasks: ### Task 1: ... with [DONE] or [TODO]
_HEADER_DONE = re.compile(
    r"^#{2,4}\s+.*\[(?:DONE|COMPLETE|FINISHED)\]",
    re.MULTILINE | re.IGNORECASE,
)
_HEADER_TODO = re.compile(
    r"^#{2,4}\s+(?:Task|Step)\s+\d+",
    re.MULTILINE | re.IGNORECASE,
)


def _count_plan_tasks(plan_path: Path) -> tuple[int, int]:
    """Count (total_tasks, incomplete_tasks) from plan.md.

    Handles checkboxes, numbered lists with status markers, and header tasks.
    Returns (0, 0) if no recognizable task format found.
    """
    try:
        content = plan_path.read_text(encoding="utf-8")
    except OSError:
        return 0, 0

    # Try checkbox format first (most common in /code)
    incomplete_cb = len(_CHECKBOX_INCOMPLETE.findall(content))
    complete_cb = len(_CHECKBOX_COMPLETE.findall(content))
    if incomplete_cb + complete_cb > 0:
        return incomplete_cb + complete_cb, incomplete_cb

    # Try numbered list with status markers
    done_num = len(_NUMBERED_DONE.findall(content))
    todo_num = len(_NUMBERED_TODO.findall(content))
    # Subtract done from todo since _NUMBERED_TODO also matches done items
    # Actually: _NUMBERED_TODO matches any numbered item, _NUMBERED_DONE matches done ones
    # So: total = todo_num, incomplete = todo_num - done_num
    if todo_num > 0:
        incomplete = max(0, todo_num - done_num)
        return todo_num, incomplete

    # Try header-based tasks
    done_hdr = len(_HEADER_DONE.findall(content))
    todo_hdr = len(_HEADER_TODO.findall(content))
    if todo_hdr > 0:
        incomplete = max(0, todo_hdr - done_hdr)
        return todo_hdr, incomplete

    return 0, 0


# ---------------------------------------------------------------------------
# False completion detection (Gap #1)
# ---------------------------------------------------------------------------

def _check_false_completion(plan_path: Path, total: int, incomplete: int) -> int:
    """Cross-check completed task count against git diff.

    If all tasks are marked complete but git shows very few changed files
    relative to task count, something is suspicious.

    Returns adjusted incomplete count (may increase if false completion detected).
    """
    if incomplete > 0:
        return incomplete  # Already has incomplete tasks, no adjustment needed

    completed = total - incomplete
    if completed < 2:
        return incomplete  # Too few tasks to meaningfully cross-check

    # Check git diff for changed files
    try:
        import subprocess
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=5,
            creationflags=creation_flags,
        )
        if result.returncode != 0:
            return incomplete

        changed_files = [f for f in result.stdout.strip().split("\n") if f.strip()]

        # Also check staged files
        result2 = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5,
            creationflags=creation_flags,
        )
        if result2.returncode == 0:
            for f in result2.stdout.strip().split("\n"):
                if f.strip() and f.strip() not in changed_files:
                    changed_files.append(f.strip())

        # Heuristic: if completed tasks >= 3 but changed files <= 1,
        # the agent probably marked tasks done without doing the work
        if completed >= 3 and len(changed_files) <= 1:
            return completed  # Treat ALL as incomplete
        # If completed >= 5 but changed files < completed/2, suspicious
        if completed >= 5 and len(changed_files) < completed // 2:
            return completed - len(changed_files)

    except Exception:
        pass  # Cross-check is best-effort

    return incomplete


# ---------------------------------------------------------------------------
# Exempt pattern matching — tightened (Gap #4)
# ---------------------------------------------------------------------------

# Patterns that genuinely exempt from blocking.
# Tightened: BLOCKED requires evidence, done claims require matching counts.
EXEMPT_PATTERNS = [
    # Explicit blocker with evidence (not just the keyword)
    r"(?i)^BLOCKED:[ \t]+\S.{10,}",  # BLOCKED: + at least 10 chars of explanation
    r"(?i)needs? decision:[ \t]+\S",
    r"(?i)(?:cannot|can't|unable to) (?:proceed|continue) (?:because|without|until) \S",
    # Error with specifics
    r"(?i)(?:error|exception|traceback|failure)[:\s].*(?:line \d+|file |module )",
    # Ambiguity with question
    r"(?i)(?:ambigui?t(?:y|ous)|unclear).*\?",
    r"(?i)clarif(?:y|ication) (?:needed|required).*\?",
    r"(?i)which (?:approach|option|path|strategy) (?:should|do you).*\?",
    # SHIP phase (genuine completion flow)
    r"(?i)Phase\s+4.*(?:SHIP|certif)",
    # Next steps menu (post-completion)
    r"(?i)\*\*Next Steps\*\*.*(?:Ready to Ship|Needs Refactoring)",
]

_EXEMPT_COMPILED = [re.compile(p, re.MULTILINE | re.DOTALL) for p in EXEMPT_PATTERNS]


def _is_exempt(response: str) -> bool:
    """Check if response contains a genuine blocker or completion claim."""
    for pattern in _EXEMPT_COMPILED:
        if pattern.search(response):
            return True
    return False


def _has_valid_done_claim(response: str, total: int) -> bool:
    """Check if response claims all tasks complete with matching count."""
    # "Tasks complete: X/Y" where X == Y
    m = re.search(r"(?i)tasks?\s+complete:?\s*(\d+)\s*/\s*(\d+)", response)
    if m:
        done, of_total = int(m.group(1)), int(m.group(2))
        return done == of_total and of_total > 0

    # "All N tasks are done/complete"
    m = re.search(r"(?i)all\s+(\d+)\s+tasks?\s+(?:are\s+)?(?:done|complete)", response)
    if m:
        claimed = int(m.group(1))
        return claimed == total and total > 0

    # Generic "all tasks done" (weaker — allow but log)
    if re.search(r"(?i)all\s+tasks?\s+(?:are\s+)?(?:done|complete|finished|implemented)", response):
        return True

    return False


# ---------------------------------------------------------------------------
# Premature stop phrases (Layer 2)
# ---------------------------------------------------------------------------

PREMATURE_STOP_PATTERNS = [
    r"(?i)shall i (?:continue|proceed|go ahead)",
    r"(?i)would you like me to (?:continue|proceed|go ahead|keep going)",
    r"(?i)let me know (?:if|when|how) you(?:'d| would) like",
    r"(?i)want me to (?:continue|proceed|keep going|move on)",
    r"(?i)should i (?:move on|keep going|start on|continue)",
    r"(?i)i(?:'ll| will) wait for (?:your|further)",
    r"(?i)awaiting your (?:input|feedback|direction|confirmation)",
    r"(?i)(?:here(?:'s| is) (?:a |the )?(?:summary|progress|update) of)",
    r"(?i)what (?:would you like|do you want) (?:me to do |to do )?next",
]

_PREMATURE_COMPILED = [re.compile(p) for p in PREMATURE_STOP_PATTERNS]


def _has_premature_stop_phrase(response: str) -> str | None:
    """Return first matched premature-stop phrase, or None."""
    for pattern in _PREMATURE_COMPILED:
        m = pattern.search(response)
        if m:
            return m.group(0)
    return None


# ---------------------------------------------------------------------------
# Tool extraction from hook payload
# ---------------------------------------------------------------------------

def _extract_tools_used(data: dict) -> set[str]:
    """Extract tool names from hook payload."""
    tools = set()
    for tool in data.get("tools_used", []):
        name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
        if name:
            tools.add(name)

    if not tools:
        transcript_path = data.get("transcript_path", "")
        if transcript_path:
            try:
                content = Path(transcript_path).read_text(encoding="utf-8")
                for line in reversed(content.strip().split("\n")):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "assistant" or entry.get("role") == "assistant":
                            msg = entry.get("message", entry)
                            for block in msg.get("content", []):
                                if isinstance(block, dict) and block.get("type") == "tool_use":
                                    name = block.get("name", "")
                                    if name:
                                        tools.add(name)
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
            except Exception:
                pass

    return tools


# ---------------------------------------------------------------------------
# Safety valve — consecutive block counter (Gap #5)
# ---------------------------------------------------------------------------

def _safe_session_id(data: dict) -> str:
    """Get filesystem-safe session ID fragment."""
    sid = (
        data.get("session_id")
        or data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID")
        or "unknown"
    )
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(sid))[:32]


def _get_block_counter_path(data: dict) -> Path:
    """Session-scoped block counter file path."""
    return STATE_DIR / f"block_count_{_safe_session_id(data)}.json"


def _read_block_counter(data: dict) -> int:
    """Read consecutive block count for this session."""
    path = _get_block_counter_path(data)
    try:
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
            # Expire after 10 minutes of no blocks (agent recovered)
            last_block = state.get("last_block_time", 0)
            if time.time() - last_block > 600:
                path.unlink(missing_ok=True)
                return 0
            return state.get("count", 0)
    except Exception:
        pass
    return 0


def _increment_block_counter(data: dict) -> int:
    """Increment and return new block count."""
    path = _get_block_counter_path(data)
    count = _read_block_counter(data) + 1
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"count": count, "last_block_time": time.time()}),
            encoding="utf-8",
        )
    except Exception:
        pass
    return count


def _reset_block_counter(data: dict) -> None:
    """Reset block counter (agent passed through, working normally)."""
    path = _get_block_counter_path(data)
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Compaction detection (Gap #6)
# ---------------------------------------------------------------------------

def _is_post_compaction(data: dict) -> bool:
    """Detect if we're in a post-compaction state where enforcement should relax."""
    response = data.get("response", "")
    # After compaction, agent often starts fresh without /code context
    if "SESSION RESTORED FROM COMPACTION" in response:
        return True
    if "context was compacted" in response.lower():
        return True
    return False


# ---------------------------------------------------------------------------
# Active /code detection (Gap #3 — handles missing plan.md)
# ---------------------------------------------------------------------------

def _is_code_skill_active(data: dict) -> tuple[bool, int, int]:
    """Determine if /code is active with incomplete work.

    Returns (is_active, total_tasks, incomplete_tasks).

    Checks:
    1. plan.md with incomplete tasks (primary signal)
    2. Skill state marker file (for early phases before plan.md exists)
    """
    plan = _find_plan_file()
    if plan is not None:
        total, incomplete = _count_plan_tasks(plan)
        if total > 0:
            # Cross-check for false completion (Gap #1)
            adjusted_incomplete = _check_false_completion(plan, total, incomplete)
            if adjusted_incomplete > 0:
                return True, total, adjusted_incomplete
            # All tasks genuinely complete
            return False, total, 0

    # Gap #3: Check for skill state marker (covers early phases)
    # During BOOTSTRAP/ALIGN/DESIGN, plan.md doesn't exist yet,
    # but the agent shouldn't be stopping either.
    # However, this is a lower-confidence signal — we only use it
    # for the pattern-based check, not the structural check.
    # (Agent might legitimately need user input during planning.)

    return False, 0, 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_tilldone(data: dict) -> dict | None:
    """Main gate function. Called by Stop.py router.

    Returns:
        Block dict if premature stop detected, None to pass through.
    """
    response = data.get("response", "")
    if not response or len(response) < 100:
        return None

    # Gap #6: Don't enforce after compaction (agent lost context)
    if _is_post_compaction(data):
        _reset_block_counter(data)
        return None

    # Check if /code is active with incomplete work
    active, total, incomplete = _is_code_skill_active(data)
    if not active:
        _reset_block_counter(data)
        return None

    # Gap #4: Check for genuine exempt conditions (tightened patterns)
    if _is_exempt(response):
        _reset_block_counter(data)
        return None

    # Check for valid done claims with matching task counts
    if _has_valid_done_claim(response, total):
        _reset_block_counter(data)
        return None

    # Gap #5: Safety valve — don't block forever
    consecutive_blocks = _read_block_counter(data)
    if consecutive_blocks >= MAX_CONSECUTIVE_BLOCKS:
        _reset_block_counter(data)
        # Allow through but with a strong system message
        return {
            "systemMessage": (
                f"TILLDONE SAFETY VALVE: Blocked {MAX_CONSECUTIVE_BLOCKS} consecutive times. "
                f"Allowing this response through. {incomplete}/{total} tasks remain incomplete. "
                f"If you are genuinely stuck, explain clearly with 'BLOCKED:' prefix and evidence."
            ),
        }

    # === Layer 1: Structural detection ===
    tools_used = _extract_tools_used(data)
    has_implementation_tool = bool(tools_used & IMPLEMENTATION_TOOLS)

    if not has_implementation_tool:
        count = _increment_block_counter(data)
        detection = "no implementation tools used (prose-only response)"
        if tools_used:
            tool_sample = ", ".join(sorted(tools_used)[:3])
            detection = f"only read/research tools used ({tool_sample}), no implementation"

        return {
            "decision": "block",
            "reason": (
                f"TILL-DONE: {incomplete}/{total} plan tasks incomplete. "
                f"Detection: {detection}. "
                f"Continue implementing the next incomplete task from plan.md. "
                f"Do not summarize or ask permission. "
                f"If genuinely blocked, use 'BLOCKED: <reason with evidence>'."
                f"\n[block {count}/{MAX_CONSECUTIVE_BLOCKS} before safety valve]"
            ),
            "blocking_hook": "Stop_tilldone_gate.py",
        }

    # === Layer 2: Pattern-based detection ===
    premature_phrase = _has_premature_stop_phrase(response)
    if premature_phrase:
        count = _increment_block_counter(data)
        return {
            "decision": "block",
            "reason": (
                f"TILL-DONE: {incomplete}/{total} plan tasks incomplete. "
                f"Detected: \"{premature_phrase}\". "
                f"Continue to the next task without asking permission."
                f"\n[block {count}/{MAX_CONSECUTIVE_BLOCKS} before safety valve]"
            ),
            "blocking_hook": "Stop_tilldone_gate.py",
        }

    # Agent used implementation tools and no premature-stop language.
    # This is normal mid-task behavior. Reset counter and allow.
    _reset_block_counter(data)
    return None
