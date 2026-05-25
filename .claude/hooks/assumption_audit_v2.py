#!/usr/bin/env python3
"""
Assumption Audit v2 - Blocking Mode
===================================

KEY CHANGE FROM v1: This hook BLOCKS responses with unverified claims,
rather than injecting a soft warning that can be ignored.

Design principle: Structural enforcement > advisory injection

v2.6.0: USER-PROVIDED ENTITY EXCLUSION
        - Extracts entities from user's last message (transcript + prompt)
        - Subtracts user-provided entities from claim entity set before scope check
        - Prevents false positives when Claude references user-pasted content
        - New allow reason: USER_PROVIDED_ENTITIES
v2.5.0: CLAIM-LOCAL SCOPE + TRACEABLE MESSAGES
        - Entity extraction uses context window around claims, not full response
        - Prevents scope inflation from long synthesis responses
        - SCOPE_MISMATCH message shows per-claim entity trace
        - Expanded COMMON_WORDS to filter generic terms (action, status, etc.)
v2.4.2: SHOW-DON'T-SUMMARIZE REMEDIATION
        - Enhanced remediation messages emphasize quoting actual evidence
        - Added summary_without_evidence category for common pattern
        - All remediation actions now specify quoting output, not summarizing
v2.4.1: SUCCESS CLAIM EARLY RETURN FIX
        - Theater detection now triggers on success claims even without entity claims
        - Fixes bug where "It's fixed!" with only `ls` would bypass theater detection
v2.4.0: VERIFICATION THEATER PREVENTION
        - Trivial bash commands (echo, mkdir, etc.) filtered from evidence
        - Success claims require diagnostic evidence (pytest, cat, grep, etc.)
        - Weak evidence (ls, dir) triggers warning for success claims
        - Pipeline handling: final command determines trivial/diagnostic status
v2.3.1: IMPROVEMENTS
        - Common word filtering in entity extraction (removes "the", "file", etc.)
        - Configurable coverage threshold via CLAIM_COVERAGE_THRESHOLD (default 50%)
v2.3.0: CLAIM-SCOPE VERIFICATION - Claims must have RELEVANT evidence, not just ANY evidence
        - Entity extraction from claims (file paths, names)
        - Entity extraction from tool evidence (paths read/checked)
        - Overlap check: claim entities must intersect evidence entities
v2.2.0: Evidence window - prior observations valid until state change
v2.1.0: Pattern-specific remediation with actionable fix instructions
v2.0.0: Block mode - claims without tools = response blocked
v1.x: Soft warning mode - claims without tools = warning injected (easily ignored)

Hook Phase: Stop
Output: JSON with decision (block/allow)
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

try:
    from evidence_store import resolve_session_id as _evidence_store_resolve_session_id
except ImportError:
    _evidence_store_resolve_session_id = None  # type: ignore

# === META-CONVERSATION GATE IMPORT ===
# Import shared helpers for meta/self-referential detection
# This gate prevents claim-coverage hooks from blocking process talk
try:
    # Import claim classifier for workload-aware enforcement
    from __lib.claim_classifier import (
        classify_claim_text,
        is_marked_as_hypothesis,
        is_promoted_fact,
        is_test_report_context,
        make_block_payload,
        mentions_history_or_blame,
        summarize_response_claim_kinds,
    )
    from __lib.claim_patterns import EXTERNAL_CLAIM_PATTERNS, has_external_claim
    from __lib.shared_helpers import (
        is_meta_conversation,
        is_question,
        is_self_referential,
        is_user_intent_statement,
        strip_non_claim_lines,
    )

    CLAIM_CLASSIFIER_AVAILABLE = True
except ImportError as e:
    # Fail fast - claim_classifier is required
    import sys

    _logger.warning("[ERROR] assumption_audit_v2.py: Failed to import required claim_classifier: %s", e)
    _logger.warning("[ERROR] Ensure P:/.claude/hooks/__lib/claim_classifier.py exists and is importable.")
    sys.exit(1)

# Configuration
ENABLED = os.environ.get("ASSUMPTION_AUDIT_V2_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("ASSUMPTION_AUDIT_V2_DEBUG", "false").lower() == "true"
UNIFIED_VERIFIER_ENABLED = (
    os.environ.get("UNIFIED_CLAIM_VERIFIER_ENABLED", "true").lower() == "true"
)
LOG_FILE = Path("P:/.claude/hooks/logs/assumption_audit_v2.jsonl")
STATE_DIR = Path("P:/.claude/hooks/state")

# v2.3.0: Claim-scope verification (can disable for rollback)
CLAIM_SCOPE_CHECK_ENABLED = os.environ.get("CLAIM_SCOPE_CHECK_ENABLED", "true").lower() == "true"

# v2.3.1: Coverage threshold for claim-entity overlap (0.0-1.0)
# Higher = stricter (more entities must be covered)
# Default 0.3 = at least 30% of claim entities must have evidence
CLAIM_COVERAGE_THRESHOLD = float(os.environ.get("CLAIM_COVERAGE_THRESHOLD", "0.3"))

# v2.5.0: New entity extraction system flag (applied at end of module)
USE_NEW_ENTITY_EXTRACTION = os.environ.get("USE_NEW_ENTITY_EXTRACTION", "false").lower() == "true"

# Terminal isolation
try:
    from __lib.terminal_detection import detect_terminal_id

    TERMINAL_ID = detect_terminal_id()
except ImportError:
    TERMINAL_ID = "unknown"

TERMINAL_HASH = hashlib.md5(TERMINAL_ID.encode()).hexdigest()[:16]

# Tools that count as verification
OBSERVATION_TOOLS = frozenset({"Read", "Bash", "Grep", "Glob", "Search", "WebFetch"})

# Tools that change state (invalidate prior observations)
STATE_CHANGING_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "Task"})

# Read-only Bash command prefixes (conservative allowlist)
# Bash commands NOT in this list are assumed to change state
READ_ONLY_BASH_PREFIXES = (
    "git status",
    "git log",
    "git diff",
    "git show",
    "git branch",
    "git remote",
    "ls",
    "cat ",
    "head ",
    "tail ",
    "grep ",
    "find ",
    "wc ",
    "stat ",
    "pwd",
    "echo ",
    "type ",
    "dir ",
    "Get-Content",
    "Get-ChildItem",
    "Test-Path",
    'python -c "import',
    "python -c 'import",  # import checks (read-only)
    'python -c "from',
    "python -c 'from",
)

# v2.4.0: DIAGNOSTIC BASH PREFIXES - commands that count as evidence
# These may technically change state (create test outputs) but their PRIMARY purpose
# is verification/diagnosis, so they count as observational evidence.
DIAGNOSTIC_BASH_PREFIXES = (
    # Test runners
    "pytest",
    "python -m pytest",
    "py.test",
    "npm test",
    "npm run test",
    "yarn test",
    "pnpm test",
    "cargo test",
    "go test",
    "mvn test",
    "gradle test",
    "jest",
    "mocha",
    "vitest",
    "ava",
    # Script execution (verifies behavior)
    "python ",
    "python3 ",
    "node ",
    "deno ",
    "bun ",
    # Build verification
    "cargo check",
    "cargo build",
    "go build",
    "npm run build",
    "tsc ",
    "mypy ",
    "ruff ",
    "flake8",
    "pylint",
)

# v2.4.0: TRIVIAL BASH COMMANDS - commands that cannot produce diagnostic information
# These are "read-only" in that they don't change state, but they provide NO verification value
# for claims about system behavior, test results, or fix correctness.
#
# RULE: Trivial commands are filtered from evidence when evaluating success claims.
# REASON: Prevents "Verification Theater" where `echo "done"` masquerades as verification.
# CONSEQUENCE: Agent blocked from claiming "fixed" based on trivial commands alone.
TRIVIAL_BASH_COMMANDS = frozenset(
    {
        # Output commands (produce text, don't observe system state)
        "echo",
        "printf",
        "write-host",
        "write-output",
        # File manipulation (change state, not observation)
        "mkdir",
        "touch",
        "rm",
        "mv",
        "cp",
        "del",
        "copy",
        "move",
        "ren",
        "rename",
        # Environment manipulation (no diagnostic value)
        "cd",
        "pushd",
        "popd",
        "pwd",
        "export",
        "set",
        "alias",
        "unalias",
        "clear",
        "cls",
        # Directory listing without diagnostic intent
        # NOTE: "ls" alone is weak evidence but not blocked - use WEAK_EVIDENCE_COMMANDS for tiering
    }
)

# Commands that are evidence but weak (Tier 4 equivalent - may trigger warnings but not blocks)
WEAK_EVIDENCE_COMMANDS = frozenset(
    {
        "ls",
        "dir",
        "tree",  # Show structure but not content/behavior
    }
)

# Success claim patterns - phrases that assert completion/correctness
# Used to detect when trivial evidence + success claim = Verification Theater
SUCCESS_CLAIM_PATTERNS = (
    r"\b(?:is|are|was|were)\s+(?:now\s+)?(?:fixed|resolved|working|passing|correct|complete|done)\b",
    r"\b(?:fixed|resolved|corrected|completed|passed)\b",
    r"\b(?:works?|passes?|succeeds?)\s+(?:now|correctly|properly|as expected)\b",
    r"\bsuccessfully\s+(?:fixed|resolved|updated|changed|modified)\b",
    r"\bthe\s+(?:bug|issue|problem|error)\s+(?:is|has been)\s+(?:fixed|resolved)\b",
    r"\btests?\s+(?:pass|passed|passing|succeed|succeeded)\b",
    r"\bverified\s+(?:that\s+)?(?:it\s+)?(?:works?|passes?|is\s+correct)\b",
    r"\bconfirmed\s+(?:the\s+)?(?:fix|solution|change)\b",
)

EQUIVALENCE_LINK_RE = re.compile(
    r"\b(?:"
    r"is|are|was|were|equals?|equal to|equivalent to|same as|same package as|"
    r"packaged as|known as|called|corresponds to|maps to|mapped to|alias(?:ed)? as|alias for|aka"
    r")\b|(?:->|=>|=)",
    re.IGNORECASE,
)
NON_EQUIVALENCE_STATE_RE = re.compile(
    r"\b(?:fixed|resolved|working|passing|correct|deleted|removed|added|created|modified|updated|changed|missing|absent|not found)\b",
    re.IGNORECASE,
)


def debug_log(msg: str):
    """Log debug message if DEBUG enabled."""
    if DEBUG:
        _logger.warning("[assumption_audit_v2] %s", msg)


def resolve_session_id(session_id: str) -> str:
    """Compatibility wrapper for session id normalization."""
    if _evidence_store_resolve_session_id is None:
        return (session_id or "").strip()
    return _evidence_store_resolve_session_id(session_id)


def load_tool_events(session_id: str, limit: int = 500, terminal_id: str = "") -> list[dict]:
    """Compatibility wrapper for recent session evidence."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    kwargs = {
        "session_id": session_id,
        "scope": SCOPE_SESSION_FRESH,
        "limit": limit,
    }
    if terminal_id:
        kwargs["terminal_id"] = terminal_id
    return load_scoped_tool_events(**kwargs)


# =============================================================================
# v2.4.0: TRIVIAL COMMAND DETECTION
# =============================================================================


