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



# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Import shared resolution functions from __lib
from __lib.import_resolver import (  # noqa: E402
    candidate_module_paths,
    collect_attribute_bases,
    extract_import_specs,
    resolve_local_imports,
)

# Type aliases for clarity
type ToolDict = dict[str, Any]
type InvestigationState = dict[str, Any]
type CheckResult = tuple[bool, str]


def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


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
    """Detect if we're in a post-compaction or new-session scenario with lost state.

    Returns True when:
    - State has no files_read (fresh or cleared)
    - transcript_path exists and contains tool calls
    """
    if input_data is None:
        return False
    if state.get("files_read"):
        return False

    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        return False

    try:
        path = Path(transcript_path)
        if not path.exists():
            return False
        content = path.read_text(encoding="utf-8")
        return '"tool_use"' in content
    except OSError:
        return False


def _reconstruct_files_read_from_input(input_data: dict) -> list[str]:
    """Reconstruct files_read from transcript_path JSONL.

    Reads the transcript JSONL to extract file paths from Read/Glob/Grep/Bash
    tool calls, recovering investigation coverage after compaction or in new sessions.

    Args:
        input_data: Hook input dict with transcript_path

    Returns:
        List of file paths that were read

    Note:
        WebFetch and WebSearch are intentionally excluded because they produce
        URLs, not file paths.
    """
    if input_data is None:
        return []

    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        return []

    READ_TOOLS = {
        "Read", "Glob", "Grep", "Bash",
        "read_file", "View", "cat", "grep", "find", "search_files",
    }
    files: list[str] = []

    try:
        path = Path(transcript_path)
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        message = entry.get("message", entry)
        message_content = message.get("content", entry.get("content", []))
        if not isinstance(message_content, list):
            continue

        for block in message_content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_name = block.get("name", "")
            if tool_name not in READ_TOOLS:
                continue
            tool_input = block.get("input", {})
            if not isinstance(tool_input, dict):
                continue
            file_path = (
                tool_input.get("file_path")
                or tool_input.get("path")
                or ""
            )
            if file_path and file_path not in files:
                files.append(file_path)

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

AUTO_READ_MAX_BYTES = 1_000_000
AUTO_READ_MAX_CHARS = 5_000
LOW_RISK = "LOW"
MEDIUM_RISK = "MEDIUM"
HIGH_RISK = "HIGH"
SENSITIVE_CODE_DIRS = {"core", "backends", "chs"}


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
        ".staging,tmp,temp,.tmp,test_fixtures,__pycache__,memory",
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
                return _normalize_state(state, terminal_id)
        except (json.JSONDecodeError, KeyError):
            state = fresh_state(terminal_id)
            if input_data and _is_compaction_scenario(state, input_data):
                recovered_files = _reconstruct_files_read_from_input(input_data)
                if recovered_files:
                    state["files_read"] = recovered_files
                    state["_reconstructed_from_transcript"] = True
            return _normalize_state(state, terminal_id)
    state = fresh_state(terminal_id)
    if input_data and _is_compaction_scenario(state, input_data):
        recovered_files = _reconstruct_files_read_from_input(input_data)
        if recovered_files:
            state["files_read"] = recovered_files
            state["_reconstructed_from_transcript"] = True
    return _normalize_state(state, terminal_id)


def fresh_state(terminal_id: str = "") -> InvestigationState:
    return {
        "timestamp": datetime.now().timestamp(),
        "terminal_id": _safe_id_str(terminal_id) if terminal_id else "default",
        "files_read": [],
        "modules_investigated": set(),
        "investigation_declared": False,
        "greenfield_declared": False,
        "searches_performed": [],
        "targets_auto_read_once": [],
        "dependency_checks": {},
        "workspace_state": {},
        "risk_context": {},
    }


