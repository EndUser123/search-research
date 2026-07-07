#!/usr/bin/env python3
r"""
Unified Evidence Enforcement Architecture (UEEA)

Consolidates all evidence gates into single validation pass:
- empirical_claims_gate.py (observation required)
- speculation_gate.py (speculative language)
- assumption_audit_v2.py (unverified assumptions)
- StopHook_investigation_required.py (diagnostic without investigation)

Single state source, unified format, no sequential loops.

Author: CSF
Version: 1.0.0
Date: 2026-02-08
"""

from __future__ import annotations

import hashlib
import json
import re as _re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

# State file location
STATE_DIR = Path(__file__).resolve().parent.parent / "state"
STATE_FILE = STATE_DIR / "ueea_state.jsonl"

# Cache TTL for grace period checks (seconds)
_GRACE_CACHE_TTL = 30

# Unified evidence format
EVIDENCE_FIELDS = ["observed_via", "observed_at", "evidence_type", "source_file", "claim_excerpt"]

# Pre-compiled regex patterns (performance optimization)
_SPECULATIVE_PATTERNS_COMPILED = [
    _re.compile(r"\bappears to be\b", _re.IGNORECASE),
    _re.compile(r"\blikely\b", _re.IGNORECASE),
    _re.compile(r"\bprobably\b", _re.IGNORECASE),
    _re.compile(r"\bseems like\b", _re.IGNORECASE),
    _re.compile(r"\bwould expect\b", _re.IGNORECASE),
]

# Keep original for backward compatibility
SPECULATIVE_PATTERNS = [
    r"\bappears to be\b",
    r"\blikely\b",
    r"\bprobably\b",
    r"\bseems like\b",
    r"\bwould expect\b",
]

# Required observation tools
OBSERVATION_TOOLS = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}

# Pre-compiled assumption patterns (performance optimization)
_ASSUMPTION_PATTERNS_COMPILED = [
    _re.compile(r"assumes? (?:that )?without", _re.IGNORECASE),
    _re.compile(r"assuming (?:that )?", _re.IGNORECASE),
    _re.compile(r"presuming (?:that )?", _re.IGNORECASE),
]

# Keep original for backward compatibility
ASSUMPTION_PATTERNS = [
    r"assumes? (?:that )?without",
    r"assuming (?:that )?",
    r"presuming (?:that )?",
]

# Pre-compiled file path pattern (performance optimization)
_FILE_PATTERN = _re.compile(
    r'[A-Z]:[\\/][^"\s+\]]+'  # Windows: C:\... or P:/...
    r"|[/\w][/\w][\w.-]+\.[\w]+"  # Unix/relative with extension: src/test.py
)

# Module-level cache for grace period checks
_grace_cache: dict[str, Any] = {"data": None, "timestamp": 0}

# =============================================================================
# MAIN VALIDATION
# =============================================================================


def check_response(data: dict[str, Any]) -> dict[str, Any]:
    """
    Single-pass validation of response against all evidence requirements.

    Args:
        data: Dict containing:
            - response: str - The response text
            - tools_used: list[str] - Tools used in this turn
            - terminal_id: str - Terminal identifier

    Returns:
        {"allowed": bool, "blocks": list[str], "remediation": str|None}
    """
    response_text = data.get("response", "")
    tools_used = data.get("tools_used", [])
    tool_names = _normalize_tool_names(tools_used)
    has_structured_evidence = _has_required_evidence_fields(response_text)

    # Persist observation receipts regardless of allow/block outcome to avoid
    # remediation dead-loops after a valid Read/Grep/Bash observation.
    if _has_observation_tool(tool_names):
        _record_observation(data, tool_names)

    blocks = []

    # Check 1: Observation required for claims
    if not has_structured_evidence and _has_claims_without_observation(response_text, tool_names):
        blocks.append("OBSERVATION_REQUIRED")

    # Check 2: Speculative language in diagnostic mode
    # Allow speculation when uncertainty is explicitly labeled or when a
    # concrete verification plan is provided.
    has_uncertainty_guard = _has_uncertainty_label_or_verification_plan(response_text)
    if not has_structured_evidence and _is_diagnostic_without_evidence(response_text, tool_names):
        if _has_speculative_language(response_text) and not has_uncertainty_guard:
            blocks.append("SPECULATION_VIOLATION")

    # Check 3: Unverified assumptions
    if _has_unverified_assumptions(response_text):
        blocks.append("ASSUMPTION_WITHOUT_EVIDENCE")

    if blocks:
        return {"allowed": False, "blocks": blocks, "remediation": _build_remediation(blocks)}

    return {"allowed": True, "blocks": [], "remediation": None}


