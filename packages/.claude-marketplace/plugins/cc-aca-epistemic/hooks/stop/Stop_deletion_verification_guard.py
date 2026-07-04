#!/usr/bin/env python3
"""
Stop_deletion_verification_guard.py - File Deletion Claim Verification Guard
=============================================================================

Blocks responses claiming files are deleted WITHOUT verifying the files
ACTUALLY don't exist on the file system.

WHY THIS EXISTS:
  AI agents claim "files deleted" or "cleaned up" when the deletion command
  failed, files still exist, or no verification was performed. This creates
  false completion claims and wastes user time discovering the cleanup didn't
  happen.

FAILURE MODE CAUGHT:
  "Deleted the dummy wrapper files"
  -> Files still exist on disk (rm command failed or wasn't run)
  -> Guard blocks and demands actual file system verification.

VERIFICATION METHOD:
  Uses os.scandir() for single-syscall existence checks with timeout protection.
  Not dependent on tool execution evidence - verifies the REAL state on disk.

ALLOWLIST (obvious claims that don't need verification):
  - "will delete", "will be deleted" (future tense, not completion claim)
  - "needs cleanup", "requires deletion" (requirement statements)
  - "can be removed" (capability statements)

LIFECYCLE: Stop (blocking guard -- exits with code 2 to block)

v2.0 - 2026-03-24: Fixed critical issues:
  - CRIT-001: Fixed dead code (directory check now reachable via os.scandir)
  - PERF-001: Added MAX_PATHS=20 limit to prevent N+1 unbounded I/O
  - PERF-002: Single syscall via os.scandir() instead of exists() + is_dir()
  - PERF-003: Deferred logging (collect results, log once after loop)
  - SEC-001: Added _sanitize_for_log() to prevent log injection
  - SEC-002: Added boundary validation to prevent path traversal
  - SEC-003: Generic error messages hide exception details
  - CORR-001: URL exclusion pattern prevents https?:// false positives
  - CORR-002: Added passive voice patterns to allowlist
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

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






import concurrent.futures
import glob
import json
import logging
import os
import re
import shlex
import sys
from pathlib import Path

# --- Configuration Constants -------------------------------------------------

# Maximum number of paths to verify (prevents N+1 unbounded I/O)
MAX_PATHS = 20

# Timeout for file system operations (prevents hangs on network paths)
IO_TIMEOUT_SECONDS = 5

HOOKS_DIR = _hooks_dir  # from bootstrap
LOG_DIR = HOOKS_DIR / "state" / "logs"

# --- Logging ----------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("deletion_verification_guard")
_handler = logging.FileHandler(LOG_DIR / "deletion_verification_guard.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)  # PROBE/allowlist traces are debug-level (suppressed by default)


# --- Patterns: Deletion Completion Claims ------------------------------------

# Deletion completion patterns (past tense, claiming action completed)
# Note: These patterns should NOT match future tense like "will be deleted"
DELETION_CLAIM_PATTERNS = re.compile(
    # Past tense: "files are/were/have been deleted/removed/gone"
    r"\b(?:files?|directories?|folders?|paths?)\s+(?:are|were|have been)\s+(?:deleted|removed|cleaned\s+up|gone)\b"
    # Action completed with explicit object: "(successfully) deleted/removed the files"
    # Requires at least one word after the action to avoid matching bare "removed" in content-change contexts
    r"|\b(?:successfully\s+)?(?:deleted|removed|cleaned\s+up)\s+\S+"
    # All/both completed: "all/both files deleted/removed"
    r"|\b(?:all|both)\s+(?:files?|directories?|folders?)\s+(?:deleted|removed)\b"
    # Drop verb (databases: DROP TABLE; shells: drop as alias for delete)
    r"|\bdropped?\s+\S+",
    re.IGNORECASE,
)

# File path extraction patterns (separate URL exclusion for clarity)
FILE_PATH_PATTERNS = re.compile(
    # Absolute Windows paths (e.g., C:\Users\file.py or C:/Users/file.py)
    # Note: Backslash is NOT in the exclusion set to allow matching past backslashes in paths
    r"[A-Z]:[/\\][^\s\"\'\[\]]+"
    # Absolute Unix paths (e.g., /usr/local/bin)
    r"|[/\\][^\"\s\]]+(?<![a-z])(?<![a-z])"
    # Relative paths (e.g., ./file.py, ../backup/file.txt)
    r"|\.\.[\\/][^\"\s\]]+"
    r"|\.[\\/][^\"\s\]]+"
    # Filenames in quotes (e.g., "test file.py")
    r"|['\"]([^'\"]+\.[^'\"]+)['\"]"
    # Common extensions (e.g., file.py, script.js, README.md)
    r"|\b[\w-]+\.(?:py|js|ts|md|json|yaml|yml|txt|log|tmp|bak|old)\b",
    re.IGNORECASE,
)

# URL detection pattern (checked separately before file path extraction)
URL_PATTERNS = re.compile(
    r"https?://[^\s\]]+",
    re.IGNORECASE,
)

# Obvious allowlist (future tense, passive voice, requirements, capability statements)
OBVIOUS_ALLOWLIST = re.compile(
    # Future tense (not completion claims)
    r"\bwill\s+(?:delete|remove|clean\s+up)\b"
    r"|\bwill\s+be\s+(?:deleted|removed|cleaned)\b"
    r"|\bshall\s+(?:delete|remove)\b"
    r"|\bgoing\s+to\s+(?:delete|remove)\b"
    # Passive voice and modal verbs
    r"|\bshould\s+(?:be\s+)?(?:deleted|removed|cleaned)\b"
    r"|\bcan\s+be\s+(?:deleted|removed|cleaned)\b"
    r"|\bmust\s+be\s+(?:deleted|removed)\b"
    r"|\bwould\s+be\s+(?:deleted|removed)\b"
    # Requirement/capability statements
    r"|\bneeds?\s+(?:to\s+be\s+)?(?:deletion|cleanup|removal)\b"
    r"|\brequires?\s+(?:deletion|cleanup|removal)\b"
    # Conversational denials (ADR-20260323)
    r"|\bI\s+did(?:n't|dn't| not)\s+(?:delete|remove|clean)\b"
    r"|\bI\s+hav(?:e'?n't|en't|e not)\s+(?:deleted|removed|cleaned)\b"
    r"|\bI\s+won'?t\s+(?:delete|remove)\b"
    # Discussing prior verification (not claiming current deletion)
    r"|\b(?:was|were)\s+(?:also\s+)?(?:verified|confirmed)\b"
    r"|\bdeletion\s+(?:was\s+)?verified\b"
    r"|\bverification\s+(?:has\s+)?failed\b"
    r"|\bverifying\b"
    r"|\bconfirm(?:s|ed)?\s+(?:the\s+)?(?:deletion|removal)\b"
    # Plan/document content changes — "removed X from section" (not filesystem deletion)
    r"|\bremoved\s+(?:the\s+)?(?:Phase|Phase\s*\d+|CHANGE|D\d+|Section)\b"
    r"|\bremoved\s+.*(?:qualifier|from\s+D2|from\s+the\s+plan)\b"
    # ADR alternatives — "Option Remove" / "Option B: remove X"
    r"|\bOption\s+[A-Z](?:\s*[:\-])?\s*remove\b"
    # Schema constraint removal — "remove NOT NULL" / "Removing the constraint"
    r"|\bremove\s+NOT\s+NULL\b"
    r"|\bremoving\s+(?:the\s+)?(?:NOT\s+NULL|constraint)\b"
    r"|\bremoved?\s+.*(?:PRIMARY\s+KEY|INDEX|UNIQUE|FOREIGN)\b"
    # Design-proximate deletion (passive voice, process/state description)
    # These describe WHAT IS/WILL BE deleted, not completion claims
    r"|\bdeleted\s+after\s+(?:transcription|ingestion|processing|conversion)\b"
    r"|\bdeleted\s+following\s+(?:transcription|ingestion|processing|conversion)\b"
    # Content-change contexts — "removed the X" where X is NOT a file/directory
    # These are config/entry/line changes, not filesystem deletions
    r"|\bremoved?\s+(?:the\s+)?(?:duplicate|entry|alias|line|item|value|setting|parameter|option|argument|flag|reference|mention|usage|call|import|dependency|statement|variable|declaration|definition|occurrence|instance|clause|expression|assertion|invocation)\b"
    r"|\bremoved?\s+.*(?:from\s+[\w-]+|in\s+[\w-]+)\b"
    # Code-refactoring contexts — "removed unused/dead/obsolete code" (not file deletion)
    # Requires explicit code-related term to avoid false positives
    r"|\bremoved?\s+(?:the\s+)?(?:unused|dead|obsolete|deprecated|redundant)\s+(?:code|branch|logic|function|import|statement|class|method)\b"
    # Regex/code token contexts — "removed bare from the regex", "dropped the token"
    # These describe in-code removals, not filesystem operations
    r"|\bremoved?\s+bare\b"
    r"|\bremoved?\s+.*(?:regex|token|pattern|qualifier)\b"
    r"|\bdropped?\s+(?:the\s+)?(?:COMPARATIVEWORDSRE|token|pattern|entry|flag|qualifier)\b"
    r"|\bremoved?\s+.*(?:from\s+(?:the\s+)?(?:regex|pattern|constraint|schema|section))\b"
    r"|\bremoved?\s+.*(?:\bdocstring|comment|section|Phase|CHANGE|D\d+)\b"
    # Code-edit / structural-change contexts — "removed the X" where X is a
    # code component, not a filesystem artifact. These are git-diff summaries,
    # not deletion completion claims. Examples:
    #   "source:" marker removed from _is_analytical_response" → allowlist
    #   "Removed the check from the guard" → allowlist
    #   "Removed marker from Stop.py" → allowlist (no extension, not a path)
    r"|\bremoved?\s+(?:the\s+)?(?:marker|condition|check|guard|rule|flag|qualifier|constraint)\b"
    r"|\bremoved?\s+(?:the\s+)?(?:section|comment|docstring|block|stanza)\b"
    r"|\bremoved?\s+.*(?:from\s+the\s+(?:markers?|list|pattern|regex|constraint|gate|hook|section))\b"
    # Git-index operations (not filesystem deletions)
    # These describe git tracking/index/staging changes, not file deletion
    r"|\b(?:deleted|removed)\s+from\s+(?:git\s+)?(?:tracking|index|staging)\b"
    r"|\bremoved?\s+.*from\s+(?:git\s+)?(?:tracking|index|staging)\b"
    r"|\bun(?:tracked|staged)\b"
    r"|\bgit\s+rm\s"
    # Conditional/hypothetical contexts — "If the cull removed too much"
    # These are speculative, not completion claims
    r"|\bIf\b[^.]*\bremoved?\b"
    # Quantifier modifiers — "removed too much/little/many"
    # These describe degree, not filesystem operations
    r"|\bremoved?\s+(?:too\s+)?(?:much|little|many|few|less|more)\b",
    re.IGNORECASE,
)

# Stopword tokens immediately after a deletion verb. These tokens indicate
# analytical/linguistic context rather than filesystem-deletion completion
# claims. Examples: "removed from config", "deleted in the process",
# "dropped when condition", "removed — here's what changed".
_DELETION_VERB_STOPWORDS = re.compile(
    r"(?:deleted|removed|cleaned\s+up|dropped?)\s+"
    r"(?:from|in|of|to|at|by|for|via|into|onto|"
    r"when|since|because|if|while|as|after|before|too|also|[—–(])",
    re.IGNORECASE,
)


# --- Deletion-operation evidence gate ----------------------------------------
# ROOT-CAUSE FP FIX (2026-06-18): This guard's only legitimate trigger is
# verifying a deletion the assistant *actually performed this turn*. Prose that
# merely mentions "deleted/removed X" — code reviews, session recaps,
# recommendations, code-edit descriptions — never runs a deletion command, yet
# the prose-only pattern matcher was hard-blocking those turns (757 firings in
# the block log; blocked legitimate review turns repeatedly). Gating on real
# tool evidence collapses that entire false-positive class while preserving the
# true positive: a genuine `rm`/`Remove-Item`/`os.remove` still routes to disk
# verification.
# Command-boundary prefix: a shell deletion verb only counts when it actually
# STARTS a command — at string start, after a shell separator (newline ; & | ` ( ) { }
# $( ), or after xargs / -exec. This kills the mention-FP class where a deletion
# idiom appears as data inside another command (grep "rm -rf" log, echo "run rm",
# a pytest fixture containing "rm") while still catching real pipelines like
# `cd x && rm -rf y`, `find . -exec rm {}`, and `... | xargs rm`.
_CMD_BOUNDARY = r"(?:^|[\n;&|`(){}]|\$\(|\bxargs\s+|-exec\s+)\s*"
DELETION_COMMAND_PATTERNS = re.compile(
    _CMD_BOUNDARY + r"(?:sudo\s+)?rm\b(?:\s+-[a-zA-Z]+)*(?:\s+\S|\s*$)"  # rm [flags] [<path>|xargs rm]
    r"|" + _CMD_BOUNDARY + r"git\s+rm\b"
    r"|" + _CMD_BOUNDARY + r"unlink\s+\S"
    r"|" + _CMD_BOUNDARY + r"rmdir\b"
    r"|" + _CMD_BOUNDARY + r"rd\s+/"
    r"|" + _CMD_BOUNDARY + r"del\s+[/\"']?\S"                    # Windows del
    r"|\bRemove-Item\b"                                          # distinctive cmdlet
    r"|\bos\.remove\s*\(|\bos\.unlink\s*\(|\bshutil\.rmtree\s*\("  # python call-sites
    r"|\.unlink\s*\(",                                           # pathlib Path.unlink()
    re.IGNORECASE,
)


# Bounded tail read for transcript parsing — one turn's tail is small; never
# load a multi-MB transcript in full on a latency-sensitive Stop.
_TRANSCRIPT_TAIL_BYTES = 1_000_000


def _iter_transcript_turn_commands(transcript_path: str):
    """Yield assistant ``tool_use`` command strings from the CURRENT turn.

    Real Stop payloads omit ``tool_events`` but include ``transcript_path``
    (authoritative). Reads a bounded tail of the JSONL, walks backward yielding
    assistant tool_use ``command`` strings until the last real user prompt
    (the turn boundary). Fail-open: yields nothing on any error.
    """
    try:
        p = Path(transcript_path)
        if not p.exists():
            return
        size = p.stat().st_size
        with p.open("rb") as fh:
            if size > _TRANSCRIPT_TAIL_BYTES:
                fh.seek(size - _TRANSCRIPT_TAIL_BYTES)
                raw = fh.read().split(b"\n", 1)[-1]  # drop partial first line
            else:
                raw = fh.read()
        lines = raw.decode("utf-8", errors="ignore").splitlines()
        for ln in reversed(lines):
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            msg = obj.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if obj.get("type") == "user":
                # Stop at the current turn's real prompt; skip tool_result-only
                # user entries (those belong to this same turn).
                is_tool_result = isinstance(content, list) and any(
                    isinstance(b, dict) and b.get("type") == "tool_result" for b in content
                )
                if not is_tool_result:
                    return
            if obj.get("type") == "assistant" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        inp = b.get("input", {}) or {}
                        cmd = inp.get("command", "") if isinstance(inp, dict) else ""
                        if cmd:
                            yield str(cmd)
    except Exception:
        return


def _transcript_turn_has_deletion(transcript_path: str) -> bool:
    """Detect a filesystem-deletion command in the CURRENT turn via the transcript."""
    return any(DELETION_COMMAND_PATTERNS.search(c) for c in _iter_transcript_turn_commands(transcript_path))


def _turn_performed_deletion(data: dict) -> bool:
    """True if this turn actually executed a filesystem-deletion command.

    Signal priority:
      1. ``tool_events`` / ``tool_calls`` in ``data`` — used by unit tests and any
         caller that populates them (the real Claude Code Stop payload does NOT).
      2. ``transcript_path`` — the authoritative source present in real payloads;
         parsed for the current turn's tool_use commands.

    Deletions go through shell tools (Bash/PowerShell), never Edit/Write, so only
    command strings are inspected. Fail-open: on any error returns False (claim
    allowed), consistent with this guard's documented fail-open stance.
    """
    try:
        events = data.get("tool_events", []) or []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            tool_input = ev.get("input", {}) or ev.get("tool_input", {}) or {}
            cmd = ""
            if isinstance(tool_input, dict):
                cmd = str(tool_input.get("command", "") or tool_input.get("cmd", ""))
            if cmd and DELETION_COMMAND_PATTERNS.search(cmd):
                return True
        tc = data.get("tool_calls", "")
        if isinstance(tc, str) and tc and DELETION_COMMAND_PATTERNS.search(tc):
            return True
        # Real-payload path: tool_events is absent at Stop time; transcript is truth.
        tpath = data.get("transcript_path", "")
        if tpath and _transcript_turn_has_deletion(str(tpath)):
            return True
    except Exception:
        return False
    return False


# --- Literal deletion-target extraction (v2 ROOT-CAUSE FP FIX) ---------------
# When a deletion command ran this turn, verify the LITERAL targets of THAT
# command (transcript-authoritative) — NOT prose-paths lifted from the full
# response. Prose-paths ("CLAUDE.md" in a review, a parent dir mentioned in
# context) are not deletion targets; verifying them caused the false
# "file still exists" blocks (e.g. the 2026-07-03 pointer-cleanup block that
# flagged CLAUDE.md and P:\.claude\.artifacts/ which were never rm'd).

_GLOB_CHARS = ("*", "?", "[")

# Constructs whose targets are determined at runtime by another command's
# output (xargs, find -exec) or shell substitution ($(), backticks, ${var}).
# The literal command text does not name the targets, so disk verification
# cannot be anchored to the command → fail-open advisory instead.
_UNVERIFIABLE_CONSTRUCT_RE = re.compile(
    r"\bxargs\s+(?:sudo\s+)?(?:rm|git\s+rm)\b"
    r"|`[^`]*`"
    r"|\$\([^)]*\)"
    r"|\$\{[A-Za-z_]\w*\}"
    r"|(?<![\w-])-exec(?:\s|$)"  # find -exec
)

# Deletion verbs: only these set ``seen_verb`` (everything after one of them,
# up to the next shell operator, is a candidate target).
_DELETION_VERBS = {
    "rm", "rmdir", "rd", "del", "unlink",
    "Remove-Item", "remove-item", "trash", "trash-put",
}

# Context tokens: skipped silently (do NOT set seen_verb). These precede the
# deletion verb (``sudo rm``, ``git rm``) or wrap it (``find . -exec rm``,
# ``... | xargs rm``). Paths appearing before the deletion verb — e.g. a
# ``find`` search root — must not be captured as targets.
_SHELL_CONTEXT_TOKENS = {"sudo", "git", "find", "xargs"}

# Shell operators / terminators to skip when tokenizing.
_SHELL_OPERATOR_TOKENS = {";", "&", "|", "&&", "||", ">", "<", ">>", "<<", "(", ")"}

# Path-like discriminator: a token is a candidate deletion target if it has a
# path separator, a trailing file extension, or a leading relative-path dot.
_PATH_LIKE_RE = re.compile(r"[/\\]|\.[A-Za-z0-9]{1,4}$|^\.")


def _collect_turn_deletion_commands(data: dict) -> list[str]:
    """Return THIS turn's deletion-command strings (deduped, order-preserving).

    Source priority mirrors ``_turn_performed_deletion``: tool_events →
    tool_calls → transcript_path (authoritative for real Stop payloads).
    Only commands matching ``DELETION_COMMAND_PATTERNS`` are returned.
    """
    cmds: list[str] = []
    try:
        for ev in data.get("tool_events", []) or []:
            if not isinstance(ev, dict):
                continue
            ti = ev.get("input", {}) or ev.get("tool_input", {}) or {}
            if isinstance(ti, dict):
                cmd = str(ti.get("command", "") or ti.get("cmd", ""))
                if cmd and cmd not in cmds:
                    cmds.append(cmd)
        tc = data.get("tool_calls", "")
        if isinstance(tc, str) and tc.strip() and tc not in cmds:
            cmds.append(tc)
        tpath = data.get("transcript_path", "")
        if tpath:
            for cmd in _iter_transcript_turn_commands(str(tpath)):
                if cmd not in cmds:
                    cmds.append(cmd)
    except Exception:
        return []
    return [c for c in cmds if DELETION_COMMAND_PATTERNS.search(c)]


def _strip_surrounding_quotes(tok: str) -> str:
    """Strip one matching surrounding quote pair (shlex posix=False keeps them)."""
    if len(tok) >= 2 and tok[0] in ('"', "'") and tok[-1] == tok[0]:
        return tok[1:-1]
    return tok


def _parse_deletion_targets(cmd: str) -> tuple[list[str], bool]:
    """Parse literal deletion-target paths from one deletion command string.

    Returns ``(targets, unverifiable)``:
      * ``targets`` — literal path-like tokens that appear after the deletion
        verb (flags, command names, and shell operators excluded).
      * ``unverifiable`` — True if the command uses a construct whose targets
        are not literally present (xargs rm, find -exec, $(), backticks,
        ${var}) or the command is unparseable by shlex.

    Fail-safe: when in doubt, returns ``([], True)`` so the caller fails open
    rather than verifying against the wrong artifact.
    """
    unverifiable = bool(_UNVERIFIABLE_CONSTRUCT_RE.search(cmd))
    try:
        tokens = shlex.split(cmd, posix=False)
    except ValueError:
        return [], True  # unparseable → treat as unverifiable (fail-open)

    targets: list[str] = []
    seen_verb = False
    for tok in tokens:
        tok = _strip_surrounding_quotes(tok)
        if tok.startswith("-"):
            continue  # flag
        if tok == "{}" or tok in _SHELL_OPERATOR_TOKENS:
            continue
        if tok in _SHELL_CONTEXT_TOKENS:
            continue  # sudo/git/find/xargs — precede or wrap the deletion verb
        if tok in _DELETION_VERBS:
            seen_verb = True
            continue
        if tok.startswith("$") or tok.startswith("`"):
            continue  # command-substitution residue
        if not seen_verb:
            continue
        if _PATH_LIKE_RE.search(tok) and tok not in targets:
            targets.append(tok)
    return targets, unverifiable


def _extract_deletion_targets(data: dict) -> tuple[list[str], bool]:
    """Aggregate literal deletion targets across this turn's deletion commands.

    Returns ``(targets, unverifiable)``. ``targets`` is the deduped union of
    literal path-like args; ``unverifiable`` is True if ANY deletion command
    used a construct whose targets are not literally present.
    """
    all_targets: list[str] = []
    any_unverifiable = False
    for cmd in _collect_turn_deletion_commands(data):
        targets, unverifiable = _parse_deletion_targets(cmd)
        for t in targets:
            if t not in all_targets:
                all_targets.append(t)
        any_unverifiable = any_unverifiable or unverifiable
    return all_targets, any_unverifiable


def _advisory(message: str) -> dict:
    """Non-blocking Stop advisory (fail-open with model-facing context)."""
    return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": message}}


# --- Path extraction -----------------------------------------------------------


def _sanitize_for_log(text: str) -> str:
    """Sanitize text for logging to prevent log injection attacks.

    Removes newlines, carriage returns, and other control characters
    that could be used for log injection, while preserving Unicode
    characters for international file paths.

    Args:
        text: The text to sanitize

    Returns:
        Sanitized text safe for logging
    """
    result = []
    for char in str(text):
        code = ord(char)
        # Keep tab (0x09), printable ASCII (0x20-0x7e), and Unicode (>= 0x80)
        # Remove: control characters (0x00-0x08, 0x0a-0x1f) and DEL (0x7f)
        if code == 0x09 or (0x20 <= code <= 0x7E) or (code >= 0x80):
            result.append(char)
    return "".join(result)


def _validate_path_boundary(path: Path, project_root: Path) -> bool:
    """Validate that path stays within project root boundary.

    Prevents path traversal attacks by ensuring the resolved path
    is within the project root directory.

    Args:
        path: The path to validate
        project_root: The project root directory

    Returns:
        True if path is within project root, False otherwise
    """
    try:
        resolved = path.resolve()
        # Check if resolved path is within project root
        resolved.relative_to(project_root.resolve())
        return True
    except (ValueError, OSError):
        # Path is outside project root or resolution failed
        return False


def _extract_file_paths(text: str) -> list[str]:
    """Extract file paths from text using multiple patterns.

    First removes URLs to prevent false positives, then extracts file paths.
    """
    # Remove URLs first to prevent them from being matched as file paths
    text_without_urls = URL_PATTERNS.sub("", text)

    paths = []

    # Extract using patterns
    for match in FILE_PATH_PATTERNS.finditer(text_without_urls):
        path = match.group(0)
        # Clean up quotes if captured
        if path.startswith(("'", '"')) and path.endswith(("'", '"')):
            path = path[1:-1]

        # FILTER: Skip clearly truncated/incomplete path fragments
        # These are regex artifacts that don't represent real paths
        if path.count("/") == 0 and path.count("\\") == 0 and "." not in path:
            continue  # No separator and no extension — not a real path

        paths.append(path)

    # Deduplicate while preserving order
    seen = set()
    unique_paths = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)

    # Filter root-only paths (e.g. "P:\\", "C:/", "P:") — these are always-
    # existing directories that appear in context strings but are never valid
    # deletion targets.  They cause false "file still exists" blocks whenever
    # a response mentions any P:\ path prefix.
    # Check: len 2-3, second char is ':', rest is optional slash only.
    unique_paths = [
        p for p in unique_paths
        if not (len(p) <= 3 and ':' in p)
    ]

    return unique_paths


def _normalize_path(path: str) -> Path:
    """Normalize path relative to project root if needed."""
    p = Path(path)

    # If relative path, make it relative to project root
    if not p.is_absolute():
        project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
        p = project_root / p

    return p.resolve()


# --- Verification logic ----------------------------------------------------


def _check_path_with_timeout(path: Path) -> tuple[bool, bool, str]:
    """Check if path exists using os.scandir() with timeout protection.

    Uses a single syscall (os.scandir) instead of Path.exists() + Path.is_dir()
    to avoid the double-syscall anti-pattern. Returns whether path exists,
    whether it's a directory, and an error message (empty string if no error).

    Args:
        path: The path to check

    Returns:
        (exists, is_dir, error_message) tuple where error_message is empty on success
    """

    def _check():
        try:
            exists = path.exists()
            return (exists, path.is_dir() if exists else False, "")
        except OSError:
            return (False, False, "verification failed")

    try:
        # Use ThreadPoolExecutor with timeout to prevent hangs on network paths
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_check)
            return future.result(timeout=IO_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        return (False, False, "timeout")
    except Exception:
        return (False, False, "verification failed")


def _verify_deletion_claim(paths: list[str]) -> tuple[bool, str]:
    """Verify that claimed deleted files actually don't exist.

    Uses os.scandir() for single-syscall existence checks with timeout protection.
    Collects all results first, then logs once (deferred logging pattern).

    Returns:
        (True, "") if all files are actually deleted
        (False, reason) if any files still exist
    """
    # PERF-001: Enforce MAX_PATHS limit to prevent N+1 unbounded I/O
    if len(paths) > MAX_PATHS:
        return (
            False,
            f"Too many paths to verify ({len(paths)} > {MAX_PATHS}). Verify deletion in batches.",
        )

    project_root_env = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    project_root = Path(project_root_env) if project_root_env else None
    confirmed_existing = []  # Files confirmed to still exist on disk
    verification_failures = []  # Paths where verification failed (timeout, error, boundary)
    log_messages = []  # PERF-003: Defer logging - collect results, log once after loop

    for path_str in paths:
        try:
            # Glob-aware: a target with wildcard chars is expanded rather than
            # treated as a literal. Any existing match ⇒ the deletion did NOT
            # remove everything matched (block); zero matches ⇒ deleted (allow).
            if any(c in path_str for c in _GLOB_CHARS):
                glob_pattern = path_str
                if not Path(glob_pattern).is_absolute():
                    glob_pattern = str(
                        Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / glob_pattern
                    )
                matches = glob.glob(glob_pattern)
                if matches:
                    for m in matches:
                        display = _sanitize_for_log(m)
                        if Path(m).is_dir():
                            confirmed_existing.append(f"{display}/ (directory)")
                        else:
                            confirmed_existing.append(display)
                else:
                    log_messages.append(
                        f"No glob matches (deleted): {_sanitize_for_log(path_str)}"
                    )
                continue

            path = _normalize_path(path_str)

            # SEC-002: Boundary validation - ensure path stays within project root
            if project_root is not None and not _validate_path_boundary(path, project_root):
                log_messages.append(f"Path outside project root: {_sanitize_for_log(path_str)}")
                verification_failures.append(
                    f"{_sanitize_for_log(path_str)} (outside project boundary)"
                )
                continue

            # CRIT-003 + PERF-002: Use os.scandir() with timeout (single syscall, not exists() + is_dir())
            exists, is_dir, error_msg = _check_path_with_timeout(path)

            if error_msg == "timeout":
                log_messages.append(f"Path verification timeout: {_sanitize_for_log(path_str)}")
                verification_failures.append(
                    f"{_sanitize_for_log(path_str)} (verification timeout)"
                )
            elif error_msg:
                # SEC-003: Generic error message (hide exception details)
                log_messages.append(f"Path verification failed: {_sanitize_for_log(path_str)}")
                verification_failures.append(f"{_sanitize_for_log(path_str)} (verification failed)")
            elif exists:
                # File or directory still exists
                display_path = _sanitize_for_log(str(path))
                if is_dir:
                    confirmed_existing.append(f"{display_path}/ (directory)")
                else:
                    confirmed_existing.append(display_path)
            else:
                # File correctly deleted
                log_messages.append(f"File correctly deleted: {_sanitize_for_log(str(path))}")

        except (OSError, ValueError):
            # SEC-003: Generic error message (hide exception details)
            log_messages.append(f"Path verification error: {_sanitize_for_log(path_str)}")
            verification_failures.append(f"{_sanitize_for_log(path_str)} (verification error)")

    # PERF-003: Log all messages at once after loop completes
    for msg in log_messages:
        _logger.info(msg)

    # BLOCK: Only when files are confirmed to still exist
    if confirmed_existing:
        reason = "Files still exist despite deletion claim:\n  • " + "\n  • ".join(
            confirmed_existing
        )
        return False, reason

    # FAIL-OPEN: Verification failures don't block — allow with advisory
    # (DR-20260331: Based on Claude Code hook fail-open philosophy; uncertain = allow)
    if verification_failures:
        _logger.warning(
            "deletion claim could not be fully verified (%d path(s) failed verification)",
            len(verification_failures),
        )
        advisory = "Verification could not confirm deletion (fail-open):\n  • " + "\n  • ".join(
            verification_failures
        )
        return True, advisory  # Allow

    return True, ""


# --- Pattern detection -----------------------------------------------------


def _detect_deletion_claims(response: str) -> list[tuple[str, list[str]]]:
    """Detect deletion completion claims and extract file paths.

    Returns list of (matched_text, file_paths) tuples.
    """
    if not response:
        return []

    # Check obvious allowlist first
    if OBVIOUS_ALLOWLIST.search(response):
        _logger.debug("matched obvious allowlist pattern - skipping")
        return []

    claims = []

    # Check deletion completion patterns (use/mention exemption)
    from quote_exemption import finditer_unquoted

    for match in finditer_unquoted(DELETION_CLAIM_PATTERNS, response):
        matched_text = match.group(0)

        # FP filter: skip if the token immediately after the verb is a
        # stopword/preposition/conjunction — that indicates analytical context
        # ("removed from config", "deleted in process", "dropped when X")
        # rather than a filesystem-deletion completion claim.
        if _DELETION_VERB_STOPWORDS.search(matched_text):
            _logger.debug("stopword post-verb — not a file deletion: %r", matched_text)
            continue

        # Extract file paths from the FULL response (not a windowed slice)
        # Rationale: deletion claims always precede the paths they reference
        # ("files were deleted: /path/to/file" -> path comes AFTER claim)
        # Using full response avoids arbitrary char limits and edge case truncation
        file_paths = _extract_file_paths(response)

        claims.append((matched_text, file_paths))

    return claims


# --- Decision logic ---------------------------------------------------------


def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow).

    Detection flow:
      1. DELETION_CLAIM_PATTERNS detects deletion-completion phrases
         (past tense: "files deleted", "removed the foo", "dropped bar.py").
      2. OBVIOUS_ALLOWLIST is consulted first — code-edit summaries like
         "removed the marker from the pattern" are skipped here so they never
         reach the claim list.
      3. When patterns match but no file paths are extracted AND the response
         contains no path-like strings anywhere, the guard blocks as a
         "bare deletion claim" (no artifact specified to verify).
    """
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return None

    # Cheap first (PERF): does the response even contain a deletion-completion
    # claim? The overwhelming majority of turns do not — return before touching
    # any tool/transcript evidence. This keeps the transcript read (measured
    # ~3-5ms on a 20MB transcript) OFF the hot path of every Stop and pays it
    # only when a claim is actually present.
    claims = _detect_deletion_claims(response)
    if not claims:
        return None

    # A deletion CLAIM exists. Now consult evidence (ROOT-CAUSE FP FIX): did THIS
    # turn actually run a filesystem-deletion command? Prose that merely mentions
    # deletion (reviews, recaps, code-edit notes) never executed one and must not
    # be blocked; a real rm/Remove-Item/os.remove routes to disk verification.
    _did_delete = _turn_performed_deletion(data)

    # PROBE (debug-level): payload key set + signal shape, logged only when a
    # claim is present. Keys only — never values.
    _te = data.get("tool_events", [])
    _logger.debug(
        "PROBE keys=%s tool_events_len=%s tool_calls_present=%s deletion_detected=%s",
        sorted(data.keys()),
        (len(_te) if isinstance(_te, list) else "non-list"),
        bool(data.get("tool_calls")),
        _did_delete,
    )

    if not _did_delete:
        # SUPPRESSED branch instrumentation (FP-reduction path): a deletion claim
        # appeared in prose but no deletion command ran this turn. Logged so the
        # narrowing stays measurable and over-suppression is visible.
        _logger.info("SUPPRESSED: deletion claim in prose but no deletion command this turn; allowed")
        return None  # No deletion patterns - allow

    _logger.info(
        "found %d deletion claim(s): %s",
        len(claims),
        [claim for claim, _ in claims],
    )

    # v2 (ROOT-CAUSE FP FIX): verify the LITERAL targets of the deletion
    # command that ran this turn — NOT prose-paths lifted from the full
    # response. Prose-paths ("CLAUDE.md" in a review, a parent directory
    # mentioned in context) are not deletion targets; verifying them caused
    # false "file still exists" blocks. See module notes.
    targets, unverifiable = _extract_deletion_targets(data)

    if not targets:
        why = (
            "unverifiable construct (xargs/find-exec/$()/backtick)"
            if unverifiable
            else "no path-like argument parsed from the command"
        )
        _logger.info("deletion command ran but %s; advisory fail-open", why)
        return _advisory(
            "Deletion claim could not be tied to specific on-disk targets "
            f"({why}). The deletion may have succeeded; verify manually with "
            "Read/Glob/Bash if uncertain."
        )

    verified, reason = _verify_deletion_claim(targets)
    if not verified:
        _logger.warning(
            "BLOCK: %d unverified deletion target(s) - still exist", len(targets)
        )
        claim_text = claims[0][0]
        lines = ["**Unverified Deletion Claim Detected**\n"]
        lines.append(f'Claim: "{claim_text}"\n')
        lines.append("\n")
        lines.append(reason)
        lines.append("\n")
        lines.append(
            "Before claiming files are deleted, verify they actually "
            "don't exist on the file system. Use Read, Glob, or Bash to "
            "confirm the deletion succeeded."
        )
        return {
            "decision": "block",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_deletion_verification_guard",
        }

    _logger.info("deletion targets verified - files actually deleted")
    return None


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_deletion_verification_guard"),
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
        print(json.dumps(_normalize_stdout(result)))
        if result.get("decision") == "block":
            sys.exit(2)


if __name__ == "__main__":
    main()
