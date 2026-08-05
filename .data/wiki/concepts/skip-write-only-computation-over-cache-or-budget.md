---
title: "Skip write-only field computation rather than cache or budget"
created: 2026-07-27
source: session-2026-07-27 (/tp + /go on verification_receipt_writer.py timeout)
tags: [decision, hook-performance, write-only-fields, producer-consumer, skip-vs-cache, evidence-collection]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  When a hook computes fields that no consumer reads (write-only fields), the
  optimal fix is to skip the computation entirely (emit `[]` or omit the field),
  not to cache the expensive result, budget-bounded the loop, or move the work to
  the consumer. "Skip" wins because the work is unnecessary, not because it's slow.
  Caching and budgeting preserve the work; skipping eliminates it. The detection
  signal is a reader-grep before profiling for the fix: if grep finds zero
  consumers, the field is write-only and the computation can be deleted, not
  optimized. Applied to verification_receipt_writer.py: 275× speedup (11.2s → 40ms),
  zero consumer impact.
relations:
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: extends
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md
    type: related
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern.md
    type: related
---

# Skip write-only field computation rather than cache or budget

## Decision context

**The problem:** `verification_receipt_writer.py` (PostToolUse hook) called `_resolve_path_identities(modified)` twice per event, producing `observed_state_identities` and `claimed_scope_identities` fields. Each call spawned `git submodule status` (4–8s per path on Windows). With 6 modified paths, the hook consumed 21,187ms against a 5,000ms timeout budget — the hook was killed (fail-open), the receipt was silently dropped, and the Stop hook could not clear obligations that needed that receipt.

