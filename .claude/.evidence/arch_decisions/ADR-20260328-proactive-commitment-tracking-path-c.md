# ADR-20260328: Proactive Commitment Tracking — Path C (Next-Session Surfacing)

**Date:** 2026-03-28
**Status:** Proposed
**Decision Maker:** Solo developer (user)
**Decomposed by:** N/A

## Context and Problem Statement

The user stated: "1 shouldn't need to rely on feedback from the user, is that possible?" — referring to the Suspicion Detector's reactive gap detection that only surfaces problems when the user explicitly complains.

**The problem:** `SessionOutcomeDetector` detects uncompleted goals but only runs when `/gto` is explicitly invoked. This is reactive — the user must first notice something is missing and complain. The system should surface commitment gaps *before* the user has to point them out.

**Driving forces:**
- Solo-dev context: User can't rely on external accountability (no team member to ask "did you finish X?")
- The GTO v3 architecture has gap detection but it's invoked reactively, not proactively
- Commitment tracking should be zero-friction within a session

**Success criteria:**
- Uncompleted commitments surfaced automatically at next session start
- No external API calls (hooks must be standalone)
- Terminal-scoped state for multi-terminal safety
- Reuses existing well-tested patterns

## Decision

**Implement Path C: Next-Session Proactive Surfacing**

At session end (any stop, not just `/gto`):
1. `StopHook_commitment_tracker` reads transcript
2. Detects stated commitments via `SessionOutcomeDetector.TASK_INTENT_PATTERNS`
3. Checks completion via `SuspicionDetector.COMPLETION_SIGNALS`
4. Persists uncompleted commitments to terminal-scoped state file

At session start:
1. `SessionStart_commitment_tracker` loads prior uncompleted commitments
2. Injects via `additionalContext` before first prompt

**Path A (same-session interrupt) is deferred to Phase 2** — higher friction, requires interrupt mechanism.

## Rationale

**Why Path C over alternatives:**

| Path | Approach | Why Rejected/Deferred |
|------|----------|----------------------|
| Path A (same-session interrupt) | Interrupt when agent starts unrelated work | High friction — if system is wrong, user feels pestered. Requires interrupt mechanism. |
| Path B (orchestrator registry) | Track promises during execution | Requires modifying `gto_orchestrator.py`. Complex coupling. |
| **Path C (next-session)** | **Surface at session boundary** | **Low friction, builds on existing patterns, natural continuity** |

**Evidence supporting Path C:**
- Research found MindStudio AI Memory and session-continuity-framework with functionally identical approaches
- Session boundary is natural checkpoint — user is already pausing
- Terminal-scoped state is already used by task_tracker and other hooks

**Why not Path A first:**
- Interrupt-driven is higher value but higher complexity
- False positives would damage trust
- Path C validates the detection logic before adding interrupt complexity

**Why not Path B:**
- Orchestrator coupling adds fragility
- Path C achieves same outcome with simpler architecture
- Detection/transcription approach is less error-prone than tracking during execution

## Alternatives Considered

| Alternative | Description | Pros | Cons | Why Rejected |
|-------------|-------------|------|------|--------------|
| **Path C (CHOSEN)** | Next-session surfacing via StopHook + SessionStart | Zero friction, reuses patterns, multi-terminal safe | Gap surfaced next session, not immediate | N/A |
| Path A | Same-session interrupt via UserPromptSubmit hook | Immediate surfacing | Requires interrupt mechanism, high friction if wrong | Deferred to Phase 2 |
| Path B | Commitment registry in orchestrator | Most precise tracking | Complex coupling, orchestrator changes required | Deferred to Phase 2 |
| No tracking | Rely on user to track | No implementation needed | Reactive only, user must complain | Does not solve problem |

**Differentiation axes:** Timing (same-session vs next-session), coupling (orchestrator vs hooks), mechanism (interrupt vs passive detection)

## Consequences

### Positive
- **Zero-friction within session**: No interruptions during focused work
- **Reuses existing patterns**: `TASK_INTENT_PATTERNS` and `COMPLETION_SIGNALS` already validated
- **Multi-terminal safe**: Terminal-scoped state prevents cross-terminal contamination
- **Complementary to SOD**: SOD runs at `/gto` for formal gap reports; this runs at every stop

