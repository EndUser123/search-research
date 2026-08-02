---
title: "Session write-path attribution gap when no mutation receipts exist"
created: 2026-08-02
source: session-019fa111-5dcb-7ff1-a4f5-415ad29bbe9e
tags: [git-state, attribution, session-tracking, write-path, mutation-receipt, close-gate, cross-session, multi-terminal]
summary: >
  When close-gates evaluates `git_state: needs_attention` and finds 27+
  uncommitted files but no session write-path receipts, the scanner cannot
  distinguish this session's files from concurrent sessions' files. The gate
  fires correctly (the working tree is dirty), but the attribution is
  indeterminate — the scanner can prove dirty state but cannot prove
  ownership. This pattern fires repeatedly when receipt-emitting hooks fail
  silently (timeout → fail-open → no receipt written) or when sessions run
  before the receipt system was installed on this host. The result is
  chronic close-gate `needs_attention` findings that no single session can
  resolve, because no single session owns all the dirty files.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
tier: warm
relations:
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: extends
  - target: wiki/concepts/concurrent-session-commit-collision.md
    type: related
  - target: wiki/concepts/close-report-design-user-centric-progressive-disclosure.md
    type: related
  - target: wiki/concepts/chronic-workspace-health-debt-inventory-2026-08-01.md
    type: related
---

# Session write-path attribution gap when no mutation receipts exist

## Decision context

**Why this finding was captured:** session 019fa111 (2026-08-01/02) emitted a `close-gates` WARN finding that recurs across sessions but is not fully documented:

```
[warn] close-gates: [SESSION] git_state: needs_attention — 27 uncommitted files
but no session write-path receipts found; cannot prove all are from other sessions.
Stale_7d: 8 files. Sample: artifacts/continuation-coverage-019fa8f8.json,
.pi/skills/notebooklm/SKILL.md
```

This is distinct from existing concepts:
- `hook-evidence-collection-cost-vs-timeout-tradeoff` documents WHY receipts go missing (timeout → fail-open → silent drop). This concept documents WHAT HAPPENS when they go missing.
- `concurrent-session-commit-collision` documents the multi-session collision itself. This concept documents the scanner's inability to attribute when receipts are absent.
- `accumulation-problem-resolution-rate-binding-constraint` documents the throughput mismatch. This concept documents the attribution dimension of that mismatch.

The three complement each other but are not redundant.

## The pattern

**Step 1 — Receipts go missing.** The mutation receipt hook (`~/.grok/hooks/scripts/mutation_receipt.py`) emits a session write-path receipt for every mutating tool call. When the hook times out (PostToolUse ceiling 10s) or the script raises, the hook fails open (`sys.exit(0)`) and no receipt is written. This is the documented cost/timeout tradeoff (see `hook-evidence-collection-cost-vs-timeout-tradeoff`).

**Step 2 — Dirty tree accumulates.** Without receipts, the close-gates scanner knows the working tree is dirty (27 uncommitted files) but cannot link specific dirty files to this session's tool calls. It cannot distinguish:
- Files this session wrote (would be commitable by this session)
- Files concurrent sessions wrote (would NOT be commitable by this session)
- Files from prior sessions that never got committed (chronic stale-dirty)

**Step 3 — Gate fires correctly but attribution is indeterminate.** The `git_state` gate correctly returns `needs_attention` because the working tree IS dirty. But the message includes the key phrase: "cannot prove all are from other sessions." The scanner is honest: it sees dirty state but lacks ownership proof.

**Step 4 — Session cannot resolve the gate.** A single session cannot commit all 27 files (some belong to concurrent or prior sessions). It cannot selectively commit only its own (no receipts = no ownership proof). The gate becomes unresolvable for the session, blocking `/close` until either (a) all sessions commit their files and the tree is clean, or (b) the gate threshold is loosened.

## What this means for our workspace

### The chronic-state overlap

This finding overlaps with `chronic-workspace-health-debt-inventory-2026-08-01` (long-dirty plugin trees, STATE_GC, etc.) and with `accumulation-problem-resolution-rate-binding-constraint`. The chain is:

