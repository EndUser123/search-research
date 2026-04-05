# Adversarial I/O Validation Review: Stop Completion/Negative Existence Guards

**Review Date**: 2026-03-31
**Files Reviewed**:
- `P:\.claude\hooks\Stop_completion_verification_guard.py`
- `P:\.claude\hooks\Stop_negative_existence_guard.py`

---

## Executive Summary

| Proposed Change | Risk Level | Verdict |
|----------------|------------|---------|
| Context window 200/200 → 400/100 | **LOW** | No new injection/traversal risk introduced |
| tool_events is None: fail-closed → fail-warn | **MEDIUM** | Security posture reduction; advisory bypass |
| Expand conversational verification phrases | **LOW** | Allowslist expansion; limited to message filtering |

**Critical Finding**: No path traversal or command injection vulnerabilities are introduced by the context window change. However, the fail-warn change on evidence unavailability represents a meaningful security posture reduction that warrants careful consideration.

---

## 1. Context Window Change Analysis (200/200 → 400/100)

### Current Implementation

**File**: `Stop_completion_verification_guard.py`, lines 372-376

```python
# Extract file paths from surrounding context
start = max(0, match.start() - 200)
end = min(len(response), match.end() + 200)
context = response[start:end]
```

### Code Flow

1. Regex patterns detect file operation claims (CREATION, MODIFICATION, DELETION, etc.)
2. Surrounding context (±200 chars) is extracted
3. `FILE_PATH_PATTERNS` regex extracts potential file paths from context
4. Extracted paths are stored in claims tuple: `(matched_text, claim_type, file_paths)`
5. Paths are used only for logging/display in block messages

### FILE_PATH_PATTERNS Regex Analysis

```python
FILE_PATH_PATTERNS = re.compile(
    r"[A-Z]:[\\/][^\"\s\]]+"           # Windows absolute: P:\path, C:/path
    r"|[/\\][^\"\s\]]+(?<![a-z])(?<![a-z])"  # Unix absolute: /path
    r"|\.\.[\\/][^\"\s\]]+"            # Relative traversal: ../path
    r"|\.[\\/][^\"\s\]]+"              # Relative current: ./path
    r"|['\"]([^'\"]+\.[^'\"]+)['\"]"   # Quoted paths
    r"|\b[\w-]+\.(?:py|js|ts|md|json|yaml|yml|txt|log|tmp|bak|old)\b",
    re.IGNORECASE,
)
```

### Adversarial Analysis: Is 400/100 Window Dangerous?

**Question**: Does expanding from ±200 to +400/-100 characters around the match point introduce new attack surface?

**Answer: NO**

**Reasoning**:

1. **No filesystem operations on extracted paths**: The extracted paths are used only for logging/display in block messages. They are NEVER passed to `os.path.*`, `Path.*`, `open()`, or any file operation function.

2. **Display-only attack vector**: Even if an adversarial path like `../../etc/passwd` or `P:\sensitive\file` is extracted and displayed in a block message, this is no worse than the LLM's original response text. The context window expansion does not amplify this.

3. **The regex itself is the actual boundary**: The actual "attack surface" is the LLM's response text itself. If the LLM writes `rm -rf /`, it does so regardless of whether we capture ±200 or ±400 characters. The guard's purpose is to detect and block such claims.

4. **No code execution**: `_extract_file_paths()` is pure regex extraction with no side effects:
   ```python
   def _extract_file_paths(text: str) -> list[str]:
       paths = []
       for match in FILE_PATH_PATTERNS.finditer(text):
           path = match.group(0)
           if path.startswith(("'", '"')) and path.endswith(("'", '"')):
               path = path[1:-1]
           paths.append(path)
       # Deduplicate...
       return unique_paths
   ```

**Minor Finding**: The `(?<![a-z])(?<![a-z])` negative lookbehind at the end of the Unix absolute path pattern is redundant (applies same check twice). This is a style issue, not a security issue.

---