def get_bash_command_name(cmd: str) -> str:
    """
    Extract the base command name from a bash command string.
    Handles pipelines by returning the LAST command (final output producer).

    Examples:
        "echo test"           -> "echo"
        "pytest tests/"       -> "pytest"
        "echo | python x.py"  -> "python"
        "cat file | grep x"   -> "grep"
    """
    if not cmd:
        return ""

    cmd = cmd.strip()

    # Handle pipelines - get last command (the one producing final output)
    if "|" in cmd:
        parts = cmd.split("|")
        cmd = parts[-1].strip()

    # Get first word (the command name)
    first_word = cmd.split()[0] if cmd.split() else ""

    # Remove path prefix if present (e.g., /usr/bin/python -> python)
    if "/" in first_word or "\\" in first_word:
        first_word = first_word.replace("\\", "/").split("/")[-1]

    # Remove .exe/.cmd/.bat suffix on Windows
    for suffix in (".exe", ".cmd", ".bat", ".ps1", ".py", ".sh"):
        if first_word.lower().endswith(suffix):
            first_word = first_word[: -len(suffix)]
            break

    return first_word.lower()


def is_trivial_bash_command(cmd: str) -> bool:
    """
    Check if a bash command is trivial (provides no diagnostic value).

    Returns True for commands like `echo "done"`, `mkdir temp`, etc.
    Returns False for diagnostic commands like `pytest`, `cat file`, `grep pattern`.

    For pipelines, checks the FINAL command (e.g., `echo | python` is NOT trivial
    because python is the final producer).
    """
    cmd_name = get_bash_command_name(cmd)
    return cmd_name in TRIVIAL_BASH_COMMANDS


def is_weak_evidence_command(cmd: str) -> bool:
    """
    Check if a bash command is weak evidence (provides some but limited value).

    Weak commands like `ls` show structure but not behavior/content.
    They count as evidence but may trigger additional warnings for success claims.
    """
    cmd_name = get_bash_command_name(cmd)
    return cmd_name in WEAK_EVIDENCE_COMMANDS


def has_success_claims(response_text: str) -> bool:
    """
    Check if response contains success/completion claims.

    Used to detect potential Verification Theater:
    If response claims success but evidence is only trivial commands.
    """
    if not response_text:
        return False

    import re

    for pattern in SUCCESS_CLAIM_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            return True
    return False


def is_diagnostic_bash_command(cmd: str) -> bool:
    """
    Check if a bash command has diagnostic value (can verify claims).

    Diagnostic commands include:
    - Test runners: pytest, npm test, cargo test
    - File inspection: cat, grep, head, tail
    - Execution: python script.py, node script.js
    - Git inspection: git status, git diff

    This is the inverse of trivial + weak (i.e., strong evidence).
    """
    cmd_name = get_bash_command_name(cmd)

    # Not trivial and not weak = diagnostic
    if cmd_name in TRIVIAL_BASH_COMMANDS:
        return False
    if cmd_name in WEAK_EVIDENCE_COMMANDS:
        return False  # Weak is not strong diagnostic

    # Additional positive signals for known diagnostic commands
    diagnostic_commands = {
        "pytest",
        "python",
        "python3",
        "node",
        "npm",
        "yarn",
        "cargo",
        "go",
        "cat",
        "grep",
        "head",
        "tail",
        "less",
        "more",
        "awk",
        "sed",
        "git",
        "curl",
        "wget",
        "jq",
        "yq",
        "type",
        "get-content",
        "select-string",  # PowerShell equivalents
    }

    return cmd_name in diagnostic_commands or cmd_name not in TRIVIAL_BASH_COMMANDS


def has_post_change_verification(tool_sequence: list[dict]) -> bool:
    """
    Check whether any observation tool ran AFTER the last state-changing tool.

    Principle: completion/success claims require post-change verification.
    Reading a file before editing it is research, not verification.
    Only observations after the final Edit/Write count as verification
    that the changes are correct.

    Returns True if at least one observation tool follows the last
    state-changing tool in the chronological tool sequence.
    Returns True if there are no state-changing tools (pure read session).
    """
    last_state_change_idx = -1
    last_observation_idx = -1

    for i, tool in enumerate(tool_sequence):
        if not isinstance(tool, dict):
            continue
        name = tool.get("name", "")

        if name in STATE_CHANGING_TOOLS:
            last_state_change_idx = i
        elif name in OBSERVATION_TOOLS:
            if name == "Bash":
                cmd = str(tool.get("command", "")).strip()
                # Only count diagnostic bash as observation
                if is_trivial_bash_command(cmd):
                    continue
                if not any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES) and not any(
                    cmd.startswith(p) for p in DIAGNOSTIC_BASH_PREFIXES
                ):
                    continue
            last_observation_idx = i

    # No state changes at all → pure read session, observations are valid
    if last_state_change_idx == -1:
        return True

    # At least one observation after the last state change
    return last_observation_idx > last_state_change_idx


def normalize_path(path_str: str) -> str:
    """Normalize path for comparison (lowercase, forward slashes)."""
    if not path_str:
        return ""
    try:
        # Simple normalization to handle P:\ vs P:/ mixed styles
        # We don't use resolve() to avoid FS access (this is a pure logic check)
        norm = path_str.replace("\\", "/").lower().strip()
        if norm.endswith("/"):
            norm = norm[:-1]
        return norm
    except Exception:
        return str(path_str).lower()


def paths_overlap(path1: str, path2: str) -> bool:
    """
    Check if paths overlap (one is parent of other or same).
    Empty path matches everything.
    """
    p1 = normalize_path(path1)
    p2 = normalize_path(path2)

    if not p1 or not p2:
        return True  # Unknown/Global scope overlaps everything

    if p1 == p2:
        return True

    # Check if one is prefix of other (directory containment)
    # Append slash to ensure we don't match partial filenames (e.g. /test vs /testing)
    p1_slash = p1 + "/"
    p2_slash = p2 + "/"

    return p1_slash.startswith(p2_slash) or p2_slash.startswith(p1_slash)


def get_tool_scope(tool: dict) -> tuple[str, str]:
    """Extract (path, terminal_id) scope from tool entry."""
    # Terminal ID
    terminal_id = tool.get("terminal_id", "")

    # Path/Cwd
    cwd = tool.get("cwd", "")
    command = tool.get("command", "")
    name = tool.get("name", "")

    path = cwd

    # For file tools, the 'command' field (containing TargetFile/AbsolutePath)
    # is the specific scope. Cwd is just context.
    # We want invalidation to be specific to the file.
    # Note: PostToolUse_router puts TargetFile/etc into 'command'
    FILE_TARGET_TOOLS = ["Read", "Write", "Edit", "View", "Grep", "Replace", "MultiEdit"]

    if name in FILE_TARGET_TOOLS and command:
        path = command
    elif not path and command:
        # Fallback for others if no cwd
        if name in FILE_TARGET_TOOLS:
            path = command

    return path, terminal_id


# =============================================================================
# v2.3.0: ENTITY EXTRACTION
# =============================================================================

# Patterns for extracting file paths from text
PATH_PATTERNS = [
    # Windows absolute paths: P:/..., C:\...
    r"[A-Za-z]:[/\\][\w./\\-]+\.[\w]+",
    # Windows paths with spaces in quotes
    r'["\'][A-Za-z]:[/\\][^"\']+["\']',
    # Unix absolute paths: /home/..., /usr/...
    r"/(?:home|usr|var|etc|opt|tmp|mnt)/[\w./\\-]+",
    # Relative paths with extension: ./file.py, ../dir/file.js
    r"\.{1,2}/[\w./\\-]+\.[\w]+",
    # Python module paths: module.submodule.file
    r"\b[\w]+(?:\.[\w]+){2,}\b",
    # Filenames with common extensions
    r"\b[\w-]+\.(?:py|js|ts|json|yaml|yml|md|txt|sh|ps1|bat|sql|html|css|jsx|tsx)\b",
]

# Patterns for extracting function/class names from claims
NAME_PATTERNS = [
    # function_name(), method_name()
    r"\b([a-z_][a-z0-9_]*)\s*\(",
    # ClassName, ModuleName (PascalCase)
    r"\b([A-Z][a-zA-Z0-9]+)\b",
    # CONSTANT_NAME
    r"\b([A-Z][A-Z0-9_]+)\b",
]

# Common words to filter from entity extraction (noise reduction)
COMMON_WORDS = frozenset(
    {
        # Articles and pronouns
        "the",
        "a",
        "an",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        # Prepositions
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "into",
        # Verbs (common in claims and tech prose)
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "must",
        "shall",
        "get",
        "got",
        "set",
        "run",
        "ran",
        "let",
        "add",
        "use",
        "used",
        "using",
        "make",
        "made",
        "find",
        "found",
        "read",
        "show",
        "fix",
        "fixable",
        "merge",
        "split",
        "filter",
        "replace",
        "expand",
        "clean",
        "implement",
        "review",
        "gather",
        # Conjunctions
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "while",
        "not",
        # Common nouns in tech context (too generic to be meaningful entities)
        "file",
        "files",
        "code",
        "data",
        "list",
        "item",
        "items",
        "test",
        "tests",
        "function",
        "class",
        "method",
        "module",
        "error",
        "result",
        "output",
        "input",
        "value",
        "name",
        "type",
        "path",
        "dir",
        "directory",
        "action",
        "actions",
        "issue",
        "issues",
        "status",
        "context",
        "system",
        "key",
        "root",
        "layer",
        "next",
        "risk",
        "results",
        "summary",
        "description",
        "location",
        "priority",
        "severity",
        "coverage",
        "success",
        "effort",
        "stage",
        "script",
        "task",
        "skill",
        "recommendation",
        "rationale",
        "findings",
        "strengths",
        "weaknesses",
        "execution",
        "generation",
        "validation",
        "formatting",
        "annotation",
        "consolidate",
        "redundant",
        "duplicate",
        "blocking",
        "identified",
        "estimated",
        "recommended",
        "architectural",
        "sequential",
        "critical",
        # Analysis/report terms (appear in synthesis outputs, never entities)
        "high",
        "low",
        "medium",
        "multi",
        "repo",
        "cli",
        "api",
        "which",
        "errors",
        "failures",
        "dead",
        "currently",
        "non",
        # Words appearing in explanatory/example text that aren't code entities
        "claim",
        "claims",
        "instead",
        "unverified",
        "pass",
        "fail",
        "trace",
        "block",
        "blocked",
        "allow",
        "allowed",
        "xyz",
        "example",
        "shows",
        "check",
        "verify",
        "verified",
        "sample",
        "specific",
        "actual",
        "expected",
        "missing",
        "covered",
        "uncovered",
        # User intent/goal language (configuration, not claims to verify)
        "intent",
        "goal",
        "goals",
        "statement",
        "statements",
        "configure",
        "behavior",
        "prefer",
        "preference",
        "minimize",
        "reduce",
        "respect",
        # Adjectives
        "new",
        "old",
        "all",
        "some",
        "any",
        "each",
        "every",
        "no",
        "none",
        # Numbers and quantities
        "one",
        "two",
        "three",
        "four",
        "five",
        "first",
        "second",
        "last",
        # Other common words
        "now",
        "just",
        "also",
        "only",
        "here",
        "there",
        "where",
        "what",
        "how",
        "yes",
        "ok",
        "true",
        "false",
        "null",
        "self",
        "you",
        "your",
        "we",
        "our",
        "they",
        "them",
        "my",
    }
)

# Compiled patterns (lazy init)
_PATH_PATTERN_RE = None
_NAME_PATTERN_RE = None


