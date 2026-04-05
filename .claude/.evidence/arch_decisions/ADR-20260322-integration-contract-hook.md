# ADR-20260322: Integration Contract Hook — Block Critical-Path Deferral in ADRs

**Date**: 2026-03-22
**Status**: Proposed
**Decider**: brsth
**Buggy behavior**: Handoff V2 capture/restore path mismatch was marked "out of scope" in ADR; zero bytes transferred across 3 weeks of sessions

---

## Context

### The Failure

During the `feature/chs-consolidation` branch merge (commit `e81a2508bd`), a PreCompact capture fix was applied to `.claude/hooks/PreCompact_handoff_capture.py`, but the complementary restore path in `handoff_context_injector.py` was explicitly excluded as "out of scope":

```
The secondary issue (handoff_context_injector.py using wrong file path pattern)
remains unaddressed — that was out of scope for the original ADR.
```

This deferred a **critical-path integration point** for 3+ weeks. The mismatch was:

| Component | Path | Filename pattern |
|-----------|------|-----------------|
| Capture (PreCompact) | `P:/packages/handoff/.claude/state/handoff/` | `{terminal_id}_handoff.json` |
| Restore (SessionStart) | `P:/.claude/hooks/state/` | `handoff_{session_id}.json` |

> **Correction (ADR-20260322-revision-1)**: The actual capture path is `P:/packages/handoff/.claude/state/handoff/` (derived from `HANDOFF_PROJECT_ROOT=P:/packages/handoff` env var set at runtime). The legacy path `P:/.claude/state/handoff/` is used when the env var is not set. Both directories exist with active files.

The paths **and** the key/scope of the filename were both mismatched. No bytes could ever transfer.

### Why Existing Hooks Didn't Catch It

The codebase has hooks for:
- Skill enforcement (skill_first_gate)
- Investigation enforcement (investigation_gate)
- Fabrication detection (cross_validator)
- Anti-lazy declaration (declaration_reminder, arch_first_enforcer)

**None of them gate the decision to defer a critical integration point in an ADR or plan.**

### The Root Problem

"Out of scope" is a **local opt-out** that has no enforcement at the decision layer. When an ADR defers a critical-path issue, there is no hook that:

1. Detects that a deferral targets a critical integration point
2. Requires explicit severity justification to override
3. Blocks the ADR from being closed with the gap intact

---

## Decision

**Add an Integration Contract Hook** that gates the close of ADRs/plans containing critical-path integration deferrals.

### Scope Definition: What Is a "Critical Integration Point"?

An integration point is **critical** when:

- Component A produces state (file, DB record, pipe, env var)
- Component B consumes that state
- The production contract (path, schema, key name) is not shared between A and B
- Both A and B are on the same operational chain (capture → restore, auth_produce → auth_consume, etc.)

**Examples of critical integration points:**
- PreCompact capture → SessionStart restore (handoff envelope)
- `HandoffFileStorage.save_handoff()` → `load_handoff_envelope()` (path + key contract)
- Token production in hook A → Token consumption in hook B
- Any cross-hook state file where writer and reader are different files

**NOT critical (can be safely deferred):**
- Standalone refactors with no consumer dependencies
- Test-only changes
- Documentation updates
- Internal-only implementation details with single-component scope

### Hook Design: UserPromptSubmit Integration Contract Gate

**Event**: UserPromptSubmit (fires when user submits a message)

**Trigger pattern**: Text matching an ADR/plan close pattern combined with critical integration language:

```python
# ADR close patterns
ADR_CLOSE_PATTERNS = [
    r"(?i)ADR.*(?:close|complete|resolved|done)",
    r"(?i)out of scope",
    r"(?i)defer(?:red)?(?:ring)?",
    r"(?i)deprioritized",
]

# Critical integration language
CRITICAL_INTEGRATION_PATTERNS = [
    r"(?i)handoff[_-]?context[_-]?injector",
    r"(?i)restore.*capture",
    r"(?i)capture.*restore",
    r"(?i)state.*file.*path",
    r"(?i)envelope.*(?:load|save|read|write)",
]
```