def _normalize_state(state: InvestigationState, terminal_id: str = "") -> InvestigationState:
    """Fill in new state fields without breaking older persisted state files."""
    if "files_read" not in state or not isinstance(state.get("files_read"), list):
        state["files_read"] = list(state.get("files_read", []) or [])
    if "timestamp" not in state:
        state["timestamp"] = 0
    if "modules_investigated" in state and isinstance(state["modules_investigated"], list):
        state["modules_investigated"] = set(state["modules_investigated"])
    if "modules_investigated" not in state:
        state["modules_investigated"] = set()
    if "searches_performed" not in state or not isinstance(state.get("searches_performed"), list):
        state["searches_performed"] = list(state.get("searches_performed", []) or [])
    if "targets_auto_read_once" not in state or not isinstance(state.get("targets_auto_read_once"), list):
        state["targets_auto_read_once"] = list(state.get("targets_auto_read_once", []) or [])
    if "dependency_checks" not in state or not isinstance(state.get("dependency_checks"), dict):
        state["dependency_checks"] = dict(state.get("dependency_checks", {}) or {})
    if "workspace_state" not in state or not isinstance(state.get("workspace_state"), dict):
        state["workspace_state"] = dict(state.get("workspace_state", {}) or {})
    if "risk_context" not in state or not isinstance(state.get("risk_context"), dict):
        state["risk_context"] = dict(state.get("risk_context", {}) or {})
    if "investigation_declared" not in state:
        state["investigation_declared"] = False
    if "greenfield_declared" not in state:
        state["greenfield_declared"] = False
    state["terminal_id"] = _safe_id_str(terminal_id) if terminal_id else state.get("terminal_id", "default")
    return state


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