def _get_path_pattern():
    global _PATH_PATTERN_RE
    if _PATH_PATTERN_RE is None:
        combined = "|".join(f"({p})" for p in PATH_PATTERNS)
        _PATH_PATTERN_RE = re.compile(combined, re.IGNORECASE)
    return _PATH_PATTERN_RE


def _get_name_pattern():
    global _NAME_PATTERN_RE
    if _NAME_PATTERN_RE is None:
        combined = "|".join(f"({p})" for p in NAME_PATTERNS)
        _NAME_PATTERN_RE = re.compile(combined)
    return _NAME_PATTERN_RE


def extract_entities_from_text(text: str) -> set[str]:
    """
    Extract file paths, function names, and other identifiable entities from text.

    Returns set of normalized entity strings for comparison.
    Filters out common words to reduce noise.
    """
    entities = set()

    if not text:
        return entities

    # Extract paths
    path_pattern = _get_path_pattern()
    for match in path_pattern.finditer(text):
        for group in match.groups():
            if group:
                # Normalize: lowercase, forward slashes, strip quotes
                normalized = group.strip("\"'").replace("\\", "/").lower()
                if len(normalized) > 3:  # Skip very short matches
                    entities.add(normalized)
                    # Also add just the filename for matching
                    if "/" in normalized:
                        filename = normalized.rsplit("/", 1)[-1]
                        if len(filename) > 3:
                            entities.add(filename)

    # Extract names (functions, classes)
    name_pattern = _get_name_pattern()
    for match in name_pattern.finditer(text):
        for group in match.groups():
            if group and len(group) > 4:
                normalized = group.lower()
                # Filter out common words
                if normalized not in COMMON_WORDS:
                    entities.add(normalized)

    # Final filter: remove any common words that slipped through
    entities = {e for e in entities if e not in COMMON_WORDS}

    return entities


def _get_claim_context_window(claim: str, response_text: str, window_chars: int = 300) -> str:
    """
    Extract a context window around a claim in the response text.

    Returns the claim + surrounding sentences (up to window_chars in each direction)
    to capture entities the claim is *about* without pulling in the entire response.
    """
    idx = response_text.find(claim)
    if idx == -1:
        # Claim not found verbatim (regex group extraction); use claim text only
        return claim

    start = max(0, idx - window_chars)
    end = min(len(response_text), idx + len(claim) + window_chars)

    # Snap to sentence boundaries (period, newline) if possible
    if start > 0:
        newline = response_text.rfind("\n", start, idx)
        period = response_text.rfind(". ", start, idx)
        boundary = max(newline, period)
        if boundary > start:
            start = boundary + 1

    if end < len(response_text):
        newline = response_text.find("\n", idx + len(claim), end)
        period = response_text.find(". ", idx + len(claim), end)
        candidates = [b for b in [newline, period] if b != -1]
        if candidates:
            end = min(candidates) + 1

    return response_text[start:end].strip()


def extract_entities_from_claims(claims: list[str], response_text: str) -> set[str]:
    """
    Extract entities from claims and their immediate context window.

    v2.5.0: Uses claim-local context (surrounding sentences) instead of the
    full response. Prevents scope inflation where entities mentioned anywhere
    in a long response get attributed to a specific claim.
    """
    entities = set()

    for claim in claims:
        # Extract from the claim text itself
        entities.update(extract_entities_from_text(claim))

        # Extract from surrounding context (nearby sentences only)
        context = _get_claim_context_window(claim, response_text)
        entities.update(extract_entities_from_text(context))

    debug_log(f"Claim entities (context-windowed): {entities}")
    return entities


def extract_user_message_entities(input_data: dict) -> set[str]:
    """
    v2.6.0: Extract entities from recent messages (User + AI).

    When Claude quotes or references content provided earlier in the session
    (pasted transcripts, code snippets, prior responses, file paths),
    those entities should not count as unverified claims.

    Returns set of entities found in the last 5 human AND assistant messages.
    """
    entities = set()

    # Try transcript_path first (most reliable source of session history)
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            content = Path(transcript_path).read_text(encoding="utf-8")
            lines = [l for l in content.strip().split("\n") if l.strip()]

            msgs_found = 0
            # Walk backwards to find the last 5 user AND assistant messages
            for line in reversed(lines):
                try:
                    entry = json.loads(line)
                    # Support both 'human'/'assistant' and 'user'/'assistant' roles
                    msg_type = entry.get("type", "")
                    role = entry.get("role", "")

                    if msg_type in ("human", "assistant") or role in ("user", "assistant"):
                        msg = entry.get("message", {})
                        # Handle different message content formats
                        content_blocks = msg.get("content", [])
                        if isinstance(content_blocks, list):
                            for block in content_blocks:
                                if block.get("type") == "text":
                                    entities.update(
                                        extract_entities_from_text(block.get("text", ""))
                                    )
                        elif isinstance(content_blocks, str):
                            entities.update(extract_entities_from_text(content_blocks))

                        msgs_found += 1
                        if msgs_found >= 10:  # 5 turns = 10 messages
                            break
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # Also check direct prompt field if available
    prompt = input_data.get("prompt", "")
    if prompt:
        entities.update(extract_entities_from_text(prompt))

    debug_log(f"User message entities: {len(entities)} found")
    return entities


def _extract_last_user_message(input_data: dict) -> str:
    """
    Extract the most recent user message text from transcript/prompt.
    """
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            content = Path(transcript_path).read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "human":
                    continue
                msg = entry.get("message", {})
                parts = []
                for block in msg.get("content", []):
                    if block.get("type") == "text":
                        txt = str(block.get("text", "")).strip()
                        if txt:
                            parts.append(txt)
                if parts:
                    return "\n".join(parts)
        except Exception:
            pass

    return str(input_data.get("prompt", "")).strip()


def is_direct_user_question(input_data: dict) -> bool:
    """
    Heuristic: determine if the latest user turn is a direct question.
    """
    text = _extract_last_user_message(input_data)
    if not text:
        return False

    lowered = text.lower().strip()
    if "?" in lowered:
        return True

    question_starters = (
        "what ",
        "why ",
        "how ",
        "where ",
        "when ",
        "who ",
        "is ",
        "are ",
        "can ",
        "could ",
        "should ",
        "would ",
        "did ",
        "does ",
    )
    return lowered.startswith(question_starters)


def extract_entities_from_evidence(tool_sequence: list[dict]) -> set[str]:
    """
    Extract entities from tool outputs/targets - what was ACTUALLY observed.

    This represents the scope of what has been verified.
    """
    entities = set()

    for tool in tool_sequence:
        if not isinstance(tool, dict):
            continue

        name = tool.get("name", "")
        command = tool.get("command", "")
        output = tool.get("output", "")
        cwd = tool.get("cwd", "")

        # Skip non-observation tools
        is_observational = name in OBSERVATION_TOOLS
        if name == "Bash":
            cmd = str(command).strip()
            is_bash_read_only = any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES)
            is_bash_diagnostic = any(cmd.startswith(p) for p in DIAGNOSTIC_BASH_PREFIXES)
            is_observational = is_bash_read_only or is_bash_diagnostic
            # Filter trivial commands (consistent with get_evidence_window)
            if is_observational and is_trivial_bash_command(cmd):
                is_observational = False

        if not is_observational:
            continue

        # Extract from command/target
        if command:
            entities.update(extract_entities_from_text(str(command)))

        # Extract from cwd
        if cwd:
            entities.update(extract_entities_from_text(str(cwd)))

        # Extract from output (paths mentioned in results)
        if output:
            entities.update(extract_entities_from_text(str(output)[:2000]))  # Cap for performance

    debug_log(f"Evidence entities: {entities}")
    return entities


def extract_evidence_chunks(tool_sequence: list[dict]) -> list[str]:
    """
    Build evidence text chunks from observed tool inputs/outputs.
    """
    chunks = []
    for tool in tool_sequence:
        if not isinstance(tool, dict):
            continue
        for field in ("command", "cwd", "output"):
            value = str(tool.get(field, "")).strip()
            if not value:
                continue
            for line in value.splitlines():
                cleaned = line.strip()
                if cleaned:
                    chunks.append(cleaned[:2000])
    return chunks


def _is_equivalence_claim(claim: str, claim_entities: set[str]) -> bool:
    """
    Heuristic classifier for equivalence claims (X is Y / X equals Y).
    """
    if len(claim_entities) < 2:
        return False
    if not EQUIVALENCE_LINK_RE.search(claim):
        return False
    if NON_EQUIVALENCE_STATE_RE.search(claim):
        return False
    return True


def _canonical_equivalence_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _canonical_tokens(value: str) -> set[str]:
    tokens = set()
    for raw in re.findall(r"[A-Za-z0-9_./-]+", value or ""):
        canon = _canonical_equivalence_token(raw)
        if canon:
            tokens.add(canon)
    return tokens


def _entities_referenced_in_claim(claim: str, candidate_entities: set[str]) -> set[str]:
    """
    Map a claim line to the subset of known claim entities it references.
    """
    claim_tokens = _canonical_tokens(claim)
    referenced = set()
    for ent in candidate_entities:
        ent_canon = _canonical_equivalence_token(ent)
        if not ent_canon:
            continue
        ent_base = ent.rsplit("/", 1)[-1] if "/" in ent else ent
        ent_base_canon = _canonical_equivalence_token(ent_base)
        if ent_canon in claim_tokens or (ent_base_canon and ent_base_canon in claim_tokens):
            referenced.add(ent)
    return referenced


def _has_equivalence_cooccurrence(claim_entities: set[str], evidence_chunks: list[str]) -> bool:
    """
    Require at least two claim entities to appear in one evidence chunk.
    """
    if len(claim_entities) < 2:
        return False
    for chunk in evidence_chunks:
        chunk_tokens = _canonical_tokens(chunk)
        if not chunk_tokens:
            continue
        matched = set()
        for claim_ent in claim_entities:
            claim_base = claim_ent.rsplit("/", 1)[-1] if "/" in claim_ent else claim_ent
            claim_canon = _canonical_equivalence_token(claim_ent)
            claim_base_canon = _canonical_equivalence_token(claim_base)
            if claim_canon and claim_canon in chunk_tokens:
                matched.add(claim_ent)
                continue
            if claim_base_canon and len(claim_base_canon) > 3 and claim_base_canon in chunk_tokens:
                matched.add(claim_ent)
        if len(matched) >= 2:
            return True
    return False