1. Receipts go missing (timeout)
2. Attribution becomes indeterminate
3. Close-gates fires `needs_attention` for all dirty files, not just attributable ones
4. Sessions accumulate unresolvable gates
5. The fleet produces more obligations (handoffs, todos) for "clean up dirty files"
6. Discovery > resolution → chronic accumulation

The attribution gap is one of the **structural causes** of accumulation, not just a symptom.

### Architectural fixes (in priority order)

1. **Receipt coverage monitor.** A periodic check (not in the hook path) that compares receipts written vs tool calls expected. When coverage drops below threshold (e.g., <90% over 1h), surface a finding. This restores visibility that fail-open hides.

2. **Per-session dirty-set reconciliation.** When close-gates runs, it should consult git reflog + session registry + receipt log to compute "dirty files attributable to this session." If attributable < dirty, surface the gap (e.g., "27 dirty, 6 attributable to this session — 21 from concurrent or stale"). This is more useful than "27 dirty, no receipts."

3. **Session-bound git worktrees.** If every session works in its own worktree (structural isolation per `auto-commit-authority-isolation`), each session's dirty set is its own. The attribution is structural; receipts become optional.

4. **Receipt persistence beyond PostToolUse.** The receipts are write-only per `hook-evidence-collection-cost-vs-timeout-tradeoff` § "Recurrence + fix applied" — no consumer reads them. If a consumer DOES read them (proposal: per-session dirty-set reconciliation), the field becomes load-bearing again, and the timeout/cost tradeoff becomes a real blocker.

### Detection signals

The pattern is firing when:
- `git_state` gate returns `needs_attention`
- The finding message includes "no session write-path receipts found" or equivalent
- The dirty count is >10 (single-session writes rarely exceed 10 files; multi-session accumulation does)
- Stale_7d >0 indicates chronic untracked state

If all four are true, this pattern fired.

## Falsifier

This concept is wrong or obsolete if:

- **The mutation receipt system is removed** — no receipts expected, no gap to document. The attribution question becomes moot (every dirty file is unattributed, always).
- **All sessions use worktrees** — structural isolation makes attribution trivial. The pattern cannot fire.
- **The close-gates scanner is updated to compute attribution without receipts** — e.g., by reading git reflog or session registry. The gap disappears; the finding format changes.

If none of these fire, the pattern is durable: receipts will continue to fail open under timeout, attribution will continue to be indeterminate, and sessions will continue to produce `git_state: needs_attention` findings they cannot resolve. The signal is worth keeping.

## Receipts

- Session 019fa111 close-gates raw evidence: `transcript signals.json` lines referencing the git_state finding
- Session 019fa111 chronic-state evidence: 25 uncommitted files in P:/, 4 in ~/.grok (raw evidence: "[fail] git-state: [SESSION] P:/: 25 uncommitted files, 15 unpushed commits ahead of origin/main" + "[fail] git-state: [SESSION] ~/.grok: 4 uncommitted files")
- `~/.grok/hooks/scripts/mutation_receipt.py:9-22` docstring — documents that /close scanner consumes receipts to prove file ownership
- `~/.grok/hooks/scripts/mutation_receipt.py:405-408` — the else branch that runs per-file loop when capture_reliable=False (the multiplies-cost behavior)
- `wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md` — the upstream cause of receipt loss
- `wiki/concepts/chronic-workspace-health-debt-inventory-2026-08-01.md` § "E. Note: NOT chronic, but session-attributed" — confirms git-state accumulation is per-session, not chronic
## Related

- [[hook-evidence-collection-cost-vs-timeout-tradeoff]] -- upstream cause of receipt loss (the cost/timeout tradeoff)
- [[concurrent-session-commit-collision]] -- multi-session collision pattern this attribution gap compounds
- [[close-report-design-user-centric-progressive-disclosure]] -- design principle: per-session attribution matters
- [[chronic-workspace-health-debt-inventory-2026-08-01]] -- the 2026-08-01 baseline this finding extends
- [[accumulation-problem-resolution-rate-binding-constraint]] -- the throughput principle this attribution gap contributes to

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[verification-receipt-systems-design-landscape]]
- [[conversation-distillation-review-packet-export]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]

