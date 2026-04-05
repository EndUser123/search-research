#!/usr/bin/env python3
"""Terminal-wide session recap via direct transcript analysis."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# AIR Gap state file path
_AIR_GAPS_KEY = "air_gap_context"
_STATE_DIR = Path("P:/") / ".claude" / "state"


def _get_session_id_from_env() -> str:
    """Get session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def load_air_gaps() -> list[dict[str, Any]]:
    """Load AIR gap classifications from state file.

    Returns:
        List of gap classifications for this session, or empty list if none.
    """
    session_id = _get_session_id_from_env()
    state_file = _STATE_DIR / f"air_gaps_{session_id}.json"
    if not state_file.exists():
        return []
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


# Regex patterns compiled at module level for performance (PERF-001)
# Require full markdown section headers to avoid garbage matches on casual text
_RE_PROBLEM = re.compile(
    r"\*\*(?:What was the )?problem(?:\*\*|:\s+)\s*(.+?)(?=\n\s*\*\*|\n\n|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_RE_USER_PROBLEM = re.compile(
    r"\*\*Problem:(?:\*\*)?\s+(.+?)(?=\n\s*\*\*|\n\n|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_RE_FIX = re.compile(
    r"\*\*(?:What was the |Root Cause|Fix Applied):\s*(.+?)(?=\n\s*\*\*|\n\s*```|\n\n|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_RE_ACTION = re.compile(
    r"\*\*(?:What did we do|Action|action taken):(?:\*\*)?\s*(.+?)(?=\n\s*\*\*|\n\s*```|\n\n|\Z)"
    r"|## Files Changed\s*\n\s*[-*]\s*(.+)",
    re.DOTALL | re.IGNORECASE,
)
_RE_TOOL = re.compile(
    r"(?:Edit|Write)[^\n]+\n[^\n]*\s*([^\n]+\.py[^\n]*)",
    re.IGNORECASE,
)
_RE_DECISION = re.compile(
    r"\*\*(?:Decision|decision):(?:\*\*)?\s*(.+?)(?=\n\s*\*\*|\n\n|\Z|\.)"
    r"|\[DECISION\]\s*(.+?)(?=\n|$)",
    re.DOTALL | re.IGNORECASE,
)
_RE_OUTCOME = re.compile(
    r"\*\*(?:Outcome|outcome|result):(?:\*\*)?\s*(.+?)(?=\n\s*\*\*|\n\n|\Z|\.)"
    r"|(?:completed|verified|done|succeeded)(?:\s+(?:task|fix|implementation)\s+(?:of\s+)?(.+?))?"
    r"|(?:Task|Fix) #?\d+: ([^\n]+)",
    re.DOTALL | re.IGNORECASE,
)


def resolve_terminal_key(terminal_id: str | None = None) -> str:
    """Resolve terminal ID from parameter, environment, or system detection.

    Priority:
    1. Explicit terminal_id parameter
    2. CLAUDE_TERMINAL_ID env var (set by SessionStart hook)
    3. WT_SESSION env var (Windows Terminal session UUID)
    4. Terminal registry active entry
    5. Empty string if no detection succeeds

    Args:
        terminal_id: Optional terminal ID override

    Returns:
        Resolved terminal key (e.g. 'console_6a2e4c2b-1272-4b8c-b50d-c8907f830513')
    """
    if terminal_id:
        return terminal_id

    # Priority 1: CLAUDE_TERMINAL_ID env var (set by SessionStart hook)
    env_terminal = os.environ.get("CLAUDE_TERMINAL_ID")
    if env_terminal:
        return env_terminal

    # Priority 2: WT_SESSION env var (Windows Terminal session UUID)
    # This is the canonical source for console_* IDs in hook_base.py's
    # detect_console_host_terminal() — more reliable than registry fallback
    # because the registry can be stale across terminal sessions.
    wt_session = os.environ.get("WT_SESSION")
    if wt_session:
        # Normalize to console_* format (same as hook_base.py)
        return f"console_{wt_session}"

    # Priority 3: Terminal registry for active terminal
    registry_path = Path.home() / ".claude" / "terminals" / "registry.json"
    if registry_path.exists():
        try:
            with open(registry_path, encoding="utf-8") as f:
                data = json.load(f)
            terminals = data.get("terminals", [])
            for term in terminals:
                if term.get("active"):
                    return term.get("terminal_id", "")
            # Fallback: return first terminal if no active flag
            if terminals:
                return terminals[0].get("terminal_id", "")
        except (json.JSONDecodeError, OSError):
            pass

    # Priority 4: No detection succeeded — return empty string
    # (PID fallback was removed: it changed every restart and caused
    # 10,700 empty directories in task #2275)
    return ""