def _resolve_repo_root(path_hint: str | None = None) -> Path:
    """Find the nearest repo root for git-aware workspace checks."""
    candidates: list[Path] = []
    if path_hint:
        path_obj = Path(path_hint).resolve()
        start = path_obj if path_obj.is_dir() else path_obj.parent
        candidates.append(start)
        candidates.extend(list(start.parents))

    cwd = Path.cwd().resolve()
    if cwd not in candidates:
        candidates.append(cwd)
    candidates.extend(parent for parent in cwd.parents if parent not in candidates)

    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _run_git_status(repo_root: Path) -> list[str]:
    """Return porcelain status lines for the repo if git is available."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _parse_git_status(repo_root: Path, target_path: Path) -> dict[str, Any]:
    """Build a structured git workspace snapshot for the target path."""
    status_lines = _run_git_status(repo_root)
    changed_paths: list[str] = []
    status_map: dict[str, str] = {}
    has_deleted_files = False
    has_staged_deletions = False
    has_conflicts = False
    has_renames = False

    target_rel = None
    try:
        target_rel = target_path.resolve(strict=False).relative_to(repo_root.resolve())
    except Exception:
        target_rel = None

    target_parent_rel = str(target_rel.parent).replace("\\", "/") if target_rel else ""

    for line in status_lines:
        if len(line) < 3:
            continue
        status = line[:2]
        path_part = line[3:] if len(line) > 3 else ""
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[-1]
        normalized_path = path_part.replace("\\", "/").strip()
        if normalized_path:
            changed_paths.append(normalized_path)
            status_map[normalized_path] = status

        if "U" in status or status in {"AA", "DD", "AU", "UA", "DU", "UD", "UU"}:
            has_conflicts = True
        if "R" in status:
            has_renames = True
        if status[0] == "D":
            has_staged_deletions = True
            has_deleted_files = True
        if status[1] == "D":
            has_deleted_files = True

    dirty_same_dir = bool(
        target_parent_rel
        and any(Path(path).parent.as_posix() == target_parent_rel for path in changed_paths)
    )

    return {
        "available": bool(status_lines),
        "changed_paths": changed_paths,
        "status_map": status_map,
        "has_deleted_files": has_deleted_files,
        "has_staged_deletions": has_staged_deletions,
        "has_conflicts": has_conflicts,
        "has_renames": has_renames,
        "dirty_same_dir": dirty_same_dir,
    }


def _read_text_file(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# Backward-compatible wrappers delegating to __lib/import_resolver.py
_extract_local_import_specs = extract_import_specs
_collect_attribute_bases = collect_attribute_bases
_candidate_module_paths = candidate_module_paths
_resolve_local_imports = resolve_local_imports


def _paths_match(a: str | Path, b: str | Path) -> bool:
    try:
        return Path(a).resolve(strict=False) == Path(b).resolve(strict=False)
    except Exception:
        return str(Path(a)).replace("\\", "/") == str(Path(b)).replace("\\", "/")


def _target_directly_read(target_path: Path, files_read: list[str]) -> bool:
    return any(_paths_match(read_path, target_path) for read_path in files_read)


def _classify_risk_tier(
    tool_name: str,
    filepath: str,
    tool_input: ToolDict,
    dependency_context: dict[str, Any],
    workspace_state: dict[str, Any],
) -> str:
    """Assign a deterministic risk tier from structured signals."""
    score = 0
    path_obj = Path(filepath)

    if tool_name == "MultiEdit":
        score += 2
    if path_obj.suffix.lower() == ".py":
        score += 1
    if path_obj.suffix.lower() == ".py" and dependency_context.get("local_import_specs"):
        score += 1
    if any(part in SENSITIVE_CODE_DIRS for part in path_obj.parts):
        score += 1
    if _is_structural_code_change(tool_name, tool_input, filepath):
        score += 1
    if workspace_state.get("dirty_same_dir"):
        score += 1
    if workspace_state.get("has_deleted_files") or workspace_state.get("has_staged_deletions"):
        score += 2
    if workspace_state.get("has_conflicts"):
        score += 3
    if dependency_context.get("unresolved_local_imports"):
        score += 3
    if dependency_context.get("deleted_or_staged_import_targets"):
        score += 3

    if score >= 5:
        return HIGH_RISK
    if score >= 2:
        return MEDIUM_RISK
    return LOW_RISK


def _required_reads_for_risk(risk_tier: str) -> int:
    if risk_tier == HIGH_RISK:
        return max(HIGH_RISK_MIN_RELATED_READS, 2)
    if risk_tier == MEDIUM_RISK:
        return max(MIN_RELATED_READS, 2)
    return MIN_RELATED_READS


def _build_risk_context(
    tool_name: str,
    tool_input: ToolDict,
    state: InvestigationState,
    terminal_id: str = "",
) -> dict[str, Any]:
    """Build the structured risk context consumed by the write gate."""
    filepath = str(tool_input.get("path") or tool_input.get("file_path") or "")
    target_path = Path(filepath) if filepath else Path.cwd()
    repo_root = _resolve_repo_root(filepath or terminal_id)
    source_text = _read_text_file(target_path) if target_path.exists() else ""
    git_snapshot = _parse_git_status(repo_root, target_path)
    dependency_context = _resolve_local_imports(target_path, repo_root, git_snapshot["status_map"], source_text)
    workspace_state = {
        "available": git_snapshot["available"],
        "has_deleted_files": git_snapshot["has_deleted_files"],
        "has_staged_deletions": git_snapshot["has_staged_deletions"],
        "has_conflicts": git_snapshot["has_conflicts"],
        "has_renames": git_snapshot["has_renames"],
        "dirty_same_dir": git_snapshot["dirty_same_dir"],
        "changed_paths": git_snapshot["changed_paths"],
    }
    target_direct_read = _target_directly_read(target_path, state.get("files_read", []))
    related_reads_count = count_related_reads(filepath, state.get("files_read", [])) if filepath else 0
    risk_tier = _classify_risk_tier(tool_name, filepath, tool_input, dependency_context, workspace_state)
    required_reads = _required_reads_for_risk(risk_tier)

    return {
        "tool_name": tool_name,
        "target_path": filepath,
        "repo_root": str(repo_root),
        "target_ext": target_path.suffix.lower() if filepath else "",
        "target_dir": str(target_path.parent) if filepath else "",
        "risk_tier": risk_tier,
        "investigation": {
            "files_read_count": len(state.get("files_read", [])),
            "target_read": target_direct_read,
            "related_reads_count": related_reads_count,
            "required_reads": required_reads,
            "discovery_declared": bool(state.get("investigation_declared")),
        },
        "workspace": workspace_state,
        "dependencies": dependency_context,
        "signals": {
            "python_target": filepath.endswith(".py"),
            "multi_file_edit": tool_name == "MultiEdit",
        },
        "decision": {
            "allow_auto_read": risk_tier == LOW_RISK,
            "requires_explicit_discovery": risk_tier != LOW_RISK,
        },
    }


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

    # Exclude functions that already exist in the target file (rewrites, not new code)
    target = Path(target_path)
    if target.exists():
        try:
            existing_content = target.read_text(encoding="utf-8")
            existing_functions = set(re.findall(r"def\s+([a-z][a-z0-9_]*)\s*\(", existing_content))
            new_functions = [f for f in new_functions if f not in existing_functions]
            if not new_functions:
                return True, ""  # All functions already exist in target — this is a rewrite
        except OSError:
            pass  # Can't read existing file, proceed with all functions

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

    # Skip CLI flags parsed from Bash commands (e.g. -80, -l, -rn)
    if filepath and filepath.startswith("-"):
        filepath = None
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
    tool_name: str,
    tool_input: ToolDict,
    state: InvestigationState,
    risk_context: dict[str, Any] | None = None,
) -> CheckResult:
    """
    Check if a write operation should be allowed.

    Returns: (allowed: bool, reason: str)
    """
    # Extract target path
    filepath = tool_input.get("path") or tool_input.get("file_path")
    if not filepath:
        return True, "No filepath detected"

    risk_context = risk_context or {}
    investigation = risk_context.get("investigation", {})
    dependency_context = risk_context.get("dependencies", {})
    workspace_state = risk_context.get("workspace", {})
    risk_tier = str(risk_context.get("risk_tier") or LOW_RISK)
    required_reads = int(investigation.get("required_reads") or MIN_RELATED_READS)
    related_reads = int(investigation.get("related_reads_count") or 0)
    target_read = bool(investigation.get("target_read"))
    normalized_target = str(Path(filepath).resolve(strict=False))
    auto_read_targets = state.get("targets_auto_read_once", [])
    if not isinstance(auto_read_targets, list):
        auto_read_targets = []
        state["targets_auto_read_once"] = auto_read_targets

    unresolved_local_imports = dependency_context.get("unresolved_local_imports", []) or []
    deleted_or_staged_import_targets = dependency_context.get("deleted_or_staged_import_targets", []) or []

    if unresolved_local_imports:
        return (
            False,
            "MISSING_DEPENDENCY_DISCOVERY: unresolved local import(s) "
            + ", ".join(str(item) for item in unresolved_local_imports),
        )

    if deleted_or_staged_import_targets:
        return (
            False,
            "IMPORT_TARGET_DELETED_OR_STAGED: "
            + ", ".join(str(item) for item in deleted_or_staged_import_targets),
        )

    if workspace_state.get("has_conflicts"):
        return False, "SUSPICIOUS_WORKSPACE_STATE: merge conflict markers present"

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

    # NEW FILE exemption - if creating a file that doesn't exist yet
    if not Path(filepath).exists():
        parent = Path(filepath).parent
        if not parent.exists() or not any(parent.iterdir()):
            return True, "New file in empty/new directory"
        # New file in existing directory: exempt if sibling files were read
        # (indicates familiarity with the directory's purpose)
        sibling_reads = sum(
            1 for r in state["files_read"]
            if Path(r).resolve().parent == parent.resolve()
        )
        if sibling_reads >= 1:
            return True, f"New file in known directory ({sibling_reads} sibling(s) read)"

    # Library-aware check for utility code
    code_content = (
        tool_input.get("content") or tool_input.get("code") or tool_input.get("new_string") or ""
    )
    if code_content and filepath.endswith(".py"):
        searches = state.get("searches_performed", [])
        lib_allowed, lib_msg = check_library_awareness(code_content, filepath, searches)
        if not lib_allowed:
            return False, lib_msg

    # LOW-risk convenience path: allow one guided auto-read per target.
    if risk_tier == LOW_RISK:
        if target_read:
            return True, f"Target file was read directly ({filepath})"

        if normalized_target not in auto_read_targets:
            try:
                file_size = Path(filepath).stat().st_size
                if file_size > AUTO_READ_MAX_BYTES:
                    raise IOError(f"File too large for auto-read ({file_size} bytes)")

                content = None
                is_binary = False
                with open(filepath, "rb") as f:
                    raw = f.read(8192)
                    if b"\x00" in raw[:1024] or any(b > 127 for b in raw[:512]):
                        is_binary = True
                    else:
                        content = raw.decode("utf-8", errors="replace")

                auto_read_targets.append(normalized_target)
                if normalized_target not in state["files_read"]:
                    state["files_read"].append(filepath)

                if is_binary:
                    preview = f"[BINARY FILE - {len(raw)} bytes, cannot preview]"
                elif content:
                    preview = content[:AUTO_READ_MAX_CHARS]
                    if len(content) > AUTO_READ_MAX_CHARS:
                        preview += f"\n\n... [{len(content) - AUTO_READ_MAX_CHARS} more characters]"
                else:
                    preview = "[empty file]"

                context_msg = (
                    f"[AUTO-READ LOW RISK] {filepath} has been read for investigation.\n\n"
                    f"File preview:\n{preview}"
                )
                return True, context_msg
            except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError, IOError):
                pass

        return (
            False,
            f"AUTO_READ_EXHAUSTED: target not yet discovered\n\n"
            f"Target: {filepath}\n"
            f"Risk tier: {risk_tier}\n"
            f"Coverage: {related_reads}/{required_reads} related files read\n\n"
            f"Required before editing:\n"
            f"1. Read: {sanitize_path(filepath)}\n"
            f"2. Understand the data flow\n\n"
            f"Recent files read: {[sanitize_path(p) for p in state['files_read'][:5]]}\n\n"
            f"Bypass: Declare 'Investigation complete: [summary]'"
        )

    # MEDIUM/HIGH: allow if target was directly read (investigation done)
    if target_read:
        return True, f"Target file was read directly ({filepath})"

    # MEDIUM/HIGH: require explicit discovery, no auto-read fallback.
    return False, (
        f"EXPLICIT_DISCOVERY_REQUIRED: discovery must be explicit at this risk level\n\n"
        f"Target: {filepath}\n"
        f"Risk tier: {risk_tier}\n"
        f"Context: {related_reads} related files read (target read required at {risk_tier} risk)\n\n"
        f"Required before editing:\n"
        f"1. Read: {sanitize_path(filepath)}\n"
        f"2. Read the dependency surface or adjacent implementation files\n"
        f"3. Re-run the write request after discovery\n\n"
        f"Recent files read: {[sanitize_path(p) for p in state['files_read'][:5]]}\n\n"
        f"This is a workflow checkpoint, not an error.\n"
        f"Bypass: Declare 'Investigation complete: [summary]'"
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

    # Check writes with auto-read fallback
    if tool_name in WRITE_TOOLS:
        risk_context = _build_risk_context(tool_name, tool_input, state, terminal_id)
        state["risk_context"] = risk_context
        state["workspace_state"] = risk_context.get("workspace", {})
        state["dependency_checks"][risk_context.get("target_path", "")] = risk_context.get(
            "dependencies", {}
        )
        allowed, reason = check_write_permission(tool_name, tool_input, state, risk_context)
        save_state(state, terminal_id)
        if not allowed:
            return False, reason

        if reason.startswith("[AUTO-READ"):
            return True, reason

        if tool_name == "Write":
            fp = tool_input.get("path") or tool_input.get("file_path")
            if fp and fp not in state["files_read"]:
                state["files_read"].append(fp)
            save_state(state, terminal_id)

        return True, message_to_return

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
    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        print("PreToolUse_investigation_gate: empty stdin, allowing", file=sys.stderr)
        sys.exit(0)
    try:
        input_data = json.loads(stdin_content)
        # json.loads(stdin_content) would throw on empty/whitespace-only stdin
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
            print(message, file=sys.stderr)
            sys.exit(2)  # Block

        # Output explicit approval JSON (Claude Code requires this)
        output = {"decision": "approve", "reason": "Investigation gate passed"}
        print(json.dumps(_normalize_stdout(output)))
        sys.exit(0)  # Allow

    except json.JSONDecodeError as e:
        # Fail FAST (fail closed) on protocol/input errors.
        err_msg = f"⛔ investigation_gate_json_parse_error: {e}"
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": err_msg,
                    "blocking_hook": "PreToolUse_investigation_gate.py",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        # Fail FAST (fail closed) to surface enforcement/runtime faults immediately.
        err_msg = f"⛔ investigation_gate_runtime_error: {e}"
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": err_msg,
                    "blocking_hook": "PreToolUse_investigation_gate.py",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(2)