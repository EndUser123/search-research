#!/usr/bin/env python3
"""
Stop_completion_verification_guard.py - File Operation Claim Verification Guard
====================================================================================

Blocks responses claiming file/folder operations WITHOUT verification tools
used THIS TURN.

WHY THIS EXISTS:
  AI agents claim "created X", "modified Y", "copied Z" without verifying those
  operations actually occurred. This creates false completion claims and wastes
  user time discovering the operation didn't happen.

FAILURE MODE CAUGHT:
  "Created the configuration file"
  -> No Write/Edit tool used THIS TURN
  -> Guard blocks and demands verification.

CLAIM TYPES COVERED:
  1. CREATION: "created X", "wrote X", "generated X"
  2. MODIFICATION: "modified X", "updated X", "changed X"
  3. DELETION: "deleted X", "removed X", "cleaned up X"
  4. COPY: "copied X to Y", "duplicated X"
  5. MOVE: "moved X to Y", "renamed X to Y"
  6. BACKUP: "backed up X", "saved copy of X"
  7. FOLDER_CREATE: "created directory X", "made folder X"
  8. FOLDER_DELETE: "deleted folder X", "removed directory X"

VERIFICATION METHOD:
  Uses the shared turn-scoped evidence helper to check what tools were used
  THIS TURN (turn-scoped verification prevents stale data and keeps spool
  fallback behavior consistent across guards).

ALLOWLIST (obvious claims that don't need verification):
  - Conversational denials: "I didn't modify X", "I haven't created X"
  - Future tense: "will create", "will be deleted"
  - Capability statements: "can be modified", "needs X"
  - Examples/paths in quotes: "like file.py", "similar to X"

LIFECYCLE: Stop (blocking guard -- exits with code 2 to block)

v1.0 - 2026-03-24: Initial implementation with 8 claim types
v1.1 - 2026-04-11: FIX - Require first-person framing in all claim patterns to prevent
                    false positives when summarizing tool output (e.g., GTO "files have changed since")
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state"
LOG_DIR = HOOKS_DIR / "state" / "logs"
sys.path.insert(0, str(HOOKS_DIR))

# --- Logging ----------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("completion_verification_guard")
_handler = logging.FileHandler(LOG_DIR / "completion_verification_guard.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


try:
    from turn_scoped_evidence import load_turn_scoped_events
    EVIDENCE_AVAILABLE = True
except ImportError as exc:
    EVIDENCE_AVAILABLE = False
    _logger.warning("evidence_store import failed: %s", exc)


# --- Tool history verification ---------------------------------------------


def _load_turn_events(session_id: str, terminal_id: str) -> list[dict] | None:
    """Load tool events for the current turn only (id > turn_start_event_id).

    Returns None when evidence system is unavailable.
    Returns [] when evidence is available but no matching events exist this turn.
    """
    if not EVIDENCE_AVAILABLE:
        _logger.warning("FAIL-WARN: evidence_store not importable")
        return None

    if not session_id:
        _logger.warning("FAIL-WARN: session_id empty/missing")
        return None

    all_events = load_turn_scoped_events(
        session_id=session_id,
        terminal_id=terminal_id,
        limit=500,
    )
    if all_events is None:
        _logger.warning("FAIL-WARN: load_turn_scoped_events returned unavailable")
        return None
    _logger.debug("loaded %d events for session=%s", len(all_events), session_id[:16])
    return all_events


# --- Claim type patterns ---------------------------------------------------

# 1. CREATION patterns - Require first-person or explicit action framing
CREATION_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:created|wrote|generated|initialized|set\s+up)\s+[\w\-\.]+(?:\.?(?:py|js|ts|md|json|yaml|txt|log|conf|cfg)?)?(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:created|made)\s+a\s+(?:new\s+)?[\w\-\.]+"
    r"|\bI\s+(?:have\s+)?(?:outputted|saved|wrote)\s+(?:to\s+)?[\w\-\.]+\.?(?:py|js|ts|md|json|yaml|txt|log)?",
    re.IGNORECASE,
)

# 2. MODIFICATION patterns - Require first-person or explicit action framing
# to distinguish user action claims from descriptive state language (e.g., GTO output)
MODIFICATION_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:modified|updated|changed|edited|refactored|adjusted)\s+[\w\-\.]+(?:\.?(?:py|js|ts|md|json|yaml|txt|log)?)?(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:fixed|corrected|improved)\s+[\w\-\.]+(?:\.?(?:py|js|ts|md|json|yaml|txt|log)?)?(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:applied|added)\s+(?:a\s+)?(?:fix|change|modification|update)\s+[\w\-\.]+",
    re.IGNORECASE,
)

# 3. DELETION patterns - Require first-person or explicit action framing
DELETION_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:deleted|removed|cleaned\s+up)\s+[\w\-\.]+(?:\.?(?:py|js|ts|md|json|yaml|txt|log|tmp|bak|old)?)?(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:deleted|removed|cleaned\s+up)\s+(?:the\s+)?files?\s+(?:successfully|complete|now|done)?",
    re.IGNORECASE,
)

# 4. COPY patterns - Require first-person or explicit action framing
COPY_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:copied|duplicated|cloned)\s+[\w\-\.]+\.?(?:py|js|ts|md|json|yaml|txt|log)?\s+to\s+[\w\-\.]+(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:created|made)\s+a\s+copy\s+(?:of\s+)?[\w\-\.]+",
    re.IGNORECASE,
)

# 5. MOVE patterns - Require first-person or explicit action framing
MOVE_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:moved|renamed|relocated)\s+[\w\-\.]+\.?(?:py|js|ts|md|json|yaml|txt|log)?\s+to\s+[\w\-\.]+(?:\s+(?:successfully|complete|now|done))?"
    r"|\bI\s+(?:have\s+)?(?:renamed)\s+[\w\-\.]+\s+(?:to\s+)?[\w\-\.]+",
    re.IGNORECASE,
)

# 6. BACKUP patterns - Require first-person or explicit action framing
BACKUP_PATTERNS = re.compile(
    # Requires file extension or path-like suffix (actual backup targets)
    r"\bI\s+(?:have\s+)?(?:backed\s+up|saved\s+(?:a\s+)?copy|created\s+backup)\s+(?:of\s+)?[\w\-\.]+(?:\.\w+)?\s*(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:backed\s+up|saved)\s+[\w\-\.]+(?:\.\w+)"  # must have extension: saved file.txt
    r"|\bI\s+(?:have\s+)?(?:created|made)\s+(?:a\s+)?backup\s+(?:of\s+)?[\w\-\.]+(?:\.\w+)?",
    re.IGNORECASE,
)

# 7. FOLDER_CREATE patterns - Require first-person or explicit action framing
FOLDER_CREATE_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:created|made)\s+[\w\-\\/]+(?:directory|folder|dir)[\w\-\\/]+\s+(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:created|made)\s+(?:the\s+)?[\w\-\\/]+(?:\s+(?:directory|folder|dir))\s+(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:created|made)\s+(?:the\s+)?(?:directory|folder|dir)\s+[\w\-\\/]+\s+(?:successfully|complete|now|done)?",
    re.IGNORECASE,
)

# 8. FOLDER_DELETE patterns - Require first-person or explicit action framing
# Handles three structural forms:
#   alt1: deleted/removed/the DIRECTORY dirname  (explicit directory keyword)
#   alt2: deleted/removed [ARG]                (bare path arg, no dir keyword)
#   alt3: deleted/removed PATH_CHAR ARG        (path starting with . or /)
#   alt4: cleaned up PATH_CHAR ARG             (cleaned up .dir or /dir)
# The (?:\s+directory|\s+folder)? clause handles bare "logs/.cache/__pycache__/dist".
FOLDER_DELETE_PATTERNS = re.compile(
    r"\bI\s+(?:have\s+)?(?:deleted|removed)\s+(?:the\s+)?[\w\-\\\/]+(?:\s+(?:directory|folder|dir))\s+(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:deleted|removed)\s+(?:the\s+)?(?:directory|folder|dir)\s+[\w\-\\\/]+\s+(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:deleted|removed)\s+[./\\][^\s]+\s+(?:successfully|complete|now|done)?"
    r"|\bI\s+(?:have\s+)?(?:cleaned\s+up)\s+[./\\][^\s]+\s+(?:successfully|complete|now|done)?",
    re.IGNORECASE,
)

# Words that indicate an Edit operation, not a folder deletion, when they
# appear immediately after "removed" or "deleted" (e.g., "removed my temp file",
# "removed the dead function").  "the" is excluded because it legitimately
# introduces a directory name ("removed the logs directory").
_FOLDER_DELETE_EDIT_WORDS = re.compile(
    r"\b(?:"
    r"my|your|his|her|our|their|a|an|some|this|that|these|those|"
    r"function|method|class|variable|constant|import|statement|block|"
    r"line|lines|code|comment|decorator|property|attribute|argument|parameter|"
    r"handler|listener|callback|closure|lambda|exception|error|bug|issue|fix|"
    r"todo|note|hack|workaround|dead|stale|old|unused|broken"
    r")\b",
    re.IGNORECASE,
)

# Combined file path extraction (used for all types)
FILE_PATH_PATTERNS = re.compile(
    r"[A-Z]:[\\/][^\"\s\]]+"
    r"|[/\\][^\"\s\]]+(?<![a-z])(?<![a-z])"
    r"|\.\.[\\/][^\"\s\]]+"
    r"|\.[\\/][^\"\s\]]+"
    r"|['\"]([^'\"]+\.[^'\"]+)['\"]"
    r"|\b[\w-]+\.(?:py|js|ts|md|json|yaml|yml|txt|log|tmp|bak|old)\b",
    re.IGNORECASE,
)

# Obvious allowlist (conversational denials, future tense, examples, verification discussion)
OBVIOUS_ALLOWLIST = re.compile(
    # Conversational denials
    r"\bI\s+did(?:n'?t|dn't| not)\s+(?:create|modify|delete|remove|write|copy|move|backup)\b"
    r"|\bI\s+hav(?:e'?n't|en't|e not)\s+(?:created|modified|deleted|removed|written|copied|moved|backed\s+up)\b"
    r"|\bI\s+never\s+(?:created|modified|deleted|removed|written|copied|moved|backed\s+up)\b"
    # Future tense
    r"|\bwill\s+(?:create|modify|delete|remove|write|copy|move|backup)\b"
    r"|\bwill\s+be\s+(?:created|deleted|removed|modified|updated)\b"
    r"|\bgoing\s+to\s+(?:create|delete|modify|remove)\b"
    # Capability/requirement statements
    r"|\bcan\s+be\s+(?:created|modified|deleted|removed)\b"
    r"|\bneeds?\s+(?:to\s+be\s+)?(?:creation|deletion|modification|removal)\b"
    r"|\brequires?\s+(?:creation|deletion|modification|removal)\b"
    # Example paths (in quotes or preceded by "like", "similar to")
    r"|\b(?:like|similar\s+to)\s+['\"]?[\w\-\.]+['\"]?"
    r"|\b(?:such\s+as|e\.g\.|for\s+example)\s+['\"]?[\w\-\.]+['\"]?"
    # Conversational verification phrases (discussing verification, not claiming completion)
    r"|\b(?:was|were)\s+(?:also\s+)?(?:verified|confirmed)\b"
    r"|\b(?:file\s+)?(?:operation\s+)?(?:was\s+)?verified\b"
    r"|\bverification\s+(?:has\s+)?failed\b"
    r"|\bverifying\b"
    r"|\bconfirm(?:s|ed)?\s+(?:the\s+)?(?:deletion|removal|creation|modification)\b"
    # Design-proximate deletion: describes state/process, not completion claims
    # e.g. "files are deleted after Whisper transcription" — design intent, not claimed completion
    r"|\bdeleted\s+after\s+(?:whisper|transcription|ingestion|processing|conversion|extraction)\b"
    r"|\bdeleted\s+following\s+(?:whisper|transcription|ingestion|processing|conversion|extraction)\b"
    r"|\bdeletes?\s+after\s+(?:whisper|transcription|ingestion|processing|conversion|extraction)\b",
    re.IGNORECASE,
)

# Verification tools that count as evidence for each claim type
VERIFICATION_TOOLS = frozenset(
    {
        "Read",
        "Glob",
        "Grep",
        "Bash",  # Only if using ls, find, git ls-files, etc.
        "Write",  # For creation/modification claims
        "Edit",  # For modification claims
    }
)

# Bash commands that indicate file system verification
BASH_VERIFICATION_COMMANDS = re.compile(
    r"\bls\b"
    r"|\bfind\b"
    r"|\bgit\s+ls-files\b"
    r"|\btest\b.*-f\b"
    r"|\b\[\b.*-f\b"
    r"|\bhead\b"
    r"|\btail\b"
    r"|\bcat\b"
    r"|\bfile\b"
    r"|\bwc\b",
    re.IGNORECASE,
)


# --- Claim detection ---------------------------------------------------------


def _detect_claims(response: str) -> list[tuple[str, str, list[str]]]:
    """Detect all file/folder operation claims in response.

    Returns list of (matched_text, claim_type, file_paths) tuples.
    """
    if not response:
        return []

    # Check obvious allowlist first
    if OBVIOUS_ALLOWLIST.search(response):
        _logger.debug("matched obvious allowlist pattern - skipping")
        return []

    claims = []

    # Check each claim type
    claim_patterns = [
        ("CREATION", CREATION_PATTERNS),
        ("MODIFICATION", MODIFICATION_PATTERNS),
        ("DELETION", DELETION_PATTERNS),
        ("COPY", COPY_PATTERNS),
        ("MOVE", MOVE_PATTERNS),
        ("BACKUP", BACKUP_PATTERNS),
        ("FOLDER_CREATE", FOLDER_CREATE_PATTERNS),
        ("FOLDER_DELETE", FOLDER_DELETE_PATTERNS),
    ]

    for claim_type, pattern in claim_patterns:
        for match in pattern.finditer(response):
            matched_text = match.group(0)

            # Exclude FOLDER_DELETE false positives: "removed the dead function"
            # matches FOLDER_DELETE_PATTERNS but is an Edit operation, not a folder deletion.
            if claim_type == "FOLDER_DELETE":
                # Two-part filter to distinguish Edit operations from genuine folder deletions.
                # Part A: The matched text itself contains a code noun (e.g., "cleaned up
                # dead code") — this is an Edit, not a folder deletion.
                # Part B: The word immediately AFTER the match is a code noun. This catches
                # cases like "removed the dead function" where the regex only captured
                # "removed the" but the Edit noun comes right after.
                if _FOLDER_DELETE_EDIT_WORDS.search(matched_text):
                    continue
                # Check the next word after the match for edit-word pattern
                remaining = response[match.end() : match.end() + 50].lstrip()
                next_word_match = re.match(r"\w+", remaining)
                if next_word_match:
                    next_word = next_word_match.group(0).lower()
                    if _FOLDER_DELETE_EDIT_WORDS.search(f" {next_word} "):
                        continue

            # Extract file paths from surrounding context
            # Context window: 400 before / 100 after (paths precede actions in natural English)
            start = max(0, match.start() - 400)
            end = min(len(response), match.end() + 100)
            context = response[start:end]

            file_paths = _extract_file_paths(context)

            claims.append((matched_text, claim_type, file_paths))

    return claims


def _extract_file_paths(text: str) -> list[str]:
    """Extract file paths from text using FILE_PATH_PATTERNS."""
    paths = []

    for match in FILE_PATH_PATTERNS.finditer(text):
        path = match.group(0)
        # Clean up quotes if captured
        if path.startswith(("'", '"')) and path.endswith(("'", '"')):
            path = path[1:-1]
        paths.append(path)

    # Deduplicate while preserving order
    seen = set()
    unique_paths = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)

    return unique_paths


def _has_verification_this_turn(tool_events: list[dict]) -> bool:
    """Check if verification tools were used THIS TURN."""
    for event in tool_events:
        tool_name = event.get("name") or event.get("tool_name", "")
        if tool_name in VERIFICATION_TOOLS:
            if tool_name == "Bash":
                command = event.get("command", "")
                if BASH_VERIFICATION_COMMANDS.search(command):
                    return True
            else:
                return True
    return False


# --- Verification logic -----------------------------------------------------


def _verify_claim_has_evidence(
    claim_type: str, file_paths: list[str], tool_events: list[dict]
) -> tuple[bool, str]:
    """Verify that a claim has corresponding tool usage evidence.

    Returns (verified, reason) tuple.
    """
    if not tool_events:
        return False, "No tool events found this turn"

    # Check for appropriate verification based on claim type
    tools_used = set()
    for event in tool_events:
        tool_name = event.get("name") or event.get("tool_name", "")
        tools_used.add(tool_name)

    # Write/Edit tools indicate creation/modification
    if claim_type in ("CREATION", "MODIFICATION"):
        if "Write" in tools_used or "Edit" in tools_used:
            return True, "Write/Edit tools used this turn"
        return False, f"No Write/Edit tools found for {claim_type} claim"

    # Deletion: Check for Bash rm/delete or Write with deletion patterns
    if claim_type == "DELETION":
        if "Write" in tools_used or "Edit" in tools_used:
            return True, "Write/Edit tools used this turn (may indicate deletion)"
        # Check for Bash deletion commands
        for event in tool_events:
            if event.get("name") == "Bash":
                command = event.get("command", "")
                if re.search(r"\brm\s+", command):
                    return True, "Bash rm command used"
                if re.search(r"\bdelete\s+", command, re.IGNORECASE):
                    return True, "Bash delete command used"
        return False, "No deletion tools found this turn"

    # Copy/Move/Backup: Need Read (source exists) + Write/Edit (destination created)
    if claim_type in ("COPY", "MOVE", "BACKUP"):
        if "Read" in tools_used and ("Write" in tools_used or "Edit" in tools_used):
            return True, "Read + Write/Edit tools used (consistent with copy/move/backup)"
        return False, f"Missing Read or Write/Edit tools for {claim_type} claim"

    # Folder operations: Check for Write/Edit or Bash mkdir
    if claim_type in ("FOLDER_CREATE", "FOLDER_DELETE"):
        if "Write" in tools_used or "Edit" in tools_used:
            return True, "Write/Edit tools used (may indicate folder operation)"
        # Check for Bash mkdir/rmdir commands
        for event in tool_events:
            if event.get("name") == "Bash":
                command = event.get("command", "")
                if re.search(r"\bmkdir\s+", command):
                    return True, "Bash mkdir command used"
                if re.search(r"\brmdir\s+", command):
                    return True, "Bash rmdir command used"
        return False, "No folder operation tools found this turn"

    return False, f"No verification tools found for {claim_type} claim"


def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow)."""
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return None

    # Detect claims
    claims = _detect_claims(response)
    if not claims:
        return None  # No claims - allow

    _logger.info(
        "found %d file operation claim(s): %s",
        len(claims),
        [(claim_type, claim_text[:50]) for claim_text, claim_type, _ in claims],
    )

    # Load tool events for THIS TURN
    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or (data.get("session") or {}).get("id", "")
        or ""
    ).strip()

    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
        or ""
    ).strip()

    supplied_events = data.get("tool_events")
    if isinstance(supplied_events, list):
        tool_events = supplied_events
    else:
        tool_events = _load_turn_events(session_id, terminal_id)

    # Evidence system unavailable - warn and allow (fail-warn)
    if tool_events is None:
        _logger.warning(
            "WARN: Evidence store unavailable - cannot verify %d file operation claim(s)",
            len(claims),
        )
        lines = ["Unverified File Operation Claim (evidence system unavailable)\n"]
        lines.append(
            "The response claims file/folder operations occurred, "
            "but the evidence system is unavailable and cannot verify whether "
            "verification tools were used this turn.\n"
        )
        for claim_text, claim_type, file_paths in claims:
            lines.append(f'- Claimed: "{claim_text}" ({claim_type})')
        lines.append("")
        lines.append(
            "Before claiming file operations, verify them: "
            "use Read, Glob, Write, or Edit tools first."
        )
        return {
            "decision": "warn",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_completion_verification_guard",
        }

    # No verification tools found (empty list) - block
    if not tool_events:
        _logger.warning(
            "BLOCK: %d unverified file operation claim(s) (no tools used this turn)",
            len(claims),
        )
        lines = ["Unverified File Operation Claim Detected\n"]
        lines.append(
            "The response claims file/folder operations occurred "
            "without evidence of verification tools used this turn.\n"
        )
        for claim_text, claim_type, file_paths in claims:
            lines.append(f'- Claimed: "{claim_text}" ({claim_type})')
        lines.append("")
        lines.append(
            "Before claiming file operations, verify them: "
            "use Read, Glob, Write, or Edit tools first."
        )
        return {
            "decision": "block",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_completion_verification_guard",
        }

    # Check each claim for verification evidence
    unverified_claims = []
    for claim_text, claim_type, file_paths in claims:
        verified, reason = _verify_claim_has_evidence(claim_type, file_paths, tool_events)
        if not verified:
            unverified_claims.append((claim_text, claim_type, reason))

    if unverified_claims:
        _logger.warning(
            "BLOCK: %d unverified file operation claim(s) (no matching tools)",
            len(unverified_claims),
        )
        lines = ["Unverified File Operation Claim Detected\n"]
        lines.append(
            "The response claims file/folder operations occurred "
            "without evidence of verification tools used this turn.\n"
        )
        for claim_text, claim_type, reason in unverified_claims:
            lines.append(f'- Claimed: "{claim_text}" ({claim_type})')
            lines.append(f"  Reason: {reason}")
        lines.append("")
        lines.append(
            "Before claiming file operations, verify them: "
            "use Read, Glob, Write, or Edit tools first."
        )
        return {
            "decision": "block",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_completion_verification_guard",
        }

    # All claims verified
    _logger.info("file operation claims verified - tools used this turn")
    return None


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_completion_verification_guard"),
        }
    return result


# --- Main ------------------------------------------------------------------


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(result))
        if result.get("decision") == "block":
            sys.exit(2)


if __name__ == "__main__":
    main()
