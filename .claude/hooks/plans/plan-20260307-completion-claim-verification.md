# Implementation Plan: Completion Claim Verification

**Date**: 2026-03-07
**Status**: REVISED (Critical issues addressed, ready for re-review)
**Priority**: HIGH
**Revision History**:
- 2026-03-07: Initial plan (DRAFT) - 3 CRITICAL blockers found during review
- 2026-03-07: REVISED - Fixed all CRITICAL and HIGH priority issues from verification

## Problem Statement

Claude Code agents frequently declare completion ("✅ ALL FILES PASS", "fixed and tested", "verified working") without runtime testing evidence. This cognitive failure pattern causes:
- Premature victory declarations with incomplete work
- User frustration from repeated "actually not fixed" cycles
- Erosion of trust in agent completion claims

**Recent Example**: Declared "✅✓✓ ALL FILES PASS SYNTAX VALIDATION ✓✓✓" when only 3 of 13+ hooks were actually fixed.

## Context Analysis

### Existing Infrastructure (Already Built)

We have mature infrastructure we can leverage:

1. **evidence_store.py** (SQLite WAL, session-scoped):
   - `append_tool_event()` (PostToolUse) tracks every tool invocation
   - `load_tool_events(session_id)` retrieves tool events for a session
   - `resolve_session_id()` resolves session_id from env or persisted context
   - Stores: tool_name, command, cwd, output_excerpt, session_id, terminal_id
   - Event dict structure: `{"name": "Bash", "command": "pytest", ...}` (NOT "tool_name")

2. **PostToolUse_router.py** (lines 379-424):
   - Already calls `append_tool_event()` for ALL tool usage
   - Links tools to session_id and terminal_id
   - Foundation for empirical validation

3. **StopHook_unverified_stance.py** (237 lines):
   - Existing verification hook for stance validation
   - Uses structlog for JSON logging
   - Has enable/disable config and warn/block modes
   - main() function ends at line 147 (insert completion check after this)
   - Stop hook input schema: transcript_path, conversation, response (NO session_id field)

### Allowed APIs (Verified from Documentation)

**From evidence_store.py:**
- `load_tool_events(session_id: str, limit: int = 500, terminal_id: str = "") -> list[dict]`
  - Returns list of tool event dictionaries
  - Each event has keys: `name`, `command`, `cwd`, `output_excerpt`, `session_id`, `terminal_id`
- `resolve_session_id(explicit: str = "") -> str`
  - Resolves session_id from explicit arg > env > persisted context
  - Use this when session_id not available in Stop hook input

**Anti-patterns to Avoid:**
- ❌ `read_session_context(session_id)` - Function takes 0 parameters, not session_id
- ❌ `event.get("tool_name")` - Event dict uses "name" key, not "tool_name"
- ❌ `data.get("session_id")` - Stop hook input doesn't have session_id field
- ❌ Regex with unclosed character classes: `r"✅.*\u2705.*complete"` causes re.error

### Key Constraints

- **No new infrastructure**: Reuse existing evidence_store and tool tracking
- **Single file change**: Extend existing Stop hook, don't create new one
- **~70 lines of code**: Minimal complexity addition (increased from ~50 due to timeout/error handling)
- **Multi-terminal safe**: Leverage existing terminal_id isolation via load_tool_events(session_id, terminal_id=...)

## Proposed Solution

### Core Approach

Extend `StopHook_unverified_stance.py` to detect completion claims and verify runtime testing evidence.

### Implementation Design

**File**: `P:\.claude\hooks\StopHook_unverified_stance.py`

**Add after line 147** (end of existing main() function):

