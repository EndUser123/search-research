# Evidence-First & Verification Hooks - Complete Source Collection

**Date:** 2026-02-08
**Purpose:** Full source code export for four core evidence-enforcement hooks

---

## 1. PostToolUse_claimguard.py

**Description:** Auto-verifies factual claims about tool outputs against actual execution results. Implements pattern-based claim extraction, verification with warning/block modes, terminal-isolated state management with file locking, and metrics tracking integration.

```python
#!/usr/bin/env python3
"""
ClaimGuard Hook (PostToolUse)

PURPOSE: Auto-verify factual claims about tool outputs to prevent false statements.

ENFORCEMENT MECHANISM:
- Pattern-based claim detection from recent assistant message
- Verification against actual tool output
- Warning/block based on severity and configuration
- Integration with metrics_tracker for KPI tracking

CONSTITUTIONAL BASIS:
- CLAUDE.md: "Truthfulness > agreement"
- CLAUDE.md: "Evidence-first verification"
- truth-v8.md: "Verification > confidence"

ENVIRONMENT VARIABLES:
- CLAIM_VERIFICATION_ENABLED: Enable/disable hook (default: true)
- CLAIM_VERIFICATION_MODE: "warn" or "block" (default: warn)
- CSF_HOOK_DEBUG: Enable debug logging (default: 0)

PATTERN EVASION MITIGATION:
- Word-boundary regex with semantic variations
- Allow-list for explicit uncertainty markers
- Allow-list for verification markers
- Regular pattern review recommended
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

try:
    import portalocker
    PORTALOCKER_AVAILABLE = True
except ImportError:
    PORTALOCKER_AVAILABLE = False

# === CONFIGURATION ===
ENABLED = os.environ.get("CLAIM_VERIFICATION_ENABLED", "true").lower() == "true"
MODE = os.environ.get("CLAIM_VERIFICATION_MODE", "warn")  # "warn" or "block"
DEBUG = os.environ.get("CSF_HOOK_DEBUG", "0") == "1"

# === TERMINAL ISOLATION ===
TERMINAL_DETECTION_PATH = Path(__file__).parent / "terminal_detection.py"
if TERMINAL_DETECTION_PATH.exists():
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from terminal_detection import detect_terminal_id

        TERMINAL_ID = detect_terminal_id()
    except ImportError:
        TERMINAL_ID = "fallback_1"
else:
    TERMINAL_ID = "fallback_1"

STATE_DIR = Path("P:/.claude/state/claimguard") / TERMINAL_ID
STATE_DIR.mkdir(parents=True, exist_ok=True)

CLAIMS_FILE = STATE_DIR / "detected_claims.json"
TTL_SECONDS = 300  # 5 minutes

# === IMPORT PATTERNS MODULE ===
# Import the pattern detection module
try:
    from claimguard_patterns import (
        extract_claims,
        verify_claim_against_output,
        has_uncertainty_marker,
        has_verification_marker,
        OUTPUT_CLAIM_PATTERNS,
        FILE_CLAIM_PATTERNS,
    )
except ImportError:
    # Fallback if module not found
    def extract_claims(response):
        return []

    def verify_claim_against_output(claim, output):
        return {"verified": None}

    def has_uncertainty_marker(text):
        return False

    def has_verification_marker(text):
        return False

    OUTPUT_CLAIM_PATTERNS = []
    FILE_CLAIM_PATTERNS = []

# === STATE MANAGEMENT ===


def load_claims() -> dict:
    """Load claims from state file with TTL cleanup and file locking."""
    if CLAIMS_FILE.exists():
        try:
            with open(CLAIMS_FILE, 'r', encoding='utf-8') as f:
                # Acquire shared lock for reading (blocking)
                if PORTALOCKER_AVAILABLE:
                    portalocker.lock(f, portalocker.LOCK_SH)
                data = json.load(f)
                # Clean expired entries
                now = datetime.now(UTC).timestamp()
                data = {
                    k: v
                    for k, v in data.items()
                    if now - v.get("timestamp", 0) < TTL_SECONDS
                }
                return data
        except (OSError, json.JSONDecodeError, portalocker.LockException):
            # If lock fails or file is corrupt, return empty
            pass
    return {}


def save_claims(claims: dict):
    """Save claims to state file with exclusive file locking."""
    CLAIMS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if PORTALOCKER_AVAILABLE:
        # Use file locking for atomic write
        with open(CLAIMS_FILE, 'w', encoding='utf-8') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            f.write(json.dumps(claims, indent=2))
    else:
        # Fallback to simple write without locking
        CLAIMS_FILE.write_text(json.dumps(claims, indent=2), encoding="utf-8")


def record_claim(
    claim_type: str, claim_text: str, verdict: str, confidence: float = 0.0
):
    """Record a detected claim for tracking and metrics with atomic read-modify-write."""
    CLAIMS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if PORTALOCKER_AVAILABLE:
        # Use file locking for atomic read-modify-write operation
        # Open in read+ mode to allow both reading and writing
        try:
            with open(CLAIMS_FILE, 'a+', encoding='utf-8') as f:
                # Acquire exclusive lock for the entire operation
                portalocker.lock(f, portalocker.LOCK_EX)

                # Read existing data
                f.seek(0)
                try:
                    if f.read(1):  # Check if file is not empty
                        f.seek(0)
                        claims = json.load(f)
                    else:
                        claims = {}
                except (json.JSONDecodeError, OSError):
                    claims = {}

                # Add new claim
                key = f"{claim_type}_{datetime.now(UTC).isoformat()}"
                claims[key] = {
                    "type": claim_type,
                    "text": claim_text[:200],
                    "verdict": verdict,
                    "confidence": confidence,
                    "timestamp": datetime.now(UTC).timestamp(),
                }

                # Clean expired entries
                now = datetime.now(UTC).timestamp()
                claims = {
                    k: v
                    for k, v in claims.items()
                    if now - v.get("timestamp", 0) < TTL_SECONDS
                }

                # Write updated data
                f.seek(0)
                f.truncate()
                f.write(json.dumps(claims, indent=2))
        except (OSError, portalocker.LockException):
            # If locking fails, fall back to non-atomic operation
            claims = load_claims()
            key = f"{claim_type}_{datetime.now(UTC).isoformat()}"
            claims[key] = {
                "type": claim_type,
                "text": claim_text[:200],
                "verdict": verdict,
                "confidence": confidence,
                "timestamp": datetime.now(UTC).timestamp(),
            }
            save_claims(claims)
    else:
        # Fallback to non-atomic operation
        claims = load_claims()
        key = f"{claim_type}_{datetime.now(UTC).isoformat()}"
        claims[key] = {
            "type": claim_type,
            "text": claim_text[:200],
            "verdict": verdict,
            "confidence": confidence,
            "timestamp": datetime.now(UTC).timestamp(),
        }
        save_claims(claims)

    # Also record to metrics tracker if available
    try:
        # Add src to path for metrics import
        src_path = Path("P:/__csf/src")
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from rca.metrics_tracker import get_metrics_tracker

        tracker = get_metrics_tracker()
        session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

        # Record claim verdict
        tracker.record_claim_verdict(
            session_id=session_id,
            claim_type=claim_type,
            verdict=verdict,
            confidence=confidence,
            metadata={"claim_text": claim_text[:200]},
        )
    except ImportError:
        # Metrics tracker not available - skip
        pass


# === MAIN HOOK LOGIC ===


def extract_response(input_data: dict) -> str:
    """Extract assistant response from various input formats."""
    response = ""

    # Try conversation field first (PostToolUse format)
    conversation = input_data.get("conversation", "") or input_data.get("messages", "")
    if isinstance(conversation, list):
        for msg in reversed(conversation):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Handle structured content
                    response = " ".join(
                        b.get("text", "") for b in content if b.get("type") == "text"
                    )
                else:
                    response = str(content)
                break
    else:
        response = str(conversation)

    return response


def process_hook(
    tool_name: str, tool_output: str, response: str
) -> tuple[bool, str | None, str]:
    """
    Main hook entry point for PostToolUse phase.

    Returns: (allow: bool, message: str | None, verdict: str)
    """
    if not ENABLED:
        return True, None, "OK"

    # Only check specific tools
    if tool_name not in ["Read", "Bash", "Grep", "Skill"]:
        return True, None, "OK"

    if DEBUG:
        print(
            f"[claimguard DEBUG] tool_name: {tool_name}, output_length: {len(tool_output)}",
            file=sys.stderr,
        )
        print(f"[claimguard DEBUG] response_length: {len(response)}", file=sys.stderr)

    # Extract claims from response
    claims = extract_claims(response)

    if not claims:
        if DEBUG:
            print("[claimguard DEBUG] No claims detected", file=sys.stderr)
        return True, None, "OK"

    # Verify each claim against tool output
    false_claims = []
    for claim in claims:
        verification = verify_claim_against_output(claim, tool_output)

        if verification["verified"] is False:
            # Record the false claim
            record_claim(
                claim_type=claim["type"],
                claim_text=claim["text"],
                verdict="FALSE",
                confidence=verification.get("confidence", 0.0),
            )
            false_claims.append(
                {
                    "claim": claim["text"],
                    "reason": verification["reason"],
                    "confidence": verification.get("confidence", 0.0),
                }
            )

    # Take action based on mode and findings
    if false_claims:
        claim_summary = "\n".join(
            f'- "{c["claim"][:80]}..."\n  Reason: {c["reason"]}'
            for c in false_claims[:3]  # Limit to first 3
        )

        message = f"""
⚠️ CLAIMGUARD: FALSE CLAIMS DETECTED

Your response contains {len(false_claims)} claim(s) that contradict actual tool output:

{claim_summary}

**Before proceeding, you MUST:**

1. **Quote the actual output** - Show exact tool output, not paraphrasing
2. **Cite your sources** - Reference file:line or command output
3. **Mark uncertainty** - Use "tentative", "preliminary", "may be" if uncertain

**Examples of correct format:**

❌ WRONG: "hook returns {{}}"
✅ RIGHT: "Hook output shows: `{{\"hookSpecificOutput\": ...}}`"

❌ WRONG: "file contains import error"
✅ RIGHT: "Read output line 42 shows: `ImportError: ...`"

**Pattern detected:** Claims about {tool_name} output without verification

**To disable this check:**
  Set "CLAIM_VERIFICATION_ENABLED": "false" in settings.json
  Or: export CLAIM_VERIFICATION_ENABLED=false
"""

        if MODE == "block":
            return False, message, "BLOCK_FALSE_CLAIM"
        else:
            # Warning mode - still allow but warn
            print(message, file=sys.stderr)
            return True, message, "WARN_FALSE_CLAIM"

    # No false claims detected
    return True, None, "OK"


# === MAIN ===

from __lib.hook_base import hook_main


@hook_main
def main():
    """
    Main hook entry point.

    Protocol (PostToolUse):
    - Input: JSON via stdin with tool_name, tool_input, tool_output, conversation
    - Output: JSON to stdout with metadata
    - Exit code: 0 = allow
    - Warning messages go to stderr
    """
    # Parse JSON input with error handling
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Return structured error response for malformed JSON
        error_response = {
            "error": "invalid_json",
            "message": str(e),
            "metadata": {
                "hook": "posttooluse_claimguard",
                "verdict": "PARSE_ERROR"
            }
        }
        print(json.dumps(error_response))
        return

    # Validate required field: tool_name
    tool_name = input_data.get("tool_name")
    if not tool_name:
        error_response = {
            "error": "missing_required_field",
            "field": "tool_name",
            "metadata": {
                "hook": "posttooluse_claimguard",
                "verdict": "VALIDATION_ERROR"
            }
        }
        print(json.dumps(error_response))
        return

    tool_output = str(input_data.get("tool_output", "") or "")
    response = extract_response(input_data)

    # Ensure metadata is always included (removed early {} return)
    if not response or len(response) < 10:
        output = {
            "warning": None,
            "metadata": {
                "hook": "posttooluse_claimguard",
                "verdict": "OK",
                "terminal_id": TERMINAL_ID,
            },
        }
        print(json.dumps(output))
        return

    allow, message, verdict_code = process_hook(tool_name, tool_output, response)

    output = {
        "warning": message if message and MODE == "warn" else None,
        "metadata": {
            "hook": "posttooluse_claimguard",
            "verdict": verdict_code,
            "terminal_id": TERMINAL_ID,
        },
    }

    print(json.dumps(output))

    if MODE == "block" and not allow and message:
        print(message, file=sys.stderr)


if __name__ == "__main__":
    main()
```

---

## 2. assumption_audit_v2.py

**Description:** Blocks responses containing unverified claims with structural enforcement. Implements claim-local entity extraction with context windows, evidence window with scoped invalidation, verification theater detection (filters trivial commands like echo/mkdir), traceable SCOPE_MISMATCH messages with per-claim entity tracing, and terminal-isolated state management.

```python
#!/usr/bin/env python3
"""
Assumption Audit v2 - Blocking Mode
===================================

KEY CHANGE FROM v1: This hook BLOCKS responses with unverified claims,
rather than injecting a soft warning that can be ignored.

Design principle: Structural enforcement > advisory injection

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

import json
import os
import re
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
ENABLED = os.environ.get("ASSUMPTION_AUDIT_V2_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("ASSUMPTION_AUDIT_V2_DEBUG", "false").lower() == "true"
UNIFIED_VERIFIER_ENABLED = os.environ.get("UNIFIED_CLAIM_VERIFIER_ENABLED", "true").lower() == "true"
LOG_FILE = Path("P:/.claude/hooks/logs/assumption_audit_v2.jsonl")
STATE_DIR = Path("P:/.claude/hooks/state")

# v2.3.0: Claim-scope verification (can disable for rollback)
CLAIM_SCOPE_CHECK_ENABLED = os.environ.get("CLAIM_SCOPE_CHECK_ENABLED", "true").lower() == "true"

# v2.3.1: Coverage threshold for claim-entity overlap (0.0-1.0)
# Higher = stricter (more entities must be covered)
# Default 0.5 = at least 50% of claim entities must have evidence
CLAIM_COVERAGE_THRESHOLD = float(os.environ.get("CLAIM_COVERAGE_THRESHOLD", "0.5"))

# v2.5.0: New entity extraction system flag (applied at end of module)
USE_NEW_ENTITY_EXTRACTION = os.environ.get("USE_NEW_ENTITY_EXTRACTION", "false").lower() == "true"

# Terminal isolation
try:
    from terminal_detection import detect_terminal_id
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
    "git status", "git log", "git diff", "git show", "git branch", "git remote",
    "ls", "cat ", "head ", "tail ", "grep ", "find ", "wc ", "stat ", "pwd",
    "echo ", "type ", "dir ", "Get-Content", "Get-ChildItem", "Test-Path",
    "python -c \"import", "python -c 'import",  # import checks (read-only)
    "python -c \"from", "python -c 'from",
)

# v2.4.0: DIAGNOSTIC BASH PREFIXES - commands that count as evidence
# These may technically change state (create test outputs) but their PRIMARY purpose
# is verification/diagnosis, so they count as observational evidence.
DIAGNOSTIC_BASH_PREFIXES = (
    # Test runners
    "pytest", "python -m pytest", "py.test",
    "npm test", "npm run test", "yarn test", "pnpm test",
    "cargo test", "go test", "mvn test", "gradle test",
    "jest", "mocha", "vitest", "ava",
    # Script execution (verifies behavior)
    "python ", "python3 ", "node ", "deno ", "bun ",
    # Build verification
    "cargo check", "cargo build", "go build", "npm run build",
    "tsc ", "mypy ", "ruff ", "flake8", "pylint",
)

# v2.4.0: TRIVIAL BASH COMMANDS - commands that cannot produce diagnostic information
# These are "read-only" in that they don't change state, but they provide NO verification value
# for claims about system behavior, test results, or fix correctness.
#
# RULE: Trivial commands are filtered from evidence when evaluating success claims.
# REASON: Prevents "Verification Theater" where `echo "done"` masquerades as verification.
# CONSEQUENCE: Agent blocked from claiming "fixed" based on trivial commands alone.
TRIVIAL_BASH_COMMANDS = frozenset({
    # Output commands (produce text, don't observe system state)
    "echo", "printf", "write-host", "write-output",
    # File manipulation (change state, not observation)
    "mkdir", "touch", "rm", "mv", "cp", "del", "copy", "move", "ren", "rename",
    # Environment manipulation (no diagnostic value)
    "cd", "pushd", "popd", "pwd", "export", "set", "alias", "unalias", "clear", "cls",
    # Directory listing without diagnostic intent
    # NOTE: "ls" alone is weak evidence but not blocked - use WEAK_EVIDENCE_COMMANDS for tiering
})

# Commands that are evidence but weak (Tier 4 equivalent - may trigger warnings but not blocks)
WEAK_EVIDENCE_COMMANDS = frozenset({
    "ls", "dir", "tree",  # Show structure but not content/behavior
})

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


def debug_log(msg: str):
    """Log debug message if DEBUG enabled."""
    if DEBUG:
        print(f"[assumption_audit_v2] {msg}", file=sys.stderr)


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
            first_word = first_word[:-len(suffix)]
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
        "pytest", "python", "python3", "node", "npm", "yarn", "cargo", "go",
        "cat", "grep", "head", "tail", "less", "more", "awk", "sed",
        "git", "curl", "wget", "jq", "yq",
        "type", "get-content", "select-string",  # PowerShell equivalents
    }

    return cmd_name in diagnostic_commands or cmd_name not in TRIVIAL_BASH_COMMANDS



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
    r'[A-Za-z]:[/\\][\w./\\-]+\.[\w]+',
    # Windows paths with spaces in quotes
    r'["\'][A-Za-z]:[/\\][^"\']+["\']',
    # Unix absolute paths: /home/..., /usr/...
    r'/(?:home|usr|var|etc|opt|tmp|mnt)/[\w./\\-]+',
    # Relative paths with extension: ./file.py, ../dir/file.js
    r'\.{1,2}/[\w./\\-]+\.[\w]+',
    # Python module paths: module.submodule.file
    r'\b[\w]+(?:\.[\w]+){2,}\b',
    # Filenames with common extensions
    r'\b[\w-]+\.(?:py|js|ts|json|yaml|yml|md|txt|sh|ps1|bat|sql|html|css|jsx|tsx)\b',
]