def check_entity_overlap(
    claim_entities: set[str],
    evidence_entities: set[str],
    claims: list[str] | None = None,
    evidence_chunks: list[str] | None = None,
    user_entities: set[str] | None = None,
) -> tuple[bool, set[str], set[str]]:
    """
    Check if claim entities have overlap with evidence entities.

    Returns: (has_overlap, overlapping, uncovered)
    """
    if user_entities is None:
        user_entities = set()
    if not claim_entities:
        # No specific entities in claims - allow (generic claims)
        return True, set(), set()

    if not evidence_entities:
        # Claims have entities but no evidence - fail
        return False, set(), claim_entities

    # Direct overlap
    overlapping = claim_entities & evidence_entities

    # Fuzzy overlap: check if any claim entity is substring of evidence or vice versa
    fuzzy_overlap = set()
    for claim_ent in claim_entities:
        for ev_ent in evidence_entities:
            # Filename matches path, or path contains filename
            if claim_ent in ev_ent or ev_ent in claim_ent:
                fuzzy_overlap.add(claim_ent)
                break
            # Basename matching
            claim_base = claim_ent.rsplit("/", 1)[-1] if "/" in claim_ent else claim_ent
            ev_base = ev_ent.rsplit("/", 1)[-1] if "/" in ev_ent else ev_ent
            if claim_base == ev_base and len(claim_base) > 3:
                fuzzy_overlap.add(claim_ent)
                break

    all_covered = overlapping | fuzzy_overlap
    uncovered = claim_entities - all_covered

    # Check coverage against configurable threshold
    coverage_ratio = len(all_covered) / len(claim_entities) if claim_entities else 1.0

    # Threshold logic:
    # - If 3+ claim entities: require threshold coverage (e.g., 50%)
    # - If 1-2 claim entities: require at least 1 covered (can't split 1 entity)
    if len(claim_entities) >= 3:
        has_sufficient_coverage = coverage_ratio >= CLAIM_COVERAGE_THRESHOLD
    else:
        has_sufficient_coverage = len(all_covered) >= 1

    if has_sufficient_coverage and claims and evidence_chunks:
        equivalence_uncovered = set()
        for claim in claims:
            candidate_entities = claim_entities - user_entities
            claim_specific_entities = _entities_referenced_in_claim(claim, candidate_entities)
            if len(claim_specific_entities) < 2 and len(candidate_entities) == 2:
                # Fallback: if canonical matching misses syntax-heavy entities (e.g. /arch),
                # use the two known claim entities.
                claim_specific_entities = set(candidate_entities)
            if not _is_equivalence_claim(claim, claim_specific_entities):
                continue
            if not _has_equivalence_cooccurrence(claim_specific_entities, evidence_chunks):
                equivalence_uncovered |= claim_specific_entities
                debug_log(
                    f"Equivalence co-occurrence failed for claim: {claim[:120]} | entities={sorted(claim_specific_entities)}"
                )
        if equivalence_uncovered:
            all_covered -= equivalence_uncovered
            uncovered |= equivalence_uncovered
            has_sufficient_coverage = False

    debug_log(
        f"Overlap: {all_covered}, Uncovered: {uncovered}, Ratio: {coverage_ratio:.2f}, Threshold: {CLAIM_COVERAGE_THRESHOLD}"
    )

    return has_sufficient_coverage, all_covered, uncovered


# =============================================================================
# EVIDENCE WINDOW (v2.2.0)
# =============================================================================


def get_evidence_window(tool_sequence: list[dict]) -> list[str]:
    """
    Calculate which observation tools count as valid evidence.
    Uses Scoped Invalidation: State changes only invalidate evidence
    with overlapping Path or Terminal scope.
    """
    # List of (tool_name, path_scope, terminal_scope)
    evidence_items = []

    for tool in tool_sequence:
        if not isinstance(tool, dict):
            continue

        name = tool.get("name", "")
        path_scope, term_scope = get_tool_scope(tool)

        # Determine tool type
        is_state_changing = name in STATE_CHANGING_TOOLS
        is_observational = name in OBSERVATION_TOOLS

        # Bash special handling
        if name == "Bash":
            cmd = str(tool.get("command", "")).strip()
            # Check if bash command is read-only OR diagnostic
            is_bash_read_only = any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES)
            is_bash_diagnostic = any(cmd.startswith(p) for p in DIAGNOSTIC_BASH_PREFIXES)

            if is_bash_read_only or is_bash_diagnostic:
                # v2.4.0: Filter out trivial commands that pass prefix check
                # but provide no diagnostic value (e.g., "echo done")
                if is_trivial_bash_command(cmd):
                    is_observational = False
                    is_state_changing = False  # Trivial output commands don't change state either
                    debug_log(f"Trivial bash filtered from evidence: {cmd[:50]}")
                else:
                    is_observational = True
                    is_state_changing = False
            else:
                is_observational = False
                is_state_changing = True

        # 1. Apply Invalidation from this tool (if state changing)
        if is_state_changing:
            next_evidence = []
            for item_name, item_path, item_term in evidence_items:
                survives = True

                # Check Path Conflict (FS linkage)
                # Appplies to ALL observational tools (Bash, Read, etc)
                if paths_overlap(item_path, path_scope):
                    survives = False

                # Check Terminal Conflict (Process state linkage)
                # Applies mainly to Bash-vs-Bash in same terminal
                # Read/File tools are not affected by Terminal isolation (only FS)
                elif item_name == "Bash" and term_scope and item_term:
                    if term_scope == item_term:
                        survives = False

                if survives:
                    next_evidence.append((item_name, item_path, item_term))
            evidence_items = next_evidence

        # 2. Add as new evidence (if observational)
        if is_observational:
            evidence_items.append((name, path_scope, term_scope))

    # Return unique tool names that have at least one valid instance
    return sorted(list({item[0] for item in evidence_items}))