### Negative
- **Next-session delay**: Gap surfaced at next start, not immediately
- **Detection limitations**: Regex-based, may miss rephrased commitments
- **State file management**: Requires cleanup strategy for old commitments

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| False positive: commitment marked incomplete when it was | Medium | Medium | Completion signals are conservative; require strong evidence |
| State file corruption | Low | High | Atomic write with locking; graceful degradation |
| Terminal ID mismatch | Low | Medium | Use consistent terminal_id detection (same as task_tracker) |

## Implementation

### Core Contracts

**`TrackedCommitment` dataclass:**
```python
@dataclass
class TrackedCommitment:
    content: str           # The commitment text
    turn_number: int       # When stated
    category: Literal["user_goal", "agent_promise", "deferred_item"]
    completed: bool = False
    completion_turn: int | None = None
```

**State file schema:**
```json
{
  "terminal_id": "console_abc",
  "session_end": "2026-03-28T...",
  "commitments": [
    {
      "content": "build the auth module",
      "turn_number": 3,
      "category": "user_goal",
      "completed": false
    }
  ]
}
```

**State path:** `~/.claude/.evidence/gto-commitments-{terminal_id}.json`

### Implementation Plan

| Phase | Description | Effort | Files |
|-------|-------------|--------|-------|
| Phase 1 | Create `lib/commitment_tracker.py` with `CommitmentTracker` class | 2h | `gto/lib/commitment_tracker.py` |
| Phase 1 | Create `StopHook_commitment_tracker.py` | 1h | `gto/hooks/StopHook_commitment_tracker.py` |
| Phase 1 | Create `SessionStart_commitment_tracker.py` | 1h | `gto/hooks/SessionStart_commitment_tracker.py` |
| Phase 1 | Register hooks in `Stop_router.py` and `settings.json` | 0.5h | `gto/hooks/Stop_router.py`, `settings.json` |
| Phase 1 | Add feature flags | 0.5h | `settings.json` |
| Phase 2 | Write tests | 2h | `gto/tests/test_commitment_tracker.py` |
| Phase 2 (future) | Path A: UserPromptSubmit interrupt hook | 3h | Deferred |

### Rollback Strategy

- **Feature flag**: `PROACTIVE_COMMITMENT_TRACKER_ENABLED=false` disables without code changes
- **Hook removal**: Delete hook files, remove registrations
- **State cleanup**: Delete `gto-commitments-*.json` files

### Success Criteria

- Uncompleted commitment from session N appears in session N+1 context injection
- Hook executes in <100ms (local-only, no external calls)
- Feature flag toggles behavior without restart

## Related Decisions

- **ADR-20260321-gto-v3-architecture.md**: GTO v3 architecture that includes gap detection
- **SessionOutcomeDetector** (implementation): Source of `TASK_INTENT_PATTERNS`
- **SuspicionDetector** (implementation): Source of `COMPLETION_SIGNALS`

## Multi-Terminal Isolation Assessment

**State sharing:** YES — creates `~/.claude/.evidence/gto-commitments-{terminal_id}.json` per terminal

**Isolation mechanism:**
- Terminal-scoped filenames use `terminal_id` suffix
- Each terminal has independent commitment history
- No shared mutable state between terminals

**Concurrency safety:**
- File locking for atomic writes
- If two sessions for same terminal overlap: last-write-wins (acceptable for commitment tracking)
- Crash recovery: atomic write ensures no partial state

**Stale data immunity:**
- State loaded fresh at session start
- No in-memory caching that could go stale across terminals
- Each terminal reads its own file only

## References

- MindStudio AI Memory for Professional Relationship Management (research finding)
- session-continuity-framework (GitHub) — 4-layer state management for session-based agents
- `session_outcome_detector.py:106` — `TASK_INTENT_PATTERNS` (existing pattern reuse)
- `suspicion_detector.py` — `COMPLETION_SIGNALS` (existing pattern reuse)
- `proactive_commitment_tracking_plan.md` — Full design document

---

**Confidence:** 80% — Design validated by research; implementation complexity is medium; detection false positives are the main risk.

**Review status:** Pending review

**Last updated:** 2026-03-28