**The investigation** (`/tp` critique) surfaced three candidate fixes from the wiki concept `hook-evidence-collection-cost-vs-timeout-tradeoff.md`:
1. **Cache** the pre-mutation identity (thread it from the PreToolUse hook through the PostToolUse hook)
2. **Budget-bounded loop** (cap at N paths, write partial receipt)
3. **Move to consumer** (the wiki concept's fix #1: record minimal evidence in hook, resolve at `/close` time)

The `/tp` critique then proposed a fourth option not in the wiki concept:
4. **Skip entirely** — the fields are write-only; no consumer reads them

The operator's `/tp` prompt explicitly separated the two problems: "not use the wiki optimally, and the actual symptomatic hooks." This decomposition was critical — it prevented the agent from conflating the meta-problem (wiki utilization) with the code problem (hook timeout). The two have different optimal fixes: the meta-problem needs a behavioral enforcement layer; the code problem needs field-level audit. Conflating them would have produced a cache-based fix that optimized unnecessary work while leaving the wiki-utilization gap unaddressed.

## The decision

**Chosen: Skip entirely.** Replace `_resolve_path_identities(...)` with `[]`. The fields remain in the schema (as empty arrays) so the wire format doesn't change; the computation simply doesn't happen.

## Key findings

- **Write-only fields are invisible in profiling.** The profiler shows `_resolve_path_identities` as the bottleneck, but the profiler doesn't know whether the output is consumed. A line-level profiler would optimize the function; a reader-grep eliminates the call.
- **The initial `/www` analysis was directionally correct but unnecessary.** The cache/budget/move-to-consumer recommendations all assumed the fields were needed. The grep would have eliminated all three before the research began. The research was a symptom of the same anti-pattern: optimizing before auditing.
- **The fix is reversible by design.** Emitting `[]` instead of deleting the field preserves the schema. If a future consumer is added, restoring the call is a one-line revert — no migration, no schema change.

### Selection criterion

**Necessary-work elimination over unnecessary-work optimization.** The criterion is: does any consumer read this field? If no, the work is unnecessary and should be eliminated, not optimized.

### Rationale

1. **Grep before profiling.** A reader-grep (`rg "observed_state_identities|claimed_scope_identities" P:/ P:/packages ~/.grok/skills`) found exactly 4 hits, all in the writer. Zero readers. The work is provably unnecessary.
2. **Obligation check doesn't need it.** `_identity_matches` (quality_gate.py:738) returns True when obligation identity is `{}` (which it was this session). The per-path identity is audit enrichment, not enforcement.
3. **Receipt coverage check doesn't need it.** `_check_receipt_coverage` (quality_gate.py:528) checks the receipt's top-level `repository_id`/`worktree_id`, not the per-path identity arrays.
4. **Zero test impact.** 21/21 suite pass unchanged. No test asserts on these fields.

### Steelman of the rejected alternatives

**Why caching (option 1) was reasonable:** it eliminates the git subprocess fan-out by reusing identity captured at PreToolUse time. This is the wiki concept's implicit assumption — the identity IS needed, just expensive to compute. Caching would work and would reduce the 21s to <1s.

**Why budget-bounded (option 2) was reasonable:** it's the defensive option — even if a new slow git operation is introduced later, the budget check ensures the hook completes in time and writes a partial-but-honest receipt rather than being killed with nothing. It bounds harm regardless of root cause.

**Why move-to-consumer (option 3) was reasonable:** it follows the proven pattern from the `mutation_post.py` 25× speedup (commit `5aa1506`). That fix moved expensive dirty-tree introspection to `/close` time. It's the established architecture in this codebase.

**Why they lose to "skip":** all three preserve work that no consumer needs. Caching optimizes unnecessary computation. Budget-bounding tolerates unnecessary computation. Move-to-consumer defers unnecessary computation. Skip eliminates it. When the work is unnecessary, elimination is strictly better than optimization, tolerance, or deferral.

The deeper principle: **audit consumption before optimizing production.** The initial `/www` research spent a full cycle exploring caching, budgeting, and deferral patterns — all of which assume the work is necessary. A 1-second reader-grep would have eliminated all three options before the research began. The `/www` cycle itself was a symptom of skipping the audit step: the agent profiled the slow function before checking whether its output was needed.

## Falsifier

This decision is wrong if:
- **A future consumer needs per-path identity.** If `/close`, `/check`, or a new audit tool starts reading `observed_state_identities` or `claimed_scope_identities`, the `[]` values will be wrong (missing identity). Mitigation: the fields remain in the schema as `[]`, so adding a consumer means restoring the call — a one-line revert, not a schema migration.
- **The fields were debugging-purpose, not audit-purpose.** If someone was using them for live debugging via receipt inspection, they're now gone. Counter-evidence: no tool in the workspace reads them, and the field names suggest audit enrichment (`_identities` suffix), not debug output.
- **The reader-grep missed a consumer.** The grep covered `P:/worktrees/dotgrok-phase3`, `P:/packages`, and `~/.grok/skills`. If a consumer lives outside these paths (e.g., a standalone script in `~/.agents/` or `~/.codex/`), it was missed. Counter-evidence: the Phase 3 hooks are self-contained in `~/.grok/hooks/scripts/`; no external consumer was designed to read receipt fields.

## Implications

The skip-vs-cache decision has a subtle implication for the Phase 3 deployment model: the deployed hooks at `~/.grok/hooks/scripts/` now diverge from the source worktree at `P:/worktrees/dotgrok-phase3`. Both were patched in the same session, but future deployments from the worktree must preserve the `[]` values or the timeout recurs. The deployment manifest should note this as a known divergence from the original schema design (the fields exist but are intentionally empty).

## What this means for our workspace

**Detection pattern (reusable):** before profiling a slow hook, grep for readers of every field the hook produces. Fields with zero readers are write-only — skip their computation, don't optimize it. This is a 1-second check that prevents hours of profiling work on code that produces dead data.

**Generalizes beyond hooks:** the same pattern applies to any producer-consumer relationship where the producer's output isn't wired to consumers. The `/risks` finding on `/refine` ([[producer-consumer-contract-drift-in-skill-chains]]) identified the same anti-pattern in skill chains: skills writing structured fields no downstream skill reads. The fix is the same: verify the consumer exists before doing the work. This connects to the broader [[hook-evidence-collection-cost-vs-timeout-tradeoff]] pattern — both are instances of "the producer's cost is justified only if the consumer exists." It also relates to [[verification-state-tracking-content-identity-vs-temporal-proxies]] — when verification state is tracked by content rather than temporal provenance, write-only fields are the most common source of invisible cost because they look like "real" state but serve no enforcement purpose.

As a skill-improvement technique, this is an instance of [[compound-skill-improvement-patterns]] — a one-time audit (grep for readers) that prevents recurring wasted optimization work. It follows the receipt-first framing pattern from [[prompting-patterns-for-ai-agent-control]]: verify consumption before optimizing production. The detection checklist (grep for readers before profiling) is the kind of structural technique documented in [[self-improving-agent-systems-techniques-and-workspace-gaps]].

**Why write-only fields accumulate:** developers add fields "for completeness" or "for future use" without wiring a consumer. The field looks harmless in the schema, passes code review, and ships. The cost only surfaces when the computation behind the field becomes expensive (more paths, bigger repos, slower platforms). The field is invisible in profiling because it's just a dict assignment — the cost is in the function call that produces the value, not the assignment itself.

**The anti-pattern of optimizing before auditing:** the initial `/www` analysis recommended three optimizations (cache, budget, move-to-consumer) without first checking whether the fields were needed. All three would have "fixed" the timeout while preserving unnecessary work. The grep-for-readers check takes 1 second and would have eliminated all three options in favor of the simpler skip. This is the structural fix for the "optimize reflexively" bias: audit consumption before optimizing production.

**Operational checklist for any slow hook:**
1. Grep for readers of every field the hook produces (1 second)
2. For fields with zero readers: skip the computation, emit `[]` or omit
3. For fields WITH readers: apply the cache/budget/move-to-consumer framework from [[hook-evidence-collection-cost-vs-timeout-tradeoff]]
4. Re-time after each change to confirm the fix landed

## Receipts

- **"No consumer reads `observed_state_identities` or `claimed_scope_identities`":** receipt — `rg "observed_state_identities|claimed_scope_identities"` across `P:/worktrees/dotgrok-phase3`, `P:/packages`, `~/.grok/skills` → 4 hits, all in `verification_receipt_writer.py` (the writer). Zero readers.
- **"`_identity_matches` returns True on empty obligation identity":** receipt — `quality_gate.py:738-739`, read this session.
- **"275× speedup":** receipt — `python P:/tmp/time_hook.py` before and after the fix: 11,218ms → 40.7ms.
- **"21/21 suite pass unchanged":** receipt — `python P:/tmp/phase3_run_tests.py` post-fix, exit 0, 21/21 pass.