def _normalize_tool_names(tools: Any) -> list[str]:
    """Normalize hook payload tools to canonical tool names."""
    if not isinstance(tools, list):
        return []
    names: list[str] = []
    for tool in tools:
        if isinstance(tool, dict):
            name = str(tool.get("name", "")).strip()
        else:
            name = str(tool).strip()
        if name:
            names.append(name)
    return names


def _has_observation_tool(tool_names: list[str]) -> bool:
    return any(name in OBSERVATION_TOOLS for name in tool_names)


def _has_required_evidence_fields(response: str) -> bool:
    required = ("observed_via:", "observed_at:", "evidence_type:")
    lowered = response.lower()
    return all(field in lowered for field in required)


def _has_claims_without_observation(response: str, tools: list[str]) -> bool:
    """
    Check if response has claims about files that were not observed.

    Per-evidence linkage: a claim about file X is only justified if file X
    was actually observed (Read/Grep/etc). Blanket grace (ANY observation
    tool excuses ALL claims) is the bug this fixes.

    Args:
        response: The response text
        tools: List of tool names used

    Returns:
        True if unobserved file claims found, False otherwise
    """
    # Extract file paths claimed about (filters to existing files only)
    claimed_files = set(_extract_file_paths_from_response(response))

    if not claimed_files:
        # No existing-file claims — allow (non-existent file claims are
        # pre-creation scenarios, not verifiable evidence claims)
        return False

    if not _has_observation_tool(tools):
        # No observation tool used at all
        return True

    # Compute observed files from this response (files actually read/grep'd)
    observed_files = set(_extract_file_paths_from_response(response))

    # Per-evidence linkage: every claimed file must have been observed.
    # Correct subset direction: claimed ⊆ observed (every claimed file
    # must be in the observed set). Wrong direction (observed ⊆ claimed)
    # incorrectly allows unobserved claims when multiple files are claimed.
    if not claimed_files.issubset(observed_files):
        return True

    return False


def _is_diagnostic_without_evidence(response: str, tools: list[str]) -> bool:
    """
    Check if response is diagnostic without evidence.

    Args:
        response: The response text
        tools: List of tool names used

    Returns:
        True if diagnostic without evidence, False otherwise
    """
    diagnostic_markers = ["root cause", "diagnosis", "appears to be", "likely"]
    return any(m.lower() in response.lower() for m in diagnostic_markers)


def _has_speculative_language(response: str) -> bool:
    """
    Check for speculative patterns.

    Args:
        response: The response text

    Returns:
        True if speculative language found, False otherwise
    """
    # Use pre-compiled patterns for performance (N+1 compilation optimization)
    for pattern in _SPECULATIVE_PATTERNS_COMPILED:
        if pattern.search(response):
            return True
    return False


def _has_uncertainty_label_or_verification_plan(response: str) -> bool:
    """Check if response labels uncertainty or includes a verification plan."""
    lowered = response.lower()
    labels = ("[unverified]", "[inferred]")
    if any(label in lowered for label in labels):
        return True

    plan_markers = (
        "required to verify:",
        "verification plan:",
        "next verification step:",
    )
    return any(marker in lowered for marker in plan_markers)


