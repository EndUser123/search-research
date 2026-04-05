# ADR-20260322: Skill-First Gate Enforcement Fix

**Status:** Proposed
**Date:** 2026-03-22
**Context:** Skill-first gate enforcement is "broken by design" due to terminal_id dependency creating a single point of failure

---

## Decision

**Implement Hybrid Fallback with Session_ID** - Always create intent files using terminal_id when available, session_id as fallback to ensure enforcement works even when terminal_id detection fails.

---

## Rationale

The current skill-first gate has a single point of failure: intent file creation in `skill_enforcer.py` (lines 152-156) returns early if `terminal_id` is missing, causing the PreToolUse gate to never fire. This violates the constitutional requirement for skill-first enforcement.

The hybrid fallback approach balances:
- **Reliability**: Enforcement works even without terminal_id
- **Multi-terminal safety**: Session-scoped fallback provides weaker but acceptable isolation
- **Graceful degradation**: System continues working with reduced guarantees rather than failing open
- **Implementation complexity**: Medium (no framework changes required)

**Evidence:**
- Codebase analysis: `PreToolUse_skill_pattern_gate.py:547` shows the gate already handles multiple intent file paths
- Web research: "Stateful enforcement is acceptable when correctness requires it" (hook design best practices 2026)
- GoT analysis: Candidate 1 has highest probability (0.65) and best risk/reward profile

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|-----------|
| **Reliability** | Enforcement works without terminal_id | Session-scoped files (weaker isolation than terminal-scoped) |
| **Maintainability** | Clear fallback logic | Adds complexity to intent file reading |
| **Security** | Graceful degradation vs fail-open | Weaker multi-terminal isolation with session fallback |

---

## Multi-Terminal Safety

**Safe with fallback strategy:**
- Terminal-scoped intent files preferred (strong isolation)
- Session-scoped fallback when terminal_id unavailable (weaker but acceptable)
- No shared mutable state across terminals
- Each terminal gets its own intent file path

**Concurrency safety:**
- Intent file paths include scope_id (terminal or session)
- No race conditions between terminals
- Graceful degradation if both terminal_id and session_id unavailable

---

## Implementation

**Phase 1: Modify Intent File Creation** (`UserPromptSubmit_modules/skill_enforcer.py`)

```python
def _log_command_intent_telemetry(context: HookContext, command: str) -> None:
    raw_session_id = _get_session_id(context)
    raw_terminal_id = _get_terminal_id(context)

    # Use terminal_id if available, otherwise session_id for isolation
    scope_id = raw_terminal_id if raw_terminal_id else raw_session_id
    scope_type = "terminal" if raw_terminal_id else "session"

    # Only skip if BOTH are missing (fail-closed)
    if not scope_id or scope_id == "unknown":
        # No isolation possible - skip rather than create shared state
        return

    # Create intent file with scope_id
    # (rest of function unchanged)
    state_file = base / f"terminals/{scope_id}/pending_command_intent.json"
```

**Phase 2: Update Gate Reading Logic** (`PreToolUse_skill_pattern_gate.py`)

The gate already checks multiple intent file paths (lines 547-589). Add comment explaining fallback behavior:

```python
# Intent file reading supports fallback:
# 1. Try terminal-scoped: terminals/{terminal_id}/pending_command_intent.json
# 2. Fallback to session-scoped: terminals/{session_id}/pending_command_intent.json
# 3. Legacy paths for backward compatibility
```

**Phase 3: Update Documentation** (`skill_enforcer.py`)

Change misleading comment (line 137):
- OLD: "TELEMETRY ONLY - NOT USED FOR ENFORCEMENT"
- NEW: "Intent files used for PreToolUse skill-first gate enforcement. Falls back to session_id when terminal_id unavailable."

**Phase 4: Testing**

- Test with terminal_id available (normal case)
- Test with terminal_id missing, session_id available (fallback case)
- Test with both missing (should skip intent file creation)
- Verify multi-terminal isolation with both scopes

---

## Alternatives

| Alternative | Pros | Cons | Rejection Rationale |
|-------------|------|------|---------------------|
| **A: Terminal ID Hardening** | Fixes root cause, strong isolation | May break workflows, complex detection, fail-closed | Too risky for production system |
| **B: Truly Stateless Gate** | No file I/O, true statelessness | Requires framework changes, schema dependency | Framework changes are high-risk |
| **C: Dual-Layer Enforcement** | Redundancy, robust | Duplicates mechanisms, violates consolidation | Violates consolidation principle |

---

## Consequences

**Positive:**
- Enforcement works even when terminal_id detection fails
- Graceful degradation without breaking existing workflows
- Clear documentation of actual behavior (vs "TELEMETRY ONLY" myth)
- Maintains multi-terminal safety with acceptable fallback

**Negative:**
- Session-scoped intent files provide weaker isolation than terminal-scoped
- Adds complexity to intent file management
- Requires documentation updates to reflect actual behavior

**Mitigations:**
- Prefer terminal-scoped files (existing behavior preserved)
- Session-scoped only as fallback (reduced scope but better than nothing)
- Add monitoring to track fallback frequency
- Document isolation guarantees per scope type

---

## Evidence Sources

- **Codebase Analysis**:
  - `P:\.claude\hooks\UserPromptSubmit_modules\skill_enforcer.py:152-156` - Intent file creation with terminal_id check
  - `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py:494-589` - "Stateless" gate reading intent files
  - `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py:137` - Contradictory "TELEMETRY ONLY" comment

- **Web Research** (via Perplexity Sonar):
  - "Stateless hook design vs stateful enforcement best practices 2026"
  - "Terminal ID detection multi-terminal isolation Claude Code hooks"
  - "Intent file design pattern skill-first gate enforcement"

- **PowerShell Transcript Analysis**:
  - `C:\Users\brsth\Downloads\PowerShell.txt` - Root cause analysis identifying three options

---

## Related

- **Constitutional Requirements**: CLAUDE.md - Multi-terminal isolation (CONSTITUTIONAL)
- **Hook Architecture**: `P:\.claude\hooks\CLAUDE.md` - Hook enforcement patterns
- **v4.0 Design Conflict**: Intent files documented as "TELEMETRY ONLY" but used for enforcement

---

**Decomposed by**: New ADR (no prior decision on this specific issue)
**Supersedes**: None (new problem identification)