```python
# === COMPLETION CLAIM VERIFICATION ===

COMPLETION_PATTERNS = [
    re.compile(r"all\s+(files|hooks|tests)\s+pass", re.IGNORECASE),
    re.compile(r"✅.*(complete|fixed|done)", re.IGNORECASE),
    re.compile(r"\b(issue|bug|problem)\s+(?:is\s+)?fixed\b", re.IGNORECASE),
    re.compile(r"test(s)?\s+passed", re.IGNORECASE),
    re.compile(r"verified\s+(?:and\s+)?working", re.IGNORECASE),
]

RUNTIME_TOOLS = {"Bash", "Edit", "Read", "Grep", "Glob"}
RUNTIME_COMMAND_PATTERNS = ["subprocess", "pytest", "python", "node", "npm test"]

def _check_completion_claim(response: str, session_id: str) -> tuple[bool, str]:
    """Check if completion claim has sufficient runtime evidence."""
    for pattern in COMPLETION_PATTERNS:
        if pattern.search(response):
            has_runtime = _check_for_runtime_tools(session_id)
            if not has_runtime:
                return False, (
                    "Completion claim without runtime testing evidence. "
                    f"Required: Tool usage from {', '.join(list(RUNTIME_TOOLS))} "
                    f"or commands containing: {', '.join(RUNTIME_COMMAND_PATTERNS)}"
                )
    return True, "Sufficient evidence"

def _check_for_runtime_tools(session_id: str) -> bool:
    """Query evidence_store for runtime tool usage."""
    try:
        from evidence_store import load_tool_events
        import signal

        # Timeout protection (1 second max for evidence query)
        def timeout_handler(signum, frame):
            raise TimeoutError("Evidence store query timeout")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)

        try:
            # CORRECTED: Use load_tool_events() instead of read_session_context()
            tool_events = load_tool_events(session_id, limit=100)

            for event in tool_events:
                # CORRECTED: Use 'name' field instead of 'tool_name'
                tool_name = event.get("name", "")
                command = event.get("command", "")

                # Check tool names
                if tool_name in RUNTIME_TOOLS:
                    return True

                # Check command strings for runtime patterns
                command_lower = command.lower()
                if any(pattern.lower() in command_lower for pattern in RUNTIME_COMMAND_PATTERNS):
                    return True

            return False
        finally:
            signal.alarm(0)  # Cancel timeout

    except (ImportError, TimeoutError, Exception) as e:
        logger.warning("evidence_store_query_failed", error=str(e))
        return False  # Fail open
```

**Integration in main() function**:

```python
# After line 147 (after existing main() logic), add:
if UNVERIFIED_STANCE_ENABLED:
    response_text = input_data.get("response", "")

    # CORRECTED: Resolve session_id from environment (Stop hook input doesn't have session_id field)
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if not session_id:
        # Fallback: try to resolve from evidence_store
        try:
            from evidence_store import resolve_session_id
            session_id = resolve_session_id("")
        except Exception:
            pass

    # Only check if we have a valid session_id
    if session_id:
        claim_valid, claim_msg = _check_completion_claim(response_text, session_id)
        if not claim_valid:
            if UNVERIFIED_STANCE_MODE == "block":
                logger.error("completion_claim_blocked", message=claim_msg)
                output_result(allow=False, reason=claim_msg)
                return
            else:  # warn mode
                logger.warning("completion_claim_warn", message=claim_msg)
                advisory = f"⚠️ {claim_msg}\n\nThis would block in non-warn mode."
                output_advisory(advisory)
                return
```

### How It Works

1. **Pattern Detection**: Regex scans response for completion claim patterns
2. **Evidence Query**: Queries evidence_store for runtime tool usage (pytest, subprocess.run, etc.)
3. **Decision**: Blocks (or warns) if claim made without runtime evidence
4. **Multi-terminal Safe**: Uses session_id for isolated validation

### Configuration

Uses existing config:
- `UNVERIFIED_STANCE_ENABLED`: Enable/disable the entire check
- `UNVERIFIED_STANCE_MODE`: "block" or "warn"

## Test Discovery

### Test Scenarios

1. **True Positive** (should block):
   - Agent says "✅ all files fixed" without running tests
   - Expected: Block with "Completion claim without runtime testing evidence"

2. **True Negative** (should allow):
   - Agent says "✅ all files fixed" after running pytest
   - Expected: Allow (runtime evidence found)

3. **False Positive Prevention**:
   - Agent discusses "fixed pattern" without claiming completion
   - Expected: Allow (no completion pattern match)

4. **Multi-terminal Isolation**:
   - Terminal A runs tests, Terminal B claims completion
   - Expected: Block Terminal B (session isolation works)

### Verification Commands

```bash
# Test 1: Block premature claim (no session_id = no evidence)
echo '{"response": "✅ all files fixed"}' | \
  python StopHook_unverified_stance.py
# Expected: Exit code 0, allow (no session_id, check skipped)

# Test 2: Block claim with session_id but no evidence
export CLAUDE_SESSION_ID="test-session-no-evidence"
echo '{"response": "✅ all files fixed"}' | \
  python StopHook_unverified_stance.py
# Expected: Advisory in warn mode (no runtime tools found)

# Test 3: Allow with runtime evidence (run Bash tool first)
# Step A: Set session_id and run a command
export CLAUDE_SESSION_ID="test-session-with-evidence"
echo "test command" | bash
# Step B: Now claim completion (evidence exists)
echo '{"response": "✅ all files fixed after testing"}' | \
  python StopHook_unverified_stance.py
# Expected: Exit code 0, allow (Bash tool found in evidence)

# Test 4: Multi-terminal isolation
# Terminal A: Run tests with session_id="test-term-a"
export CLAUDE_SESSION_ID="test-term-a"
pytest tests/ -q
# Terminal B: Try to claim completion with different session_id
export CLAUDE_SESSION_ID="test-term-b"
echo '{"response": "✅ all files fixed"}' | \
  python StopHook_unverified_stance.py
# Expected: Advisory (no evidence in session test-term-b)
```