def _get_project_hash(project_path: Path) -> str:
    """Derive the Claude Code project hash for a project path.

    Claude Code stores project transcripts under ~/.claude/projects/{hash}/,
    where the hash is derived from the absolute project path.
    Each path separator and colon is replaced with a dash.

    Args:
        project_path: Absolute path to the project root

    Returns:
        Project hash string (e.g., 'P--' for 'P:\\')
    """
    path_str = str(project_path.resolve())
    # Replace both path separators and colons with dash
    path_str = path_str.replace("/", "-").replace("\\", "-").replace(":", "-")
    return path_str


def _get_sessions_index_path(project_path: Path) -> Path | None:
    """Find the sessions-index.json for a given project.

    Args:
        project_path: The project root path (e.g. P:\\)

    Returns:
        Path to sessions-index.json or None if not found
    """
    project_hash = _get_project_hash(project_path)
    index_path = Path.home() / ".claude" / "projects" / project_hash / "sessions-index.json"
    if index_path.exists():
        return index_path
    return None


def load_sessions_index(index_path: Path) -> list[dict[str, Any]]:
    """Load and parse a sessions-index.json file.

    The sessions-index.json uses a dict-keyed schema:
        {sessionId: {summary, lastPrompt, lastActiveAt, createdAt, fullPath}}

    Args:
        index_path: Path to sessions-index.json

    Returns:
        List of session index entries sorted by creation time (oldest first),
        normalized to the format expected by build_session_chain().
    """
    try:
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    # Handle both schemas: dict-keyed (actual) and array-based (legacy)
    raw_entries: list[dict[str, Any]]
    if isinstance(data, dict) and "entries" not in data:
        # Actual schema: {sessionId: {summary, lastPrompt, lastActiveAt, createdAt, fullPath}}
        raw_entries = []
        for session_id, entry in data.items():
            if not isinstance(entry, dict):
                continue
            # Convert epoch ms to ISO string for sort compatibility
            created_val = entry.get("createdAt", "")
            if isinstance(created_val, (int, float)):
                from datetime import datetime, timezone

                created_str = datetime.fromtimestamp(
                    created_val / 1000, tz=timezone.utc
                ).isoformat()
            else:
                created_str = str(created_val)

            # Prefer summary over lastPrompt for goal text
            goal = entry.get("summary") or entry.get("lastPrompt") or ""
            if isinstance(goal, str):
                goal = goal.strip()

            raw_entries.append(
                {
                    "sessionId": session_id,
                    "created": created_str,
                    "transcript_path": entry.get("fullPath", ""),
                    "last_goal": goal[:200],  # Truncate for display
                    "summary": goal,
                }
            )
    else:
        # Legacy array schema: {entries: [{sessionId, created, projectPath, ...}]}
        raw_entries = data.get("entries", [])

    # Sort chronologically: oldest first
    raw_entries.sort(key=lambda e: e.get("created", ""))
    return raw_entries


def _get_project_from_terminal(terminal_id: str) -> Path | None:
    """Get the project path from the terminal's registry file.

    The terminal file at ~/.claude/terminals/{terminal_id}.json contains
    the authoritative project path for this terminal session.

    Args:
        terminal_id: Terminal identifier

    Returns:
        Project root path or None if not found
    """
    term_file = Path.home() / ".claude" / "terminals" / f"{terminal_id}.json"
    if not term_file.exists():
        return None
    try:
        with open(term_file, encoding="utf-8") as f:
            term_data = json.load(f)
        project = term_data.get("project")
        if project:
            return Path(project)
    except (json.JSONDecodeError, OSError):
        pass
    return None


_MAX_RECENT_SESSIONS = 30  # Parse only the N most recent sessions


