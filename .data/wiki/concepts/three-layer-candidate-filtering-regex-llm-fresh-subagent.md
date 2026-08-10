---
title: "Three-layer candidate filtering: regex → LLM → fresh-subagent audit"
slug: three-layer-candidate-filtering-regex-llm-fresh-subagent
created: 2026-08-10
source: session-20260810
tags: [todo-skill, llm-judgment-hooks, fresh-subagent, closure-pressure, candidate-filtering, externalized-verification, transferable-technique, skill-design]
summary: >
  When a skill uses regex (Layer 1) to extract candidates and an LLM
  (Layer 2) to classify them, Layer 2 can silently drop real items under
  closure pressure — classifying "discussed" as "resolved." The fix is
  Layer 3: a fresh subagent that audits Layer 2's drops for correctness.
  The subagent sees only the dropped candidates and their reasons, not
  the session context that produced the closure pressure. This is the
  /tp two-lens pattern (Costa & Kallick 1993) applied to filtering output.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "P:/.data/wiki/concepts/externalized-verification-over-intrinsic-self-correction.md (this workspace — the research basis for why Layer 2 can't reliably self-audit)"
  - "P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md (this workspace — why Layer 2 misclassifies under pressure)"
  - "Costa & Kallick (1993), 'Through the Lens of a Critical Friend,' Educational Leadership 51(2)"
relations:
  - target: wiki/concepts/externalized-verification-over-intrinsic-self-correction.md
    type: complements
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: complements
  - target: wiki/concepts/llm-judgment-hooks.md
    type: refines
---

# Three-layer candidate filtering: regex → LLM → fresh-subagent audit

## Decision context

**The problem:** session 019fe7e9 (2026-08-09) demonstrated that `/todo`'s
two-layer architecture (regex scanner → LLM classifier) silently dropped a
real recommendation (the SSE-shim improvement). Layer 1 (the regex scanner)
correctly surfaced the candidate. Layer 2 (the orchestrator LLM)
misclassified it as "discussed" because the conversation had moved past it —
even though the operator had never actually resolved the decision.

The root cause: Layer 2 shares the session's closure pressure. When the
conversation moved on, the LLM's pattern-completion pathway generated
"handled" as the classification — not because the item was resolved, but
because the conversation's momentum said it was.

## The three-layer architecture

| Layer | Who | What | Recall/Precision | Failure mode |
|-------|-----|------|-----------------|--------------|
| **Layer 1** | Regex scanner (`scan_transcript.py`) | Extract ALL candidates (high recall, accepts low precision) | High recall | Misses items that don't match regex patterns |
| **Layer 2** | Orchestrator LLM (the agent running the skill) | Classify: real recommendation or noise? Drop or surface? | Balanced | **Closure-pressure misclassification**: drops real items as "discussed" |
| **Layer 3** | Fresh subagent (no session context) | Audit Layer 2's drops: was each drop correct? | Catches Layer 2 errors | Latency (~30-60s); needs ≥3 drops to be worth spawning |

Layer 3 receives ONLY the dropped candidates and their reasons — not the
surfaced list, not the session transcript, not the conversation that
produced the closure pressure. Its job is narrow: for each drop, "was the
drop reason valid, or was this a closure-pressure misclassification?"

## Why Layer 3 works where Layer 2 self-checking doesn't

The research consensus (documented in
[[externalized-verification-over-intrinsic-self-correction]]) is that
intrinsic self-correction fails — the same model that made the
classification can't reliably re-check it because it shares the same
pattern-completion pathway. Layer 3 externalizes the audit to a different
context (fresh subagent), which is the proven approach.