def _has_unverified_assumptions(response: str) -> bool:
    """
    Check for unverified assumptions.

    Args:
        response: The response text

    Returns:
        True if unverified assumptions found, False otherwise
    """
    # Use pre-compiled patterns for performance (N+1 compilation optimization)
    for pattern in _ASSUMPTION_PATTERNS_COMPILED:
        if pattern.search(response):
            return True
    return False


def _build_remediation(blocks: list[str]) -> str:
    """
    Build unified remediation message.

    Args:
        blocks: List of block types

    Returns:
        Remediation message string
    """
    lines = ["UNIFIED EVIDENCE BLOCK", ""]

    if "OBSERVATION_REQUIRED" in blocks:
        lines.append("Your response makes claims without observation.")
        lines.append("Run Read/Grep/Glob/Bash/View/WebFetch, then respond with:")
        lines.append("")
        lines.append("  observed_via: <tool>")
        lines.append("  observed_at: <timestamp>")
        lines.append("  evidence_type: <code|filesystem|execution|any>")

    if "SPECULATION_VIOLATION" in blocks:
        if "OBSERVATION_REQUIRED" in blocks:
            lines.append("")
        lines.append("Speculative language detected (appears to be, likely, probably).")
        lines.append("Use INVESTIGATION REQUIRED format:")
        lines.append("")
        lines.append("  Observation: [what you see]")
        lines.append("  Hypothesis: [what you suspect - UNVERIFIED]")
        lines.append("  Required to verify: [specific files/commands]")
        lines.append("")
        lines.append("Cannot proceed without evidence.")

    if "ASSUMPTION_WITHOUT_EVIDENCE" in blocks:
        if "OBSERVATION_REQUIRED" in blocks or "SPECULATION_VIOLATION" in blocks:
            lines.append("")
        lines.append("Unverified assumptions detected.")
        lines.append("Verify assumptions before proceeding.")

    return "\n".join(lines)


def _extract_file_paths_from_response(response: str) -> list[str]:
    """Extract file paths referenced in the response for mtime tracking."""
    paths = _FILE_PATTERN.findall(response)
    # Filter to paths that actually exist on disk
    valid = []
    for p in paths:
        try:
            pp = Path(p)
            if pp.is_file():
                valid.append(str(pp.resolve()))
        except (OSError, ValueError):
            continue
    return valid[:20]  # Cap at 20 to avoid bloating state


def _snapshot_file_hashes(file_paths: list[str]) -> dict[str, str]:
    """Snapshot content hash for each file path. Skip files that don't exist.

    Uses SHA-256 truncated to 16 hex chars for compactness.
    Hash-based detection is more reliable than mtime because:
    - mtime resolution on NTFS is ~100ms (misses rapid writes)
    - git checkout / stash can preserve or backdate mtime
    - copy operations may or may not preserve mtime
    """
    hashes: dict[str, str] = {}
    for fp in file_paths:
        try:
            content = Path(fp).read_bytes()
            hashes[fp] = hashlib.sha256(content).hexdigest()[:16]
        except OSError:
            continue
    return hashes


def _record_observation(data: dict[str, Any], tool_names: list[str] | None = None) -> None:
    """
    Record observation for mtime-based cross-turn grace.

    Stores file paths referenced in the response along with their mtimes,
    so future turns can verify files haven't changed since observation.

    Args:
        data: Dict containing terminal_id, tools_used, response
    """
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    if tool_names is None:
        tool_names = _normalize_tool_names(data.get("tools_used", []))

    response = data.get("response", "")
    observed_paths = _extract_file_paths_from_response(response)
    file_hashes = _snapshot_file_hashes(observed_paths)

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "terminal_id": data.get("terminal_id"),
        "tools_used": tool_names,
        "response_length": len(response),
        "observed_files": file_hashes,
    }

    # JSON schema validation (security hardening)
    _REQUIRED_RECORD_KEYS = {"timestamp", "terminal_id", "tools_used", "response_length"}
    if not _REQUIRED_RECORD_KEYS.issubset(record.keys()):
        raise ValueError(f"Invalid record schema: missing {_REQUIRED_RECORD_KEYS - record.keys()}")

    # Invalidate cache when new observation recorded
    global _grace_cache
    _grace_cache["data"] = None
    _grace_cache["timestamp"] = 0

    try:
        from file_lock import append_jsonl_safe
        append_jsonl_safe(STATE_FILE, record)
    except OSError:
        return