# Patterns for extracting function/class names from claims
NAME_PATTERNS = [
    # function_name(), method_name()
    r'\b([a-z_][a-z0-9_]*)\s*\(',
    # ClassName, ModuleName (PascalCase)
    r'\b([A-Z][a-zA-Z0-9]+)\b',
    # CONSTANT_NAME
    r'\b([A-Z][A-Z0-9_]+)\b',
]

# Common words to filter from entity extraction (noise reduction)
COMMON_WORDS = frozenset({
    # Articles and pronouns
    "the", "a", "an", "it", "its", "this", "that", "these", "those",
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "into",
    # Verbs (common in claims and tech prose)
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "can", "must", "shall", "get", "got", "set", "run", "ran", "let",
    "add", "use", "used", "using", "make", "made", "find", "found",
    "read", "show", "fix", "fixable", "merge", "split", "filter",
    "replace", "expand", "clean", "implement", "review", "gather",
    # Conjunctions
    "and", "or", "but", "if", "then", "else", "when", "while", "not",
    # Common nouns in tech context (too generic to be meaningful entities)
    "file", "files", "code", "data", "list", "item", "items", "test", "tests",
    "function", "class", "method", "module", "error", "result", "output",
    "input", "value", "name", "type", "path", "dir", "directory",
    "action", "actions", "issue", "issues", "status", "context", "system",
    "key", "root", "layer", "next", "risk", "results", "summary",
    "description", "location", "priority", "severity", "coverage",
    "success", "effort", "stage", "script", "task", "skill",
    "recommendation", "rationale", "findings", "strengths", "weaknesses",
    "execution", "generation", "validation", "formatting", "annotation",
    "consolidate", "redundant", "duplicate", "blocking", "identified",
    "estimated", "recommended", "architectural", "sequential", "critical",
    # Analysis/report terms (appear in synthesis outputs, never entities)
    "high", "low", "medium", "multi", "repo", "cli", "api",
    "which", "errors", "failures", "dead", "currently", "non",
    # Words appearing in explanatory/example text that aren't code entities
    "claim", "claims", "instead", "unverified", "pass", "fail",
    "trace", "block", "blocked", "allow", "allowed", "xyz",
    "example", "shows", "check", "verify", "verified", "sample",
    "specific", "actual", "expected", "missing", "covered", "uncovered",
    # Adjectives
    "new", "old", "all", "some", "any", "each", "every", "no", "none",
    # Numbers and quantities
    "one", "two", "three", "four", "five", "first", "second", "last",
    # Other common words
    "now", "just", "also", "only", "here", "there", "where", "what", "how",
    "yes", "no", "ok", "true", "false", "null", "none", "self",
    "you", "your", "we", "our", "they", "them", "my",
})

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
                normalized = group.strip('"\'').replace("\\", "/").lower()
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
            is_observational = any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES)

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


