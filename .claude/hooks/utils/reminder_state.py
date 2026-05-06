"""Shared utilities for reminder recovery hooks.

Provides terminal-isolated state management, MEMORY.md reading,
and reminder deduplication via SHA256 hashing.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# MEMORY.md: Search upward from hooks dir for nearest memory/MEMORY.md
# Hooks: P:/.claude/hooks/ → parent: P:/.claude/ → grandparent: P:/
# Memory can live at any of: P:/memory/MEMORY.md, P:/.claude/memory/MEMORY.md,
# or project-level: P:/../memory/MEMORY.md (for P:/projects/P--/memory/MEMORY.md)
_hooks_root = Path(__file__).resolve().parent.parent


def _find_memory_md() -> Path:
    """Search upward from hooks dir for memory/MEMORY.md."""
    search_paths = [
        _hooks_root / "memory" / "MEMORY.md",
        _hooks_root.parent / "memory" / "MEMORY.md",
        _hooks_root.parent.parent / "memory" / "MEMORY.md",
        Path.home() / ".claude" / "projects" / "P--" / "memory" / "MEMORY.md",
    ]
    for p in search_paths:
        if p.exists():
            return p
    return search_paths[0]  # Return first candidate for graceful degradation


_MD_PATH = _find_memory_md()
del _hooks_root  # Don't expose mutable module-level var


def artifacts_dir(terminal_id: str) -> Path:
    """Return the terminal-isolated artifacts directory."""
    artifacts = Path.home() / ".claude" / ".artifacts" / terminal_id
    artifacts.mkdir(parents=True, exist_ok=True)
    return artifacts


def read_compaction_state(terminal_id: str) -> dict[str, Any] | None:
    """Read compaction state from terminal-scoped file.

    Returns None if file missing or corrupted.
    """
    state_file = artifacts_dir(terminal_id) / "compaction_state.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_compaction_state(
    terminal_id: str, state: dict[str, Any], update_timestamp: bool = True
) -> bool:
    """Write compaction state to terminal-scoped file.

    Uses retry-on-lock for Windows compatibility.
    Set update_timestamp=False to preserve the existing timestamp.
    """
    state_file = artifacts_dir(terminal_id) / "compaction_state.json"
    if update_timestamp:
        state["timestamp"] = datetime.now(timezone.utc).isoformat()
    content = json.dumps(state, indent=2, ensure_ascii=False)
    _write_with_retry(state_file, content)
    return True


def _write_with_retry(path: Path, content: str, max_attempts: int = 5) -> None:
    """Write content to path with retry on lock (Windows)."""
    for attempt in range(max_attempts):
        try:
            path.write_text(content, encoding="utf-8")
            return
        except (PermissionError, OSError) as e:
            if attempt < max_attempts - 1:
                import time as _time
                _time.sleep(0.25 * (attempt + 1))
            else:
                raise


def score_as_correction_heuristic(line: str) -> tuple[float, list[str]]:
    """Score a line as correction-like using bounded heuristic.

    Returns (score, reasons) where score is 0.0-1.0.
    Categories are mutually exclusive to avoid double-counting.
    Only applies to lines that START with correction-like patterns,
    not prose that happens to contain keywords.
    """
    line_stripped = line.strip()
    line_lower = line_stripped.lower()

    # Must start with correction-intent marker (not just contain keywords)
    # Exclude markdown links, URLs, table rows
    if line_lower.startswith(("[", "http", "see ", "|")):
        return 0.0, ["skip:md_link"]
    if "github" in line_lower or ".md`" in line_lower or ".md]" in line_lower:
        return 0.0, ["skip:md_ref"]

    # Category 1: Strong imperative start (highest confidence)
    # Line MUST start with these verb patterns
    strong_starters = (
        "always ", "must ", "should ", "need to ", "prefer ",
        "ensure ", "verify ", "check ", "run ", "avoid ",
    )
    for starter in strong_starters:
        if line_lower.startswith(starter):
            return 0.80, [f"imperative:{starter.strip()}"]

    # Category 2: Action verb start (medium-high confidence)
    action_starters = ("use ", "add ", "remove ", "set ", "update ",
                       "fix ", "create ", "delete ", "remember to ",
                       "document ", "test ", "commit ")
    for starter in action_starters:
        if line_lower.startswith(starter):
            return 0.75, [f"action:{starter.strip()}"]

    # Category 3: Contrastive correction (high confidence)
    # "X not Y", "X rather than Y", "instead of X" at start
    if line_lower.startswith(("instead ", "rather than ", "not ")):
        return 0.70, ["contrastive"]

    # Category 4: Obligation modal with strong corrective intent
    # "required", "mandatory" at start
    obligation_starters = ("required", "mandatory", "critical to",
                           "essential to", "important to")
    for starter in obligation_starters:
        if line_lower.startswith(starter):
            return 0.65, [f"obligation:{starter}"]

    # Category 5: Negation-based correction at start
    # "Don't...", "Never...", "X is not Y"
    negation_starters = ("don't ", "never ", "do not ", "cannot ",
                         "won't ", "shouldn't ")
    for starter in negation_starters:
        if line_lower.startswith(starter):
            return 0.85, [f"negation:{starter.strip()}"]

    # Category 6: Error/reference markers (needs strong code context)
    # Only if starts with error marker AND has specific file/tool refs
    error_starters = ("bug:", "issue:", "error:", "problem:", "fix:")
    for starter in error_starters:
        if line_lower.startswith(starter):
            # Check for specific refs
            code_refs = (".py", "file", "function", "test", "tool",
                         "command", "api", "endpoint", "auth", "db")
            if any(r in line_lower for r in code_refs):
                return 0.60, ["error_ref"]
            return 0.0, ["error_ref_weak"]

    return 0.0, []


def read_memory_md() -> list[str]:
    """Read corrections from MEMORY.md.

    Extracts corrections using hybrid pattern + heuristic approach:
    - Layer 1: High-precision pattern matching (existing behavior)
    - Layer 2: Bounded heuristic on unmatched lines in correction sections

    Returns empty list if file missing or unreadable.
    """
    if not _MD_PATH.exists():
        return []
    try:
        lines = _MD_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    corrections: list[str] = []
    corrections_set: set[str] = set()

    for line in lines:
        stripped = line.strip()
        # Layer 1: High-precision pattern extraction
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("|")
            and not stripped.startswith("- [")
            and ("Don't" in stripped or "do not" in stripped.lower()
                 or "never" in stripped.lower()
                 or "use" in stripped.lower() and "instead" in stripped.lower()
                 or "use" in stripped.lower() and "NOT" in stripped
                 or "corrected" in stripped.lower()
                 or "correction" in stripped.lower())
        ):
            # Truncate very long lines
            if len(stripped) > 200:
                stripped = stripped[:200].rstrip() + "..."
            if stripped not in corrections_set:
                corrections.append(stripped)
                corrections_set.add(stripped)

    # Layer 2: Heuristic extraction for unmatched lines
    # Only apply to lines that look like they belong in corrections section
    for line in lines:
        stripped = line.strip()
        # Skip already extracted, headers, table rows, links
        if stripped in corrections_set:
            continue
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("|"):
            continue
        if stripped.startswith("- [") and "]: " in stripped:
            continue  # Topic index links
        if stripped.startswith("[") or stripped.startswith("http"):
            continue  # Links and references
        if len(stripped) < 15:  # Too short to be a rule
            continue

        # Apply heuristic
        score, reasons = score_as_correction_heuristic(stripped)
        # Threshold: 0.55+ for extraction (conservative)
        if score >= 0.55:
            if len(stripped) > 200:
                stripped = stripped[:200].rstrip() + "..."
            if stripped not in corrections_set:
                corrections.append(stripped)
                corrections_set.add(stripped)

    return corrections


def hash_reminder(text: str) -> str:
    """Return SHA256 hash prefix of reminder text for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def is_state_fresh(timestamp: str | None, max_age_minutes: int) -> bool:
    """Check if ISO-8601 timestamp is fresh within max_age_minutes.

    Returns True if timestamp is None (field missing).
    Returns False if timestamp is unparseable.
    """
    if timestamp is None:
        return True  # No timestamp = treat as fresh
    try:
        dt = datetime.fromisoformat(timestamp.rstrip("Z"))
        # Make naive datetimes timezone-aware (UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now - dt
        return age <= timedelta(minutes=max_age_minutes)
    except (ValueError, TypeError):
        return False


def extract_recent_messages(
    transcript_path: Path | str | None, n: int = 10
) -> list[str]:
    """Extract last n user messages from transcript JSONL.

    Returns empty list on error or if transcript unavailable.
    """
    if not transcript_path:
        return []
    path = Path(transcript_path)
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    messages: list[str] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            if item.get("type") == "user" and item.get("message"):
                content = item["message"].get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") == "text":
                            messages.append(block["text"])
                elif isinstance(content, str):
                    messages.append(content)
                if len(messages) >= n:
                    break
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return list(reversed(messages))