def build_session_chain(cwd: Path | None = None) -> list[dict[str, Any]]:
    """Build a chronological chain of recent sessions for the current project.

    Loads sessions from sessions-index.json, filters to those with existing transcript
    files, takes the N most recent, parses each transcript, and returns the parsed data
    in the format expected by format_recap().

    Args:
        cwd: Optional working directory override (defaults to Path.cwd())

    Returns:
        List of parsed session summaries sorted by created timestamp (oldest first)
    """
    if cwd is None:
        cwd = Path.cwd()

    # Try to get project path from terminal registry (authoritative)
    terminal_id = resolve_terminal_key(None)
    project_root = _get_project_from_terminal(terminal_id)
    if not project_root:
        # Fallback: derive from cwd traversal
        project_root = get_project_root()

    index_path = _get_sessions_index_path(project_root)
    if not index_path:
        return []

    entries = load_sessions_index(index_path)
    if not entries:
        return []

    # Filter to entries with existing transcript files, newest first
    recent_with_transcript = []
    for entry in reversed(entries):  # newest first
        transcript_path_str = entry.get("transcript_path", "")
        if not transcript_path_str:
            continue
        tp = Path(transcript_path_str)
        # Normalize Windows short-path prefix (e.g., cts\ -> C:\Users\...)
        if str(tp).startswith("cts" + "\\"):
            tp = Path(str(tp).replace("cts\\", str(Path.home()).replace("\\", "/") + "/"))
        if tp.exists() and _is_transcript_file(tp):
            recent_with_transcript.append(entry)
            if len(recent_with_transcript) >= _MAX_RECENT_SESSIONS:
                break

    # Reverse to oldest-first for chronological display
    recent_with_transcript.reverse()

    # Parse each transcript and return summaries in format_recap format
    result: list[dict[str, Any]] = []
    for entry in recent_with_transcript:
        transcript_path_str = entry.get("transcript_path", "")
        if not transcript_path_str:
            continue
        tp = Path(transcript_path_str)
        if str(tp).startswith("cts" + "\\"):
            tp = Path(str(tp).replace("cts\\", str(Path.home()).replace("\\", "/") + "/"))
        if not tp.exists():
            continue
        entries_list = load_transcript_entries(str(tp))
        summaries = extract_sessions_from_transcript(entries_list)
        if summaries:
            # Use the first (and typically only) summary from this file
            summary = summaries[0]
            # Attach the index goal if the parsed one is empty
            if not summary.get("last_goal"):
                idx_goal = entry.get("summary") or entry.get("last_goal", "")
                if idx_goal:
                    summary["last_goal"] = idx_goal[:200]
            result.append(summary)

    return result


