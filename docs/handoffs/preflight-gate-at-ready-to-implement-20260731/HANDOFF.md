---
thread_id: preflight-gate-at-ready-to-implement-20260731
parent_handoff_path: none
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
produced_at: 2026-07-31T16:00:00Z
status: needs-design-decision
handoff_type: design
---

# Preflight gate at handoff `ready-to-implement`

## Objective

Add a verification gate that fires when a handoff is marked `status: ready-to-implement`.
This would have caught the "8,646 stubs" error (proposing to gitignore irreplaceable
files without listing them) before it propagated to future sessions.

## Problem

Across 5 sessions, the same hook timeout was investigated, analyzed, and documented —
but the fix was never applied. The pattern:

1. Session produces RCA → wiki concept → handoff with `status: ready-to-implement`
2. Next session reads the handoff, references it as "highest-leverage" → doesn't apply it
3. Timeout recurs → another RCA

Separately, a bad proposal (gitignore wiki/sources/ as "stubs") was about to be applied.
The handoff `quality-gate-pretooluse-timeout-20260728` proposed the wrong fix
(timeout bump instead of dirty-tree cleanup) and it survived 4 sessions because nothing
validated its central claim.

## Design decision needed (operator)

Two options for where preflight should fire:

### Option A: Blocking (inside handoff skill)

The handoff skill refuses to mark `status: ready-to-implement` until a preflight check
confirms the handoff's central claim (e.g., "run `ls` on the target directory and confirm
the claim matches reality").

**Pros:** bad proposals can't propagate. Mechanical enforcement.
**Cons:** adds friction to handoff creation. May block valid handoffs if preflight is
too strict. Requires preflight to understand arbitrary claims (hard NLP problem).

### Option B: Advisory (separate check at session start)

Session start scans for aging `ready-to-implement` handoffs (e.g., >3 days old) and
surfaces them: "This handoff has been ready-to-implement for 5 days. Apply it or close it?"

**Pros:** no friction on handoff creation. Surfaces stale items. Simpler to implement.
**Cons:** doesn't prevent bad proposals — only surfaces aging ones. Still depends on
the operator/agent choosing to act.

### Recommendation

**Option B first** — it's simpler, lower-risk, and addresses the "4 sessions unapplied"
problem directly. The bad-proposal problem (Option A) is harder and rarer; it can be
addressed by the list-before-claim rule (already shipped) for the common case.

## Context

- Wiki concept: `P:/.data/wiki/concepts/list-before-claim-for-destructive-proposal-actions.md`
- Incident RCA: `P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md`
  (updated with "RESOLVED" section showing the dirty-tree root cause)
- The hook timeout is now FIXED (dirty tree 1388 → 399). This handoff is about preventing
  the PATTERN (analysis without application, bad proposals propagating) not the specific
  timeout.

## Acceptance criteria

- [ ] Operator decides: Option A (blocking), Option B (advisory), or defer
- [ ] If Option B: implement session-start scan for aging `ready-to-implement` handoffs
- [ ] If Option A: design the claim-verification mechanism (likely a preflight integration)
