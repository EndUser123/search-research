---
thread_id: close-v6-deferred-design-findings-20260722
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T14:45:00Z
status: open
handoff_type: investigation
assigned_to: unassigned
accurate_as_of_head: 642c7ab
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: /close v6 deferred design findings (from /tp critique)

## Objective (one sentence)

Document 5 design-level findings from the /tp critique of /close v6 that were deferred (not mechanical fixes) so a future session can evaluate and act on them.

## Context

A `/tp` critique of `/close` v6 (11 gates, 40.8KB scanner) by glm-5-2 found 9 findings. Items 1-4 were mechanical fixes (broken tests, stale gate count, wrong --no-loop row, missing tests) — being fixed by a concurrent session. Items 5-9 are design decisions that need evaluation, not just editing. This handoff captures those 5.

## Deferred findings

### Finding 5: `quota` gate is overhead — should it be a gate or a summary line?

**Current:** `scan_quota()` returns a static dict, always resolves to `pre_satisfied`, never blocks, never loops. It exists as a gate only to surface a reminder string.

**Subagent recommendation:** Remove as a gate; keep as a summary-template line.

**Pushback (from synthesis):** The gate abstraction is uniform — removing one gate adds a special case. Alternative: add a `tier: "informational"` field so the architecture self-documents why it never blocks.

**Decision needed:** Is uniformity (keep as gate) or simplicity (summary line) the right trade-off? The `tier` field is a third option.

### Finding 6: `session_observations` gate always fires `needs_attention` for substantive sessions

**Current:** Forces a handoff even when there are "No observations this session" (`status CLOSED`). The reliability argument ("mechanical reliability — always write it") means every substantive close triggers this gate → potentially triggers the loop.

**Concern:** High false-positive rate for the loop trigger. Sessions that genuinely had no observations still produce a `needs_attention` gate.

**Decision needed:** Should this gate default to `pre_satisfied` (write the empty handoff silently) instead of `needs_attention` (force the LLM to acknowledge it)? The current design prioritizes mechanical reliability over loop efficiency.

### Finding 7: Backslash regex in `scan_referenced_files` likely dead

**Current:** The regex `r'(P:\\\\...)'` matches literal `P:\\` (double backslash). In markdown prose, paths are typically `P:/...` (forward slash) or single backslash. The double-backslash pattern would only match escaped paths in code blocks.

**Verification needed:** Read `scan_referenced_files` fully and determine whether the backslash pattern catches any real handoff content. If not, it's dead code that creates a false sense of coverage.

**Priority:** Low — the forward-slash patterns are correct and catch most references. The backslash pattern is likely a belt-and-suspenders artifact.

### Finding 8: Decisions auto-promotion can invalidate wiki gate state

**Current:** When the decisions gate auto-promotes decisions to wiki concepts, those concepts exist on disk — but the wiki gate was already resolved earlier in the scanner run. The wiki gate's state is now stale (it said "0 concepts" but the decisions gate just created 2).

**Why the loop doesn't catch it:** The loop triggers only on `needs_attention` gates. The decisions gate resolves to `needs_llm_check`, not `needs_attention`. So the stale wiki gate doesn't trigger a re-scan.

**Impact:** Minor — the LLM notes promoted concepts in the summary, and the next session's scanner sees them. But it's a gap in the "scanner thinks" architecture: LLM actions during gate resolution can invalidate other gates without the loop catching it.

**Possible fix:** After decisions auto-promotion, force a wiki gate re-resolution (without a full re-scan — just re-check the wiki count). Or: add a flag `gate_invalidation = true` when auto-promotion runs, and let the loop catch it.

**Priority:** Medium — affects architecture correctness, but the practical impact is low (next session self-heals).

### Finding 9: No gate-pruning mechanism — growth-only lifecycle

**Current:** The skill grew from 4 gates (v1) to 13 gates (v6) across 6 versions. No version removed a gate. The falsifier says "loop never fires → remove the loop" but there's no equivalent for individual gates.

**Concern:** Without a pruning rule, gates accumulate. Each gate adds resolution logic, a branch in `resolve_gates`, a line in the variant table, documentation in SKILL.md, and (ideally) tests. The complexity is monotonically increasing.

**Possible fix:** Add to the falsifier: "if any gate is `pre_satisfied` across 10 consecutive sessions, evaluate whether it should be removed or downgraded to a summary-template line." This requires the scanner to track per-gate state history across sessions (a small state file in `.artifacts/`).

**Priority:** Low now, higher as the gate count grows. Worth adding the falsifier text even without the tracking mechanism — it plants the seed.

## Acceptance criteria for the future session

1. Each finding has a disposition: act / defer / reject (with rationale)
2. If acting on finding 5: the quota gate is either removed (with summary-line replacement) or gets a `tier` field
3. If acting on finding 6: the session_observations gate default state changes (or the current design is documented as intentional)
4. If acting on finding 8: the wiki-gate-invalidation issue is fixed or explicitly accepted
5. Finding 9's pruning rule is added to the SKILL.md falsifier (low effort, high future value)

## Related artifacts

- /close SKILL.md: `C:/Users/brsth/.grok/skills/close/SKILL.md`
- Scanner: `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py`
- /tp critique (this session's): glm-5-2 subagent, 9 tool calls, 170s
- Test-code drift handoff: `P:/docs/handoffs/test-code-drift-multi-agent-20260722/HANDOFF.md`
- API guessing handoff: `P:/docs/handoffs/api-guessing-without-verification-20260722/HANDOFF.md`

## Falsifier

This handoff is unnecessary if the concurrent session's fixes (items 1-4) also address items 5-9. If the skill is stable after the mechanical fixes and no design changes are warranted, close this handoff with "no action needed."