def find_transcript_file(terminal_id: str) -> Path | None:
    """Find the transcript file for this terminal.

    Args:
        terminal_id: Terminal identifier

    Returns:
        Path to transcript file or None if not found
    """
    # Strategy 1: Check terminal file registry from /term skill
    term_file = Path.home() / ".claude" / "terminals" / f"{terminal_id}.json"
    if term_file.exists():
        try:
            with open(term_file, encoding="utf-8") as f:
                term_data = json.load(f)
            transcript_path = term_data.get("transcript_path")
            if transcript_path:
                path = Path(transcript_path)
                if path.exists():
                    return path
        except (json.JSONDecodeError, OSError):
            pass

    # Strategy 2: Check common transcript locations
    cwd = Path.cwd()
    candidates = [
        # Project-local .claude directory
        cwd / ".claude" / "transcripts" / f"{terminal_id}.jsonl",
        # User-level transcript storage
        Path.home() / ".claude" / "transcripts" / f"{terminal_id}.jsonl",
        # Check current directory
        cwd / f"{terminal_id}.jsonl",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Strategy 3: Fallback — scan project transcript directory for actual transcript files
    # This handles the case where sessions-index is stale but .jsonl files still exist
    transcript_path = _find_project_transcript()
    if transcript_path:
        return transcript_path

    return None


def _find_project_transcript() -> Path | None:
    """Find the most recent project transcript file with actual user/assistant content.

    Searches in ~/.claude/projects/{project}/ for .jsonl files and returns the most
    recently modified one that contains real transcript entries (user or assistant types).

    Returns:
        Path to the most recent transcript file, or None
    """
    # Find project root to locate transcript directory
    project_root = _find_project_root_for_transcripts()
    if not project_root:
        return None

    transcript_dir = project_root
    if not transcript_dir.exists():
        return None

    # Find .jsonl files with real transcript content
    candidates: list[tuple[float, Path]] = []
    for jsonl_file in transcript_dir.glob("*.jsonl"):
        try:
            mtime = jsonl_file.stat().st_mtime
            # Quick check: does this file have actual transcript entries?
            if _is_transcript_file(jsonl_file):
                candidates.append((mtime, jsonl_file))
        except OSError:
            continue

    if not candidates:
        # Fallback: try home directory transcript storage
        # This handles the case where cwd-based project root has no transcripts
        # but user's home directory (~/.claude/projects) contains transcript files
        home_transcripts = Path.home() / ".claude" / "projects"
        if home_transcripts.exists() and home_transcripts != transcript_dir:
            # Check both flat .jsonl files and nested project/*.jsonl files
            # (transcripts live in project subdirs like ~/.claude/projects/P--/*.jsonl)
            for glob_pattern in ["*.jsonl", "*/*.jsonl"]:
                for jsonl_file in home_transcripts.glob(glob_pattern):
                    try:
                        mtime = jsonl_file.stat().st_mtime
                        if _is_transcript_file(jsonl_file):
                            candidates.append((mtime, jsonl_file))
                    except OSError:
                        continue

    if not candidates:
        return None

    # Return most recently modified
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _is_transcript_file(path: Path) -> bool:
    """Check if a .jsonl file is a real transcript (has user/assistant entries)."""
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 200:  # Check first 200 lines (transcripts may have metadata before content)
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    t = entry.get("type", "")
                    if t in ("user", "assistant"):
                        return True
                except json.JSONDecodeError:
                    continue
        return False
    except OSError:
        return False


def _find_project_root_for_transcripts() -> Path | None:
    """Find the project root that contains transcript .jsonl files."""
    cwd = Path.cwd()

    # Look for .claude/projects/{project}/ pattern
    for parent in cwd.parents:
        projects_dir = parent / ".claude" / "projects"
        if projects_dir.is_dir():
            # Find the most recent project directory with transcripts
            try:
                for project in sorted(
                    projects_dir.iterdir(),
                    key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
                    reverse=True,
                ):
                    if project.is_dir():
                        # Projects that ARE the root (e.g. P--) store .jsonl at project level
                        # Projects that are subdirs (e.g. packages/*) have .claude subdir
                        # Check both patterns: project has .jsonl directly OR has .claude subdir with .jsonl
                        if any(project.glob("*.jsonl")):
                            return project
                        if (project / ".claude").exists() and any(
                            (project / ".claude").glob("**/*.jsonl")
                        ):
                            return project
            except OSError:
                continue
        claude_dir = parent / ".claude"
        if claude_dir.is_dir():
            # Maybe transcripts are directly under ~/.claude/projects/P--/
            for jsonl_file in parent.glob("*.jsonl"):
                return parent

    # Fallback: check cwd directly
    if any(cwd.glob("*.jsonl")):
        return cwd

    # Check home directory
    home_transcripts = Path.home() / ".claude" / "projects"
    if home_transcripts.is_dir():
        try:
            for project in sorted(
                home_transcripts.iterdir(),
                key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
                reverse=True,
            ):
                if project.is_dir() and any(project.glob("*.jsonl")):
                    return project
        except OSError:
            pass

    return None


def get_project_root() -> Path:
    """Detect project root from current working directory."""
    cwd = Path.cwd()

    # Look for .claude directory or common project markers
    if (cwd / ".claude").exists():
        return cwd

    # Check parent directories
    for parent in cwd.parents:
        if (parent / ".claude").exists():
            return parent

    # Fallback to current directory
    return cwd


def load_transcript_entries(transcript_path: str | None) -> list[dict[str, Any]]:
    """Load and parse transcript JSONL file.

    Args:
        transcript_path: Path to transcript file

    Returns:
        List of transcript entries
    """
    if not transcript_path:
        return []

    path = Path(transcript_path)
    if not path.exists():
        return []

    try:
        entries = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    entries.append(entry)
        return entries
    except (json.JSONDecodeError, OSError):
        return []


def extract_sessions_from_transcript(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract session summaries from transcript entries.

    Args:
        entries: Transcript entries

    Returns:
        List of session summaries with goals, timestamps, message counts
    """
    if not entries:
        return []

    # Filter out file-history-snapshot entries (metadata, not real transcript content)
    # and skip entries with empty type
    real_entries = [
        e
        for e in entries
        if e.get("type") not in ("file-history-snapshot", None, "") and e.get("sessionId")
    ]

    sessions = []
    current_session_id = None
    current_session_entries = []

    for entry in real_entries:
        session_id = entry.get("sessionId")  # Transcripts use "sessionId" not "session_chain_id"
        # None sessionId means metadata/tool_result — append to current session, don't split
        if session_id is None:
            current_session_entries.append(entry)
            continue
        if session_id != current_session_id:
            # Session boundary - save current session
            if current_session_entries:
                sessions.append(_summarize_session(current_session_entries, current_session_id))
            current_session_id = session_id
            current_session_entries = []
        current_session_entries.append(entry)

    # Don't forget the last session
    if current_session_entries:
        sessions.append(_summarize_session(current_session_entries, current_session_id))

    return sessions


def _extract_content(entry: dict[str, Any]) -> str:
    """Extract text content from a transcript entry, skipping tool_result blocks.

    Args:
        entry: A transcript entry dict with optional 'content' or 'message.content' fields

    Returns:
        The text content, or '' if no meaningful content found
    """
    content = entry.get("content")
    if content is None:
        message = entry.get("message", {})
        content = message.get("content")
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            # Skip tool_result blocks — they contain command output, not user intent
            if block.get("type") == "tool_result":
                continue
            text = block.get("text", "")
            if text:
                return text
        # All blocks were skipped (e.g., all tool_result) — return empty
        return ""


def _condense_transcript(
    entries: list[dict[str, Any]],
    max_chars: int = 2000,
) -> str:
    """Extract meaningful text from entries within a character budget.

    Skips tool_result blocks (command output noise). Accumulates user/assistant
    message text until max_chars is reached, then stops.

    The LLM (this agent) uses this raw text as evidence for synthesis —
    this replaces both regex extraction and external LLM calls.

    Args:
        entries: Transcript entries for a session
        max_chars: Maximum characters to return

    Returns:
        Condensed transcript text for LLM reasoning
    """
    result_parts: list[str] = []
    total = 0

    for entry in entries:
        text = _extract_content(entry)
        if not text:
            continue

        # Strip <local-command-*> and <command-*> XML blocks — transcript infrastructure, not evidence
        text = re.sub(r"<(?:local-)?command-\w+>.*?</(?:local-)?command-\w+>", "", text, flags=re.DOTALL)
        text = text.strip()
        if not text:
            continue

        estimate = len(text)

        if total + estimate > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                result_parts.append(text[:remaining] + "[…]")
            break

        result_parts.append(text)
        total += estimate

    return "\n---\n".join(result_parts)


def _regex_extract_semantic(
    entries: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Fallback regex-based semantic extraction (for when LM Studio is unavailable).

    Pattern-matches against structured output sections that appear in Claude Code responses.
    Each returned list contains unique, truncated entries.

    Args:
        entries: Transcript entries for a session

    Returns:
        Dict with keys: problems, fixes, actions, decisions, outcomes
    """
    all_text: list[str] = []
    for entry in entries:
        content = entry.get("content")
        if content is None:
            message = entry.get("message", {})
            content = message.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            all_text.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if text:
                        all_text.append(text)

    combined = "\n".join(all_text)

    def _filter(items: list[str]) -> list[str]:
        """Filter out low-quality extractions: too short, backticks, or ASCII art."""
        result = []
        for s in items:
            s = s.strip()
            # Discard: short strings, backtick noise, ASCII art chars, control sequences
            if len(s) < 15:
                continue
            if s.startswith("`") or s.startswith("-" * 40):
                continue
            if "\n" in s and len(s) < 30:  # Multi-line but very short
                continue
            result.append(s)
        return result

    problems: list[str] = []
    for match in _RE_PROBLEM.finditer(combined):
        problems.append(match.group(1).lstrip("* "))
    user_texts = [e.get("content", "") for e in entries if e.get("type") == "user"]
    for text in user_texts[:3]:
        for match in _RE_USER_PROBLEM.finditer(str(text)[:500]):
            if len(match.group(1)) > 20:
                problems.append(match.group(1).strip())

    fixes: list[str] = []
    for match in _RE_FIX.finditer(combined):
        fixes.append(match.group(1).lstrip("* "))

    actions: list[str] = []
    for match in _RE_ACTION.finditer(combined):
        actions.append((match.group(1) or match.group(2) or "").lstrip("* "))
    for match in _RE_TOOL.finditer(combined):
        if match.group(1) and len(match.group(1)) > 10:
            actions.append(match.group(1).strip())

    decisions: list[str] = []
    for match in _RE_DECISION.finditer(combined):
        decisions.append((match.group(1) or match.group(2) or "").lstrip("* "))

    outcomes: list[str] = []
    for match in _RE_OUTCOME.finditer(combined):
        outcomes.append((match.group(1) or match.group(2) or match.group(3) or "").lstrip("* "))

    # Apply quality filter before returning
    problems = _filter(problems)
    fixes = _filter(fixes)
    actions = _filter(actions)
    decisions = _filter(decisions)
    outcomes = _filter(outcomes)

    return {
        "problems": _unique_truncate(problems),
        "fixes": _unique_truncate(fixes),
        "actions": _unique_truncate(actions),
        "decisions": _unique_truncate(decisions),
        "outcomes": _unique_truncate(outcomes),
    }


def _unique_truncate(items: list[str], max_len: int = 150) -> list[str]:
    """Deduplicate while preserving order, then truncate."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            if len(normalized) > max_len:
                normalized = normalized[: max_len - 3] + "..."
            result.append(normalized)
    return result


def _extract_semantic_content(
    entries: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Extract semantic content (problems, fixes, actions, decisions, outcomes) from transcript entries.

    Uses strict regex patterns that require full markdown section headers to avoid garbage matches.
    Results are filtered for minimum quality (length >= 15 chars, no backtick noise, no ASCII art).

    Args:
        entries: Transcript entries for a session

    Returns:
        Dict with keys: problems, fixes, actions, decisions, outcomes
    """
    return _regex_extract_semantic(entries)


def _summarize_session(entries: list[dict[str, Any]], session_id: str | None) -> dict[str, Any]:
    """Summarize a session from its entries.

    Args:
        entries: Transcript entries for this session
        session_id: Session chain ID

    Returns:
        Session summary dict with semantic content
    """
    user_entries = [e for e in entries if e.get("type") == "user"]
    assistant_entries = [e for e in entries if e.get("type") == "assistant"]

    # last_goal: find the last user entry that contains meaningful user intent
    # Skip entries whose content is ONLY tool_result blocks (transcript stores tool output as type=="user")
    last_goal = ""
    for entry in reversed(user_entries):
        content = entry.get("content")
        if content is None:
            message = entry.get("message", {})
            content = message.get("content")
        # Skip entries that are entirely tool_result blocks (no user intent)
        if isinstance(content, list):
            blocks = [b for b in content if isinstance(b, dict)]
            if blocks and all(b.get("type") == "tool_result" for b in blocks):
                continue  # Entire entry is tool result output — not a goal
            # Mixed content: extract from the first text block
            last_goal = _extract_content(entry)
            break
        elif isinstance(content, str) and content.strip():
            last_goal = content.strip()
            break

    # Truncate goals for display
    def truncate(s: str, max_len: int = 100) -> str:
        if len(s) <= max_len:
            return s
        return s[: max_len - 3] + "..."

    # Extract semantic content
    semantic = _extract_semantic_content(entries)

    return {
        "session_id": session_id or "unknown",
        "entry_count": len(entries),
        "user_message_count": len(user_entries),
        "assistant_message_count": len(assistant_entries),
        "last_goal": truncate(str(last_goal)),
        "problem": semantic["problems"][0] if semantic["problems"] else None,
        "fix": semantic["fixes"][0] if semantic["fixes"] else None,
        "action": semantic["actions"][0] if semantic["actions"] else None,
        "problems": semantic["problems"],
        "fixes": semantic["fixes"],
        "actions": semantic["actions"],
        "decisions": semantic["decisions"],
        "outcomes": semantic["outcomes"],
        # Raw transcript text for LLM reasoning — replaces garbled regex extraction
        "transcript": _condense_transcript(entries),
    }


def format_brief(sessions: list[dict[str, Any]]) -> str:
    """Format a brief catch-up summary from sessions.

    Args:
        sessions: List of session summaries

    Returns:
        Brief catch-up string
    """
    if not sessions:
        return "No session history found."

    # Get the most recent session
    latest = sessions[-1]

    parts = []
    parts.append("Last session in this terminal:")
    parts.append(f"- Goal: {latest['last_goal']}")

    if latest.get("last_goal"):
        parts.append(f"- Current goal: {latest['last_goal']}")

    parts.append(
        f"- Messages: {latest['user_message_count']} user, {latest['assistant_message_count']} assistant"
    )

    return "\n".join(parts)


def format_recap(
    sessions: list[dict[str, Any]],
    terminal_id: str,
    brief: bool = False,
) -> str:
    """Format session data into a terminal recap.

    Args:
        sessions: List of session summaries
        terminal_id: Terminal identifier
        brief: If True, show brief catch-up format only

    Returns:
        Formatted recap string
    """
    if brief:
        return format_brief(sessions)

    lines = []
    lines.append(f"# Terminal Recap: {terminal_id}")
    lines.append("")

    # Macro-Audit: Verify historical intent hasn't been violated
    lines.append("## Macro-Audit")
    lines.append("")
    lines.append(
        "**Verify:** Assume I have no context. Does the recap provide enough Evidence "
        "for me to understand Why each decision was made?"
    )
    lines.append("")

    # Session history from transcript
    if sessions:
        lines.append("## Session History")
        lines.append("")
        lines.append(f"**Total Sessions**: {len(sessions)}")
        lines.append("")

        for i, session in enumerate(sessions, 1):
            lines.append(f"**[Session {i}]** {session['session_id'][:12]}...")
            lines.append(f"- Entries: {session['entry_count']}")
            lines.append(f"- User messages: {session['user_message_count']}")
            lines.append(f"- Assistant messages: {session['assistant_message_count']}")
            if session.get("last_goal"):
                lines.append(f"- Goal: {session['last_goal']}")

            # Semantic content: problem/fix/action (from structured output patterns)
            # These are the extracted facts — the LLM responding uses these as input
            # to synthesize: what was the problem, what was done, and what is the optimal fix?
            if session.get("problem"):
                lines.append(f"- Problem: {session['problem']}")
            if session.get("fix"):
                lines.append(f"- Fix: {session['fix']}")
            if session.get("action"):
                lines.append(f"- Action: {session['action']}")

            # Decisions and outcomes if found
            if session.get("decisions"):
                for decision in session["decisions"][:3]:  # Show up to 3
                    lines.append(f"- Decision: {decision}")
            if session.get("outcomes"):
                for outcome in session["outcomes"][:3]:  # Show up to 3
                    lines.append(f"- Outcome: {outcome}")

            # Condensed transcript — raw context for LLM (this agent) to reason over
            # when regex-extracted fields are garbage. The LLM synthesizes directly
            # from this text to answer the Macro-Audit question.
            if session.get("transcript"):
                transcript_preview = session["transcript"]
                if len(transcript_preview) > 800:
                    transcript_preview = transcript_preview[:800] + "[…]"
                lines.append("")
                lines.append("### Raw Context")
                lines.append(transcript_preview)

            lines.append("")
    else:
        lines.append("## Session History")
        lines.append("")
        lines.append("No session history found in transcript.")
        lines.append("")

    # Add Quick Argument section if AIR gaps exist
    quick_arg = format_quick_argument_section()
    if quick_arg:
        lines.append(quick_arg)

    return "\n".join(lines)


def format_quick_argument_section() -> str:
    """Format AIR gap classifications into Quick Argument section.

    Returns:
        Formatted Quick Argument section, or empty string if no gaps.
    """
    gaps = load_air_gaps()
    if not gaps:
        return ""

    lines = []
    lines.append("")
    lines.append("## Quick Argument")

    for i, gap in enumerate(gaps[:5], 1):  # Limit to 5 most recent
        gap_type = gap.get("type", "unknown")
        directive = gap.get("directive", "none")
        action = gap.get("action", "unknown")
        evidence = gap.get("evidence", "")
        timestamp = gap.get("timestamp", "")

        # Determine rationale based on gap type
        if gap_type == "hallucinated":
            rationale = "Action claimed but no verifiable diff produced"
        elif gap_type == "silent_pivot":
            rationale = "Action taken without explicit user directive in window"
        elif gap_type == "unjustified_revert":
            rationale = "Revert lacks technical justification in commit message"
        else:
            rationale = "Gap classification complete"

        # Format type label
        if gap_type == "hallucinated":
            type_label = "Heuristic"
        elif gap_type == "silent_pivot":
            type_label = "Silent Pivot"
        elif gap_type == "unjustified_revert":
            type_label = "Directed"
        else:
            type_label = gap_type

        lines.append("")
        lines.append(f"### Gap {i}: {gap_type.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Type** | {type_label} |")
        lines.append(
            f"| **Action** | {action[:100]} |"
            if len(action) > 100
            else f"| **Action** | {action} |"
        )
        lines.append(
            f"| **Evidence** | {evidence[:150]} |"
            if len(evidence) > 150
            else f"| **Evidence** | {evidence} |"
        )
        lines.append(f"| **Rationale** | {rationale} |")

    return "\n".join(lines)


def _load_all_sessions_via_history_index(
    project_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load sessions in the current terminal's chain via history_chain.py.

    Uses parentUuid chain traversal (not parentSessionId which doesn't exist).
    1. Find the most recent transcript file to get current session ID
    2. Walk the parentUuid chain via history_chain.py
    3. If chain walk fails (session not in index), fall back to current transcript

    Args:
        project_root: Project root path (defaults to detected project)

    Returns:
        List of session summaries (same format as extract_sessions_from_transcript)
    """
    if project_root is None:
        project_root = get_project_root()

    # Find the most recent transcript file to get current session ID
    current_session_id = _get_current_session_id(project_root)
    if not current_session_id:
        return []

    # Import chain modules lazily to avoid circular imports
    try:
        import sys

        sys.path.insert(
            0, str(Path(__file__).resolve().parents[3] / "packages" / "search-research")
        )
        from core.session_chain import SessionChainEntry, walk_session_chain
    except (ImportError, ValueError):
        return []

    # Walk the session chain using the unified session_chain module
    chain_sessions: list[dict[str, Any]] = []
    try:
        chain_result = walk_session_chain(session_id=current_session_id)
        if chain_result.entries:
            for entry in chain_result.entries:
                transcript_path = entry.transcript_path
                if transcript_path and Path(transcript_path).exists():
                    entries = load_transcript_entries(str(transcript_path))
                    session_summaries = extract_sessions_from_transcript(entries)
                    chain_sessions.extend(session_summaries)
    except (ValueError, OSError):
        pass

    if chain_sessions:
        # Sort by creation time (oldest first)
        chain_sessions.sort(key=lambda s: s.get("metadata", {}).get("created", ""))
        return chain_sessions

    # Final fallback: session not found in index (e.g., current session after compaction).
    # Read the current transcript directly.
    transcript_dir = _find_transcript_dir(project_root)
    if transcript_dir:
        # Find the most recent transcript file
        jsonl_files: list[tuple[float, Path]] = []
        for jsonl_file in transcript_dir.glob("*.jsonl"):
            if _is_transcript_file(jsonl_file):
                try:
                    mtime = jsonl_file.stat().st_mtime
                    jsonl_files.append((mtime, jsonl_file))
                except OSError:
                    continue
        if jsonl_files:
            jsonl_files.sort(key=lambda x: x[0], reverse=True)
            most_recent = jsonl_files[0][1]
            entries = load_transcript_entries(str(most_recent))
            return extract_sessions_from_transcript(entries)

    return []


def _get_current_session_id(project_root: Path | None) -> str | None:
    """Find the current session ID from the most recent transcript file.

    Args:
        project_root: Project root path

    Returns:
        Session ID string, or None if not found
    """
    transcript_dir = _find_transcript_dir(project_root)
    if not transcript_dir or not transcript_dir.exists():
        return None

    # Find most recently modified transcript file
    jsonl_files: list[tuple[float, Path]] = []
    for jsonl_file in transcript_dir.glob("*.jsonl"):
        if _is_transcript_file(jsonl_file):
            try:
                mtime = jsonl_file.stat().st_mtime
                jsonl_files.append((mtime, jsonl_file))
            except OSError:
                continue

    if not jsonl_files:
        return None

    jsonl_files.sort(key=lambda x: x[0], reverse=True)
    most_recent = jsonl_files[0][1]

    # Read first entry to get sessionId
    try:
        with open(most_recent, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    sid = entry.get("sessionId")
                    if sid:
                        return str(sid)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    return None


def _chain_entry_to_session_summary(entry: Any) -> dict[str, Any] | None:
    """Convert a SessionChainEntry to a session summary dict.

    Args:
        entry: SessionChainEntry from core.session_chain

    Returns:
        Session summary dict matching extract_sessions_from_transcript format
    """
    from core.session_chain import SessionChainEntry as SCE

    if not isinstance(entry, SCE):
        return None

    # Build metadata
    metadata: dict[str, Any] = {
        "session_id": entry.session_id,
        "created": entry.created.isoformat() if entry.created else None,
    }

    # Extract summary text from first_user_message
    summary_text = entry.first_user_message or ""

    return {
        "session_id": entry.session_id,
        "metadata": metadata,
        "summary": summary_text,
        "entry_count": 1,
        "user_message_count": 1,
        "assistant_message_count": 0,
    }


def _find_transcript_dir(project_root: Path | None) -> Path | None:
    """Find the directory containing transcript files for this project.

    Returns:
        Path to transcript directory, or None if not found
    """
    # Check home directory transcript storage first - this is where
    # actual transcript files live (not project_root which is P:\)
    home_transcripts = Path.home() / ".claude" / "projects"
    if home_transcripts.exists():
        # Verify it has .jsonl files before returning
        jsonl_files = list(home_transcripts.glob("*.jsonl"))
        if jsonl_files:
            return home_transcripts

    # Also check project-specific location if project_root is provided
    if project_root:
        # Check if project_root/.claude/projects/{project} pattern exists
        claude_projects = project_root / ".claude" / "projects"
        if claude_projects.exists():
            jsonl_files = list(claude_projects.glob("*.jsonl"))
            if jsonl_files:
                return claude_projects

    return None


def main() -> None:
    """Generate terminal-wide recap via direct transcript analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Terminal-wide session catch-up")
    parser.add_argument(
        "command",
        nargs="?",
        default="recap",
        choices=["recap", "brief"],
        help="Command: recap (full) or brief (catch-up summary)",
    )
    args = parser.parse_args()

    terminal_id = resolve_terminal_key(None)
    project_root = get_project_root()

    # Primary: load sessions from sessions-index.json, parse their transcripts
    sessions = build_session_chain(project_root)

    # Fallback: if no sessions found, try single-file approach (current terminal transcript only)
    if not sessions:
        transcript_path = find_transcript_file(terminal_id)
        if transcript_path and transcript_path.exists():
            entries = load_transcript_entries(str(transcript_path))
            sessions = extract_sessions_from_transcript(entries)

    # Format and print recap (format_recap handles empty sessions gracefully)
    is_brief = args.command == "brief"
    recap = format_recap(sessions, terminal_id, brief=is_brief)
    print(recap)


if __name__ == "__main__":
    main()