def _check_files_unchanged(observed_files: dict[str, str]) -> bool:
    """Check that all observed files still have the same content hash.

    Returns True if all files are unchanged (or missing from disk, which
    means nothing has overwritten them). Returns False if any file's
    content hash differs from the recorded hash.
    """
    if not observed_files:
        # No files tracked — fall back to allowing (observation was valid)
        return True
    for fp, recorded_hash in observed_files.items():
        try:
            current_hash = hashlib.sha256(Path(fp).read_bytes()).hexdigest()[:16]
            if current_hash != recorded_hash:
                return False  # File content changed since observation
        except OSError:
            # File no longer exists — not stale, just gone
            continue
    return True


def check_grace(terminal_id: str) -> bool:
    """
    Check if terminal has active grace from a previous-turn observation.

    Grace is valid when:
    1. A previous turn for this terminal used an observation tool
    2. The files referenced in that observation haven't been modified since

    This is terminal-isolated: Terminal A's observations don't grant
    grace to Terminal B.

    Args:
        terminal_id: The terminal identifier to check

    Returns:
        True if grace period active and evidence is still fresh, False otherwise
    """
    # Use cache if fresh (performance optimization - reduces file I/O)
    now = time.time()
    global _grace_cache
    if _grace_cache["timestamp"] + _GRACE_CACHE_TTL > now:
        cached_data = _grace_cache["data"]
        if cached_data and cached_data.get("terminal_id") == terminal_id:
            return cached_data.get("has_observation", False)

    if not STATE_FILE.exists():
        return False

    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            # Read only last 100 lines (optimization for large files)
            # This is sufficient to capture the last 10 relevant entries
            lines = f.readlines()[-100:]
    except OSError:
        return False

    # Check last entry for this terminal
    result = False
    for line in reversed(lines[-10:]):  # Last 10 entries
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("terminal_id") == terminal_id:
            # Has observation tools
            normalized = _normalize_tool_names(record.get("tools_used", []))
            if _has_observation_tool(normalized):
                # Verify observed files haven't changed (content hash check)
                observed_files = record.get("observed_files", {})
                if _check_files_unchanged(observed_files):
                    result = True
                # else: files changed since observation, grace invalid
                break

    # Update cache
    _grace_cache["data"] = {"terminal_id": terminal_id, "has_observation": result}
    _grace_cache["timestamp"] = now
    return result


# =============================================================================
# IN-PROCESS HOOK PROTOCOL
# =============================================================================


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    In-process hook protocol for Stop_router.py integration.

    Args:
        data: Dict containing response, tools_used, terminal_id

    Returns:
        {"block": True, "reason": "..."} to block
        {"allow": True} or None to allow
    """
    result = check_response(data)

    if not result["allowed"]:
        return {"block": True, "reason": result["remediation"], "blocks": result["blocks"]}

    return {"allow": True}


# =============================================================================
# CLI / SUBPROCESS ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Import hook_main decorator for subprocess mode
    from hook_base import hook_main

    @hook_main
    def main():
        """Main hook entry point for subprocess execution."""
        import sys

        data = json.loads(sys.stdin.read())
        result = check_response(data)

        # Format output for Stop hook
        output = {
            "allow": result["allowed"],
            "blocks": result["blocks"],
            "reason": result["remediation"] or "All checks passed",
        }

        print(json.dumps(output))

        # Exit code: 0 for allow, 2 for block
        sys.exit(0 if result["allowed"] else 2)

    main()