**Detection logic**:
1. If message matches ADR_CLOSE_PATTERNS AND any CRITICAL_INTEGRATION_PATTERNS → flag
2. Extract the deferred issue
3. Check if a severity downgrade rationale is present (`--severity-downgrade`, explicit justification)
4. If no override: block with integration contract violation message

**Block message**:
```
⛔ INTEGRATION CONTRACT VIOLATION: CRITICAL-PATH DEFERRAL BLOCKED

The ADR/plan closes with an unaddressed critical integration point:

  Deferred issue: {extracted_issue}
  Capture path:   {path_A}
  Restore path:   {path_B}
  Mismatch type:  [directory | filename_key | schema | both]

Critical integration points cannot be deferred without explicit override.
Rationale must justify why the gap is acceptable (e.g., "intentional migration window").

Allowed overrides (must be explicit in the message):
  --integration-contract-override="reason"
  --severity-downgrade="reason"

To proceed: Either fix the integration point now, or add an override flag with
justification that explains why the gap is acceptable.
```

### Severity Downgrade Criteria

A critical integration point can be deferred ONLY if one of:

1. **Migration window**: Explicit date-based deadline for the fix
2. **Consumption deferred**: Producer AND consumer are both deferred to same milestone
3. **Intentional divergence**: Documented architectural decision with rationale

A bare "out of scope" without one of these is **always a violation**.

### Graceful Degradation

- If the hook cannot parse paths from the ADR → warn only, don't block
- If the ADR is from a previous session (older than 7 days) → warn only, don't block
- If `CONSTITUTIONAL_HOOKS_BYPASS=1` → allow with warning logged

---

## Consequences

### Pros

- **Prevents the specific failure**: Critical-path gaps can't be silently closed
- **Minimal false-positive surface**: Requires both ADR close language AND critical integration language
- **Self-documenting**: The block message shows the actual path mismatch, forcing resolution
- **Low overhead**: UserPromptSubmit hook, runs only when ADR language is present

### Cons

- **Adds friction to ADR closing**: Legitimate deprecations may need override flags
- **Requires path extraction logic**: ADR text may not always contain parseable paths
- **7-day lookback limit**: Doesn't catch ADRs from ancient sessions

###未解决的后续问题 (Unresolved Follow-ups)

- Path extraction from natural-language ADR text is fragile; consider requiring a structured format
- No integration test for the hook itself (unit test only)
- No CKS entry linking this failure mode to prevent recurrence

---

## Implementation Notes

**Files to create/modify**:
- New: `P:/.claude/hooks/UserPromptSubmit_modules/integration_contract_gate.py`
- Modify: `P:/.claude/hooks/UserPromptSubmit_router.py` — register the hook
- Add tests: `P:/.claude/hooks/tests/test_integration_contract_gate.py`

**Registration**:
```python
# UserPromptSubmit_router.py — HOOK_PRIORITY
"integration_contract_gate": 3.5,  # Before handoff_context_injector (5.0)

# HOOK_DISPATCH
"integration_contract_gate": run_integration_contract_gate,
```

**Evidence required for bypass** (must be extracted from message):
- `--integration-contract-override="migration to X completes 2026-04-01"`
- `--severity-downgrade="A and B both deferred to v2.0"`

**Related memory entries**:
- `ADR-20260322-handoff-sync.md` — the original ADR that deferred this
- `perf_file_lock_timeout.md` — similar systemic deferral failure in handoff_store.py

---

## Test Cases

| Input | Expected |
|-------|----------|
| "ADR-001 is complete, the handoff path issue was deferred" | BLOCK |
| "ADR-001 is complete, deferred to v2.0 --severity-downgrade='A+B both deferred'" | ALLOW |
| "ADR-001 is complete, out of scope — unrelated fix" | ALLOW |
| "ADR-001 is complete, --integration-contract-override='migration window'" | ALLOW |
| "ADR-001 is complete, handoff envelope path mismatch deferred" | BLOCK |

---

*Generated from failure analysis of `feature/chs-consolidation` handoff gap (2026-03-22)*
