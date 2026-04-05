#!/usr/bin/env python3
"""
StopHook_rca_contract.py - RCA Contract Structural Gate
=======================================================

Stateless structural gate for RCA turns. Validates 8-field schema
with evidence-links. Only active when rca_turn=True (derived from
skill_state by Stop_router.py).

RCA Contract Schema (8 Required Fields):

| # | Field                | Required | Validation Rules                                        |
|---|----------------------|---------|--------------------------------------------------------|
| 1 | Symptom              | Yes     | Must describe observable error/behavior, not hypothesis |
| 2 | Evidence             | Yes     | Must cite >=1 current-turn tool call (Read/Grep/Bash)   |
| 3 | Executed Path        | Yes     | Must name >=1 function/file reachable via current-turn   |
|   |                      |         | Read/Grep/Bash evidence. Cannot be dead code (0 callers)|
| 4 | Alternative Hypothesis| Yes    | Must exist (can be brief)                              |
| 5 | Falsifier           | Yes     | Must exist and must refute Alternative Hypothesis        |
| 6 | Root Cause           | Yes     | Must name file/symbol/path appearing in Executed Path    |
| 7 | Fix                 | Yes     | Must describe concrete action (file edit, config, etc.) |
| 8 | Verification         | Yes     | Must describe how to confirm fix works                   |

Block Reasons (structural, not wording-based):
- missing-executed-path: No executed path shown
- unreachable-root-cause: Root cause not in Executed Path
- dead-code-in-path: Executed Path references function with 0 callers
- unlabeled-transcript-evidence: Evidence section contains transcript-only
  facts without `transcript-time:` label
- missing-alternative: Alternative Hypothesis absent
- missing-falsifier: Falsifier absent or does not refute alternative
- missing-verification: Verification plan absent or non-specific

LIFECYCLE: Stop (blocking gate -- exits with code 2 to block)
ACTIVATION: Only fires when rca_turn=True (set by Stop_router.py)
STATE: Stateless across turns -- reads skill_state but maintains no durable state
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from pathlib import Path

_logger = logging.getLogger(__name__)

try:
    from evidence_store import load_tool_events_for_context
except Exception:
    load_tool_events_for_context = None

# Import evidence_store functions for binding validation (TASK-006)
try:
    from evidence_store import (
        load_epistemic_bindings,
        load_epistemic_commitments,
    )
except Exception:
    load_epistemic_commitments = None
    load_epistemic_bindings = None

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state"
LOG_DIR = HOOKS_DIR / "state" / "logs"

# --- Logging ---------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)


def _get_logger():
    """Lazy logger initialization to avoid issues at import time."""
    import logging

    logger = logging.getLogger("rca_contract")
    handler = logging.FileHandler(LOG_DIR / "rca_contract.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


# --- RCA Contract Schema Fields -------------------------------------------

REQUIRED_FIELDS = [
    "Symptom",
    "Evidence",
    "Executed Path",
    "Alternative Hypothesis",
    "Falsifier",
    "Root Cause",
    "Fix",
    "Verification",
]

# Block reason codes
BLOCK_REASONS = {
    "missing-symptom": "Symptom section missing or only contains hypothesis",
    "missing-evidence": "No current-turn evidence cited in Evidence section",
    "missing-executed-path": "No executed path shown in Executed Path section",
    "unreachable-root-cause": "Root Cause not reachable from Executed Path",
    "dead-code-in-path": "Executed Path references function with 0 callers",
    "unlabeled-transcript-evidence": "Evidence contains unlabeled transcript-time facts",
    "missing-alternative": "Alternative Hypothesis section missing",
    "missing-falsifier": "Falsifier missing or does not refute alternative",
    "missing-fix": "Fix section missing or only describes symptom",
    "missing-verification": "Verification plan absent or non-specific",
    # TASK-006: Semantic binding validation block reasons
    "unbound-evidence": "Evidence claims not bound to tool events",
    "stale-evidence": "Evidence not from current turn",
    "cross-terminal-evidence": "Evidence from different terminal session",
    "stale-binding": "Binding marked stale due to mutations",
    "evidence-without-tool-events": "Evidence without corresponding tool execution",
    # TASK-004: Structure validation block reasons
    "missing-artifact": "Artifact path cited in Evidence does not exist on disk",
    # TASK-001: Zero-tool-call guard block reason
    "zero-tool-calls-for-confirmed-root-cause": (
        "Confirmed Root Cause declared with zero tool calls — no investigation occurred"
    ),
    # ANTI-PATTERN-1: Single-hypothesis-lock — overfits to first plausible explanation
    "single-hypothesis-lock": (
        "Only one hypothesis presented before declaring root cause. "
        "Generate ≥2 ranked alternatives using hypothesis-scoring.md formula. "
        "Do NOT name root cause until ≥2 hypotheses are explored and falsified."
    ),
    # ANTI-PATTERN-2: No call-site evidence — reasoning from partial reads
    "no-call-site-evidence": (
        "Executed Path names a function without showing callers (call-site evidence). "
        "Run: grep -r 'funcName(' src/ to prove the function is actually called. "
        "Functions with 0 callers are dead code and cannot be the root cause."
    ),
    # ANTI-PATTERN-2: Automatic dead-code detection
    "auto-dead-code": (
        "Function '{func}' has 0 callers in codebase — dead code cannot be root cause. "
        "Trace the actual execution path: find what calls the failing code."
    ),
    # ANTI-PATTERN-3: Band-aid chain — defends local consistency too long
    "band-aid-chain": (
        "XY-SUSPECT: {file} has received {count}+ RCA fixes in this terminal session. "
        "Repeated patches to the same file suggest the root cause is elsewhere. "
        "Consider: Is there a shared dependency or upstream cause?"
    ),
    # ANTI-PATTERN-5: Stale execution path — does not re-ground after codebase changes
    "stale-execution-path": (
        "Executed Path references file(s) modified AFTER this RCA session began. "
        "The execution path may no longer reflect current code. "
        "Re-trace the execution path with current file versions."
    ),
}

# Verification tool names
VERIFICATION_TOOLS = frozenset(
    {
        "Read",
        "Grep",
        "Glob",
        "Bash",
        "View",
        "WebFetch",
    }
)


# --- Turn-scoped Evidence Loading -----------------------------------------


def _get_current_turn_tools(tool_events: list[dict]) -> set[str]:
    """Extract tool names used this turn from tool_events."""
    tools = set()
    for event in tool_events:
        name = event.get("name") or event.get("tool_name", "")
        if name:
            tools.add(name)
    return tools


def _load_turn_scoped_tool_events(session_id: str, terminal_id: str) -> list[dict]:
    """Load turn-safe tool events scoped to both session and terminal."""
    if not session_id or not terminal_id or load_tool_events_for_context is None:
        return []
    try:
        return list(load_tool_events_for_context(session_id, terminal_id, limit=200))
    except Exception as exc:
        _logger.exception("load_turn_scoped_tool_events failed: %s", exc)
        return []


def _has_verification_this_turn(tool_events: list[dict]) -> bool:
    """Check if verification tools (Read/Grep/Bash/etc.) were used this turn."""
    tools = _get_current_turn_tools(tool_events)
    return bool(tools & VERIFICATION_TOOLS)


def _contains_transcript_only_claim(content: str) -> bool:
    lowered = content.lower()
    return "transcript" in lowered and "transcript-time:" not in lowered


def _normalize_section_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def _get_section(sections: dict[str, str], field: str) -> str:
    target = _normalize_section_name(field)
    for key, value in sections.items():
        if _normalize_section_name(key) == target:
            return value
    return ""


# --- Section Parsing ------------------------------------------------------


def _extract_sections(response: str) -> dict[str, str]:
    """Extract RCA sections from response text.

    Returns dict mapping section name to section content.
    Sections are identified by lines starting with "## " or "### " markdown headers,
    or all-caps headings without markdown.
    """
    sections = {}
    lines = response.split("\n")
    current_section = None
    current_content = []

    # Also check for uppercase non-markdown headings: "SYMPTOM:" or "SYMPTOM\n======="
    markdown_header = re.compile(r"^#{1,3}\s+([A-Za-z ]+):?\s*$")
    underline_header = re.compile(r"^([A-Z][A-Z\s]+)\n=+$")
    colon_header = re.compile(r"^([A-Z][A-Za-z\s]+):\s*$")

    for line in lines:
        # Check for markdown header
        md_match = markdown_header.match(line.strip())
        if md_match:
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = md_match.group(1).strip().rstrip(":")
            current_content = []
            continue

        # Check for underline header (SYMPTOM\n=======)
        ul_match = underline_header.match(line.strip())
        if ul_match:
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = ul_match.group(1).strip()
            current_content = []
            continue

        # Check for colon header (SYMPTOM:\n)
        col_match = colon_header.match(line.strip())
        if col_match:
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = col_match.group(1).strip()
            current_content = []
            continue

        # Check for standalone all-caps line followed by content
        if current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _section_exists(sections: dict, field: str) -> bool:
    """Check if a section exists and has non-empty content."""
    content = _get_section(sections, field)
    return bool(content and content.strip())


def _section_has_current_turn_evidence(sections: dict, field: str) -> bool:
    """Check if a section contains evidence of current-turn tool usage.

    Evidence is indicated by:
    - `transcript-time:` label (for transcript-only facts)
    - Direct citation patterns like "Read on X", "Grep found", "Bash showed"
    """
    content = _get_section(sections, field)
    if not content:
        return False

    # Check for explicit current-turn indicators
    current_turn_patterns = [
        r"Read on [`'\"]",
        r"Grep (?:found|matched|showed)",
        r"Bash (?:showed|output|returned|executed)",
        r"From (?:Read|Grep|Bash|Glob|View)",
        r"\btargets?\s+[`'\"](?!.*transcript)",
    ]

    for pattern in current_turn_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def _find_function_mentions(func_name: str) -> int:
    count = 0
    needle = f"{func_name}("
    for path in HOOKS_DIR.rglob("*.py"):
        try:
            count += path.read_text(encoding="utf-8").count(needle)
        except Exception as exc:
            _logger.exception("Failed to read %s: %s", path, exc)
            continue
    return count


def _extract_function_names(text: str) -> list[str]:
    seen: list[str] = []
    for match in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text):
        if match not in seen:
            seen.append(match)
    return seen


def _count_hypothesis_rows(hypothesis_text: str) -> int:
    """Count the number of hypothesis rows in a markdown hypothesis table.

    Looks for table rows (lines starting with |) that contain a score value.
    """
    if not hypothesis_text:
        return 0
    rows = 0
    for line in hypothesis_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("|") and any(c in line for c in ("0.", "1.", "Tier")):
            rows += 1
    return rows


def _check_dead_code_auto(executed_path: str, root_cause: str, falsifier: str) -> list[str]:
    """Automatically detect dead code — ALL function names in Executed Path.

    Unlike _check_dead_code (marker-based), this scans every function name
    mentioned in the Executed Path and checks if it has callers.

    Returns list of dead function names, empty if all functions have callers.

    PERFORMANCE: Scans files once (O(M)), not once per function (O(N×M)).
    """
    func_names = _extract_function_names(executed_path)
    if not func_names:
        return []

    # Start with all functions as potentially dead; remove each found in a file
    dead_functions: set[str] = set(func_names)

    # Scan each file once, checking all needles against each file
    for path in HOOKS_DIR.rglob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
            for func_name in list(dead_functions):
                if f"{func_name}(" in content:
                    dead_functions.discard(func_name)
        except Exception as exc:
            _logger.exception("Failed to read %s: %s", path, exc)
            continue

    return list(dead_functions)


def _has_call_site_evidence(executed_path: str, evidence: str) -> bool:
    """Check if Evidence section shows grep/call-site evidence for Executed Path functions.

    Anti-pattern 2: Reasons from partial reads instead of tracing full execution path.
    If Executed Path names a function, Evidence should show callers (grep results).
    """
    func_names = _extract_function_names(executed_path)
    if not func_names:
        return True  # No functions named, nothing to prove

    # Evidence must show grep results for at least one function in Executed Path
    # Patterns that indicate call-site evidence: "grep found", "callers:", "X calls"
    call_evidence_patterns = [
        r"grep\s+(?:found|matched|calls?|callers?)",
        r"\bcallers?\s*[:=]",
        r"\b\d+\s+callers?",
    ]
    for pattern in call_evidence_patterns:
        if re.search(pattern, evidence, re.IGNORECASE):
            return True
    return False


# --- AP3: Band-Aid Chain Detector ---------------------------------------------
# Multi-terminal isolated via terminal_id. Persists across session compaction.


BAND_AID_FILE = "rca_band_aid.json"
BAND_AID_THRESHOLD = 3
BAND_AID_STATE_TTL = 3600  # 1-hour terminal state TTL (safety net for stale state)


def _load_band_aid_state(terminal_id: str) -> dict:
    """Load band-aid chain state for terminal. Returns empty dict if none."""
    if not terminal_id:
        return {}
    try:
        from __lib.state_paths import get_terminal_state_path
    except Exception:
        return {}
    try:
        path = get_terminal_state_path(terminal_id, BAND_AID_FILE)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            # Safety: check TTL using monotonic time (immune to NTP clock jumps)
            if time.monotonic() - data.get("_ts", 0) > BAND_AID_STATE_TTL:
                return {}
            return data
    except Exception:
        pass
    return {}


def _save_band_aid_state(terminal_id: str, state: dict) -> None:
    """Atomically save band-aid state to terminal-scoped file."""
    if not terminal_id:
        return
    try:
        from __lib.state_paths import get_terminal_state_path
    except Exception:
        return
    path: Path | None = None
    try:
        path = get_terminal_state_path(terminal_id, BAND_AID_FILE)
        state["_ts"] = time.monotonic()
        # Atomic write: write to temp then rename
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, encoding="utf-8"), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        _logger.error(
            "Failed to save band-aid state to %s: %s. "
            "AP3 band-aid chain detection may not persist across sessions.",
            path,
            exc,
        )
    except Exception as exc:
        _logger.error("Unexpected error saving band-aid state: %s", exc)


def _extract_fix_files(fix_text: str) -> list[str]:
    """Extract file paths from Fix section."""
    if not fix_text:
        return []
    # Match paths like src/foo.py or path/to/file.ext
    # Also matches Windows paths: C:/foo/bar.py
    paths: list[str] = []
    for match in re.finditer(r"([A-Za-z]:[\\\/])?[\w./\\-]+\.py\b", fix_text):
        path = match.group()
        if path and len(path) > 3:  # Skip short false positives
            paths.append(path)
    return paths


def _check_band_aid_chain(fix_text: str, terminal_id: str) -> list[str]:
    """Check if Fix section targets a file that's been patched >= BAND_AID_THRESHOLD times.

    Anti-pattern 3: Defends local consistency too long — repeated patches to same file
    signal a systemic issue, not a root cause.

    Returns list of block messages for files exceeding threshold.
    """
    if not terminal_id or not fix_text:
        return []

    files = _extract_fix_files(fix_text)
    if not files:
        return []

    # Import here to avoid import-time side effects
    try:
        from __lib.file_lock import FileLock
        from __lib.state_paths import get_terminal_state_path
    except Exception:
        return []

    lock_path = get_terminal_state_path(terminal_id, BAND_AID_FILE).with_suffix(".lock")
    try:
        with FileLock(lock_path, timeout=5.0):
            state = _load_band_aid_state(terminal_id)
            fixes: dict = state.get("fixes", {})

            block_messages: list[str] = []
            for fpath in files:
                # Normalize to forward slashes for consistent key
                key = fpath.replace("\\", "/")
                count = fixes.get(key, 0) + 1
                fixes[key] = count
                if count >= BAND_AID_THRESHOLD:
                    block_messages.append(
                        BLOCK_REASONS["band-aid-chain"].format(file=key, count=BAND_AID_THRESHOLD)
                    )

            state["fixes"] = fixes
            _save_band_aid_state(terminal_id, state)
            return block_messages
    except TimeoutError:
        _logger.warning(
            "Could not acquire lock for band-aid state update on terminal %s. "
            "Skipping band-aid chain check this turn.",
            terminal_id,
        )
        return []
    except Exception as exc:
        _logger.error("Unexpected error in band-aid chain check: %s", exc)
        return []


# --- AP5: Filesystem Freshness Validator --------------------------------------
# Stateless — no terminal state needed. Checks mtime on each call.


def _extract_file_paths_from_path(executed_path: str) -> list[str]:
    """Extract file paths from Executed Path text."""
    if not executed_path:
        return []
    paths: list[str] = []
    # Match Python file paths: src/module.py, package/module.py, etc.
    # Also matches Windows paths: P:/foo/bar.py, C:/Users/...
    for match in re.finditer(r"([A-Za-z]:[\\\/])?[\w./\\-]+\.py\b", executed_path):
        path = match.group()
        if path and len(path) > 3:
            paths.append(path)
    return paths


def _get_file_mtime(file_path: str) -> float | None:
    """Get modification time of a file, or None if not found.

    Returns None only when the file does not exist.
    Permission errors, I/O errors, and other exceptions are logged and
    re-raised so callers can distinguish "not found" from "access denied".
    """
    p: Path = Path(file_path)
    if not p.is_absolute():
        # Try project root (P:/) for relative paths
        p = Path("P:/") / file_path
    try:
        if p.exists():
            return p.stat().st_mtime
        return None  # File not found — normal case, return None
    except PermissionError as exc:
        _logger.error("Permission denied accessing %s: %s", p, exc)
        raise
    except OSError as exc:
        _logger.error("I/O error accessing %s: %s", p, exc)
        raise
    except Exception as exc:
        _logger.error("Unexpected error accessing %s: %s", p, exc)
        raise


def _check_stale_execution_path(
    executed_path: str,
    rca_timestamp: float | None,
) -> list[str]:
    """Check if files in Executed Path were modified after RCA session start.

    Anti-pattern 5: Does not re-ground after codebase changes underneath it.
    If a file in the Executed Path has mtime > rca_timestamp, the execution path
    may be stale.

    Args:
        executed_path: The Executed Path section text
        rca_timestamp: Unix timestamp when RCA session started (from session start or first turn)

    Returns list of block messages for stale files.
    """
    if not rca_timestamp or not executed_path:
        return []

    files = _extract_file_paths_from_path(executed_path)
    if not files:
        return []

    block_messages: list[str] = []
    for fpath in files:
        mtime = _get_file_mtime(fpath)
        if mtime is not None and mtime > rca_timestamp:
            block_messages.append(
                f"stale-execution-path:{fpath} (modified {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))} > RCA session start)"
            )

    return block_messages


def _contains_unverified_token(text: str) -> bool:
    """Check for UNVERIFIED as a standalone word token, not substring.

    Used to exempt tentative RCA conclusions from the zero-tool-call guard.
    """
    return bool(re.search(r"\bUNVERIFIED\b", text, re.IGNORECASE))


# --- Structure Validation (TASK-004): Artifact Path Existence -----------------------


def _validate_artifact_paths_exist(sections: dict) -> list[str]:
    """Validate that artifact paths cited in Evidence actually exist on disk.

    Returns list of block reasons for missing artifacts.
    """
    evidence = _get_section(sections, "Evidence")
    if not evidence:
        return []

    artifact_paths = _extract_artifact_paths(evidence)
    if not artifact_paths:
        return []

    block_reasons = []
    for path_str in artifact_paths:
        # Skip URL-like paths (http://, https://, etc.)
        if path_str.startswith(("http://", "https://", "ftp://", "file://")):
            continue
        # Try as absolute path first
        p = Path(path_str)
        if not p.is_absolute():
            # Try relative to project root (P:\)
            p = Path("P:/") / path_str
        if not p.exists():
            block_reasons.append(f"missing-artifact:{path_str}")

    return block_reasons


# --- Semantic Binding Validation (TASK-006) --------------------------------


def _extract_artifact_paths(evidence_text: str) -> list[str]:
    """Extract artifact paths from evidence text.

    Looks for file path patterns like:
    - Read `path/to/file.py`
    - path/to/file.py:123
    - Grep found in `directory/`

    Returns normalized artifact paths.
    """
    if not evidence_text:
        return []

    # Pattern for file paths in backticks or after Read/Grep/etc
    path_patterns = [
        r'Read\s+(?:on\s+)?(?:from\s+)?[`"]([^`"]+)[`"]',  # Read `path` (with optional "on"/"from", supports Windows paths)
        r'Grep\s+found\s+(?:\w+\s+)?in\s+[`"]([^`"]+)[`"]',  # Grep found [pattern] in `path`
        r'Bash\s+(?:showed|output).*?in\s+[`"]([^`"]+)[`"]',  # Bash in `path`
        r":\s*([\\w./-]+\\\w[\\w./-]+)",  # file.py:123 format
    ]

    artifacts = set()
    for pattern in path_patterns:
        for match in re.finditer(pattern, evidence_text, re.IGNORECASE):
            artifact = match.group(1)
            # Normalize backslashes to forward slashes
            artifact = artifact.replace("\\", "/")
            # Extract directory path for file:line format (but preserve Windows drive letters)
            if ":" in artifact:
                # Check if colon is a line number (comes after path separator) or drive letter (before any path separator)
                if "/" in artifact and artifact.find("/") < artifact.rfind(":"):
                    # Line number format: "path/to/file.py:123" - slash comes before colon
                    artifact = artifact.rsplit(":", 1)[0]
                # else: Windows drive letter like "C:/path" - keep as is
            if artifact:
                artifacts.add(artifact)

    return sorted(artifacts)


def _validate_evidence_bindings(
    sections: dict,
    tool_events: list[dict],
    session_id: str,
    terminal_id: str,
) -> list[str]:
    """Validate that evidence claims are bound to actual tool events.

    Checks:
    1. Artifact paths in Evidence section have bindings to tool events
    2. Bindings are from the same terminal (no cross-terminal contamination)
    3. Bindings reference tool events that actually occurred this turn

    Returns list of block reasons (empty if all valid).
    """
    if not load_epistemic_bindings:
        return []  # Fail-open if binding system unavailable

    evidence = _get_section(sections, "Evidence")
    if not evidence:
        return []  # No evidence to validate

    block_reasons = []

    # Extract artifact paths from evidence
    artifact_paths = _extract_artifact_paths(evidence)

    if not artifact_paths:
        return []  # No artifacts to validate

    # Get current turn tool event IDs
    tool_event_ids = set()
    for event in tool_events:
        event_id = event.get("id")
        if event_id:
            tool_event_ids.add(event_id)

    if not tool_event_ids:
        # No tool events this turn, but evidence claims artifacts
        if artifact_paths:
            block_reasons.append("evidence-without-tool-events")
        return block_reasons

    # Load bindings for this session/terminal
    try:
        bindings = list(
            load_epistemic_bindings(
                session_id=session_id,
                terminal_id=terminal_id,
            )
        )
    except Exception as exc:
        _logger.exception("Evidence binding validation failed: %s", exc)
        return []  # Fail-open on binding load failure

    # Check each artifact path has valid bindings
    for artifact_path in artifact_paths:
        # Find bindings for this artifact
        artifact_bindings = [b for b in bindings if b.get("artifact_path", "") == artifact_path]

        if not artifact_bindings:
            block_reasons.append(f"unbound-evidence:{artifact_path}")
            continue

        # Check bindings reference current-turn tool events
        valid_bindings = [b for b in artifact_bindings if b.get("tool_event_id") in tool_event_ids]

        if not valid_bindings:
            block_reasons.append(f"stale-evidence:{artifact_path}")
            continue

        # Check for cross-terminal contamination
        cross_terminal_bindings = [
            b for b in artifact_bindings if b.get("terminal_id", "") != terminal_id
        ]

        if cross_terminal_bindings:
            block_reasons.append(f"cross-terminal-evidence:{artifact_path}")
            continue

        # Check if binding is marked stale
        stale_bindings = [b for b in artifact_bindings if b.get("is_stale") == 1]

        if stale_bindings:
            block_reasons.append(f"stale-binding:{artifact_path}")

    return block_reasons


# --- Main Validation Logic ------------------------------------------------


def _validate_rca_contract(
    response: str,
    tool_events: list[dict],
    rca_turn: bool,
    session_id: str = "",
    terminal_id: str = "",
    rca_timestamp: float | None = None,
) -> tuple[bool, list[str]]:
    """Validate RCA contract fields.

    Returns (is_valid, block_reasons) tuple.
    is_valid is True if all required fields pass.
    block_reasons is list of failure codes.
    """
    if not rca_turn:
        return True, []  # Not an RCA turn, skip validation

    block_reasons: list[str] = []
    sections = _extract_sections(response)

    symptom = _get_section(sections, "Symptom")
    evidence = _get_section(sections, "Evidence")
    executed_path = _get_section(sections, "Executed Path")
    alternative = _get_section(sections, "Alternative Hypothesis")
    falsifier = _get_section(sections, "Falsifier")
    root_cause = _get_section(sections, "Root Cause")
    fix = _get_section(sections, "Fix")
    verification = _get_section(sections, "Verification")

    # Field 1: Symptom
    if not symptom:
        block_reasons.append(BLOCK_REASONS["missing-symptom"])

    # Field 2: Evidence - must have current-turn tool evidence
    if not evidence:
        block_reasons.append(BLOCK_REASONS["missing-evidence"])
    elif _contains_transcript_only_claim(evidence):
        block_reasons.append(BLOCK_REASONS["unlabeled-transcript-evidence"])
    elif not _has_verification_this_turn(tool_events) or not _section_has_current_turn_evidence(
        sections, "Evidence"
    ):
        block_reasons.append(BLOCK_REASONS["missing-evidence"])
    else:
        # TASK-006: Validate evidence bindings (only if evidence exists and has current-turn indicators)
        binding_block_reasons = _validate_evidence_bindings(
            sections, tool_events, session_id, terminal_id
        )
        block_reasons.extend(binding_block_reasons)

    # TASK-004: Structure validation - artifact paths must exist (independent of tool-events gate)
    if evidence and not _contains_transcript_only_claim(evidence):
        path_block_reasons = _validate_artifact_paths_exist(sections)
        block_reasons.extend(path_block_reasons)

    # Field 3: Executed Path
    if not executed_path:
        block_reasons.append(BLOCK_REASONS["missing-executed-path"])
    elif _contains_transcript_only_claim(executed_path):
        block_reasons.append(BLOCK_REASONS["unlabeled-transcript-evidence"])

    # ANTI-PATTERN-2: Call-site evidence — must show callers for named functions
    # Only fires when Executed Path names functions AND Evidence exists
    func_names_in_path = _extract_function_names(executed_path)
    if func_names_in_path and evidence and not _has_call_site_evidence(executed_path, evidence):
        block_reasons.append(BLOCK_REASONS["no-call-site-evidence"])

    # ANTI-PATTERN-5: Stale execution path — files modified after RCA session started
    # rca_timestamp is passed in; if not available, skip this check (fail-open)
    stale_block_reasons = _check_stale_execution_path(executed_path, rca_timestamp)
    block_reasons.extend(stale_block_reasons)

    # ANTI-PATTERN-1: Single-hypothesis-lock — overfits to first plausible explanation
    # Require ≥2 ranked alternatives before declaring root cause
    if root_cause and alternative:
        hypo_count = _count_hypothesis_rows(alternative)
        if hypo_count < 2:
            block_reasons.append(BLOCK_REASONS["single-hypothesis-lock"])

    # Field 4: Alternative Hypothesis
    if not alternative:
        block_reasons.append(BLOCK_REASONS["missing-alternative"])

    # Field 5: Falsifier
    if not falsifier:
        block_reasons.append(BLOCK_REASONS["missing-falsifier"])
    elif alternative:
        alternative_tokens = {
            token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", alternative)
        }
        falsifier_lower = falsifier.lower()
        if alternative_tokens and not any(token in falsifier_lower for token in alternative_tokens):
            block_reasons.append(BLOCK_REASONS["missing-falsifier"])

    # Field 6: Root Cause - must be reachable from Executed Path
    if not root_cause:
        block_reasons.append(BLOCK_REASONS["unreachable-root-cause"])
    else:
        identifiers = re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*",
            root_cause,
        )
        identifiers = [idf for idf in identifiers if len(idf) > 2]
        if executed_path and identifiers:
            executed_lower = executed_path.lower()
            found = any(idf.lower() in executed_lower for idf in identifiers)
            if not found:
                block_reasons.append(BLOCK_REASONS["unreachable-root-cause"])
        # ANTI-PATTERN-2: Automatic dead-code detection — scan ALL functions in Executed Path
        dead_funcs = _check_dead_code_auto(executed_path, root_cause, falsifier)
        if dead_funcs:
            for func in dead_funcs:
                block_reasons.append(
                    BLOCK_REASONS["auto-dead-code"].format(func=func)
                )

    # Field 7: Fix
    if not fix:
        block_reasons.append(BLOCK_REASONS["missing-fix"])

    # ANTI-PATTERN-3: Band-aid chain — repeated patches to same file signal systemic issue
    # Check after Fix is parsed so we know what files were patched
    if fix and terminal_id:
        band_aid_messages = _check_band_aid_chain(fix, terminal_id)
        block_reasons.extend(band_aid_messages)

    # Field 8: Verification
    if not verification:
        block_reasons.append(BLOCK_REASONS["missing-verification"])
    else:
        # Check for vague verification (just "test it", "verify", etc.)
        vague_patterns = [
            r"^test\s+it\s*$",
            r"^verify\s*$",
            r"^check\s+it\s*$",
            r"^run\s+the?\s+test",
        ]
        is_vague = any(re.match(p, verification.strip(), re.IGNORECASE) for p in vague_patterns)
        if is_vague:
            block_reasons.append(BLOCK_REASONS["missing-verification"])

    unique_reasons = list(dict.fromkeys(block_reasons))

    # TASK-001: Zero-tool-call guard — INSIDE _validate_rca_contract so tool_events is resolved
    # This runs after all 8 fields are validated, with tool_events already loaded via fallback
    root_cause_confirmed = bool(root_cause) and not _contains_unverified_token(root_cause)
    if root_cause_confirmed and not tool_events:
        unique_reasons.append(BLOCK_REASONS["zero-tool-calls-for-confirmed-root-cause"])

    return len(unique_reasons) == 0, unique_reasons


# --- Public Interface -----------------------------------------------------


def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow)."""
    # Only validate if rca_turn is set
    rca_turn = data.get("rca_turn", False)
    if not rca_turn:
        return None  # Not an RCA turn, skip

    response = data.get("assistant_response", "") or data.get("response", "") or ""
    if not response:
        return None  # No response to validate

    # Get session_id and terminal_id for binding validation (TASK-006)
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")

    # AP5: Get RCA session start timestamp for stale execution path check
    rca_timestamp: float | None = data.get("session_start_ts", None)

    # Get tool events
    tool_events = data.get("tool_events", [])
    if not tool_events:
        tool_events = _load_turn_scoped_tool_events(session_id, terminal_id)

    is_valid, block_reasons = _validate_rca_contract(
        response, tool_events, rca_turn, session_id, terminal_id, rca_timestamp
    )

    if is_valid:
        return None  # All checks pass

    # Build block message
    logger = _get_logger()
    logger.info("RCA contract validation failed: %s", block_reasons)

    reason_lines = [
        "**RCA Contract Structural Validation Failed**\n",
        "Your RCA response is missing required structural elements:\n",
    ]
    for reason in block_reasons:
        reason_lines.append(f"- {reason}")

    reason_lines.extend(
        [
            "",
            "Required sections: Symptom, Evidence (>=1 current-turn tool), Executed Path,",
            "Alternative Hypothesis, Falsifier, Root Cause (in Executed Path), Fix, Verification.",
            "",
            "Do NOT block on wording style -- only on missing structural proof.",
        ]
    )

    return {
        "decision": "block",
        "reason": "\n".join(reason_lines),
        "blocking_hook": "StopHook_rca_contract",
        "block_reasons": block_reasons,
    }


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "StopHook_rca_contract"),
        }
    return result


# --- Main ----------------------------------------------------------------


def main() -> None:
    """Entry point for subprocess mode."""
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
    else:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