## 2. tool_events is None: Fail-Closed → Fail-Warn

### Current Behavior (Both Guards)

**Stop_completion_verification_guard.py**, lines 519-542:
```python
# Evidence system unavailable - ALWAYS block (fail-closed)
if tool_events is None:
    _logger.warning(
        "BLOCK: Evidence store unavailable - cannot verify %d file operation claim(s)",
        len(claims),
    )
    lines = ["**Unverified File Operation Claim Detected**\n"]
    # ... block message ...
    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_completion_verification_guard",
    }
```

**Stop_negative_existence_guard.py**, lines 476-504:
```python
# Evidence system unavailable - ALWAYS block (fail-closed)
if tool_events is None:
    _logger.warning(
        "BLOCK: Evidence store unavailable - cannot verify %d negative existence claim(s)",
        len(claims),
    )
    # ... block message ...
    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_negative_existence_guard",
    }
```

### Proposed Change

Change `tool_events is None` handling from hard block to advisory warning (fail-warn).

### Security Impact Analysis

| Aspect | Current (fail-closed) | Proposed (fail-warn) |
|--------|------------------------|---------------------|
| **Security Posture** | Blocks unverified claims when evidence system is down | Allows claims through when evidence system is down |
| **Failure Mode** | Deny-until-verified | Allow-until-verified |
| **Attack Vector** | Cannot be exploited (blocks) | Adversary could make unverified claims when evidence store is unavailable |
| **False Positive Rate** | High (blocks legitimate work when system is degraded) | Zero (never blocks due to this condition) |

**Risk**: If evidence store becomes unavailable (import fails, `load_tool_events()` raises, spool files missing), the guard currently BLOCKS responses making file existence claims. Under fail-warn, those claims would be ALLOWED through.

**Severity**: MEDIUM - This is a deliberate security posture reduction. The rationale appears to be reducing false positives during evidence system outages at the cost of allowing some unverified claims through.

**Concurrency Note**: The evidence store can be unavailable in one terminal while working in another. The current fail-closed behavior protects against a single point of failure. Fail-warn removes that protection.

---

## 3. Conversational Verification Phrases Allowlist Expansion

### Current Patterns

**Stop_completion_verification_guard.py**, lines 282-299:
```python
OBVIOUS_ALLOWLIST = re.compile(
    # Conversational denials
    r"\bI\s+did(?:n'?t|dn't| not)\s+(?:create|modify|delete|...)"
    r"|\bI\s+hav(?:e'?n't|en't|e not)\s+(?:created|modified|...)"
    # Future tense
    r"|\bwill\s+(?:create|modify|delete|...)"
    # ...
)
```

**Stop_negative_existence_guard.py**, lines 96-120:
```python
OBVIOUS_ALLOWLIST = re.compile(
    # Capability/network statements
    r"\bno\s+(?:internet\s+access|network\s+access|network)\b"
    r"|\b(?:offline|no\s+connection)\b"
    # Domain knowledge
    r"|\bno\s+configuration\s+needed\b"
    # Conversational denials (expanded in ADR-20260323)
    r"|\bI\s+didn(?:'?t)?\s+(?:change|modify|delete|...)"
    r"|\bI\s+haven(?:'?t)?\s+(?:changed|modified|...)"
    # Additional conversational forms
    r"|\bI\s+don(?:'?t)?\s+(?:think\s+)?I\s+(?:change|...)"
    r"|\bI\s+wasn(?:'?t)?\s+(?:the\s+one\s+who\s+)?(?:changed|...)"
    # ...
)
```

### Proposed Expansion

The user mentions "add conversational verification phrases to allowlist" - likely additional forms like:
- "I didn't touch X"
- "I haven't looked at Y"
- "I never accessed Z"

### Security Impact

**Risk**: LOW

The allowlist is used to FILTER OUT false positives - claims that should NOT trigger blocking even though they superficially match the detection patterns. Expanding the allowlist REDUCES false positives but does not create new attack surface.

