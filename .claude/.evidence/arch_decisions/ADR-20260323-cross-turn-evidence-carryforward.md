# ADR-20260323: Cross-Turn Evidence Carryforward for Stop Negative Existence Guard

**Status:** Proposed
**Date:** 2026-03-23
**Context:** Task #2379 — Investigate cross-turn evidence carryforward for Stop hook verification

---

## Problem Statement

`Stop_negative_existence_guard.py` blocks responses claiming files don't exist without verification evidence. The hook filters events to **this turn only** (`id > turn_start_event_id`), making prior-turn verification invisible.

**Failure Mode:**
```
Turn 1: User asks "What's in the hooks directory?"
Turn 1: Claude runs Glob → VERIFIED file listing exists
Turn 2: User asks "Are there any test files?"
Turn 2: Claude responds "There are no test files" → BLOCKED
        (No verification tool in Turn 2, so guard blocks)
```

The guard's strict "this turn" scoping is designed to prevent stale evidence bypass ("I verified 3 hours ago"). However, it creates false positives when verification in a prior turn is still contextually relevant.

---

## Evidence

**Source:** `Stop_negative_existence_guard.py:252-256`

```python
min_id = _read_turn_marker(session_id, terminal_id)
if min_id is None:
    return all_events  # Fallback: full session (safe but may miss stale)

return [e for e in all_events if int(e.get("id", 0)) > min_id]
```

**Research Validation:**
- GitHub #640 (ruvnet/claude-flow): Documents similar verification gaps where agents claim completion without evidence across turns. Proposes Mandatory Verification Pipeline with continuous validation.
- paddo.dev blog: Confirms Stop hooks work as deterministic guards with exit codes; cross-turn scoping not documented.
- No direct solution found in Claude Code hook documentation.

---

## Multi-Terminal Safety Requirements

Any solution MUST satisfy:

| Requirement | Rationale |
|-------------|-----------|
| **Terminal isolation** | Each terminal's evidence must not leak to other terminals |
| **Stale data immunity** | Old evidence from prior sessions must not bypass current context |
| **Compact event handling** | Turn markers may be compacted/renumbered during session compaction |

---

## Solution: Cross-Turn Evidence Carryforward with Session Boundary

### Core Logic

```python
def _load_turn_events(session_id: str, terminal_id: str) -> list[dict] | None:
    """Load tool events with cross-turn carryforward within session boundary.

    Returns None when evidence system is unavailable.
    Returns [] when evidence is available but no matching events found.
    """
    if not EVIDENCE_AVAILABLE:
        return None

    if not session_id:
        return None

    # Test mode: use spool files directly
    if not re.match(r"^[a-f0-9\-]{36}$", session_id.lower()):
        return _load_spool_files(session_id, terminal_id)

    try:
        all_events = load_tool_events(session_id=session_id, limit=200)
    except Exception:
        return None

    min_id = _read_turn_marker(session_id, terminal_id)
    if min_id is None:
        return all_events  # No turn marker: use full session

    current_turn_events = [e for e in all_events if int(e.get("id", 0)) > min_id]

    # CROSS-TURN CARRYFORWARD: If current turn has no events, use full session
    # This handles the case where Turn 2 has no verification tools but
    # Turn 1's verification is still contextually relevant
    if not current_turn_events:
        _logger.info(
            "No events this turn (turn_start_event_id=%d) - "
            "using full session evidence for verification",
            min_id
        )
        return all_events

    return current_turn_events
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Fall back to full session only when current turn is empty** | Preserves strict "this turn" behavior for normal cases; only relaxes when no evidence exists this turn |
| **Session boundary maintained** | `load_tool_events(session_id=...)` already scopes to current session; no cross-session leakage |
| **Turn marker still required** | Without `min_id`, we cannot determine which events are "this turn" vs prior turns within session |
| **Compact event handling** | `_read_turn_marker()` returns `int(event_id)` from marker file; compact events may have lower IDs but are still within session boundary |

### Compact Event Handling

During session compaction, event IDs may be renumbered. The critical invariant:

> **If `turn_start_event_id` exists, all events with `id > turn_start_event_id` are from this turn, regardless of renumbering.**

The compaction process:
1. Creates new event IDs sequentially
2. Updates `turn_start_event_id` in marker file
3. All pre-compaction events retain their relative order

The carryforward only triggers when `current_turn_events` is empty (no events with `id > min_id`), which means either:
- No tools were used this turn
- All events were compacted away

In both cases, falling back to `all_events` is safe because:
- All remaining events are from the current session
- No stale evidence from other sessions can leak through

---

## OBVIOUS_ALLOWLIST Expansion (Complementary Quick Fix)

While the carryforward fix addresses the core issue, expanding the allowlist reduces false positives for conversational patterns:

```python
# Existing patterns (lines 100-122)
OBVIOUS_ALLOWLIST = re.compile(
    # Capability/network statements
    r"\bno\s+(?:internet\s+access|network\s+access|network)\b"
    r"|\b(?:offline|no\s+connection)\b"
    # Domain knowledge
    r"|\bno\s+configuration\s+needed\b"
    r"|\bno\s+config\s+required\b"
    r"|\bno\s+setup\s+needed\b"
    # Conversational denials of actions
    r"|\bI\s+didn'?t\s+(?:change|modify|delete|remove|create|make|do)\b"
    r"|\bI\s+haven'?t\s+(?:change|modify|delete|remove|create|make|do)\b"
    r"|\bI\s+never\s+(?:change|modify|delete|remove|create|make|do)\b"
    # ... existing patterns
)
```

**Already implemented** (from summary): The allowlist expansion for conversational denials was applied to this hook.

---

## Multi-Terminal Isolation Verification

| Test Case | Expected Behavior |
|-----------|------------------|
| Terminal A verifies files in Turn 1 | Terminal B cannot see Terminal A's evidence |
| Terminal A claims "no files" in Turn 2 | Terminal B's claim is independent |
| Concurrent compaction on Terminal A | Turn marker updated atomically |

**Verification:**
```python
# Terminal-scoped state files
turn_marker_path = STATE_DIR_TURN_MARKERS / f"turn_start_{session_id}__{terminal_id}.json"
#                                        ↑ terminal_id ensures isolation
```

---

## Implementation Plan

### Phase 1: Core Fix (Cross-Turn Carryforward)

**File:** `P:\.claude\hooks\Stop_negative_existence_guard.py`

**Change:** Modify `_load_turn_events()` at lines 252-256:

```python
# CURRENT (lines 252-256)
min_id = _read_turn_marker(session_id, terminal_id)
if min_id is None:
    return all_events  # Fallback: full session (safe but may miss stale)