This is the `/tp` two-lens pattern (Costa & Kallick 1993 — "you cannot
refocus your own glasses") applied to skill output filtering instead of
decision critique. The structural insight is the same: a fresh lens
catches what the same lens can't see in itself.

## Design decisions

**Adaptive firing:** Layer 3 only spawns when the `_dropped_items` list
contains ≥3 HIGH or MEDIUM severity items. Below that threshold, the
operator can scan the audit list manually (the `_dropped_items` rendering
makes drops visible). This avoids the latency cost when there's nothing
meaningful to audit.

**Fail-open contract:** if Layer 3 fails to spawn, times out, or returns
nothing useful, the skill presents the original output without the Layer-3
check. The `_dropped_items` audit still provides the operator-visible
check. Layer 3 is an enhancement, not a gate.

**Scoped prompt:** the subagent sees only the drops, not the session. This
is critical — if it saw the session context, it would inherit the same
closure pressure that caused the misclassification.

## What this means for our workspace

1. **`/todo` now has three layers** (implemented in the SKILL.md Step 1c,
   commit `ab6f08a`). The `_dropped_items` audit (Step 1b) is the
   operator-visible Layer 2.5; the fresh subagent (Step 1c) is Layer 3.

2. **The pattern generalizes to any skill with LLM-filtered candidates.**
   Any skill where Layer 1 extracts candidates and Layer 2 filters them
   can benefit from Layer 3. Candidates: `/insight` (session scan),
   `/aar` (opportunity discovery), `/review` (finding triage). Each has
   a Layer 2 that could silently drop real items under closure pressure.

3. **The `_dropped_items` audit is the cheaper Layer 3** (operator-visible,
   zero latency) and should be the first implementation. The fresh-subagent
   Layer 3 is the stronger fix but adds latency — use it only when the
   operator-visible audit proves insufficient (i.e., the operator
   consistently catches wrong drops that Layer 3 would have caught
   automatically).

## Falsifier

This pattern is wrong if:
- **Layer 3 consistently agrees with Layer 2** — the fresh subagent never
  finds misclassifications, meaning the audit is unnecessary overhead.
  Measure: over 10 runs, how many items does Layer 3 promote? If <1 per
  10 runs, the layer isn't earning its latency cost.
- **Layer 3 itself misclassifies** — the fresh subagent promotes noise back
  into the surfaced list (false positives). Measure: of promoted items,
  how many does the operator act on vs ignore? If most are ignored, Layer 3
  has the same precision problem as Layer 1.
- **The latency cost (>30s) makes operators skip the step** — the skill
  becomes too slow and operators stop using it. The adaptive firing
  threshold (≥3 HIGH/MEDIUM drops) is the mitigation; if it's too low,
  raise it.

## Receipts

- **Session 019fe7e9:** the SSE-shim recommendation was dropped by Layer 2
  because the orchestrator classified it as "discussed." Verified: the
  operator asked "did all the gaps get captured?" and the drop was caught
  manually. Layer 3 would have caught it automatically.
- **Implementation:** `/todo` SKILL.md Step 1c, commit `ab6f08a` on
  `~/.grok`. The step documents the spawn prompt, the adaptive firing
  threshold, and the fail-open contract.
- **Research basis:** [[externalized-verification-over-intrinsic-self-correction]]
  documents why Layer 2 can't self-audit (intrinsic self-correction fails).

## Sources

- [[externalized-verification-over-intrinsic-self-correction]] (this workspace, 2026-08-09) — the research consensus that intrinsic self-correction fails and externalized verification works
- [[reactive-pattern-matching-and-closure-pressure]] (this workspace, 2026-07-24) — why Layer 2 misclassifies under closure pressure
- [[llm-judgment-hooks]] (this workspace) — the two-layer hybrid architecture that Layer 1+2 implement; this concept adds Layer 3
- Costa & Kallick (1993), "Through the Lens of a Critical Friend," *Educational Leadership* 51(2) — the "you cannot refocus your own glasses" principle

## Auto-related

- [[predictable-enforcement-for-recommendation-commitment]]
- [[context-firewall-architecture]]
- [[scope-matching-verification-discipline]]
- [[skill-catalog]]
- [[agent-control-plane-enforcement-architectures-2026]]

