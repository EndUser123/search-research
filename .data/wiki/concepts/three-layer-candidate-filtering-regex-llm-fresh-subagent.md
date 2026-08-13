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
| **Layer 3** | Fresh subagent (no session context) | Audit Layer 2's drops: was each drop correct? | Catches Layer 2 errors | Latency (~30-60s) — mitigated by 4 speed optimizations (see below); **fires always, no threshold** (operator decision 2026-08-13) |

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

**Always-fire (operator decision 2026-08-13):** Layer 3 fires on ANY
dropped candidate, no count or severity threshold. The previous ≥3
HIGH/MEDIUM threshold was a magic number unmoored from any measured
property — and it prevented the measurement that would justify or kill it
(the gate blocked evidence collection). One HIGH-severity misclassified
drop is exactly the high-cost failure Layer 3 exists to catch; the
threshold let single-drop cases through unaudited every time.

**Speed optimizations (make always-fire acceptable):**

1. **Content-hash cache.** SHA256 of (candidate title + drop reason) →
   cached audit result. The same handoff drop-reason recurs every session
   until the handoff closes — cache hit returns instantly. Workspace
   precedent: `www_dedup.py`, crawl4ai SHA256, `coding_agent_session_search`
   BLAKE3 content dedup.

2. **Mechanical pre-filter.** Drops with deterministic reasons
   (`"duplicate"` + citation, `"done"` + commit SHA, `"prose"` + LOW)
   classify in <1ms via string check. Only the residual hits the LLM.

3. **Fast model (mechanical lane).** Layer 3's task is binary
   classification, not deep reasoning — the fresh-lens value comes from
   independent context, not reasoning power. Research: AgentForesight
   (arXiv 2605.08715, 2026) — compact 7B outperforms GPT-4.1 on audit
   tasks (+19.9% Exact-F1); MAV (arXiv 2502.20379, 2025) — off-the-shelf
   LLMs work as verifiers without training. Use `pick_model.py mechanical`.

4. **Progressive/streaming (never block).** Present Layer 1+2 output
   immediately; spawn Layer 3 in background; append promotions on arrival.
   Research: AWS Agentic AI Lens — "user-facing agent begins streaming as
   soon as minimum inputs are available." Operator never waits for Layer 3.

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
- **The latency cost (>30s) makes operators skip the step** — measure
  median latency across 10 sessions with the four speed optimizations
  (cache + mechanical filter + fast model + progressive). If median
  latency exceeds 15s AFTER optimizations, the always-fire decision
  needs revisiting — but with a measured number, not a threshold guess.
  Cache hit rate and mechanical-filter pass rate are the instrumentation:
  if cache hit rate >40% and mechanical filter removes >30%, the combined
  approach is clearly worth it. These are `[INFERENCE]` estimates until
  measured.

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