**Key Point**: Allowlist expansion cannot enable an attack. At worst, it allows a legitimate-looking claim through that should have been blocked, but:
1. The claim must still match the conversational pattern (not arbitrary text)
2. No new code paths are executed based on allowlisted text
3. The extracted paths (if any) are still not used for filesystem operations

---

## 4. Path Extraction Validation

### Current State: NO VALIDATION

Both files extract paths but do NOT validate them:

**Stop_completion_verification_guard.py**:
```python
def _extract_file_paths(text: str) -> list[str]:
    """Extract file paths from text using FILE_PATH_PATTERNS."""
    paths = []
    for match in FILE_PATH_PATTERNS.finditer(text):
        path = match.group(0)
        if path.startswith(("'", '"')) and path.endswith(("'", '"')):
            path = path[1:-1]
        paths.append(path)
    # ... deduplicate ...
    return unique_paths
```

**Where used**:
- Line 378: `claims.append((matched_text, claim_type, file_paths))`
- Line 495: Logged but never used for filesystem operations
- Lines 531-532, 555-556: Displayed in block message only

**Stop_negative_existence_guard.py**:
- Uses `_extract_read_targets()` to track what was read
- Uses `_should_exempt_claim()` for exemption logic
- No path validation against filesystem

### Potential Improvement (Not Currently Needed)

If paths were to be validated (e.g., checking if file exists), the proper approach would be:

```python
# Safe path validation (if ever needed)
from pathlib import Path

def _is_safe_path(path: str) -> bool:
    """Check if path is safe for filesystem operations."""
    try:
        p = Path(path)
        # Resolve to absolute and check it's within allowed roots
        resolved = p.resolve()
        # Define allowed roots (e.g., project directory)
        allowed_roots = [Path.cwd()]
        return any(str(resolved).startswith(str(root)) for root in allowed_roots)
    except (OSError, ValueError):
        return False
```

However, this is NOT needed currently since paths are display-only.

---

## 5. Findings Summary

### No Path Traversal Risk

- Expanding context window does NOT introduce path traversal vulnerabilities
- Extracted paths are used only for logging/display, never for filesystem operations
- The `FILE_PATH_PATTERNS` regex correctly bounds the extraction

### No Command Injection Risk

- No extracted paths are passed to `subprocess`, `os.system`, or shell commands
- No dynamic code execution based on extracted paths
- Display-only use means injection payloads have no effect

### Fail-Warn Change Requires Careful Consideration

The proposed change from fail-closed to fail-warn for `tool_events is None` is a security posture decision:

**Pros**:
- Reduces false positives when evidence system is degraded
- Allows legitimate work to continue during transient failures

**Cons**:
- Allows unverified file operation claims when evidence unavailable
- Removes defense-in-depth for availability compromise scenarios

**Recommendation**: Document this as an intentional security trade-off. Consider adding a telemetry event so the frequency of evidence unavailability can be monitored.

### No File Existence Checks Needed

Given that:
1. Extracted paths are display-only (never used for filesystem ops)
2. The guards BLOCK responses (not individual file operations)
3. No `open()`, `os.path.exists()`, or similar calls on extracted paths

...adding file existence validation at this level would be over-engineering. The existing `PreToolUse_*` hooks that validate actual file operations are the appropriate layer for such checks.

---

## 6. Test Recommendations

If implementing these changes, verify:

1. **Context window change**:
   - Old and new windows extract same paths for typical claims
   - Larger window does not cause regex catastrophic backtracking on adversarial input
   - Block messages remain readable with expanded path lists

2. **Fail-warn change**:
   - `tool_events is None` now returns advisory instead of block
   - `tool_events == []` (empty, not None) still blocks correctly
   - Logs capture the advisory events for monitoring

3. **Allowlist expansion**:
   - New patterns do not create false negatives for actual file operation claims
   - "I didn't touch X" correctly exempts denial without requiring verification
   - "I haven't looked at Y" correctly exempts denial without requiring verification