return [e for e in all_events if int(e.get("id", 0)) > min_id]

# PROPOSED
min_id = _read_turn_marker(session_id, terminal_id)
if min_id is None:
    return all_events

current_turn_events = [e for e in all_events if int(e.get("id", 0)) > min_id]

if not current_turn_events:
    _logger.info(
        "No events this turn (turn_start_event_id=%d) - "
        "using full session evidence for verification",
        min_id
    )
    return all_events

return current_turn_events
```

### Phase 2: Verification Tests

**Test file:** `P:\.claude\hooks\tests\test_stop_negative_existence_guard\test_cross_turn_carryforward.py`

```python
class TestCrossTurnCarryforward:
    """Verify cross-turn evidence carryforward is multi-terminal safe."""

    def test_current_turn_has_events_no_carryforward(self, tmp_path):
        """When current turn has events, don't fall back to full session."""
        # Events exist this turn → normal behavior
        pass

    def test_current_turn_empty_uses_full_session(self, tmp_path):
        """When current turn is empty, use full session evidence."""
        # Edge case: no events this turn → carry forward
        pass

    def test_terminal_isolation(self, tmp_path):
        """Terminal A's evidence doesn't leak to Terminal B."""
        # Multi-terminal safety verification
        pass

    def test_compact_events_within_session_boundary(self, tmp_path):
        """Compacted events still respect session boundary."""
        # Compact event handling
        pass
```

---

## Consequences

| Aspect | Impact |
|--------|--------|
| **False positives reduced** | Claims in Turn 2 won't block if Turn 1 verified relevant context |
| **Stale data protection maintained** | Evidence still scoped to current session |
| **Multi-terminal safety** | Turn markers include terminal_id for isolation |
| **Backward compatibility** | Normal case (events this turn) unchanged |

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Correctness** | Legitimate claims not blocked | — |
| **Safety** | Stale evidence still blocked by session boundary | — |
| **Complexity** | Minimal (5 lines added) | — |
| **Performance** | — | Marginal: one extra list comprehension when current turn has events |

---

## Rollback Strategy

If issues arise, revert `_load_turn_events()` to original:

```python
min_id = _read_turn_marker(session_id, terminal_id)
if min_id is None:
    return all_events
return [e for e in all_events if int(e.get("id", 0)) > min_id]
```

**Reversibility Score:** 1.0 (Trivial — single function revert)

---

## References

- `Stop_negative_existence_guard.py` — Current implementation
- `Stop_unverified_existence_gate.py` — `_read_turn_marker()` reference
- `evidence_store.py` — `load_tool_events()` session-scoped function
- ADR-20260323 (prior) — Stop hook friction reduction (related)
