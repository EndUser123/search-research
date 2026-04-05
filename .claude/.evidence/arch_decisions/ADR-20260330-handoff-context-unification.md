# ADR-20260330-handoff-context-unification: Unify Handoff Restore Contracts

**Status:** Accepted
**Date:** 2026-03-30
**Context:** Handoff V2 has two restore paths producing different output formats for the same envelope data.

## Decision

1. **Unify restore contracts** — Both SessionStart and UPS compaction-marker recovery must emit the same `<compact-restore>` block. Change `_build_recovery_message()` in `handoff_task_injector.py` to delegate to `build_restore_message_compact()`.

2. **Add `conversation_summary` to snapshot** — Extend `build_resume_snapshot()` schema with a bounded field capturing: original intent, key clarifications, constraints, decisions, anti-goals.

3. **Add session-chain tracking** — Add `parent_session_id` to envelope and surface in restore message. Enables stale-context rejection and boundary-aware summary extraction.

**Not priority:** Three-file pattern (premature without token pressure evidence), Pull-don't-push scratchpad (orthogonal to core handoff continuity).

## Rationale

The gap is **contract divergence**, not missing consumer. `handoff_task_injector.py` (UPS path) produces freeform "CONTEXT RESTORED" prose. SessionStart path produces `<compact-restore>` XML block. Both read the same envelope. The UPS path is richer (calls `_extract_and_format_user_context()` with 15-message window) but formats output differently.

Multi-terminal safety is preserved — both paths use terminal-scoped handoff files with atomic writes.

## Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Unify to `<compact-restore>` | Single contract, machine-readable, already implemented in SessionStart | Loses UPS prose richness | Acceptable tradeoff |
| Keep two formats | SessionStart XML, UPS prose | Preserves UPS richer context extraction | Two contracts for same system | Violates single-responsibility |
| Three-file pattern | Split envelope into manifest/state/boot | 10x token reduction (claimed) | Coordination complexity, premature | No token pressure evidence yet |

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Consistency | Single restore contract across all paths | — |
| Observability | Easier to parse/test machine-readable format | — |
| Richness | conversation_summary adds refinement capture | Loses freeform prose richness from UPS |

## Multi-Terminal Safety

- **Safe** — Both paths use terminal-scoped handoff files; marker uses `{terminal_id}` prefix; atomic write via `os.replace` already in use
- Marker is one-shot deleted after UPS injection — no stale marker between terminals

## Edge Case Considerations

- **Concurrent access:** Same terminal cannot compact twice simultaneously — marker is one-shot
- **Crash recovery:** If UPS crashes after marker deletion but before injection, SessionStart still restores on next session
- **State propagation:** Both paths read same envelope — no divergence risk between paths

## Implementation

### P0: Unify restore contracts

**File:** `P:\.claude\hooks\UserPromptSubmit_modules\handoff_task_injector.py`
**Change:** Replace `_build_recovery_message()` body with delegation:

```python
def _build_recovery_message(envelope: dict) -> str:
    """Format a concise restoration context block from a Handoff V2 envelope."""
    # Delegate to shared compact formatter for contract consistency
    from scripts.hooks.__lib.handoff_v2 import build_restore_message_compact
    return build_restore_message_compact(envelope)
```

**Verification:** Both SessionStart and UPS produce `<compact-restore>` block with same fields.

### P1: Add conversation_summary

**File:** `P:\packages\handoff\scripts\hooks\__lib\handoff_v2.py`
**Change:** Add `conversation_summary` to `build_resume_snapshot()` schema. Capture via transcript re-read at restore time (not PreCompact — hooks prohibit LLM calls at capture time).

```python
snapshot = {
    # ... existing fields ...
    "conversation_summary": _extract_conversation_summary(transcript_path, max_tokens=400),
}
```

**Constraint:** `_extract_conversation_summary()` must be deterministic/replayable from transcript — no LLM call at capture time.

### P2: Session-chain tracking

**File:** `P:\packages\handoff\scripts\hooks\__lib\handoff_v2.py`
**Change:** Add `parent_session_id` field to envelope. Surface in restore message as `resumed_from_session: {parent_session_id}`.

## Consequences

- **Positive:** Single restore contract across all handoff paths; machine-readable format enables tooling; conversation_summary improves restore faithfulness after long sessions
- **Negative:** Loses UPS freeform prose richness (mitigated by conversation_summary); UPS loses direct `_extract_and_format_user_context()` call (absorbed into conversation_summary)
