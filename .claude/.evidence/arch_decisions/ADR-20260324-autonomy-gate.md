# ADR-20260324: Autonomy Gate — Enforcing Execution Directives

**Status**: Accepted
**Date**: 2026-03-24
**Context**: User gives explicit execution signal (trailing "0") but AI defers back with "Should I proceed?" instead of executing. From MiniMax transcript: AI ignores execution directive and offers path choices instead of proceeding autonomously.

## Decision

**Implement a stateless Stop hook that blocks deferral patterns after explicit execution signals.**

### Problem Statement

When a user issues an autonomous execution signal (e.g., trailing "0" meaning "execute all"), the AI sometimes:
1. Asks "Should I proceed with Domain 6, or skip to Domain 7?"
2. Offers path choices instead of executing
3. Defers decision-making back to the user

This violates the user's explicit intent for autonomous execution.

### Solution

A stateless Stop hook (`autonomy_gate.py`) that:
- Detects execution signals in user input (currently: trailing "0")
- Detects deferral patterns in assistant response
- Blocks when signal detected AND response defers

### Implementation

| Component | Location | Purpose |
|-----------|----------|---------|
| **Gate module** | `P:/.claude/hooks/autonomy_gate.py` | Pure function evaluation |
| **Router integration** | `Stop_router.py:HOOK_SEQUENCE` | After existing gates |
| **Environment toggle** | `AUTONOMY_GATE_ENABLED` (default: `true`) | Enable/disable |
| **Tests** | `tests/test_autonomy_gate.py` | 7 test cases |

### Detection Logic

**Execution signals** (currently narrow scope):
- Trailing "0" in user prompt: `"Implement Domain 6a now 0"`

**Deferral patterns** (regex + similarity match):
- `r"\bshould\b.*\bproceed\b"`
- `r"\bshould\b.*\bskip\b"`
- `r"\bskip to\b.*\bdomain\b"`
- `r"\bwould you like me to\b"`
- `r"\bdo you want me to\b"`
- Template similarity threshold: 0.70

### Payload Mapping

**Critical fix from proposal**: Use actual Stop router payload fields:

```python
# WRONG (from proposal):
draft = payload.get("assistant_draft", "") or ""

# CORRECT (use actual fields):
user_prompt = payload.get("prompt", "") or payload.get("user_prompt", "") or ""
response = payload.get("assistant_response", "") or payload.get("response", "") or ""
```

See `Stop_router.py:531-534` for field definitions.

## Multi-Terminal Safety

- **Safe**: Stateless design, payload-based evaluation
- **Isolation**: Each terminal processes its own Stop payload independently
- **No shared state**: No cross-terminal contamination
- **Compact-safe**: Only cares about current turn, not history

## Constitutional Compliance

| Principle | Status | Evidence |
|------------|--------|----------|
| **Multi-terminal isolation** | ✅ Safe | Stateless, no shared mutable state |
| **Hook design constraints** | ✅ Compliant | No external APIs, stdlib only |
| **Fail-open** | ✅ Enabled | Returns `{"continue": True}` on ambiguity |

## Integration Points

### 1. Add to HOOK_SEQUENCE

**File**: `P:\.claude/hooks\Stop_router.py` (after line ~150)

```python
HOOK_SEQUENCE = [
    # ... existing hooks ...
    ("Stop_tdd_refactor_gate.py", "TDD_REFACTOR_GATE_ENABLED", True, "inprocess"),
    ("autonomy_gate.py", "AUTONOMY_GATE_ENABLED", True, "inprocess"),  # NEW
]
```

### 2. Add to ACTIVE_RUNTIME_HOOKS

**File**: `P:\.claude/hooks\Stop_router.py` (line ~169)

```python
ACTIVE_RUNTIME_HOOKS = frozenset({
    # ... existing hooks ...
    "Stop_tdd_refactor_gate.py",
    "autonomy_gate.py",  # NEW
})
```

### 3. Environment Variable

**File**: `P:\.claude\settings.json`

```json
{
  "env": {
    "AUTONOMY_GATE_ENABLED": "true"
  }
}
```

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|-----------|
| **Autonomy** | ✅ AI respects execution directives | ⚠️ Less "helpful" deferring (intentional) |
| **Reliability** | ✅ Explicit commands executed | ⚠️ Pattern matching may have false positives |
| **Maintainability** | ✅ Simple, stateless, stdlib-only | ⚠️ Deferral patterns may need tuning |

## Failure Conditions

**False Positive Risk**: Legitimate questions containing "should I proceed" could be blocked
- **Mitigation**: Patterns are narrow (requires exact phrasing)
- **Mitigation**: User can disable via `AUTONOMY_GATE_ENABLED=false`

**False Negative Risk**: AI might use different deferral phrasing
- **Mitigation**: Add patterns as discovered
- **Mitigation**: Similarity threshold catches variations

## Implementation Effort

| Task | Time |
|------|------|
| Create `autonomy_gate.py` | 30 min |
| Add to HOOK_SEQUENCE and settings.json | 15 min |
| Write tests | 30 min |
| Integration testing and validation | 45 min |
| **Total** | **~2 hours** |

## Reversibility

**Score**: 1.25 (Trivial)
- Can be disabled via environment variable
- Can be removed from HOOK_SEQUENCE
- No permanent state changes

## Prevention

**Architectural rule**: When user gives explicit execution directive ("0", "!!exec", etc.), AI MUST either:
1. Proceed directly with execution, OR
2. Explicitly say "cannot comply" with reason

AI MUST NOT defer back with "should I proceed?" or offer path choices.

## Alternative Considered

**Option B: UserPromptSubmit hook** — Detect execution signal earlier and inject context reminder.
- **Rejected**: Stop-time is the critical moment; deferral happens in draft response
- **Selected**: Stop hook (Option A) over UserPromptSubmit (Option B)

## Related Decisions

- **ADR-20260312**: Skill enforcement enhancement — Three-layer defense against slash command bypass
- **ADR-20260323**: Terminal ID normalization — Multi-terminal isolation patterns
- **Hook design constraints**: No external APIs, fail-open, stateless design

## References

- Source transcript: `ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/1a3ee5db-40c9-4c16-a014-163f0c9a662a/03-23-2025-it-lies-0.txt`
- Proposal: `ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/43f80955-7b4f-4383-ba64-6e7922a2acdd/review_bundle_hooks_memories_debugRCA_2026-03-23.md`
- Hook architecture: `P:\.claude\hooks\CLAUDE.md`
- Stop router: `P:\.claude\hooks\Stop_router.py`