## Risks, Success Criteria, Dependencies

### Risks

1. **Pattern Over-Matching**:
   - Risk: Regex blocks legitimate discussion of "fixed" concepts
   - Mitigation: Patterns require specific completion phrasing ("all files pass", "verified working")
   - Severity: LOW (warn mode available for tuning)

2. **Evidence Store Failure**:
   - Risk: evidence_store query fails, causes false positives
   - Mitigation: `_check_for_runtime_tools()` fails open (returns False on exception, but doesn't crash)
   - Severity: LOW (graceful degradation)

3. **Multi-terminal Race**:
   - Risk: Test run in Terminal A not immediately visible in Terminal B
   - Mitigation: SQLite WAL mode provides concurrent access; session_id isolation
   - Severity: LOW (existing infrastructure handles this)

### Success Criteria

1. **Blocks premature claims**: "✅ all fixed" without tests → block
2. **Allows verified claims**: "✅ all fixed" after pytest → allow
3. **Zero false negatives**: Legitimate completion with evidence never blocked
4. **<50 lines added**: Minimal complexity, no new infrastructure

### Dependencies

1. **evidence_store.py**: Must have `load_tool_events()` function
   - Status: ✅ Verified exists at line 376
   - API: `load_tool_events(session_id: str, limit: int = 500, terminal_id: str = "") -> list[dict]`
   - Event dict keys: `name`, `command`, `cwd`, `output_excerpt`, `session_id`, `terminal_id`

2. **evidence_store.py**: Must have `resolve_session_id()` function
   - Status: ✅ Verified exists at line 196
   - API: `resolve_session_id(explicit: str = "") -> str`
   - Use for: Resolving session_id when not in Stop hook input

3. **PostToolUse_router.py**: Must be tracking tool events
   - Status: ✅ Verified exists at lines 379-424
   - Calls: `append_tool_event(session_id, terminal_id, tool_name, command, cwd, output_excerpt)`

4. **StopHook_unverified_stance.py**: Must have structlog infrastructure
   - Status: ✅ Verified exists (lines 1-236)
   - Has: UNVERIFIED_STANCE_ENABLED, UNVERIFIED_STANCE_MODE config
   - main() function ends at line 147 (insert completion check after this)

5. **Stop Router** (Stop_router.py): Must verify session_id availability in Stop input
   - Status: ⚠️ NEEDS VERIFICATION
   - Check: Does Stop hook input include session_id field?
   - Fallback: Use `os.environ.get("CLAUDE_SESSION_ID")` if not in input

## Implementation Plan

### Phase 1: Add Completion Claim Detection
**File**: `StopHook_unverified_stance.py`
**Lines**: Add ~70 lines after line 147

1. Add COMPLETION_PATTERNS regex list (with corrected syntax)
2. Add RUNTIME_TOOLS set (Bash, Edit, Read, Grep, Glob)
3. Add RUNTIME_COMMAND_PATTERNS list (subprocess, pytest, python, etc.)
4. Add _check_completion_claim() function
5. Add _check_for_runtime_tools() function with timeout protection
6. Integrate into main() function after line 147

**CORRECTED API USAGE**:
- Use `load_tool_events(session_id)` NOT `read_session_context(session_id)`
- Resolve session_id from environment: `os.environ.get("CLAUDE_SESSION_ID")`
- Access event fields: `event.get("name")` NOT `event.get("tool_name")`

**Estimated Effort**: M (1-2 hours)
**Verification**: Run Test 1 and Test 2 scenarios

### Phase 2: Evidence Store Integration Testing
**Task**: Verify evidence_store API integration works correctly

1. Test load_tool_events() returns actual tool events
2. Test resolve_session_id() fallback when session_id not in environment
3. Test timeout protection doesn't crash hook
4. Test event dict field names match code expectations

**Estimated Effort**: M (1 hour)
**Verification**: Unit tests with synthetic evidence data

### Phase 3: Configuration Validation
**Task**: Verify existing config hooks work correctly

1. Test UNVERIFIED_STANCE_ENABLED=false disables the check
2. Test UNVERIFIED_STANCE_MODE=warn produces warnings without blocking
3. Test UNVERIFIED_STANCE_MODE=block actually blocks
4. Test multi-terminal isolation with different session_ids

**Estimated Effort**: S (30 minutes)
**Verification**: Manual testing with config variations

### Phase 4: Documentation
**Task**: Update CLAUDE.md or hooks documentation

1. Document completion claim verification feature
2. Document allowed APIs from evidence_store.py
3. Document how to disable if too aggressive
4. Document pattern tuning (add/remove patterns)
5. Add anti-patterns section showing common mistakes

**Estimated Effort**: S (30 minutes)
**Verification**: Review documentation for clarity

## Rollback Strategy

If completion claim verification proves too aggressive:

1. **Immediate rollback**: Set `UNVERIFIED_STANCE_ENABLED=false` in config
2. **Pattern tuning**: Remove over-matching patterns from COMPLETION_PATTERNS
3. **Mode switch**: Change from "block" to "warn" mode
4. **Complete removal**: Delete added ~50 lines (single file change, easy to revert)

## Next Actions

1. **Implement Phase 1**: Add completion claim detection to StopHook_unverified_stance.py
2. **Test with Test 1**: Verify premature claims are blocked
3. **Test with Test 2**: Verify legitimate claims with evidence are allowed
4. **Monitor for false positives**: If patterns too aggressive, tune in Phase 2
5. **Document**: Add to hooks documentation once stable

---

**Sign-off**: Ready for implementation when user approves approach.

## Verification Fixes Applied (2026-03-07)

This section documents the critical issues found during plan verification and the fixes applied.

### Critical Issues Fixed (BLOCKERS → RESOLVED)

1. **[PR-001] Wrong API signature** - FIXED
   - **Issue**: Plan used `read_session_context(session_id)` but function takes 0 parameters
   - **Fix**: Changed to `load_tool_events(session_id)` with correct API signature
   - **Reference**: evidence_store.py line 376

2. **[PR-002] Missing session_id field** - FIXED
   - **Issue**: Plan assumed `data.get("session_id")` but Stop hook input doesn't have this field
   - **Fix**: Resolve session_id from environment: `os.environ.get("CLAUDE_SESSION_ID")`
   - **Fallback**: Use `resolve_session_id("")` if environment variable not set

3. **[PR-003] Regex syntax error** - FIXED
   - **Issue**: Pattern had unclosed character class: `r"✅.*\u2705.*complete|fixed|done"`
   - **Fix**: Changed to `r"✅.*(complete|fixed|done)"` with proper grouping

### High Priority Issues Fixed

4. **[PR-004] Wrong event field names** - FIXED
   - **Issue**: Plan used `event.get("tool_name")` but actual dict uses `"name"` key
   - **Fix**: Changed to `event.get("name")` to match evidence_store.py:428 structure
   - **Also fixed**: Added word boundaries to prevent over-matching "discussing fixed bugs"

5. **[PR-005] Timeout protection** - FIXED
   - **Issue**: No timeout protection on evidence_store queries (can hang 5 seconds)
   - **Fix**: Added signal.alarm(1) timeout wrapper around load_tool_events() call
   - **Fallback**: Return False on timeout, log warning

6. **[PR-006] RUNTIME_TOOLS set** - FIXED
   - **Issue**: Plan checked for "subprocess.run" but actual tool_name values are "Bash", "Edit", etc.
   - **Fix**: Updated RUNTIME_TOOLS to `{"Bash", "Edit", "Read", "Grep", "Glob"}`
   - **Also added**: RUNTIME_COMMAND_PATTERNS to check command strings for "subprocess", "pytest", etc.

### Documentation Improvements

7. **Added "Allowed APIs" subsection** to Context Analysis:
   - Documents correct function signatures from evidence_store.py
   - Lists event dict structure with actual field names
   - Provides anti-patterns section showing common mistakes

8. **Updated test scenarios** with concrete commands:
   - Test 1: Block premature claim (no session_id)
   - Test 2: Block claim with session_id but no evidence
   - Test 3: Allow with runtime evidence (Bash tool found)
   - Test 4: Multi-terminal isolation verification

9. **Added Phase 2: Evidence Store Integration Testing**:
   - Test load_tool_events() returns actual tool events
   - Test resolve_session_id() fallback behavior
   - Test timeout protection doesn't crash hook
   - Test event dict field names match code expectations

### Plan Quality Improvements

- **Insertion point corrected**: "Add after line 147" (end of main()) instead of line 120
- **API references added**: Specific line numbers for all evidence_store.py functions
- **Test commands updated**: Concrete bash commands showing how to test each scenario
- **Dependency verification**: Added NEEDS VERIFICATION for Stop router session_id availability

### Re-Review Status

All CRITICAL and HIGH priority issues from adversarial review have been addressed. Plan is now ready for re-verification with `/plan-workflow review`.