def check_entity_overlap(claim_entities: set[str], evidence_entities: set[str]) -> tuple[bool, set[str], set[str]]:
    """
    Check if claim entities have overlap with evidence entities.

    Returns: (has_overlap, overlapping, uncovered)
    """
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

    debug_log(f"Overlap: {all_covered}, Uncovered: {uncovered}, Ratio: {coverage_ratio:.2f}, Threshold: {CLAIM_COVERAGE_THRESHOLD}")

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
    session_id = os.environ.get("CLAUDE_SESSION_ID", "").strip().lower()
    if not re.fullmatch(r"[a-f0-9\-]{36}", session_id):
        session_id = ""

    # Preferred path: durable session-scoped evidence store
    try:
        from evidence_store import load_tool_events, resolve_session_id
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
                terminal_id="",
                require_scoped_metadata=False,
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
# PATTERN-SPECIFIC REMEDIATION
# =============================================================================

CLAIM_REMEDIATION = {
    "test_execution": {
        "patterns": [
            r"(?:tests?|pytest)\s+(?:pass|fail|succeed|run|show)",
            r"(?:tests?)\s+(?:are|is)\s+(?:passing|failing)",
            r"\d+\s+(?:passed|failed|skipped)",
        ],
        "action": "Run: pytest <path> -v\\nThen quote ACTUAL output: 'pytest shows: 30 passed'",
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
        "action": "QUOTE the tool output that found it.\\nDon't summarize: show actual lines from output.",
    },
    "code_behavior": {
        "patterns": [
            r"(?:running|executing|calling)\s+.*(?:returns?|produces?|outputs?|shows?)",
            r"(?:function|method|class)\s+(?:returns?|takes?|accepts?|raises?)",
            r"(?:code|script|module)\s+(?:executes?|runs?|works?)",
        ],
        "action": "Run: Bash python -c \\\"<test code>\\\"\\nThen quote ACTUAL execution output.",
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
        "action": "Run: Read <error_source>\\nThen quote the error lines with evidence.",
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


def get_remediation_for_claims(claims: list[str], response_text: str, scope_mismatch: bool = False) -> tuple[str, str]:
    """Match detected claims to remediation actions."""
    if scope_mismatch:
        return "scope_mismatch", CLAIM_REMEDIATION["scope_mismatch"]["action"]

    response_lower = response_text.lower()

    is_summary = any(word in response_lower for word in [
        "complete", "summary", "done", "finished", "implemented",
        "all tests", "tdd cycle", "final"
    ])

    for category, config in CLAIM_REMEDIATION.items():
        for pattern in config["patterns"]:
            if re.search(pattern, response_text, re.IGNORECASE):
                action = config["action"]
                if is_summary:
                    action = f"⚠️ SUMMARY DETECTED - Re-verify before claiming.\n\n{action}"
                return category, action

    return "unspecified", "Use Read, Bash, or Grep to verify your claim.\nShow tool output as evidence."


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def detect_claims(response_text: str) -> list[str]:
    """Find factual claims about code/files/state in response."""
    if not response_text:
        return []

    pattern = _get_claim_patterns()
    matches = pattern.findall(response_text)

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
    """Check if response is exempt from verification requirement."""
    if not response_text:
        return True

    text = response_text.strip()

    if len(text) < 30:
        claims = detect_claims(text)
        if claims:
            return False
        return True

    pattern = _get_exemption_patterns()
    if pattern.search(text):
        claims = detect_claims(text)
        if claims:
            return False
        return True

    return False


def evaluate_response(response_text: str, tools_used: list[str], tool_sequence: list[dict] = None) -> dict:
    """
    Main evaluation function.

    v2.3.0: Now checks for CLAIM-EVIDENCE SCOPE OVERLAP, not just tool presence.
    v2.4.1: Theater detection runs on SUCCESS claims even without entity claims.

    Returns:
        dict with decision (block/allow), reason, and optional message/claims
    """
    # Preferred mode: unified claim verifier (single source of truth).
    if UNIFIED_VERIFIER_ENABLED:
        try:
            from unified_claim_verifier import evaluate_claims
            result = evaluate_claims(
                response_text=response_text,
                tools_used=tools_used,
                session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
            )
            if result.get("decision") == "block":
                missing = result.get("missing_claims", [])
                if result.get("reason") == "NO_EVIDENCE":
                    return {
                        "decision": "block",
                        "reason": "NO_EVIDENCE",
                        "message": format_block_message(missing or detect_claims(response_text), response_text, False),
                        "claims_detected": missing or detect_claims(response_text),
                    }
                return {
                    "decision": "block",
                    "reason": "UNVERIFIED_CLAIMS",
                    "message": format_block_message(missing or detect_claims(response_text), response_text, True),
                    "claims_detected": missing or detect_claims(response_text),
                    "uncovered_entities": result.get("evidence_entities", []),
                    "evidence_entities": result.get("evidence_entities", []),
                }
            return {
                "decision": "allow",
                "reason": "CLAIMS_VERIFIED",
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
        return {
            "decision": "allow",
            "reason": "NO_CLAIMS"
        }

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
            "claims_detected": claims
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
                debug_log(f"Verification Theater detected: success claims with weak evidence: {weak_cmds}")
                return {
                    "decision": "block",
                    "reason": "VERIFICATION_THEATER",
                    "message": format_verification_theater_message(claims, weak_cmds),
                    "claims_detected": claims,
                    "weak_commands": weak_cmds
                }
            elif bash_in_fallback:
                # Bash was used but ALL commands were trivial (filtered out)
                # This is theater - the agent ran commands but none had diagnostic value
                debug_log("Verification Theater detected: Bash used but all commands were trivial")
                return {
                    "decision": "block",
                    "reason": "VERIFICATION_THEATER",
                    "message": format_verification_theater_message(claims, ["(all bash commands were trivial - echo, mkdir, etc.)"]),
                    "claims_detected": claims,
                    "trivial_commands_filtered": True
                }

    # v2.3.0: CLAIM-SCOPE VERIFICATION
    # v2.5.0: Claim-local entity extraction + traceable error messages
    if CLAIM_SCOPE_CHECK_ENABLED:
        # Extract entities from claims (context-windowed, not full response)
        claim_entities = extract_entities_from_claims(claims, response_text)

        # Extract entities from evidence
        evidence_entities = extract_entities_from_evidence(valid_tool_entries)

        # Check overlap
        has_overlap, covered, uncovered = check_entity_overlap(claim_entities, evidence_entities)

        if not has_overlap and claim_entities:
            # Build per-claim entity map for traceability
            claim_entity_map = {}
            for claim in claims:
                claim_ents = extract_entities_from_text(claim)
                ctx = _get_claim_context_window(claim, response_text)
                claim_ents |= extract_entities_from_text(ctx)
                claim_uncovered = claim_ents - (covered | evidence_entities)
                if claim_uncovered:
                    claim_entity_map[claim] = claim_uncovered

            return {
                "decision": "block",
                "reason": "SCOPE_MISMATCH",
                "message": format_scope_mismatch_message(claims, claim_entity_map, uncovered, evidence_entities),
                "claims_detected": claims,
                "uncovered_entities": list(uncovered),
                "evidence_entities": list(evidence_entities)
            }

    # Evidence exists and covers claims (or scope check disabled) - allow
    return {
        "decision": "allow",
        "reason": "VERIFIED" if not CLAIM_SCOPE_CHECK_ENABLED else "SCOPE_VERIFIED",
        "evidence_tools": evidence_tools
    }


def format_block_message(claims: list[str], response_text: str = "",
                         scope_mismatch: bool = False,
                         uncovered: set[str] = None,
                         evidence: set[str] = None) -> str:
    """Format the block message with pattern-specific remediation."""
    category, action = get_remediation_for_claims(claims, response_text, scope_mismatch)

    claim_list = "\n".join(f"  • \"{c}\"" for c in claims[:3])

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


def format_scope_mismatch_message(claims: list[str],
                                   claim_entity_map: dict[str, set[str]],
                                   uncovered: set[str],
                                   evidence: set[str]) -> str:
    """
    v2.5.0: Traceable SCOPE_MISMATCH message.

    Shows which claim references which unverified entities,
    so the LLM (and user) can see exactly what triggered the block.
    """
    # Build per-claim trace lines
    trace_lines = []
    for claim_text, ents in list(claim_entity_map.items())[:3]:
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
    claim_list = "\n".join(f"  • \"{c}\"" for c in claims[:3])
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


def format_hook_output(decision: str, reason: str, message: str = "", claims: list = None, **kwargs) -> str:
    """Format output for hook protocol."""
    # Map internal decision values to schema-compliant values
    # Internal: "allow" | "block" → Schema: "approve" | "block"
    schema_decision = "approve" if decision == "allow" else "block"

    output = {
        "decision": schema_decision,
        "reason": reason
    }

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
            **data
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


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
            from evidence_store import resolve_session_id, load_tool_events
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
        print(json.dumps({"decision": "allow", "reason": "DISABLED"}))
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

    if not response_text:
        print(format_hook_output(decision="allow", reason="NO_RESPONSE_TEXT"))
        sys.exit(0)

    result = evaluate_response(response_text, tools_used)

    elapsed_ms = (time.time() - start_time) * 1000

    log_event(result["decision"], {
        "tools_used": tools_used,
        "claims": result.get("claims_detected", []),
        "duration_ms": elapsed_ms,
        "response_snippet": response_text[:100] if response_text else "",
        "scope_check": CLAIM_SCOPE_CHECK_ENABLED,
        "uncovered": result.get("uncovered_entities", []),
    })

    print(format_hook_output(
        decision=result["decision"],
        reason=result["reason"],
        message=result.get("message", ""),
        claims=result.get("claims_detected"),
        uncovered_entities=result.get("uncovered_entities"),
        evidence_entities=result.get("evidence_entities"),
    ))

    sys.exit(0 if result["decision"] == "allow" else 2)


# =============================================================================
# v2.5.0: NEW ENTITY EXTRACTION SYSTEM
# =============================================================================
# Applied AFTER all function definitions to properly override them.
# Set USE_NEW_ENTITY_EXTRACTION=false to disable.

_entity_extraction_patched = False

if USE_NEW_ENTITY_EXTRACTION:
    try:
        from entity_extraction.migrate import (
            extract_entities_from_text as _new_extract_text,
            extract_entities_from_claims as _new_extract_claims,
            extract_entities_from_evidence as _new_extract_evidence,
            check_entity_overlap as _new_check_overlap,
        )

        # Override the functions defined above
        extract_entities_from_text = _new_extract_text
        extract_entities_from_claims = _new_extract_claims
        extract_entities_from_evidence = _new_extract_evidence
        check_entity_overlap = _new_check_overlap

        _entity_extraction_patched = True

        if DEBUG:
            print("[assumption_audit_v2] Using new entity extraction (v2.5.0)", file=sys.stderr)

    except ImportError as e:
        if DEBUG:
            print(f"[assumption_audit_v2] entity_extraction not available: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

---

## 3. StopHook_cross_validator.py

**Description:** Detects "fixed" claims without empirical verification using pattern-based detection and evidence verification. Separates generation from verification to reduce confirmation bias, implements terminal-isolated state management, provides cross-validation with counterfactual requirements, and offers verbose/block modes.

```python
#!/usr/bin/env python3
from __future__ import annotations

"""
Cross-Validation Hook (Stop)

PURPOSE: Detect "fixed" claims without empirical verification.

PROBLEM ADDRESSED:
- AI claims "issue is fixed" without testing
- Reads router files (structural compliance) but doesn't verify hook output
- Procedural compliance without actual problem-solving

CONSTITUTIONAL BASIS:
- CLAUDE.md: "Evidence Tiers" - Tier 1 requires execution artifacts
- CLAUDE.md: "Multi-Component Validation" - validate with verifiable evidence

RESEARCH BASIS:
- Cross-Validation / Self-Verification (Duke, MIT CSAIL)
- Separation of generation and verification reduces confirmation bias
- Evidence Access Tracking (arXiv 2509.17995)
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    from block_protocol import block_response

    BLOCK_PROTOCOL_AVAILABLE = True
except ImportError:
    BLOCK_PROTOCOL_AVAILABLE = False

# === CONFIGURATION ===
ENABLED = os.environ.get("CROSS_VALIDATION_HOOK_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
VERBOSE = os.environ.get("CROSS_VALIDATION_VERBOSE", "false").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
DEBUG = os.environ.get("CSF_HOOK_DEBUG", "0") == "1"

# === TERMINAL ISOLATION ===
# Import terminal detection for session-safe state management
TERMINAL_DETECTION_PATH = Path(__file__).parent / "terminal_detection.py"
if TERMINAL_DETECTION_PATH.exists():
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from terminal_detection import detect_terminal_id

        TERMINAL_ID = detect_terminal_id()
    except ImportError:
        TERMINAL_ID = "fallback_1"
else:
    TERMINAL_ID = "fallback_1"

# State directory per terminal (prevents cross-terminal bleed)
STATE_DIR = Path("P:/.claude/state/cross_validation") / TERMINAL_ID
try:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    # Fallback to temp if state dir is not writable in current environment.
    STATE_DIR = Path(tempfile.gettempdir()) / "claude_hooks" / "cross_validation" / TERMINAL_ID
    STATE_DIR.mkdir(parents=True, exist_ok=True)

CLAIMS_FILE = STATE_DIR / "claims.json"
VERIFICATIONS_FILE = STATE_DIR / "verifications.json"

# === PATTERN DETECTION ===

# "Fixed" claim patterns (high confidence that AI is claiming completion)
FIXED_CLAIM_PATTERNS = [
    # Direct "fixed" statements
    r"(?i)^(the\s+)?(issue|problem|bug|error)\s+(is\s+)?(fixed|resolved|solved|corrected)(?!\.?\s+(but|however|except))",
    r"(?i)^(i\s+)?(have\s+)?fixed\b",
    # Note: "should fix" is in WHITELIST_PATTERNS as speculative
    r"(?i)^(this\s+)?should\s+fix",
    # "Resolved" variations
    r"(?i)^(this\s+)?resolves?\b(?!\.?\s+(the\s+(following|below)|partially))",
    r"(?i)^(the\s+)?(hook|system|code)\s+now\s+(works|functions|behaves)\s+correctly",
    # "Done" without qualification (anchors removed to match within response)
    r"(?i)^(done|complete|completed)(?!\.?\s+(but|however|except|partially|with|by))",
]

# Evidence patterns (shows AI actually verified the fix)
VERIFICATION_PATTERNS = [
    # Test execution
    r"(?i)(ran|executed|tested|verified)\s+(pytest|test|the\s+test|the\s+hook)",
    r"(?i)pytest\s+(passed|succeeded|showed)\s+\d+",
    # Hook output verification
    r"(?i)hook\s+returns?\s+({\"ok\":\s*true|allow.*true)",
    r"(?i)echo\s+.*\|\s+python\s+.*hook",
    # Direct evidence of execution
    r"(?i)(tested|verified)\s+the\s+fix\s+works?",
    r"(?i)confirmed\s+(the\s+)?(fix|solution)\s+(works?|is\s+functional)",
    # "Verified by running" pattern
    r"(?i)verified\s+by\s+running",
    # Before/after comparison
    r"(?i)before:\s*.*after:\s*",
    # Actual output shown
    r"(?i)(test\s+)?output\s+shows?",
]

# Whitelist patterns (legitimate "fixed" claims that don't need verification)
WHITELIST_PATTERNS = [
    # Documenting what was done (past tense narrative)
    r"(?i)this\s+(commit|change|edit)\s+fixed\b",
    # Speculative/hypothetical
    r"(?i)(should|would|could)\s+fix\b",
    # Partial fixes acknowledged
    r"(?i)partially\s+fixed",
    r"(?i)fixes?\s+(but|however|except)\s+",
    # Quoting someone else
    r"(?i)according\s+to",
    r"(?i)[\"'][^\"']+fixed[^\"']*[\"']",
]


# === STATE MANAGEMENT ===


def load_claims() -> dict:
    """Load claims from state file."""
    if CLAIMS_FILE.exists():
        try:
            return json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_claims(claims: dict):
    """Save claims to state file."""
    CLAIMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLAIMS_FILE.write_text(json.dumps(claims, indent=2), encoding="utf-8")


def load_verifications() -> dict:
    """Load verifications from state file."""
    if VERIFICATIONS_FILE.exists():
        try:
            return json.loads(VERIFICATIONS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_verifications(verifications: dict):
    """Save verifications to state file."""
    VERIFICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATIONS_FILE.write_text(json.dumps(verifications, indent=2), encoding="utf-8")


# === ANALYSIS ===


def detect_fixed_claim(response: str) -> dict | None:
    """
    Detect if response contains a "fixed" claim without verification.

    Returns:
        dict with 'matched', 'pattern', 'confidence' if detected, None otherwise
    """
    if not response or len(response) < 3:
        return None

    # Check whitelist first (these are OK, no blocking)
    for pattern in WHITELIST_PATTERNS:
        if re.search(pattern, response, re.MULTILINE):
            return None  # Whitelisted, allow

    # Look for "fixed" claims
    for pattern in FIXED_CLAIM_PATTERNS:
        match = re.search(pattern, response, re.MULTILINE)
        if match:
            # Found a "fixed" claim - check if verified
            has_verification = any(
                re.search(vp, response, re.MULTILINE) for vp in VERIFICATION_PATTERNS
            )

            if not has_verification:
                return {
                    "matched": match.group(0),
                    "pattern": pattern,
                    "confidence": (
                        "high" if "fix" in match.group(0).lower() else "medium"
                    ),
                }

    return None


def check_recent_verification(tool_context: dict) -> bool:
    """
    Check if recent tool usage includes verification evidence.

    Args:
        tool_context: Dict with 'recent_tools' list of tool executions

    Returns:
        True if verification tools were used recently
    """
    recent_tools = tool_context.get("recent_tools", [])

    # Look for test execution or verification in recent tools
    for tool_entry in recent_tools[-5:]:  # Check last 5 tools
        tool_name = tool_entry.get("name", "")
        tool_input = tool_entry.get("input", {})

        # Bash with pytest/test commands
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if any(cmd in command.lower() for cmd in ["pytest", "test", "verify"]):
                return True

        # Read of hook file (may indicate verification)
        if tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            if "hook" in file_path.lower():
                # Read alone isn't verification - need execution
                pass

    return False


# === MAIN HOOK LOGIC ===


def extract_response(input_data: dict) -> str:
    """Extract assistant response from various input formats."""
    response = ""

    # Try transcript_path first
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript = Path(transcript_path)
            if transcript.exists():
                content = transcript.read_text(encoding="utf-8")
                for line in reversed(content.strip().split("\n")):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        # Handle message wrapper format: {"type": "message", "role": "assistant", "message": {"content": [...]}}
                        if (
                            entry.get("type") == "message"
                            and entry.get("role") == "assistant"
                        ):
                            msg = entry.get("message", {})
                            msg_content = msg.get("content", [])

                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                        # Handle type field format: entry["type"] == "assistant"
                        elif entry.get("type") == "assistant":
                            msg = entry.get("message", {})
                            msg_content = msg.get("content", [])

                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                        # Handle role field without type wrapper
                        elif entry.get("role") == "assistant":
                            msg = entry.get("message", entry)
                            msg_content = msg.get("content", entry.get("content", "")

                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    # Fallback to conversation field
    if not response:
        conversation = input_data.get("conversation", "") or input_data.get(
            "messages", ""
        )
        if isinstance(conversation, list):
            for msg in reversed(conversation):
                if msg.get("role") == "assistant":
                    response = msg.get("content", "")
                    break
        else:
            response = str(conversation)

    # Final fallback
    if not response:
        response = input_data.get("response", "")

    return response


def process_hook(response: str, tool_context: dict) -> tuple[bool, str | None, str]:
    """
    Main hook entry point for Stop phase.

    Returns: (allow: bool, message: str | None, verdict: str)
    """
    if not ENABLED:
        return True, None, "OK"

    # Check for unverified "fixed" claims
    claim_info = detect_fixed_claim(response)

    if claim_info:
        # Check if recent tools show verification
        has_verification = check_recent_verification(tool_context)

        if not has_verification:
            # Block - require verification
            blocked_message = f"""
⚠️ CROSS-VALIDATION REQUIRED

You claim the issue is fixed: "{claim_info['matched'][:80]}"

Before completing, you MUST provide empirical verification:

1. **Show evidence it works** (test output, not file read)
   - Run: pytest (if tests exist)
   - Run: echo '{{"tool_name":"Bash",...}}' | python hook.py
   - Show actual before/after behavior

2. **Explain HOW you verified it works**
   - What command did you run?
   - What output confirmed the fix?

3. **What would have shown this fix didn't work?**
   - Counterfactual: "If this didn't work, I would see X"

Example valid verification:
  Before: Hook returned {{"type": "error"}} (missing "ok": true)
  After: Hook returns {{"ok": true, "type": "success"}}
  Verified by: echo '{{...}}' | python .claude/hooks/StopHook_cross_validator.py

---
To disable this check temporarily:
  Set "CROSS_VALIDATION_HOOK_ENABLED": "false" in settings.json
Reference: .claude/hooks/CLAUDE.md section "Cross-Validation Hooks"
"""

            if VERBOSE:
                # Verbose mode: warn but allow
                return True, blocked_message, "WARN_UNVERIFIED_FIX"
            else:
                # Block mode: deny completion
                return False, blocked_message, "BLOCK_UNVERIFIED_FIX"

    return True, None, "OK"


# === MAIN ===

from __lib.hook_base import hook_main


@hook_main
def main():
    """
    Main hook entry point.

    Protocol (Stop):
    - Input: JSON via stdin with transcript_path, conversation, or messages
    - Output: JSON to stdout with "allow", "reason", "metadata" fields
    - Exit code: 0 = allow, 1 = block
    - Block message goes to stderr
    """
    input_data = json.load(sys.stdin)

    # DEBUG: Log input structure for diagnosis
    if DEBUG:
        print(
            f"[cross_validator DEBUG] input_data keys: {list(input_data.keys())}",
            file=sys.stderr,
        )
        resp_preview = repr(
            input_data.get("response", "MISSING")[:100]
            if input_data.get("response")
            else "EMPTY/MISSING"
        )
        print(
            f"[cross_validator DEBUG] response field: {resp_preview}", file=sys.stderr
        )
        print(
            f"[cross_validator DEBUG] transcript_path: {input_data.get('transcript_path', 'MISSING')}",
            file=sys.stderr,
        )

    response = extract_response(input_data)

    if DEBUG:
        print(
            f"[cross_validator DEBUG] extracted response length: {len(response)}",
            file=sys.stderr,
        )
        print(
            f"[cross_validator DEBUG] extracted response preview: {repr(response[:200])}",
            file=sys.stderr,
        )

    if not response or len(response) < 3:
        print(json.dumps({"allow": True, "reason": "Response too short"}))
        return

    # Build tool context (we don't have full tool history in Stop phase)
    tool_context = {"recent_tools": []}

    allow, message, verdict_code = process_hook(response, tool_context)

    if not allow:
        block_message = message or "CROSS_VALIDATION: Unverified fixed claim"
        output = {
            "decision": "block",
            "reason": block_message,
            "message": block_message,
            "metadata": {
                "hook": "stop_cross_validation",
                "verdict": verdict_code,
                "terminal_id": TERMINAL_ID,
            },
        }
        print(json.dumps(output))
        if BLOCK_PROTOCOL_AVAILABLE:
            block_response(reason=block_message, hook="stop_cross_validation")
        print(block_message, file=sys.stderr)
        sys.exit(2)

    output = {
        "decision": "approve",
        "reason": "OK",
        "metadata": {
            "hook": "stop_cross_validation",
            "verdict": verdict_code,
            "terminal_id": TERMINAL_ID,
        },
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## 4. speculation_gate.py

**Description:** Blocks responses making diagnostic claims without evidence by enforcing investigation-before-diagnosis principles. Implements speculation marker detection, error explanation pattern validation without verification, high confidence claims requiring evidence tier citations, root cause claim validation with source read verification, hypothesis confirmation checks, structural verification via ToolSequenceManager, evidence tier pattern enforcement, and SQLite/constructional_blocks logging.

```python
"""
Stop Hook: Speculation Gate
Blocks responses that make diagnostic claims without evidence.

Constitutional basis: CLAUDE_updated.md Part C.2 Anti-Speculation Gate

v2.1.0 (2026-01-26): Added tool-sequence verification
  - Now checks actual tool calls (Read, Bash, Glob) not just text patterns
  - Uses ToolSequenceManager for structural verification

v2.0.0 (2026-01-26): Merged error_explanation_gate patterns
  - Added ERROR_EXPLANATION_PATTERNS for unverified error claims
  - Consolidated from PostToolUse (where response text unavailable)
"""

import json
import sys
import re
import os
from typing import Optional
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Import tool sequence manager for structural verification
try:
    from tool_sequence_manager import ToolSequenceManager
    TOOL_TRACKING_AVAILABLE = True
except ImportError:
    TOOL_TRACKING_AVAILABLE = False

# Speculation markers that indicate unverified claims
SPECULATION_MARKERS = [
    r"\blikely cause\b",
    r"\bmay not be\b",
    r"\bmay have a bug\b",
    r"\bprobably\b",
    r"\bI believe\b",
    r"\bmost likely\b",
    r"\bappears to be\b",
    r"\bseems like\b",
    r"\bcould be\b",
    r"\bmight be\b",
    r"\bI think\b",
    r"\bI suspect\b",
]

# Error explanation patterns (merged from error_explanation_gate.py)
# These indicate explaining errors without verifying actual system state
ERROR_EXPLANATION_PATTERNS = [
    r"(?:can't|cannot|couldn't|unable to) access",
    r"workspace restrict(?:ion)?s?",
    r"permission denied",
    r"(?:path|file|directory) (?:doesn't|does not|isn't|is not) exist",
    r"no such file or directory",
]

# Tools that constitute verification (structural check)
VERIFICATION_TOOLS = {"Read", "Bash", "Glob", "Grep", "ListDir"}

# High confidence claims that need evidence backing
HIGH_CONFIDENCE_PATTERN = r"(?:Confidence|confidence):\s*(\d{2,3})%"

# Evidence tier citations
EVIDENCE_TIER_PATTERN = r"\[Tier [1-4]\]|\[UNVERIFIED\]|\[INFERRED\]"

# Root cause claim patterns
ROOT_CAUSE_PATTERNS = [
    r"ROOT CAUSE",
    r"root cause",
    r"Root Cause",
    r"The cause is",
    r"The issue is",
    r"The problem is",
]

# Patterns indicating source code was actually read
SOURCE_READ_PATTERNS = [
    r"Read\([^)]+\.py\)",
    r"read .+\.py",
    r"file:line",
    r"Line \d+:",
    r"lines? \d+-\d+",
]


def check_speculation_violations(content: str) -> list[dict]:
    """Check for speculation patterns without proper evidence."""
    violations = []

    # Check for speculation markers
    for marker in SPECULATION_MARKERS:
        matches = re.findall(marker, content, re.IGNORECASE)
        if matches:
            violations.append({
                "type": "SPECULATION_MARKER",
                "detail": f"Found speculation language: '{matches[0]}'"
            })

    # Check for error explanation patterns without verification
    # v2.1.0: Uses STRUCTURAL verification (did tool get called?) not just text patterns
    for pattern in ERROR_EXPLANATION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            # First check: structural verification via tool sequence
            has_structural_verification = False
            if TOOL_TRACKING_AVAILABLE:
                recent_tools = ToolSequenceManager.get_recent(20)
                verification_tool_names = {t.get("name") for t in recent_tools}
                has_structural_verification = bool(verification_tool_names & VERIFICATION_TOOLS)

            # Fallback: text pattern verification (less reliable)
            has_text_verification = any(
                re.search(p, content) for p in SOURCE_READ_PATTERNS
            )

            if not has_structural_verification and not has_text_verification:
                violations.append({
                    "type": "ERROR_EXPLANATION_NO_VERIFICATION",
                    "detail": f"Error explanation without verification: matched '{pattern}'"
                })
                break  # One error explanation violation is enough

    # Check for high confidence without evidence tier
    confidence_matches = re.findall(HIGH_CONFIDENCE_PATTERN, content)
    has_evidence_tier = bool(re.search(EVIDENCE_TIER_PATTERN, content))

    for conf in confidence_matches:
        if int(conf) > 75 and not has_evidence_tier:
            violations.append({
                "type": "HIGH_CONFIDENCE_NO_TIER",
                "detail": f"{conf}% confidence claimed without evidence tier citation"
            })

    # Check for root cause claims without source file evidence
    has_root_cause_claim = any(
        re.search(pattern, content) for pattern in ROOT_CAUSE_PATTERNS
    )
    has_source_read = any(
        re.search(pattern, content) for pattern in SOURCE_READ_PATTERNS
    )

    if has_root_cause_claim and not has_source_read:
        violations.append({
            "type": "ROOT_CAUSE_NO_SOURCE",
            "detail": "Root cause claimed without reading source file (no Read() or file:line citation)"
        })

    # Check for hypothesis confirmation without verification
    hypothesis_confirmed = re.search(
        r"(?:Hypothesis|hypothesis).*?(?:Status|status):\s*✅",
        content,
        re.DOTALL
    )
    if hypothesis_confirmed and not has_source_read:
        violations.append({
            "type": "PREMATURE_CONFIRMATION",
            "detail": "Hypothesis marked confirmed (✅) without source code verification"
        })

    return violations


def format_block_message(violations: list[dict]) -> str:
    """Format the block message for the user."""
    violation_list = "\n".join(
        f"  - {v['type']}: {v['detail']}" for v in violations
    )

    return f"""⚠️ SPECULATION GATE VIOLATION

Response blocked due to unverified diagnostic claims:
{violation_list}

REQUIRED before diagnosis:
1. READ the executor/dispatcher source (not just config)
2. TRACE the actual execution path
3. TAG confidence with evidence tier [Tier 1-4] or [UNVERIFIED]

Response should instead use format:
```
## INVESTIGATION REQUIRED

**Observation:** [what I see]
**Hypothesis:** [what I suspect - UNVERIFIED]
**Required to verify:**
- [ ] Read: [specific file needed]
- [ ] Trace: [execution path to follow]
- [ ] Test: [experiment to run]

Cannot proceed without this evidence.
```"""


@hook_main
def main():
    """Main hook entry point."""
    input_data = json.load(sys.stdin)

    response = input_data.get("response", "")
    if not response:
        print(json.dumps({}))
        return 0

    violations = check_speculation_violations(response)

    if not violations:
        print(json.dumps({}))
        return 0

    # Log violations for audit trail
    snippet = response[:200]
    log_violation(violations, snippet)
    log_to_constructional_blocks(violations, snippet)

    # Block the response
    message = format_block_message(violations)
    print(json.dumps({
        "decision": "block",
        "reason": "SPECULATION_GATE",
        "message": message,
    }))
    return 2


def log_violation(violations: list[dict], content_snippet: str):
    """Log violation to SQLite for pattern analysis."""
    try:
        import sqlite3
        from datetime import datetime
        from pathlib import Path

        db_path = Path("P:/.claude/hooks/speculation_violations.sqlite")
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                violation_types TEXT,
                snippet TEXT
            )
        """)
        conn.execute(
            "INSERT INTO violations (timestamp, violation_types, snippet) VALUES (?, ?, ?)",
            (
                datetime.now().isoformat(),
                json.dumps([v["type"] for v in violations]),
                content_snippet
            )
        )
        conn.commit()
        conn.close()
    except Exception:
        # Don't fail the hook if logging fails
        pass


def log_to_constructional_blocks(violations: list[dict], content_snippet: str):
    """Log to constructional_blocks.jsonl for hook-audit integration."""
    try:
        from datetime import datetime
        from pathlib import Path

        log_file = Path("P:/.claude/hooks/logs/constructional_blocks.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        for v in violations:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "hook": "speculation_gate",
                "reason": f"{v['type']}: {v['detail'][:100]}",
                "command": content_snippet[:200],
                "action": "block"
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())
```

---

**End of Collection**
**Total Lines:** 2,485 lines across 4 hooks
**Export Date:** 2026-02-08
**Status:** Complete, unmodified source code
