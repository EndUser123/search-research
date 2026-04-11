#!/usr/bin/env python3
"""Investigation Gate Enforcement Hook (PreToolUse).

PURPOSE: Block code modifications that bypass Investigation Gate.
PROBLEM ADDRESSED: AI proposes fixes from error patterns without understanding architecture.
TRANSCRIPT REFERENCE: Parts 1, 2, 4 - all showed fix attempts without reading relevant files.

ENFORCEMENT MECHANISM:
- Tracks files read in session
- Blocks writes to files/modules not yet investigated
- Requires minimum read coverage before allowing modifications

CONSTITUTIONAL BASIS:
- userPreferences: "Before proposing ANY solution... Check: Does the system already solve this?"
- CLAUDE_updated.md: "Plan-Then-Act Pattern"
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Type aliases for clarity
type ToolDict = dict[str, Any]
type InvestigationState = dict[str, Any]
type CheckResult = tuple[bool, str]


def sanitize_path(path: str | None) -> str:
    """Remove dangerous characters from file paths for safe logging.

    Prevents log injection attacks by removing newlines, carriage returns,
    ANSI escape sequences, and null bytes from file paths before they
    are interpolated into error messages.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path safe for logging, or '<unknown>' if path is None/empty
    """
    if not path:
        return "<unknown>"
    # Remove newlines, carriage returns, ANSI escapes, and null bytes
    return re.sub(r"[\n\r\x1b\x00]", "", str(path))


def _safe_id_str(s: str) -> str:
    """Sanitize string for use in filenames.

    Strips <>:\"//|?*, replaces spaces with _, truncates to 64 chars.

    Args:
        s: Raw terminal_id string

    Returns:
        Sanitized string safe for use in filenames
    """
    if not s or not s.strip():
        return "default"
    # Replace special chars with underscore (each char individually, not as group)
    result = re.sub(r"[!@#<>:\"'/\\|?*]", "_", s)
    result = result.replace(" ", "_")
    return result[:64]


def _is_compaction_scenario(state: InvestigationState, input_data: dict) -> bool:
    """Detect if we're in a post-compaction scenario with lost state.

    Compaction indicators:
    - State has no files_read (fresh or cleared)
    - Transcript entries exist in input (compaction preserves transcript context)
    - State timestamp is recent (within current session window)

    Returns:
        True if compaction detected and transcript has prior tool calls
    """
    if state.get("files_read"):
        return False

    transcript_entries = input_data.get("transcript_entries", [])
    if not transcript_entries:
        return False

    # Check for tool calls that predate the state (compaction preserved them)
    state_ts = state.get("timestamp", 0)
    for entry in transcript_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") == "tool":
            entry_ts = entry.get("timestamp", 0)
            if entry_ts and entry_ts < state_ts:
                return True

    return False


def _reconstruct_files_read_from_input(input_data: dict) -> list[str]:
    """Reconstruct files_read from transcript entries in hook input.

    After session compaction, the transcript preserves tool call history.
    This function extracts Read/Grep/Glob file paths from transcript entries
    to reconstruct investigation coverage.

    Args:
        input_data: Hook input dict with transcript_entries

    Returns:
        List of file paths that were read before compaction

    Note:
        WebFetch and WebSearch are intentionally excluded from file path extraction
        because they produce URLs, not file paths. They remain in the broader
        "investigation activity" concept but don't contribute to files_read.
    """
    READ_TOOLS = {
        "read_file", "View", "cat", "grep", "find",
        "search_files", "Bash", "Read", "Glob", "Grep",
    }
    transcript_entries = input_data.get("transcript_entries", [])
    files: list[str] = []

    for entry in transcript_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "tool":
            continue
        # Schema fallback: 'name' or 'tool_name', 'input' or 'args'
        tool_name = entry.get("name") or entry.get("tool_name", "")
        if tool_name not in READ_TOOLS:
            continue

        tool_input = entry.get("input") or entry.get("args") or {}
        path = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or ""
        )
        if path and path not in files:
            files.append(path)

    return files


# Add CSF to path for CKS access
_csf_src = Path(__file__).resolve().parent.parent.parent / "__csf" / "src"
if _csf_src.exists():
    sys.path.insert(0, str(_csf_src))

# Import CKS cache for performance (lazy load only when needed)
CKS_CACHE_ENABLED = False
CKS_CACHE = None


def get_cks_cache():
    """Lazy load CKS cache only when needed (for write operations)."""
    global CKS_CACHE, CKS_CACHE_ENABLED
    if CKS_CACHE is None:
        try:
            from _cks_cache import get_cache, maybe_clear_cache

            maybe_clear_cache()  # Clear if environment variable set
            CKS_CACHE = get_cache()
            CKS_CACHE_ENABLED = True
        except ImportError:
            CKS_CACHE = None
            CKS_CACHE_ENABLED = False
    return CKS_CACHE


hooks_dir = Path(__file__).resolve().parent

# CKS pre-load - lazy import only when needed for write blocks
CKS_PRELOAD_AVAILABLE = False
is_model_ready = lambda: False


def _load_cks_preload():
    """Lazy load CKS preload module only when needed."""
    global CKS_PRELOAD_AVAILABLE, is_model_ready
    try:
        import importlib.util

        preload_spec = importlib.util.spec_from_file_location(
            "SessionStart_cks_preload", hooks_dir / "SessionStart_cks_preload.py"
        )
        if preload_spec and preload_spec.loader:
            preload_module = importlib.util.module_from_spec(preload_spec)
            preload_spec.loader.exec_module(preload_module)
            CKS_PRELOAD_AVAILABLE = True
            is_model_ready = preload_module.is_model_ready
    except Exception:
        CKS_PRELOAD_AVAILABLE = False
        is_model_ready = lambda: False


# === CONFIGURATION ===

# CKS trigger words for this hook
HOOK_TRIGGERS = [
    "debug",
    "investigate",
    "diagnose",
    "monitor",
    "stuck",
    "error",
    # Memory-specific triggers (for Git, TTL, state management lessons)
    "git",
    "multi-terminal",
    "concurrent",
    "race condition",
    "ttl",
    "time to live",
    "session state",
    "shared state",
    "state management",
    "cache",
    "storage",
]

# Architectural recommendation patterns (anti-laziness gate)
# Detects suggestions to move/relocate code without prior investigation
ARCH_RECOMMENDATION_ENABLED = os.environ.get("CSF_ARCH_RECOMMENDATION_GATE", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

# Combined pattern: action verbs + common destinations
# Matches: "move X to Y", "belongs in Z", "should go to /skill", etc.
_ARCH_RECOMMENDATION_PATTERN = re.compile(
    r"(?:move|belongs|suggest|put|fit).+(?:cognitive-stack|main|/[\w-]+)", re.IGNORECASE
)

# Problem statement detection pattern
# Detects diagnostic claims like "hook is broken", "file is not working", "not registered"
# Named group 'target' captures the specific file/hook being claimed as broken
_PROBLEM_STATEMENT_PATTERN = re.compile(
    r"(?i)("
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?working|"
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?broken|"
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?failing|"
    r"\b(?:hook|file|script)\s+(?:doesn't|does\s+not|isn't|is\s+not)\s+(?:work|firing|registered)|"
    r"\bnot\s+(?:registered|loading|firing)|"
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?malformed|"
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?error|"
    r"\b(?:hook|file|script|module)\s+(?:is\s+)?(?:not\s+)?crash|"
    r"(?:hook|file|script)\s+(?:is\s+)?(?:not\s+)?not\s+firing"
    r")"
)

# Pattern to extract the target filename from problem statements
_TARGET_EXTRACTION_PATTERN = re.compile(
    r"(?i)\b(?P<target>\w+\.py|\w+_tldr\.py|\w+_gate\.py|\w+_hook\.py|Session\w+\.py)\b"
)

# Common destination keywords that trigger the gate
ARCH_DESTINATION_KEYWORDS = ["cognitive-stack", "main", "/s", "/all", "/arch", "/code", "/refactor"]

# Architecture files that count as investigation
ARCHITECTURE_FILES = ["SKILL.md", "CLAUDE.md", "ARCHITECTURE.md", "README.md"]

# Bypass flag for architectural recommendations
ARCH_RECOMMENDATION_BYPASS = "--allow-arch-rec"

# Mode: "block" (default) or "warn" (advisory only, logs to file)
ARCH_RECOMMENDATION_MODE = os.environ.get("CSF_ARCH_RECOMMENDATION_MODE", "block").lower()

# Log file for warn mode
ARCH_REC_LOG_FILE = (
    Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    / "logs"
    / "investigation_gate_arch_rec.jsonl"
)

ENABLED = os.environ.get("CSF_INVESTIGATION_GATE", "1").lower() in ("1", "true", "yes", "on")
STATE_FILE = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state")) / "investigation_state.json"
MIN_RELATED_READS = int(os.environ.get("CSF_MIN_READS_BEFORE_WRITE", "1"))
HIGH_RISK_MIN_RELATED_READS = int(
    os.environ.get(
        "CSF_MIN_READS_HIGH_RISK",
        str(max(MIN_RELATED_READS + 1, 2)),
    )
)
if HIGH_RISK_MIN_RELATED_READS < MIN_RELATED_READS:
    HIGH_RISK_MIN_RELATED_READS = MIN_RELATED_READS
DEBUG = os.environ.get("CSF_HOOK_DEBUG", "0") == "1"

# Directories exempt from investigation requirement (staging, temp, test fixtures).
# New file creation in these dirs doesn't require prior reads.
INVESTIGATION_EXEMPT_DIRS = {
    s.strip()
    for s in os.environ.get(
        "CSF_INVESTIGATION_EXEMPT_DIRS",
        ".staging,tmp,temp,.tmp,test_fixtures,__pycache__",
    ).split(",")
    if s.strip()
}

# Tools that count as "investigation"
READ_TOOLS = {
    "read_file",
    "View",
    "cat",
    "grep",
    "find",
    "search_files",
    "Bash",
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
}
# Tools that require prior investigation
WRITE_TOOLS = {
    "write_file",
    "str_replace_editor",
    "edit_file",
    "Write",
    "patch",
    "Edit",
    "MultiEdit",
}

# CRITICAL: "Write" in READ_TOOLS would auto-track writes as reads, bypassing investigation.
# Remove "Write" from READ_TOOLS to prevent write-before-read bypass.

# === STATE MANAGEMENT ===

_RESOLVED_STATE_FILE: Path | None = None


def _state_file_candidates(terminal_id: str = "") -> list[Path]:
    safe_terminal = _safe_id_str(terminal_id) if terminal_id else "default"
    configured = (
        Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
        / f"investigation_state_{safe_terminal}.json"
    )
    local_fallback = (
        hooks_dir / "session_data" / f"investigation_state_{safe_terminal}.json"
    )
    temp_fallback = (
        Path(tempfile.gettempdir())
        / "claude_hooks"
        / f"investigation_state_{safe_terminal}.json"
    )
    return [configured, local_fallback, temp_fallback]


def _candidate_is_writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        probe = path.parent / ".investigation_state_probe"
        with open(probe, "a", encoding="utf-8"):
            pass
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass
        return True
    except (OSError, PermissionError):
        return False


def _resolve_state_file(terminal_id: str = "") -> Path:
    for candidate in _state_file_candidates(terminal_id):
        if _candidate_is_writable(candidate):
            return candidate
    raise PermissionError("No writable investigation state path available")


def load_state(terminal_id: str = "", input_data: dict | None = None) -> InvestigationState:
    """Load investigation state from persistent storage.

    Args:
        terminal_id: Terminal identifier for state scoping
        input_data: Hook input dict (for compaction detection and transcript reconstruction)
    """
    state_file = _resolve_state_file(terminal_id)
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
                # Validate required keys exist
                if "files_read" not in state:
                    state["files_read"] = []
                if "timestamp" not in state:
                    state["timestamp"] = 0
                # Restore set type for modules_investigated after deserialization
                if "modules_investigated" in state and isinstance(state["modules_investigated"], list):
                    state["modules_investigated"] = set(state["modules_investigated"])
                # Reconstruct from transcript if compaction detected
                if input_data and _is_compaction_scenario(state, input_data):
                    recovered_files = _reconstruct_files_read_from_input(input_data)
                    if recovered_files:
                        state["files_read"] = recovered_files
                        state["_reconstructed_from_transcript"] = True
                return state
        except (json.JSONDecodeError, KeyError):
            state = fresh_state(terminal_id)
            if input_data and _is_compaction_scenario(state, input_data):
                recovered_files = _reconstruct_files_read_from_input(input_data)
                if recovered_files:
                    state["files_read"] = recovered_files
                    state["_reconstructed_from_transcript"] = True
            return state
    state = fresh_state(terminal_id)
    if input_data and _is_compaction_scenario(state, input_data):
        recovered_files = _reconstruct_files_read_from_input(input_data)
        if recovered_files:
            state["files_read"] = recovered_files
            state["_reconstructed_from_transcript"] = True
    return state


def fresh_state(terminal_id: str = "") -> InvestigationState:
    return {
        "timestamp": datetime.now().timestamp(),
        "terminal_id": _safe_id_str(terminal_id) if terminal_id else "default",
        "files_read": [],
        "modules_investigated": set(),
        "investigation_declared": False,
        "greenfield_declared": False,
        "searches_performed": [],
    }


def save_state(state: InvestigationState, terminal_id: str = "") -> None:
    """Persist investigation state."""
    state_file = _resolve_state_file(terminal_id)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    # Convert set to list for JSON
    state_copy = state.copy()
    if isinstance(state_copy.get("modules_investigated"), set):
        state_copy["modules_investigated"] = list(state_copy["modules_investigated"])
    with open(state_file, "w") as f:
        json.dump(state_copy, f, indent=2)


# === PATH ANALYSIS ===


def extract_module(filepath: str) -> str | None:
    """Extract module/directory from filepath for relationship tracking."""
    path = Path(filepath)
    parent = path.parent
    # Never track drive/root as a module; it creates universal ancestry matches.
    if str(parent) == parent.anchor:
        return None
    if path.suffix in {".py", ".js", ".ts", ".tsx"}:
        return str(parent)
    return str(parent) if parent != path else None


def paths_related(read_path: str, write_path: str) -> bool:
    """Check if a read path provides investigation coverage for a write path."""
    read_mod = extract_module(read_path)
    write_mod = extract_module(write_path)

    if not read_mod or not write_mod:
        return False

    # Same directory = related
    if read_mod == write_mod:
        return True

    # Parent/child relationship
    try:
        read_p = Path(read_mod).resolve()
        write_p = Path(write_mod).resolve()
        # Root-level parents (e.g., P:\) are not meaningful module coverage.
        if str(read_p) == read_p.anchor or str(write_p) == write_p.anchor:
            return False
        return read_p in write_p.parents or write_p in read_p.parents
    except (OSError, ValueError):
        return False


def count_related_reads(write_path: str, files_read: list[str]) -> int:
    """Count how many read files provide coverage for a write target."""
    return sum(1 for rp in files_read if paths_related(rp, write_path))


def _is_structural_code_change(tool_name: str, tool_input: ToolDict, filepath: str) -> bool:
    """Detect edits that are likely to affect module/API behavior."""
    code_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"}
    if Path(filepath).suffix.lower() not in code_exts:
        return False

    if tool_name in {"MultiEdit", "patch"}:
        return True

    old_s = str(tool_input.get("old_string") or "")
    new_s = str(tool_input.get("new_string") or "")
    content = str(tool_input.get("content") or tool_input.get("code") or "")
    combined = "\n".join([old_s, new_s, content])

    structural_patterns = [
        r"\b(def|class|async\s+def)\b",
        r"^\s*(from|import)\s+",
        r"^\s*(public|private|protected)\s+",
        r"\b(interface|enum|type)\b",
        r"\b(return|raise|throw)\b",
    ]
    if any(re.search(pat, combined, re.MULTILINE) for pat in structural_patterns):
        return True

    if combined.count("\n") >= 8:
        return True

    return False


def _required_related_reads(tool_name: str, tool_input: ToolDict, filepath: str) -> tuple[int, str]:
    """
    Risk-based investigation policy:
    - Low risk: target-file understanding is enough (>= MIN_RELATED_READS).
    - High risk (structural code changes): require broader context.
    """
    if _is_structural_code_change(tool_name, tool_input, filepath):
        return HIGH_RISK_MIN_RELATED_READS, "high"
    return MIN_RELATED_READS, "low"


# === ARCHITECTURAL RECOMMENDATION DETECTION ===


def _log_arch_rec_warning(
    user_message: str,
    destination: str,
    files_read: list[str],
    recommendation_context: str = "",
    pattern_confidence: float = 0.0,
    full_message: str = "",
) -> None:
    """Log enhanced architectural recommendation warning to JSONL file for monitoring.

    Enhanced logging includes:
    - files_read_detail: Categorized file reading information
    - recommendation_context: What the AI was responding to
    - pattern_confidence: Detection confidence score (0.0-1.0)
    - full_message: Complete user message for analysis
    """
    try:
        import datetime
        import json

        # Ensure log directory exists
        ARCH_REC_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Categorize files read for detailed analysis
        files_read_detail = {
            "architecture_files": [
                fp for fp in files_read if any(arch_file in fp for arch_file in ARCHITECTURE_FILES)
            ],
            "skill_files": [fp for fp in files_read if "/skills/" in fp or "SKILL.md" in fp],
            "other_files": [
                fp
                for fp in files_read
                if not any(arch_file in fp for arch_file in ARCHITECTURE_FILES)
                and "/skills/" not in fp
                and "SKILL.md" not in fp
            ],
            "total_count": len(files_read),
        }

        # Extract keywords for pattern confidence analysis
        destination_keywords = [
            kw for kw in ARCH_DESTINATION_KEYWORDS if kw.lower() in destination.lower()
        ]
        pattern_confidence = (
            min(1.0, len(destination_keywords) * 0.3)
            if pattern_confidence == 0.0
            else pattern_confidence
        )

        # Create enhanced log entry
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "warning",
            "event": "architectural_recommendation_without_investigation",
            "user_message_excerpt": user_message[:100],
            "full_message": full_message[:200],  # More context for analysis
            "destination": destination,
            "files_read": files_read[:3] if files_read else [],
            "files_read_detail": files_read_detail,
            "recommendation_context": recommendation_context[:200]
            if recommendation_context
            else "",
            "pattern_confidence": pattern_confidence,
            "destination_keywords_matched": destination_keywords,
            "mode": ARCH_RECOMMENDATION_MODE,
        }

        # Append to log file
        with open(ARCH_REC_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except (OSError, TypeError):
        # Fail silently - logging shouldn't break the hook
        pass


def check_architecture_file_investigation(
    user_message: str, files_read: list[str]
) -> tuple[bool, str]:
    """
    Check if architectural recommendation is preceded by reading relevant architecture files.

    This prevents lazy pattern-matching recommendations (e.g., "move X to cognitive-stack"
    because of keyword "cognitive" without reading /s/SKILL.md to verify actual fit).

    Args:
        user_message: The user's message that may contain architectural recommendations
        files_read: List of files read in the current session

    Returns:
        (allowed: bool, message: str) - If False, contains block message with guidance
    """
    if not ARCH_RECOMMENDATION_ENABLED:
        return True, ""

    # Check if user message contains bypass flag
    if ARCH_RECOMMENDATION_BYPASS in user_message.lower():
        return True, "Bypass flag present"

    # Check if message matches architectural recommendation pattern
    if not _ARCH_RECOMMENDATION_PATTERN.search(user_message):
        return True, ""  # No architectural recommendation detected

    # Check if any architecture file was read
    architecture_files_read = [
        fp for fp in files_read if any(arch_file in fp for arch_file in ARCHITECTURE_FILES)
    ]

    if architecture_files_read:
        return True, f"Architecture files read: {architecture_files_read}"

    # Extract destination from recommendation for clearer error message
    destination_match = _ARCH_RECOMMENDATION_PATTERN.search(user_message)
    destination = destination_match.group(0) if destination_match else "destination"

    # Build the warning/block message
    message = (
        f"⛔ ARCHITECTURAL RECOMMENDATION WITHOUT INVESTIGATION\n\n"
        f'You suggested: "{destination}"\n\n'
        f"Before recommending destinations, you must:\n\n"
        f"1. **Read target skill/file SKILL.md** to understand actual purpose\n"
        f"   Example: Read P:/.claude/skills/s/SKILL.md before suggesting /s\n\n"
        f"2. **Verify architectural fit** (don't pattern-match on keywords)\n"
        f"   Example: Does /s generate multi-persona outputs? (Check SKILL.md)\n\n"
        f"3. **Then recommend based on evidence**, not assumptions\n\n"
        f"Files read so far: {files_read[:3] if files_read else 'None'}\n\n"
        f"To bypass: Add {ARCH_RECOMMENDATION_BYPASS} to your message\n"
        f"Source: plan-20260312-anti-laziness-arch-verification.md\n"
    )

    # Handle warn mode vs block mode
    if ARCH_RECOMMENDATION_MODE == "warn":
        # Log warning to file for monitoring with enhanced context
        # Note: recommendation_context is empty for PreToolUse (no AI response yet)
        _log_arch_rec_warning(
            user_message=user_message,
            destination=destination,
            files_read=files_read,
            recommendation_context="",  # No AI response in PreToolUse hook
            pattern_confidence=0.0,  # Let function calculate from keywords
            full_message=user_message,
        )

        # Still log to /hook-audit for observability
        _log_hook_block(
            hook_name="investigation_gate_arch_recommendation",
            reason=message[:200],
            user_message=user_message,
            files_read=files_read,
        )

        # Allow operation to proceed (warn mode)
        return True, f"[WARN MODE] {message}"

    # Block mode: deny the operation
    return False, message


# === PROBLEM STATEMENT VERIFICATION ===


PROBLEM_STMT_VERIFICATION_ENABLED = os.environ.get(
    "PROBLEM_STMT_VERIFICATION_ENABLED", "true"
).lower() in (
    "1",
    "true",
    "yes",
    "on",
)


def check_problem_statement_verification(user_message: str, files_read: list[str]) -> CheckResult:
    """
    Check if a problem statement (e.g., "hook is broken") is verified before diagnosis.

    This prevents diagnosing why something is broken without first verifying it IS broken
    in the form assumed. Problem statements are hypotheses, not facts.

    Args:
        user_message: The user's message that may contain problem statements
        files_read: List of files read in the current session

    Returns:
        (allowed: bool, message: str) - If False, contains block message with guidance
    """
    if not PROBLEM_STMT_VERIFICATION_ENABLED:
        return True, ""

    # Check if message matches problem statement pattern
    if not _PROBLEM_STATEMENT_PATTERN.search(user_message):
        return True, ""  # No problem statement detected

    # Extract the target filename for precise verification
    target_match = _TARGET_EXTRACTION_PATTERN.search(user_message)
    extracted_target = target_match.group("target") if target_match else None
    problem_text = extracted_target if extracted_target else "the target"

    # Problem statement detected - require verification
    # User must have read either:
    # 1. The specific target file itself (if identified)
    # 2. settings.json to check registration status
    # 3. Git status to check for uncommitted changes

    # Check for settings.json or git status (always valid verification)
    has_registration_check = any(
        "settings.json" in fp.lower() or "git" in fp.lower() for fp in files_read
    )

    # If we extracted a target, check if that specific file was read
    if extracted_target:
        has_target_read = any(extracted_target.lower() in fp.lower() for fp in files_read)
        has_verification = has_registration_check or has_target_read
    else:
        # No target extracted - any .py file read serves as verification
        has_verification = has_registration_check or any(fp.endswith(".py") for fp in files_read)

    if has_verification:
        return True, "Problem statement verified via file read"

    # Block - problem stated without verification
    message = (
        f"⛔ PROBLEM STATEMENT UNVERIFIED\n\n"
        f'You stated: "{problem_text}" is broken\n\n'
        f"Before diagnosing the cause, you must VERIFY the problem exists:\n\n"
        f"1. **Read settings.json** to confirm hook registration status\n"
        f"   Example: Read P:/.claude/settings.json\n\n"
    )

    if extracted_target:
        message += (
            f"2. **Read the specific file** to verify actual behavior\n"
            f"   Example: Read P:/.claude/hooks/{extracted_target}\n\n"
        )
    else:
        message += (
            "2. **Read the hook/script file** to verify actual code behavior\n"
            "   Example: Read P:/.claude/hooks/SessionStart_tldr.py\n\n"
        )

    message += (
        f"3. **Check git status** for uncommitted changes\n"
        f"   Example: Bash git status\n\n"
        f"Problem statements are HYPOTHESES, not facts.\n"
        f"Verify before diagnosing.\n\n"
        f"Files read so far: {files_read[:3] if files_read else 'None'}\n"
    )

    return False, message


# === LIBRARY-AWARE DEVELOPMENT ===

LIBRARY_AWARE_ENABLED = os.environ.get("CSF_LIBRARY_AWARE_GATE", "true").lower() in ("1", "true")


def check_library_awareness(
    code_content: str, target_path: str, searches_performed: list[str]
) -> CheckResult:
    """
    Check if utility code is being written without awareness of existing solutions.

    Implements "Know Before You Go" pattern:
    - Detects new function definitions
    - Requires prior search OR justification comment
    - Allows any decision (reuse, enhance, replace) as long as it's informed

    Returns: (allowed: bool, message: str)
    """
    if not LIBRARY_AWARE_ENABLED or not code_content:
        return True, ""

    # Check for new function definitions
    new_functions = re.findall(r"def\s+([a-z][a-z0-9_]*)\s*\(", code_content)

    if not new_functions:
        return True, ""  # No functions being defined

    # Get target directory for search scope
    target_dir = Path(target_path).parent

    # Check if any search was performed in the target directory
    dir_searched = any(
        str(target_dir) in search
        or target_dir.name in search
        or any(func.lower() in search.lower() for func in new_functions)
        for search in searches_performed
    )

    if dir_searched:
        return True, ""  # Search was performed

    # Check for justification comment (indicates informed decision to create new)
    justification_patterns = [
        r"#\s*(?:NOTE|REASON|WHY|JUSTIFICATION|REPLACING|NEW):",
        r"#\s*Not using .+ because",
        r"#\s*Creating new .+ because",
        r"#\s*Existing .+ (?:is|does not|doesn)",
    ]

    for pattern in justification_patterns:
        if re.search(pattern, code_content, re.IGNORECASE):
            return True, ""  # Explicit justification provided

    # Block with guidance - only for non-trivial functions
    if len(new_functions[0]) < 4:  # Skip very short names like 'run', 'log'
        return True, ""

    func_names = ", ".join(new_functions[:3])
    if len(new_functions) > 3:
        func_names += f", ... (+{len(new_functions) - 3} more)"

    return False, (
        f"⚠️ LIBRARY-AWARE DEVELOPMENT REQUIRED\n\n"
        f"You are defining new function(s): `{func_names}`\n"
        f"Target directory: {target_dir}\n\n"
        f"Before creating utility code, you must:\n\n"
        f"1. **SEARCH** for existing implementations:\n"
        f'   grep -r "{new_functions[0]}" {target_dir}/\n\n'
        f"2. **DECIDE**: Reuse, Enhance, or Replace\n\n"
        f"3. If replacing, add justification comment:\n"
        f"   # NOTE: Not using existing_func() because [reason]\n\n"
        f"This ensures you don't reinvent existing solutions.\n"
        f"(Set CSF_LIBRARY_AWARE_GATE=false to disable this check)"
    )


# === /hook-audit INTEGRATION ===


def _log_hook_block(hook_name: str, reason: str, user_message: str, files_read: list[str]) -> None:
    """Log hook block to /hook-audit for observability.

    Args:
        hook_name: Name of the hook that blocked
        reason: Block message/reason
        user_message: The user message that triggered the block
        files_read: Files read in the session (for context)
    """
    try:
        import datetime

        from shared_utils import log_hook_event

        # Extract destination from user message for data report
        destination_match = _ARCH_RECOMMENDATION_PATTERN.search(user_message)
        destination = destination_match.group(0) if destination_match else "unknown"

        # Create data report for observability
        data_report = {
            "pattern_matched": destination,
            "target_destination": destination,
            "investigation_status": "insufficient" if not files_read else "sufficient",
            "architecture_files_read": [
                fp for fp in files_read if any(arch_file in fp for arch_file in ARCHITECTURE_FILES)
            ],
            "total_files_read": len(files_read),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Log the block event
        log_hook_event(
            hook_name=hook_name,
            event_type="block",
            data={
                "reason": reason[:200],  # Truncate for readability
                "user_message_excerpt": user_message[:100],
                "data_report": data_report,
            },
        )
    except (ImportError, AttributeError, OSError, RuntimeError):
        # /hook-audit integration is optional - fail silently
        pass


# === HOOK LOGIC ===


def record_read(
    tool_name: str, tool_input: ToolDict, state: InvestigationState
) -> InvestigationState:
    """Record a file read for investigation tracking."""
    filepath = None

    # Extract filepath from various tool input formats
    if "path" in tool_input:
        filepath = tool_input["path"]
    elif "file_path" in tool_input:
        filepath = tool_input["file_path"]
    elif "command" in tool_input:
        # Parse common read commands
        cmd = tool_input["command"]
        # cat, head, tail, less, grep with file
        match = re.search(r'(?:cat|head|tail|less|grep.*?)\s+["\']?([^\s"\'|>]+)', cmd)
        if match:
            filepath = match.group(1)

    if filepath and filepath not in state["files_read"]:
        state["files_read"].append(filepath)
        module = extract_module(filepath)
        if module:
            if isinstance(state["modules_investigated"], list):
                state["modules_investigated"] = set(state["modules_investigated"])
            state["modules_investigated"].add(module)

    # Track search queries for library-aware development
    if "searches_performed" not in state:
        state["searches_performed"] = []

    # Extract search query from Grep tool
    search_query = (
        tool_input.get("query")
        or tool_input.get("pattern")
        or tool_input.get("Query")
        or tool_input.get("SearchPath", "")
    )
    if search_query and search_query not in state["searches_performed"]:
        state["searches_performed"].append(search_query)

    return state


def check_write_permission(
    tool_name: str, tool_input: ToolDict, state: InvestigationState
) -> CheckResult:
    """
    Check if a write operation should be allowed.

    Returns: (allowed: bool, reason: str)
    """
    # Extract target path
    filepath = tool_input.get("path") or tool_input.get("file_path")
    if not filepath:
        return True, "No filepath detected"

    # Greenfield exemption
    if state.get("greenfield_declared"):
        return True, "Greenfield project declared"

    # Explicit investigation completion
    if state.get("investigation_declared"):
        return True, "Investigation Gate completed"

    # Exempt directories: staging, temp, test fixtures don't need investigation
    try:
        file_path_obj = Path(filepath)
        if any(exempt_dir in file_path_obj.parts for exempt_dir in INVESTIGATION_EXEMPT_DIRS):
            return (
                True,
                f"Exempt directory ({', '.join(p for p in file_path_obj.parts if p in INVESTIGATION_EXEMPT_DIRS)})",
            )
    except (TypeError, ValueError):
        pass

    # Check read coverage (risk-based: structural code edits require broader context)
    required_reads, risk_tier = _required_related_reads(tool_name, tool_input, filepath)
    related_reads = count_related_reads(filepath, state["files_read"])

    if related_reads >= required_reads:
        return True, (
            f"Sufficient investigation ({related_reads} related files read, "
            f"required={required_reads}, risk={risk_tier})"
        )

    # Self-read exemption applies only to low-risk edits.
    # For high-risk structural edits, maintain broader context requirement.
    try:
        normalized_filepath = str(Path(filepath).resolve())
        if any(str(Path(rp).resolve()) == normalized_filepath for rp in state["files_read"]):
            if required_reads <= MIN_RELATED_READS:
                return True, f"Target file was read directly ({filepath})"
    except (OSError, ValueError):
        pass

    # NEW FILE exemption - if creating in empty directory or new project
    if not Path(filepath).exists():
        parent = Path(filepath).parent
        if not parent.exists() or not any(parent.iterdir()):
            return True, "New file in empty/new directory"

    # Library-aware check for utility code
    code_content = (
        tool_input.get("content") or tool_input.get("code") or tool_input.get("new_string") or ""
    )
    if code_content and filepath.endswith(".py"):
        searches = state.get("searches_performed", [])
        lib_allowed, lib_msg = check_library_awareness(code_content, filepath, searches)
        if not lib_allowed:
            return False, lib_msg

    # BLOCK
    return False, (
        f"⛔ INVESTIGATION GATE: File not yet read\n\n"
        f"Target: {filepath}\n"
        f"Risk tier: {risk_tier}\n"
        f"Coverage: {related_reads}/{required_reads} related files read\n\n"
        f"Required before editing:\n"
        f"1. Read: {sanitize_path(filepath)}\n"
        f"2. Understand the data flow\n\n"
        f"Recent files read: {[sanitize_path(p) for p in state['files_read'][:5]]}\n\n"
        f"This is a workflow checkpoint, not an error.\n"
        f"Bypass: Declare 'Investigation complete: [summary]'\n"
        f"         or 'Greenfield: [reason]'"
    )


def process_hook(
    tool_name: str,
    tool_input: ToolDict,
    user_message: str = "",
    terminal_id: str = "",
    input_data: dict | None = None,
) -> CheckResult:
    """
    Main hook entry point.

    Returns: (allowed: bool, block_message: str | None)
    """
    if not ENABLED:
        return True, None

    state = load_state(terminal_id, input_data)

    # Track message from architectural check (for warn mode)
    message_to_return: str | None = None

    # Check architectural recommendations BEFORE write operations
    # This prevents lazy pattern-matching recommendations (e.g., "move X to cognitive-stack"
    # without reading /s/SKILL.md to verify actual architectural fit)
    if user_message:
        arch_allowed, arch_msg = check_architecture_file_investigation(
            user_message, state["files_read"]
        )
        if not arch_allowed:
            # Log to /hook-audit for observability
            _log_hook_block(
                hook_name="investigation_gate_arch_recommendation",
                reason=arch_msg,
                user_message=user_message,
                files_read=state["files_read"],
            )
            save_state(state, terminal_id)
            return False, arch_msg
        # Preserve warning message from warn mode
        if arch_msg:
            message_to_return = arch_msg

    # Check problem statement verification
    # This prevents diagnosing why something is broken without first verifying it IS broken
    if user_message:
        prob_allowed, prob_msg = check_problem_statement_verification(
            user_message, state["files_read"]
        )
        if not prob_allowed:
            _log_hook_block(
                hook_name="investigation_gate_problem_statement",
                reason=prob_msg,
                user_message=user_message,
                files_read=state["files_read"],
            )
            save_state(state, terminal_id)
            return False, prob_msg
        # Preserve warning message from warn mode
        if prob_msg and not prob_msg.startswith("[WARN MODE]"):
            message_to_return = prob_msg

    # Track reads
    if tool_name in READ_TOOLS or tool_name == "Bash":
        state = record_read(tool_name, tool_input, state)
        save_state(state, terminal_id)
        return True, message_to_return

    # Check writes
    if tool_name in WRITE_TOOLS:
        allowed, reason = check_write_permission(tool_name, tool_input, state)
        if not allowed:
            save_state(state, terminal_id)
            return False, reason
        save_state(state, terminal_id)

    return True, message_to_return


# === CONTEXT INJECTION ===


def mark_investigation_complete(summary: str) -> None:
    """Called when AI declares investigation complete."""
    state = load_state()
    state["investigation_declared"] = True
    state["investigation_summary"] = summary
    save_state(state)


def mark_greenfield(reason: str) -> None:
    """Called when AI declares greenfield project."""
    state = load_state()
    state["greenfield_declared"] = True
    state["greenfield_reason"] = reason
    save_state(state)


def reset_session() -> None:
    """Reset investigation state for new session."""
    save_state(fresh_state())


def get_last_user_message_from_input(input_data: ToolDict) -> str:
    """Extract last user message from hook input data.

    Args:
        input_data: The hook input data containing conversation history.

    Returns:
        The last user message text, or empty string if not found.
    """
    # Try conversation/history
    conversation = input_data.get("conversation", []) or input_data.get("messages", [])
    if conversation:
        for msg in reversed(conversation):
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
    return ""


# === MAIN ===

if __name__ == "__main__":
    """
    Main hook entry point.

    Protocol (PreToolUse):
    - Input: JSON via stdin with tool_name, tool_input
    - Output: Exit code 0 = allow, 2 = block
    - Block message goes to stderr
    """
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Extract user message for architectural recommendation check
        user_message = get_last_user_message_from_input(input_data)

        # Extract terminal_id — same pattern as PreToolUse.py:1040-1044
        terminal_id = str(
            input_data.get("terminal_id")
            or input_data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        ).strip()

        allowed, message = process_hook(tool_name, tool_input, user_message, terminal_id, input_data)

        if not allowed:
            # Query CKS for related patterns if triggers match (with caching)
            if any(trigger in user_message.lower() for trigger in HOOK_TRIGGERS):
                try:
                    # Add CSF staging to path for discovery service
                    _csf_staging = Path("P:/__csf/.staging")
                    if str(_csf_staging) not in sys.path:
                        sys.path.insert(0, str(_csf_staging))

                    from cks_daemon_discovery import query_cks_daemon

                    # Check cache first (lazy load cache only when needed for write blocks)
                    cached_advisory = None
                    cache = get_cks_cache()
                    if cache:
                        cached_advisory = cache.get(user_message)

                    if cached_advisory:
                        message += cached_advisory
                    else:
                        # Cache miss: query CKS via dynamic daemon (fast!)
                        response = query_cks_daemon(user_message, limit=1)
                        if response:
                            results = response.get("results", [])
                            if results and len(results) > 0:
                                r = results[0]
                                title = r.get("title", "Pattern")
                                content = r.get("content", "")[:150]
                                advisory = (
                                    f"\n\n💡 **Related pattern**:\n   {title}\n   {content}..."
                                )

                                # Cache for future queries
                                if cache:
                                    cache.set(user_message, advisory)

                                message += advisory

                    # Debug logging (use stdout to avoid stderr violation)
                    if cache and os.environ.get("CKS_CACHE_DEBUG"):
                        print(f"[CKS] {cache.stats()}")
                except (ImportError, AttributeError, OSError, RuntimeError):
                    pass  # CKS unavailable - advisory is optional

            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": message,
                        "blocking_hook": "PreToolUse_investigation_gate.py",
                    }
                )
            )
            sys.exit(2)  # Block

        # Output explicit approval JSON (Claude Code requires this)
        output = {"decision": "approve", "reason": "Investigation gate passed"}
        print(json.dumps(output))
        sys.exit(0)  # Allow

    except json.JSONDecodeError as e:
        # Fail FAST (fail closed) on protocol/input errors.
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": f"investigation_gate_json_parse_error: {e}",
                    "blocking_hook": "PreToolUse_investigation_gate.py",
                }
            )
        )
        sys.exit(2)
    except Exception as e:
        # Fail FAST (fail closed) to surface enforcement/runtime faults immediately.
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": f"investigation_gate_runtime_error: {e}",
                    "blocking_hook": "PreToolUse_investigation_gate.py",
                }
            )
        )
        sys.exit(2)