def get_evidence_window_with_paths(tool_sequence: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Like get_evidence_window but also returns the full tool entries for entity extraction.

    Returns: (tool_names, valid_tool_entries)
    """
    evidence_items = []  # (tool_name, path_scope, terminal_scope, full_tool_dict)

    for tool in tool_sequence:
        if not isinstance(tool, dict):
            continue

        name = tool.get("name", "")
        path_scope, term_scope = get_tool_scope(tool)

        is_state_changing = name in STATE_CHANGING_TOOLS
        is_observational = name in OBSERVATION_TOOLS

        if name == "Bash":
            cmd = str(tool.get("command", "")).strip()
            is_bash_read_only = any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES)
            is_bash_diagnostic = any(cmd.startswith(p) for p in DIAGNOSTIC_BASH_PREFIXES)
            if is_bash_read_only or is_bash_diagnostic:
                # v2.4.0: Filter out trivial commands
                if is_trivial_bash_command(cmd):
                    is_observational = False
                    is_state_changing = False
                    debug_log(f"Trivial bash filtered from evidence (with_paths): {cmd[:50]}")
                else:
                    is_observational = True
                    is_state_changing = False
            else:
                is_observational = False
                is_state_changing = True

        if is_state_changing:
            next_evidence = []
            for item in evidence_items:
                item_name, item_path, item_term, _ = item
                survives = True
                if paths_overlap(item_path, path_scope):
                    survives = False
                elif item_name == "Bash" and term_scope and item_term:
                    if term_scope == item_term:
                        survives = False
                if survives:
                    next_evidence.append(item)
            evidence_items = next_evidence

        if is_observational:
            evidence_items.append((name, path_scope, term_scope, tool))

    tool_names = sorted(list({item[0] for item in evidence_items}))
    tool_entries = [item[3] for item in evidence_items]

    return tool_names, tool_entries


def load_tool_sequence_for_evidence() -> list[dict]:
    """Load full tool sequence for evidence window calculation."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    terminal_id = (TERMINAL_ID or "").strip()

    # Preferred path: durable session-scoped evidence store
    try:
        session_id = resolve_session_id(session_id)
        if session_id:
            events = load_tool_events(session_id=session_id, limit=500)
            if events:
                return events
    except Exception:
        pass

    # Legacy fallback path: tool sequence JSON
    try:
        from tool_sequence_manager import load_tool_sequence_filtered

        return list(
            load_tool_sequence_filtered(
                session_id=session_id,
                terminal_id=terminal_id,
                require_scoped_metadata=bool(session_id or terminal_id),
            )
        )
    except Exception:
        return []


# =============================================================================
# CLAIM DETECTION PATTERNS
# =============================================================================

CLAIM_PATTERNS = [
    # File/module/class existence and content
    r"(?:file|module|class|function)\s+(?:exists|contains|has|returns|raises)",
    r"(?:file|module)\s+(?:is|was)\s+(?:located|found)\s+",
    r"(?:file|module|class|database|service)\s+(?:is|are)\s+(?:now|currently)\s+\w+",
    # ABSENCE/EXISTENCE CLAIMS (word-boundary aware)
    r"\b(?:skill|file|module|command|directory|config)\s+(?:is|are)\s+missing\b",
    r"\bno\s+(?:skill|file|module|command)\s+found\b",
    r"\b(?:skill|file|module|command)\s+not\s+found\b",
    r"\bmissing\s+[-–]\s*(?:no|not|cannot)",
    r"\bunable\s+to\s+(?:find|locate)\b",
    r"\b(?:does|do)\s+not\s+exist\b",
    r"\b(?:doesn't|don't)\s+exist\b",
    # Test/execution claims
    r"(?:tests?|pytest)\s+(?:pass|fail|succeed|run|show)",
    r"(?:tests?)\s+(?:are|is)\s+(?:passing|failing)",
    r"\d+\s+(?:passed|failed|skipped)",
    r"(?:error|exception|bug)\s+(?:is|was|occurs?|found)",
    r"(?:code|script|module)\s+(?:executes?|runs?|works?)",
    # Discovery/identification claims
    r"(?:I\s+)?(?:found|discovered|identified|located)\s+(?:the|a|an|\d+|\w+)",
    r"(?:there\s+(?:is|are)|contains?|includes?)\s+\d+\s+(?:file|error|issue|test|function|class|method|item)",
    r"there\s+are\s+\d+\s+\w+",
    # State assertions
    r"(?:is|are)\s+(?:currently|now|already)\s+(?:set|configured|enabled|disabled|connected)",
    r"(?:has\s+been|was)\s+(?:created|modified|deleted|updated|changed)",
    r"(?:is|was)\s+(?:created|modified|deleted|updated)\s+successfully",
    # Behavioral claims
    r"(?:running|executing|calling)\s+.*(?:returns?|produces?|outputs?|shows?)",
    r"(?:function|method|class)\s+(?:returns?|takes?|accepts?|raises?)",
    # Enumeration patterns (common hallucination triggers)
    r"(?:system|code|file)\s+(?:rotates?|contains?|has)\s+(?:logs?|every|\d+)",
    r"(?:these|those|the)\s+\d+\s+(?:items?|files?|functions?|errors?)",
    r"(?:file|module|class)\s+has\s+\d+\s+(?:function|method|class)",
    # Summary/aggregation claims (v2.3.0)
    r"\b(?:all|every|each)\s+(?:\d+\s+)?(?:files?|tests?|items?|issues?)\s+(?:are|is|have|has|were|was)\b",
    r"\b(?:all|everything)\s+(?:is|are)\s+(?:fixed|done|complete|working|passing)\b",
    # Equivalence/alias claims between technical identifiers (e.g. /arch == architectural-validator)
    r"(?:`[^`\n]{2,}`|/?[A-Za-z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*)\s+"
    r"(?:"
    r"equals?|equal to|equivalent to|same as|same package as|packaged as|known as|called|corresponds to|maps to|mapped to|aka|"
    r"(?:is|are|was|were)(?:\s+(?:(?:an?\s+)?alias\s+for|(?:the\s+)?same\s+as|equal to|equivalent to|called|known as|packaged as|corresponds to|maps to|mapped to))?"
    r")\s+"
    r"(?:`[^`\n]{2,}`|/?[A-Za-z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*)",
]

_CLAIM_PATTERN_RE = None


def _get_claim_patterns():
    global _CLAIM_PATTERN_RE
    if _CLAIM_PATTERN_RE is None:
        combined = "|".join(f"({p})" for p in CLAIM_PATTERNS)
        _CLAIM_PATTERN_RE = re.compile(combined, re.IGNORECASE | re.MULTILINE)
    return _CLAIM_PATTERN_RE


# =============================================================================
# EXEMPTION PATTERNS
# =============================================================================

EXEMPTION_PATTERNS = [
    # Definitional knowledge
    r"^(?:A|An|The)\s+(?:[\w\-]+\s+)*[\w\-]+\s+(?:is|are|allows?|enables?|provides?)\s+",
    # General knowledge markers
    r"(?:generally|typically|usually|commonly|by\s+default)",
    r"(?:in\s+(?:python|javascript|rust)|according\s+to)",
    # Questions/clarifications
    r"(?:what|which|how|where|when|why|should|would|could)\s+(?:\w+\s+)*\?",
    r"(?:can\s+you|would\s+you|should\s+I)",
    # Intent to verify
    r"(?:Let\s+me|I'll|I\s+will|I\s+need\s+to)\s+(?:check|verify|read|search|look|run)\b",
    # Advisory/imperative mode - recommendations about what to do, not assertions about state
    r"(?:you\s+should|start\s+by|aim\s+for|try\s+to|make\s+sure|consider)\s+",
    r"(?:phase|step)\s+\d",
    r"(?:here(?:'s| is) (?:a|the|my|how|what))",
    r"(?:I(?:'d| would)\s+(?:suggest|recommend|advise|start))",
    r"(?:when\s+you(?:'re| are)\s+ready)",
    # Already marked uncertain
    r"\[UNVERIFIED\]",
    r"\[NEEDS\s+VERIFICATION\]",
]

_EXEMPTION_PATTERN_RE = None


def _get_exemption_patterns():
    global _EXEMPTION_PATTERN_RE
    if _EXEMPTION_PATTERN_RE is None:
        combined = "|".join(f"({p})" for p in EXEMPTION_PATTERNS)
        _EXEMPTION_PATTERN_RE = re.compile(combined, re.IGNORECASE | re.MULTILINE)
    return _EXEMPTION_PATTERN_RE


# =============================================================================
# v2.7.0: CODE FABRICATION REMEDIATION
# =============================================================================


def format_code_fabrication_message(fabrications: list[str]) -> str:
    """
    Format block message for code fabrication detection.

    v2.7.0: When LLM quotes code that was never read,
    it's fabricating evidence - this must be blocked.
    """
    fabricated_list = "\n".join(f"  • {f[:80]}" for f in fabrications[:3])

    return f"""
⛔ BLOCKED: CODE FABRICATION DETECTED

You included code quotes in your response that don't match any files
you actually Read with the Read tool.

Detected fabrications:
{fabricated_list}

This is EVIDENCE FABRICATION - quoting code that was never verified.

REQUIRED ACTION:
1. NEVER quote code unless you've Read the file with the Read tool
2. If you want to reference code, use Read first, then quote the ACTUAL output
3. Mark unverified code references with [UNVERIFIED] instead of quotes
4. Respond only after reading and verifying the actual file content

📖 WHY THIS BLOCKS: Fabricating code evidence undermines trust in your
verification. You MUST read files before quoting their contents.

Config: CODE_QUOTE_VERIFICATION (v2.7.0)
"""


# =============================================================================
# PATTERN-SPECIFIC REMEDIATION
# =============================================================================

CLAIM_REMEDIATION = {
    "test_execution": {
        "patterns": [
            r"(?:tests?|pytest)\s+(?:pass|fail|succeed|run|show)",
            r"(?:tests?)\s+(?:are|is)\s+(?:passing|failing)",
            r"\d+\s+(?:passed|failed|skipped)",
        ],
        "action": "Run: Read <path> or pytest <path> -v\\nThen quote ACTUAL output: 'pytest shows: 30 passed'",
    },
    "file_state": {
        "patterns": [
            r"(?:file|module|class|function)\s+(?:exists|contains|has|returns|raises)",
            r"(?:file|module)\s+(?:is|was)\s+(?:located|found)\s+",
        ],
        "action": "Run: Read <filepath>\\nThen QUOTE the actual content, not 'contains section headings'",
    },
    "discovery": {
        "patterns": [
            r"(?:I\s+)?(?:found|discovered|identified|located)\s+(?:the|a|an|\d+|\w+)",
            r"there\s+are\s+\d+\s+\w+",
            r"(?:there\s+(?:is|are)|contains?|includes?)\s+\d+\s+(?:file|error|issue|test|function)",
        ],
        "action": "Run: Read <path> or Grep/Glob.\\nQUOTE the tool output that found it.\\nDon't summarize: show actual lines from output.",
    },
    "code_behavior": {
        "patterns": [
            r"(?:running|executing|calling)\s+.*(?:returns?|produces?|outputs?|shows?)",
            r"(?:function|method|class)\s+(?:returns?|takes?|accepts?|raises?)",
            r"(?:code|script|module)\s+(?:executes?|runs?|works?)",
        ],
        "action": 'Run: Read <source> then Bash python -c \\"<test code>\\"\\nThen quote ACTUAL execution output.',
    },
    "state_change": {
        "patterns": [
            r"(?:has\s+been|was)\s+(?:created|modified|deleted|updated|changed)",
            r"(?:is|was)\s+(?:created|modified|deleted|updated)\s+successfully",
        ],
        "action": "Run: Read <filepath>\\nThen quote specific lines showing the change.",
    },
    "error_diagnosis": {
        "patterns": [
            r"(?:error|exception|bug)\s+(?:is|was|occurs?|found)",
        ],
        "action": "Run: Read <error_source> or check logs.\\nThen quote the error lines with evidence.",
    },
    "summary_without_evidence": {
        "patterns": [
            r"(?:description|contains?|includes?|has)\s+(?:section|heading|parts?)",
            r"(?:updated|enhanced)\s+with\s+(?:detailed|more)\s+(?:descriptions?|info)",
        ],
        "action": "SHOW, DON'T SUMMARIZE. Quote actual content from TaskGet output.\\nPattern: 'Verified from TaskGet: \\\"[actual description text]\\\"'",
    },
    "scope_mismatch": {
        "patterns": [],  # Special category, not pattern-matched
        "action": "Your claims reference entities not covered by your evidence.\nRead/verify the SPECIFIC files/items mentioned in your claims.",
    },
}


def get_remediation_for_claims(
    claims: list[str], response_text: str, scope_mismatch: bool = False
) -> tuple[str, str]:
    """Match detected claims to remediation actions."""
    if scope_mismatch:
        return "scope_mismatch", CLAIM_REMEDIATION["scope_mismatch"]["action"]

    response_lower = response_text.lower()

    is_summary = any(
        word in response_lower
        for word in [
            "complete",
            "summary",
            "done",
            "finished",
            "implemented",
            "all tests",
            "tdd cycle",
            "final",
        ]
    )

    for category, config in CLAIM_REMEDIATION.items():
        for pattern in config["patterns"]:
            if re.search(pattern, response_text, re.IGNORECASE):
                action = config["action"]
                if is_summary:
                    action = f"⚠️ SUMMARY DETECTED - Re-verify before claiming.\n\n{action}"
                return category, action

    return (
        "unspecified",
        "Use Read, Bash, or Grep to verify your claim.\nShow tool output as evidence.",
    )


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def detect_claims(response_text: str) -> list[str]:
    """Find factual claims about code/files/state in response."""
    if not response_text:
        return []

    # Strip structural formatting before claim detection
    cleaned_text = strip_non_claim_lines(response_text)

    # Filter out question lines (questions are not factual claims)
    non_question_lines = [
        line for line in cleaned_text.splitlines() if not is_question(line.strip())
    ]
    cleaned_text = "\n".join(non_question_lines)

    pattern = _get_claim_patterns()
    matches = pattern.findall(cleaned_text)

    claims = []
    for match in matches:
        if isinstance(match, tuple):
            for m in match:
                if m and m not in claims:
                    claims.append(m)
        elif match and match not in claims:
            claims.append(match)

    return claims[:5]


def is_exempt_response(response_text: str) -> bool:
    """Check if response is exempt from verification requirement.

    v2.5.1: Advisory override — when exemption signals (advisory, imperative,
    general-knowledge markers) outnumber claim signals, the response is treated
    as advisory and exempt.  This prevents false positives where "get tests
    passing" inside a recommendation list is flagged as a factual claim.
    """
    if not response_text:
        return True

    text = response_text.strip()

    if len(text) < 30:
        claims = detect_claims(text)
        if claims:
            return False
        return True

    pattern = _get_exemption_patterns()
    exemption_matches = list(pattern.finditer(text))

    if exemption_matches:
        claims = detect_claims(text)
        if not claims:
            return True
        # Advisory override: if exemption signals >= claim signals, treat as advisory.
        # Rationale: a response with 5 advisory markers and 1 incidental claim-pattern
        # match is giving advice, not asserting facts about the codebase.
        if len(exemption_matches) >= len(claims):
            debug_log(
                f"Advisory override: {len(exemption_matches)} exemptions >= {len(claims)} claims"
            )
            return True
        return False

    return False


def evaluate_response(
    response_text: str,
    tools_used: list[str],
    tool_sequence: list[dict] = None,
    user_entities: set[str] = None,
    input_data: dict = None,
) -> dict:
    """
    Main evaluation function.

    v2.3.0: Now checks for CLAIM-EVIDENCE SCOPE OVERLAP, not just tool presence.
    v2.4.1: Theater detection runs on SUCCESS claims even without entity claims.
    v2.5.1: Phase 2 - Check verification cache before full verification.
    v2.6.0: User-provided entities excluded from scope mismatch checks.

    Returns:
        dict with decision (block/allow), reason, and optional message/claims
    """
    if user_entities is None:
        user_entities = set()
    if input_data is None:
        input_data = {}
    flags = (
        summarize_response_claim_kinds(response_text)
        if CLAIM_CLASSIFIER_AVAILABLE
        else {
            "has_external_fact": has_external_claim(response_text),
            "has_meta": False,
            "has_self_explanation": False,
        }
    )
    # Legacy path
    # Check for entity claims (specific claims about files, functions, etc.)
    claims = detect_claims(response_text)

    # Phase 2: Check verification cache before full verification
    # If all claims are cached and valid, skip full verification
    if claims:
        all_cached = True
        for claim in claims:
            if not is_claim_cached(claim):
                all_cached = False
                break

        if all_cached:
            debug_log(f"All {len(claims)} claims found in cache - skipping verification")
            return {
                "decision": "allow",
                "reason": "CACHED_VERIFICATION",
                "evidence_tools": tools_used,
                "claims_cached": len(claims),
            }

    # Preferred mode: unified claim verifier (single source of truth).
    if UNIFIED_VERIFIER_ENABLED:
        try:
            from unified_claim_verifier import evaluate_claims

            result = evaluate_claims(
                response_text=response_text,
                tools_used=tools_used,
                session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
                tool_sequence=tool_sequence,
                user_entities=user_entities,
            )
            if result.get("decision") == "block":
                missing = result.get("missing_claims", [])
                if result.get("reason") == "NO_EVIDENCE":
                    return {
                        "decision": "block",
                        "reason": "NO_EVIDENCE",
                        "message": format_block_message(
                            missing or detect_claims(response_text), response_text, False
                        ),
                        "claims_detected": missing or detect_claims(response_text),
                    }
                return {
                    "decision": "block",
                    "reason": "UNVERIFIED_CLAIMS",
                    "message": format_block_message(
                        missing or detect_claims(response_text), response_text, True
                    ),
                    "claims_detected": missing or detect_claims(response_text),
                    "uncovered_entities": result.get("evidence_entities", []),
                    "evidence_entities": result.get("evidence_entities", []),
                }
            # Preserve the unified verifier's reason for allow cases
            # (e.g., NO_CLAIMS should be preserved, not changed to CLAIMS_VERIFIED)
            # Phase 2: Cache verified claims from unified verifier
            verified_claims = result.get("verified_claims", [])
            if verified_claims:
                cache_verified_claims(verified_claims, time.time())

            return {
                "decision": "allow",
                "reason": result.get("reason", "CLAIMS_VERIFIED"),
                "evidence_tools": tools_used,
            }
        except Exception:
            # Fall through to legacy logic if unified verifier fails.
            pass

    # Legacy path
    # Check for entity claims (specific claims about files, functions, etc.)
    claims = detect_claims(response_text)

    # Check for success claims ("it's fixed", "tests pass", etc.)
    # v2.4.1: Success claims trigger theater detection even without entity claims
    success_claims_present = has_success_claims(response_text)

    if not claims and not success_claims_present:
        # No entity claims AND no success claims - nothing to verify
        return {"decision": "allow", "reason": "NO_CLAIMS"}

    # Load tool sequence if not provided
    if tool_sequence is None:
        tool_sequence = load_tool_sequence_for_evidence()

    # Get valid evidence window with full tool entries
    evidence_tools, valid_tool_entries = get_evidence_window_with_paths(tool_sequence)

    # Fallback: also check this-turn tools
    if tools_used:
        for t in tools_used:
            if t in OBSERVATION_TOOLS and t not in evidence_tools:
                evidence_tools.append(t)

    if not evidence_tools:
        # No observation tools at all - block
        return {
            "decision": "block",
            "reason": "NO_EVIDENCE",
            "message": format_block_message(claims, response_text, False),
            "claims_detected": claims,
        }

    # v2.4.0: VERIFICATION THEATER DETECTION
    # If response claims success but evidence is only weak commands (ls, dir, tree)
    # this is likely Verification Theater - claiming fix based on irrelevant observation
    if has_success_claims(response_text):
        # Check if ALL bash evidence is weak (non-diagnostic)
        bash_entries = [t for t in valid_tool_entries if t.get("name") == "Bash"]
        non_bash_evidence = [t for t in valid_tool_entries if t.get("name") != "Bash"]

        has_strong_evidence = len(non_bash_evidence) > 0  # Read, Grep, etc. are strong

        # Check bash commands for diagnostic value
        for bash_tool in bash_entries:
            cmd = str(bash_tool.get("command", "")).strip()
            if is_diagnostic_bash_command(cmd) and not is_weak_evidence_command(cmd):
                has_strong_evidence = True
                break

        # v2.4.0: Also detect when Bash was in tools_used but got filtered entirely
        # This catches the case where only trivial commands were run
        bash_in_fallback = "Bash" in evidence_tools and len(bash_entries) == 0

        if not has_strong_evidence:
            if bash_entries:
                # Weak bash evidence for success claims - Verification Theater
                weak_cmds = [str(t.get("command", ""))[:40] for t in bash_entries]
                debug_log(
                    f"Verification Theater detected: success claims with weak evidence: {weak_cmds}"
                )
                return {
                    "decision": "block",
                    "reason": "VERIFICATION_THEATER",
                    "message": format_verification_theater_message(claims, weak_cmds),
                    "claims_detected": claims,
                    "weak_commands": weak_cmds,
                }
            elif bash_in_fallback:
                # Bash was used but ALL commands were trivial (filtered out)
                # This is theater - the agent ran commands but none had diagnostic value
                debug_log("Verification Theater detected: Bash used but all commands were trivial")
                return {
                    "decision": "block",
                    "reason": "VERIFICATION_THEATER",
                    "message": format_verification_theater_message(
                        claims, ["(all bash commands were trivial - echo, mkdir, etc.)"]
                    ),
                    "claims_detected": claims,
                    "trivial_commands_filtered": True,
                }

        # v2.8.0: POST-CHANGE VERIFICATION CHECK
        # Even with strong evidence, success/completion claims require that
        # at least some observation happened AFTER the last state change.
        # Pre-change reads are research, not verification of correctness.
        # Principle: "completion claims require post-change verification evidence"
        if has_strong_evidence and tool_sequence:
            if not has_post_change_verification(tool_sequence):
                debug_log(
                    "Verification Theater detected: strong evidence but all observations are pre-change"
                )
                return {
                    "decision": "block",
                    "reason": "VERIFICATION_THEATER",
                    "message": (
                        "🎭 BLOCKED: COMPLETION CLAIM WITHOUT POST-CHANGE VERIFICATION\n\n"
                        "You claimed success/completion, and you do have observation evidence — "
                        "but all of it is from BEFORE your last Edit/Write.\n\n"
                        "Pre-change reads are research, not verification.\n\n"
                        "To verify your changes are correct, you need to:\n"
                        "1. Re-read the files you changed to confirm the edits are correct, or\n"
                        "2. Run tests (pytest, /test, /verify) to confirm behavior, or\n"
                        "3. Rephrase as hypothesis: 'I believe the changes are correct' "
                        "instead of asserting completion.\n\n"
                        "Principle: completion claims require post-change verification evidence."
                    ),
                    "claims_detected": claims,
                    "pre_change_only": True,
                }

    # v2.3.0: CLAIM-SCOPE VERIFICATION
    # v2.5.0: Claim-local entity extraction + traceable error messages
    # v2.7.0: Code quote verification (T-006) - Check BEFORE entity overlap
    # This prevents fabricated code from being treated as verified claims
    has_code_quotes, fabrications = verify_code_quotes(response_text, tool_sequence or [])

    if has_code_quotes and fabrications:
        # Code quotes detected that don't match Read files - block
        debug_log(f"Code quote verification failed: {len(fabrications)} fabrications detected")
        return {
            "decision": "block",
            "reason": "CODE_FABRICATION",
            "message": format_code_fabrication_message(fabrications),
            "claims_detected": claims,
            "fabricated_quotes": fabrications,
        }

    # v2.6.0: User-provided entities excluded from novel claim check
    if CLAIM_SCOPE_CHECK_ENABLED:
        # Extract entities from claims (context-windowed, not full response)
        claim_entities = extract_entities_from_claims(claims, response_text)

        # v2.6.0: Remove entities that came from the user's message.
        # If the user pasted a transcript, code, or file paths, Claude
        # referencing those isn't a novel claim requiring verification.
        if user_entities:
            novel_claim_entities = claim_entities - user_entities
            debug_log(
                f"User entity exclusion: {len(claim_entities)} claim entities, "
                f"{len(user_entities)} user entities, "
                f"{len(novel_claim_entities)} novel after exclusion"
            )
            claim_entities = novel_claim_entities

        # Extract entities from evidence
        evidence_entities = extract_entities_from_evidence(valid_tool_entries)
        evidence_chunks = extract_evidence_chunks(valid_tool_entries)

        # Check overlap
        has_overlap, covered, uncovered = check_entity_overlap(
            claim_entities,
            evidence_entities,
            claims=claims,
            evidence_chunks=evidence_chunks,
            user_entities=user_entities,
        )

        if not has_overlap and claim_entities:
            # Build per-claim entity map for traceability
            claim_entity_map = {}
            for claim in claims:
                claim_ents = extract_entities_from_text(claim)
                ctx = _get_claim_context_window(claim, response_text)
                claim_ents |= extract_entities_from_text(ctx)
                # v2.6.0: Also subtract user entities from per-claim trace
                claim_ents -= user_entities
                claim_uncovered = claim_ents - (covered | evidence_entities)
                if claim_uncovered:
                    claim_entity_map[claim] = claim_uncovered

            # v2.6.0: If all claims resolved after user entity exclusion, allow
            if not claim_entity_map:
                debug_log("All scope mismatches resolved by user entity exclusion")
                return {
                    "decision": "allow",
                    "reason": "USER_PROVIDED_ENTITIES",
                    "evidence_tools": evidence_tools,
                }

            if CLAIM_CLASSIFIER_AVAILABLE:
                # Use standardized block payload with observability
                return make_block_payload(
                    reason=format_scope_mismatch_message(
                        claims, claim_entity_map, uncovered, evidence_entities, input_data
                    ),
                    data=input_data,
                    flags=flags,
                    hook_name="assumption_audit_v2",
                )
            else:
                # Fallback to legacy format
                return {
                    "decision": "block",
                    "reason": "SCOPE_MISMATCH",
                    "message": format_scope_mismatch_message(
                        claims, claim_entity_map, uncovered, evidence_entities, input_data
                    ),
                    "claims_detected": claims,
                    "uncovered_entities": list(uncovered),
                    "evidence_entities": list(evidence_entities),
                }

    # Evidence exists and covers claims (or scope check disabled) - allow
    # Phase 2: Cache verified claims for future invocations
    if claims:
        cache_verified_claims(claims, time.time())

    return {
        "decision": "allow",
        "reason": "VERIFIED" if not CLAIM_SCOPE_CHECK_ENABLED else "SCOPE_VERIFIED",
        "evidence_tools": evidence_tools,
    }


def format_block_message(
    claims: list[str],
    response_text: str = "",
    scope_mismatch: bool = False,
    uncovered: set[str] = None,
    evidence: set[str] = None,
) -> str:
    """Format the block message with pattern-specific remediation."""
    category, action = get_remediation_for_claims(claims, response_text, scope_mismatch)

    claim_list = "\n".join(f'  • "{c}"' for c in claims[:3])

    msg = f"""
⛔ BLOCKED: Unverified {category.replace('_', ' ').title()} Claim

Detected claims without matching evidence:
{claim_list}
"""

    if scope_mismatch and uncovered:
        uncovered_list = ", ".join(list(uncovered)[:5])
        msg += f"""
SCOPE MISMATCH: Your claims reference:
  {uncovered_list}

But your evidence only covers:
  {", ".join(list(evidence)[:5]) if evidence else "(none)"}
"""

    msg += f"""
REQUIRED ACTION:
{action}

Do NOT:
- Rephrase the same claim
- Add [UNVERIFIED] and proceed
- Describe what you "would" find

Verify first. Then respond.

📖 WHY THIS HAPPENED: See P:\\.claude\\hooks\\docs\\claim_verification_troubleshooting.md
   Config: CLAIM_SCOPE_CHECK_ENABLED, CLAIM_COVERAGE_THRESHOLD (current: {CLAIM_COVERAGE_THRESHOLD})
"""
    return msg


def format_scope_mismatch_message(
    claims: list[str],
    claim_entity_map: dict[str, set[str]],
    uncovered: set[str],
    evidence: set[str],
    data: dict = None,
) -> str:
    """
    v2.5.0: Traceable SCOPE_MISMATCH message.

    Shows which claim references which unverified entities,
    so the LLM (and user) can see exactly what triggered the block.
    """
    if data is None:
        data = {}
    # Build per-claim trace lines
    trace_lines = []
    for claim_text, ents in list(claim_entity_map.items())[:3]:
        # v2.3.1: Hypothesis-aware gating
        # Check if claim is explicitly marked as hypothesis/possible gap
        if is_marked_as_hypothesis(claim_text):
            # This is explicitly labeled as a hypothesis/possible gap.
            # Track or allow instead of blocking hard.
            # You may log it, but do not emit a BLOCK decision solely because it's unverified.
            continue

        # General principle: promotion, blame/history detection
        # These helpers apply uniformly (gaps, success, blame, etc.)
        is_promotion = is_promoted_fact(claim_text)
        talks_about_history_or_blame = mentions_history_or_blame(claim_text)

        # 1. Hypotheses that stay hypotheses are not blocked just for being unverified
        #    (already handled by is_marked_as_hypothesis check above)
        #
        # 2. Promoted facts (gaps, success, blame, "already handled")
        #    are high-risk and should go through full verification.
        #    (No change needed - existing external_fact verification logic handles this)
        #
        # 3. History/blame claims should only be made when user asked for them
        #    AND supporting evidence (diffs/history) has been consulted.
        # Check if data has user_asked_for_history and history_evidence flags
        user_asked_for_history = data.get("user_asked_for_history", False)
        has_history_evidence = bool(data.get("history_evidence"))

        if talks_about_history_or_blame and not (user_asked_for_history and has_history_evidence):
            # Unrequested, unsupported blame/history statements are blocked.
            # Focus on current state, not speculation about causes.
            # This is a candidate for BLOCK or at least WARN.
            # For now, track as high-risk and let existing verification handle it.
            pass  # Existing scope check will catch missing evidence

        ent_list = ", ".join(sorted(ents)[:5])
        # Truncate long claim text for readability
        short_claim = claim_text[:80] + "..." if len(claim_text) > 80 else claim_text
        trace_lines.append(f'  Claim: "{short_claim}"\n    Unverified: [{ent_list}]')

    trace_block = "\n".join(trace_lines) if trace_lines else "  (no per-claim trace available)"

    evidence_sample = ", ".join(sorted(evidence)[:5]) if evidence else "(none)"

    return f"""
⛔ BLOCKED: SCOPE_MISMATCH — claims reference entities not covered by evidence

{trace_block}

Evidence covers: [{evidence_sample}]

REQUIRED ACTION:
Read/verify the specific files or entities mentioned in the claims above.
Quote actual tool output as evidence for your claims.

Do NOT:
- Rephrase the same claim
- Add [UNVERIFIED] and proceed
- Describe what you "would" find

Verify first. Then respond.

📖 Config: CLAIM_SCOPE_CHECK_ENABLED, CLAIM_COVERAGE_THRESHOLD (current: {CLAIM_COVERAGE_THRESHOLD})
"""


def format_verification_theater_message(claims: list[str], weak_commands: list[str]) -> str:
    """
    Format block message for Verification Theater detection.

    Verification Theater = claiming success based on trivial/weak commands
    that cannot actually verify the claim.
    """
    claim_list = "\n".join(f'  • "{c}"' for c in claims[:3])
    cmd_list = "\n".join(f"  • {c}..." for c in weak_commands[:3])

    return f"""
🎭 BLOCKED: VERIFICATION THEATER DETECTED

You claimed success:
{claim_list}

But your only "evidence" was:
{cmd_list}

These commands cannot verify a fix or confirm correctness.

REQUIRED ACTION:
Run a REAL verification:
  • pytest <test_file>     - Run actual tests
  • python <script>        - Execute the code
  • cat <file> | grep <x>  - Inspect specific output
  • git diff               - Show actual changes

Commands that DON'T verify:
  • echo "done" / echo "test"
  • ls / dir (shows structure, not behavior)
  • mkdir / touch / cp (file manipulation)

You claimed it works. PROVE it works.

📖 WHY: Trivial commands masquerading as verification undermine reliability.
   This is v2.4.0 anti-theater enforcement.
"""


def format_hook_output(
    decision: str, reason: str, message: str = "", claims: list = None, **kwargs
) -> str:
    """Format output for hook protocol."""
    # Map internal decision values to schema-compliant values
    # Internal: "allow" | "block" → Schema: "approve" | "block"
    schema_decision = "approve" if decision == "allow" else "block"

    output = {"decision": schema_decision, "reason": reason}

    if decision == "block":
        output["message"] = message
        if claims:
            output["claims_detected"] = claims
        for k, v in kwargs.items():
            if v:
                output[k] = v

    return json.dumps(output)


# =============================================================================
# LOGGING
# =============================================================================


def log_event(event_type: str, data: dict):
    """Log events for analysis."""
    if not ENABLED:
        return

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "terminal_id": TERMINAL_ID,
            "version": "2.4.2",
            **data,
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# =============================================================================
# VERIFICATION STATE PERSISTENCE (Phase 2)
# =============================================================================

VERIFICATION_CACHE_FILE = STATE_DIR / "verification_cache.json"


def claim_hash(claim: str) -> str:
    """
    Create a unique identifier for a claim using MD5 hash.

    Args:
        claim: The claim text to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.md5(claim.strip().lower().encode()).hexdigest()


def cache_verified_claims(claims: list[str], timestamp: float = None) -> bool:
    """
    Cache verified claims with timestamp for persistence across hook invocations.

    Args:
        claims: List of verified claim strings to cache
        timestamp: Optional timestamp (defaults to current time)

    Returns:
        True if caching succeeded, False otherwise
    """
    if not claims:
        return True  # Nothing to cache is not an error

    if timestamp is None:
        timestamp = time.time()

    try:
        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        cache = {}
        if VERIFICATION_CACHE_FILE.exists():
            try:
                with open(VERIFICATION_CACHE_FILE) as f:
                    cache = json.load(f)
            except json.JSONDecodeError:
                cache = {}

        # Update cache with new verified claims
        for claim in claims:
            claim_id = claim_hash(claim)
            cache[claim_id] = {"claim": claim, "verified_at": timestamp}

        # Write updated cache
        with open(VERIFICATION_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

        debug_log(f"Cached {len(claims)} verified claims")
        return True

    except OSError as e:
        debug_log(f"Failed to cache verified claims: {e}")
        return False


def is_claim_cached(claim: str, max_age_seconds: float = 3600) -> bool:
    """
    Check if a claim has been previously verified and cached.

    Args:
        claim: The claim text to check
        max_age_seconds: Maximum age of cache entry in seconds (default 1 hour)

    Returns:
        True if claim is cached and within max age, False otherwise
    """
    try:
        if not VERIFICATION_CACHE_FILE.exists():
            return False

        with open(VERIFICATION_CACHE_FILE) as f:
            cache = json.load(f)

        claim_id = claim_hash(claim)
        if claim_id not in cache:
            return False

        entry = cache[claim_id]
        verified_at = entry.get("verified_at", 0)
        age = time.time() - verified_at

        is_valid = age <= max_age_seconds
        if is_valid:
            debug_log(f"Claim found in cache (age: {age:.0f}s)")

        return is_valid

    except (OSError, json.JSONDecodeError) as e:
        debug_log(f"Failed to check claim cache: {e}")
        return False


def invalidate_cache_on_state_change() -> bool:
    """
    Invalidate the verification cache when state changes occur.

    This should be called by Write/Edit hooks when files are modified,
    as cached verifications may no longer be valid.

    Returns:
        True if invalidation succeeded, False otherwise
    """
    try:
        if not VERIFICATION_CACHE_FILE.exists():
            return True  # No cache to invalidate is not an error

        VERIFICATION_CACHE_FILE.unlink()
        debug_log("Verification cache invalidated due to state change")
        return True

    except OSError as e:
        debug_log(f"Failed to invalidate cache: {e}")
        return False


# =============================================================================
# HOOK ENTRY POINT
# =============================================================================


def extract_response_and_tools(input_data: dict) -> tuple[str, list[str]]:
    """Extract response text and tools used from hook input."""
    response_text = ""
    tools_used = []

    response_text = input_data.get("response", "")

    if not response_text:
        transcript_path = input_data.get("transcript_path", "")

        if transcript_path:
            try:
                content = Path(transcript_path).read_text(encoding="utf-8")
                lines = content.strip().split("\n")

                for line in reversed(lines):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "assistant":
                            msg = entry.get("message", {})
                            for block in msg.get("content", []):
                                if block.get("type") == "text":
                                    response_text += block.get("text", "")
                                elif block.get("type") == "tool_use":
                                    tools_used.append(block.get("name", ""))
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

    input_tools = input_data.get("tools_used", [])
    if input_tools:
        for tool in input_tools:
            name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
            if name and name not in tools_used:
                tools_used.append(name)

    if not tools_used:
        try:
            session_id = resolve_session_id(os.environ.get("CLAUDE_SESSION_ID", ""))
            if session_id:
                for tool in load_tool_events(session_id, limit=200):
                    name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
                    if name and name not in tools_used:
                        tools_used.append(name)
        except Exception:
            pass

    if not tools_used:
        try:
            from tool_sequence_manager import load_tool_sequence

            for tool in load_tool_sequence():
                name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
                if name and name not in tools_used:
                    tools_used.append(name)
        except Exception:
            pass

    return response_text, tools_used


def main():
    """Hook entry point."""
    start_time = time.time()

    if not ENABLED:
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    try:
        raw_input = sys.stdin.read()
        # Strip BOM that PowerShell may prepend
        clean_input = raw_input.lstrip("\ufeff")
        input_data = json.loads(clean_input)
    except json.JSONDecodeError as e:
        log_event("json_error", {"error": str(e)})
        print(format_hook_output(decision="allow", reason="JSON_ERROR"))
        sys.exit(0)

    if input_data.get("stop_hook_active", False):
        print(format_hook_output(decision="allow", reason="LOOP_PREVENTION"))
        sys.exit(0)

    response_text, tools_used = extract_response_and_tools(input_data)
    response_text, tools_used = extract_response_and_tools(input_data)

    # Get transcript for meta-conversation gate
    transcript = input_data.get("transcript", [])

    if not response_text:
        print(format_hook_output(decision="allow", reason="NO_RESPONSE_TEXT"))
        sys.exit(0)

    # === POST-EDIT READBACK EXTRACTION ===
    # Extract post_edit_readbacks for edit-result claim verification
    post_edit_readbacks = input_data.get("post_edit_readbacks") or []
    has_post_edit_read = bool(post_edit_readbacks)

    # === CLAIM CLASSIFICATION & WORKLOAD TYPE ===
    workload_type = input_data.get("workload_type", "unknown")
    is_docs_only = workload_type == "docs"

    # === EDIT-RESULT CLAIM PATTERNS ===
    # Patterns for claims about edit results that require post_edit_readbacks
    EDIT_RESULT_PATTERNS = [
        "the edit was applied correctly",
        "the typo is present",
        "the typo is now fixed",
        "the file now shows",
        "the change has been applied",
        "successfully edited",
        "the edit was successful",
    ]

    if CLAIM_CLASSIFIER_AVAILABLE:
        flags = summarize_response_claim_kinds(response_text)
        has_ext = flags["has_external_fact"]
        has_meta_or_self = flags["has_meta"] or flags["has_self_explanation"]
    else:
        # Fallback: use existing pattern-based detection
        is_meta = is_meta_conversation(transcript) or is_self_referential(response_text)
        has_external_claim_result = has_external_claim(response_text)
        has_meta_or_self = is_meta
        has_ext = has_external_claim_result
        flags = {
            "has_external_fact": has_ext,
            "has_meta": is_meta_conversation(transcript),
            "has_self_explanation": is_self_referential(response_text),
        }

    # === DOCS-ONLY SOFTENING ===
    # Documentation-only work without external fact claims → downgrade to WARN
    if is_docs_only and not has_ext:
        # Documentation-only change; skip strict coverage enforcement
        if DEBUG:
            log_event(
                "docs_mode_softened",
                {
                    "workload_type": workload_type,
                    "has_external_fact": has_ext,
                },
            )
        print(
            format_hook_output(
                decision="allow",
                reason="DOCS_MODE_SOFTENED",
                note="Docs-only change; skipping strict coverage enforcement.",
            )
        )
        sys.exit(0)

    # === META-CONVERSATION GATE ===
    # Skip verification for pure meta/self-explanation WITHOUT external claims
    if has_meta_or_self and not has_ext:
        # Pure meta/process/self-report → skip this hook entirely
        debug_log("Meta-conversation/self-referential gate: skipping claim verification")
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

    # === EDIT-RESULT CLAIM GATE ===
    # Check for edit-result claims ("the edit was applied correctly", "typo is now fixed")
    # These require post_edit_readbacks from PostToolUse_edit_verifier.py
    response_lower = response_text.lower()
    is_edit_result_claim = any(pattern in response_lower for pattern in EDIT_RESULT_PATTERNS)

    if is_edit_result_claim and not has_post_edit_read:
        # Edit-result claim without readback evidence → require explicit Read
        debug_log("Edit-result claim detected without post_edit_readbacks")
        print(
            format_hook_output(
                decision="block",
                reason="NO_POST_EDIT_READ",
                message=(
                    "Claim about edit result requires verification.\n\n"
                    'You said something like "the edit was applied correctly" or "the typo is now fixed" '
                    "without performing a Read in this turn.\n\n"
                    "Please:\n"
                    "1. Read the file you just edited\n"
                    "2. Then describe what you see, quoting the actual content"
                ),
                claims_detected=[p for p in EDIT_RESULT_PATTERNS if p in response_lower],
            )
        )
        sys.exit(2)

    # === GENERAL PRINCIPLE: EVIDENCE-BOUND, GOAL-BOUND ANSWERS ===
    # Check claims for promoted facts and history/blame BEFORE full verification
    if CLAIM_CLASSIFIER_AVAILABLE:
        claims = detect_claims(response_text)
        user_asked_for_history = bool(input_data.get("user_asked_for_history", False))
        has_history_evidence = bool(input_data.get("history_evidence", False))
        evidence_items = input_data.get("evidence_items") or []
        has_any_evidence = bool(evidence_items)

        for claim in claims:
            claim_text = claim if isinstance(claim, str) else ""
            kind = classify_claim_text(claim_text)

            is_hypothesis = is_marked_as_hypothesis(claim_text)
            is_promotion = is_promoted_fact(claim_text)
            talks_about_history_or_blame = mentions_history_or_blame(claim_text)

            # 1) Hypotheses are allowed as hypotheses.
            if is_hypothesis and not is_promotion:
                # Optionally log, but do not BLOCK solely for lack of evidence.
                continue

            # 2) Promoted facts (success/gap/absence/"already handled"/"pre-existing")
            #    are high-risk and must have evidence from this turn.
            if is_promotion:
                if not has_any_evidence:
                    # Keep your existing BLOCK logic for external_fact claims here.
                    # For example, require a Read/tool output that mentions
                    # same entities as this claim.
                    pass  # (hook's existing external_fact handling applies)
                # If you already have evidence, fall through to your normal checks.

            # 3) History/blame claims require explicit user request + evidence.
            #    EXCEPTION: Test/coverage reports use classification language
            #    ("pre-existing gaps") as factual reporting, not blame-shifting.
            if talks_about_history_or_blame:
                if is_test_report_context(response_text):
                    debug_log(
                        f"History/blame term in test-report context, skipping: {claim_text[:80]}"
                    )
                    continue
                if not (user_asked_for_history and has_history_evidence):
                    # Do not allow unrequested, unsupported blame/history statements.
                    # Treat this as BLOCK or strip these claims from the answer.
                    debug_log(f"History/blame claim without user request: {claim_text[:80]}")
                    print(
                        format_hook_output(
                            decision="block",
                            reason="HISTORY_BLAME_CLAIM",
                            message=(
                                "Unrequested history or blame statement detected.\n\n"
                                'You said something like "pre-existing", "introduced by this change", '
                                'or "unrelated to my edits" without the user asking for history/blame.\n\n'
                                "Please:\n"
                                "1. Remove history/blame claims from your response\n"
                                "2. Focus on current state and what is needed for the user's goal"
                            ),
                            claims_detected=[claim],
                        )
                    )
                    sys.exit(2)

    # Otherwise proceed with existing claim evaluation logic
    # (External claims present OR not meta = run full verification)

    # v2.6.0: Extract user-provided entities to avoid false positives
    # when Claude references content user pasted
    user_entities = extract_user_message_entities(input_data)

    result = evaluate_response(
        response_text, tools_used, user_entities=user_entities, input_data=input_data
    )

    # Meta-explanation bypass: downgrade blocks when discussing hook/system internals
    if result["decision"] == "block":
        try:
            from meta_explanation_detector import is_meta_explanation

            if is_meta_explanation(response_text):
                debug_log("Meta explanation detected, downgrading block to allow")
                result = {
                    "decision": "allow",
                    "reason": "META_WARN",
                }
        except ImportError:
            pass

    # Direct question fast-path: prioritize answering user questions over
    # claim-scope/no-evidence bookkeeping blocks.
    if result["decision"] == "block" and result.get("reason") in {
        "SCOPE_MISMATCH",
        "NO_EVIDENCE",
        "UNVERIFIED_CLAIMS",
    }:
        try:
            if is_direct_user_question(input_data) and not has_success_claims(response_text):
                debug_log("Direct question detected, downgrading scope/evidence block to allow")
                result = {
                    "decision": "allow",
                    "reason": "DIRECT_QUESTION_FAST_PATH",
                }
        except Exception:
            pass

    elapsed_ms = (time.time() - start_time) * 1000

    log_event(
        result["decision"],
        {
            "tools_used": tools_used,
            "claims": result.get("claims_detected", []),
            "duration_ms": elapsed_ms,
            "response_snippet": response_text[:100] if response_text else "",
            "scope_check": CLAIM_SCOPE_CHECK_ENABLED,
            "uncovered": result.get("uncovered_entities", []),
        },
    )

    print(
        format_hook_output(
            decision=result["decision"],
            reason=result["reason"],
            message=result.get("message", ""),
            claims=result.get("claims_detected"),
            uncovered_entities=result.get("uncovered_entities"),
            evidence_entities=result.get("evidence_entities"),
        )
    )

    sys.exit(0 if result["decision"] == "allow" else 2)


# =============================================================================
# v2.5.0: NEW ENTITY EXTRACTION SYSTEM
# =============================================================================
# Applied AFTER all function definitions to properly override them.
# Set USE_NEW_ENTITY_EXTRACTION=false to disable.

# =============================================================================
# v2.7.0: CODE QUOTE VERIFICATION
# =============================================================================

# v2.7.0: Code quote verification
# Detects when response contains quoted code that doesn't match actual file contents
# Prevents LLM from fabricating code that was never read

# Pattern to match ```code``` blocks (with or without language identifier)
# Uses [\s\S]+? which matches whitespace followed by non-whitespace (the code)
# Then manually find the closing backticks position
CODE_QUOTE_PATTERN = re.compile(
    r"```(?:[a-z]+\n)?([\s\S]+?)```",
    re.IGNORECASE,
)

INLINE_CODE_PATTERN = re.compile(
    r"`([^`\n]{3,})`",
    re.IGNORECASE,
)


def verify_code_quotes(response_text: str, tool_sequence: list[dict]) -> tuple[bool, list[str]]:
    """
    v2.7.0: Verify that code quotes in response match actual file contents.

    Prevents fabrication of code that was never read. When response contains
    quoted code blocks, this function checks if any Read tool actually read
    those files. If not, the code is likely fabricated.

    Args:
        response_text: The assistant's response text to check
        tool_sequence: List of tool invocations in current turn

    Returns:
        (has_quotes, fabrications) where:
        - has_quotes: True if code quotes found
        - fabrications: List of code snippets that don't match Read files
    """
    import re

    if not response_text:
        return False, []

    # Extract code quotes from response
    code_quotes = []

    # Check for ```code``` blocks
    for match in CODE_QUOTE_PATTERN.finditer(response_text):
        quoted_code = match.group(1).strip()
        if quoted_code:
            code_quotes.append(("```", quoted_code))

    # Check for `inline code` quotes
    for match in INLINE_CODE_PATTERN.finditer(response_text):
        quoted_code = match.group(1).strip()
        if quoted_code:
            code_quotes.append(("`", quoted_code))

    if not code_quotes:
        return False, []

    # Get content from Read tools to verify quotes
    # Store both file paths AND the actual content read from them
    read_contents = {}  # file_path -> content read
    for tool in tool_sequence:
        if isinstance(tool, dict) and tool.get("name") == "Read":
            file_path = tool.get("command", tool.get("input", {})).get("file_path", "")
            # Extract the actual read content from tool output/response
            tool_output = tool.get("response", tool.get("output", {}))
            if isinstance(tool_output, dict):
                content = tool_output.get("content", "")
            else:
                content = str(tool_output) if tool_output else ""

            if file_path and content:
                normalized_path = file_path.replace("\\", "/").lower()
                read_contents[normalized_path] = content

    # Check each quote against actually-read file contents
    fabrications = []
    for quote_type, quoted_code in code_quotes:
        # Normalize the quoted code for comparison
        normalized_quote = quoted_code.strip().lower()

        # Quote is verified if:
        # 1. It appears in any Read tool's output content, OR
        # 2. It's very short (< 30 chars - likely variable/function name)
        is_verified = (
            len(normalized_quote) < 30  # Short snippets are OK
            or any(
                normalized_quote in read_content.lower() for read_content in read_contents.values()
            )
        )

        # For code with function/class definitions, require stronger verification
        if not is_verified:
            func_def_pattern = r"\b(?:def|class|async def)\s+[\w_]+"
            has_func_def = re.search(func_def_pattern, quoted_code, re.IGNORECASE)
            if has_func_def:
                # Function/class definition without matching Read content = fabrication
                fabrications.append(
                    f"Unverified code quote containing function/class definition: {quoted_code[:80]}..."
                )

    return len(code_quotes) > 0, fabrications


# =============================================================================
# END v2.7.0: CODE QUOTE VERIFICATION
# =============================================================================

_entity_extraction_patched = False

if USE_NEW_ENTITY_EXTRACTION:
    try:
        from entity_extraction.migrate import (
            check_entity_overlap as _new_check_overlap,
        )
        from entity_extraction.migrate import (
            extract_entities_from_claims as _new_extract_claims,
        )
        from entity_extraction.migrate import (
            extract_entities_from_evidence as _new_extract_evidence,
        )
        from entity_extraction.migrate import (
            extract_entities_from_text as _new_extract_text,
        )

        # Override the functions defined above
        extract_entities_from_text = _new_extract_text
        extract_entities_from_claims = _new_extract_claims
        extract_entities_from_evidence = _new_extract_evidence
        check_entity_overlap = _new_check_overlap

        _entity_extraction_patched = True

        if DEBUG:
            _logger.warning("[assumption_audit_v2] Using new entity extraction (v2.5.0)")

    except ImportError as e:
        if DEBUG:
            _logger.warning("[assumption_audit_v2] entity_extraction not available: %s", e)


if __name__ == "__main__":
    main()
