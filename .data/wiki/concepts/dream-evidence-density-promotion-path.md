---
title: "Dream Evidence-Density Promotion Path"
created: 2026-08-05
source: session-20260805
tags: [dream, promotion-gate, epistemics, architecture-decision, knowledge-management, evidence-density]
summary: >
  Design decision: the dream skill's Pass 1 auto-promotion gate now has two
  paths — corpus-frequency (≥2 instances across sessions) and evidence-density
  (operator-commissioned research with ≥10 cited external sources). The
  evidence-density path exists because the 2-instance floor conflated provenance
  quality with corpus frequency. An operator-commissioned deep research report
  citing 30 academic sources has higher evidence density than most ideas appearing
  in 2 handoffs. Deferring it as "n=1" is epistemically wrong. Promotes with
  verification: evidence-density-verified to distinguish from both multi-source-
  verified and single-source-verified.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/epistemic-knowledge-system-design-2026.md
    type: extends
  - target: wiki/concepts/persistent-kb-architecture-model-sunset-survivability.md
    type: related
  - target: wiki/concepts/research-system-novel-ideas-external-synthesis.md
    type: related
  - target: wiki/concepts/sdlc-command-cognitive-jobs-taxonomy.md
    type: related
---

# Dream Evidence-Density Promotion Path

## Decision context

**Why this decision was needed:** during session 2026-08-04, the dream skill's Pass 1 deferred 4 high-value ideas from operator-commissioned Perplexity deep research as "below the 2-instance floor." Each conversation had 30-55 cited academic sources. The operator correctly identified the problem: "we are also deliberately ignoring potentially useful info." The 2-instance floor was treating provenance quality as if it were corpus frequency.

**The root problem:** the floor measured "did this idea appear in ≥2 handoffs?" — a statistical frequency question. But it was applied as if it measured "is this idea trustworthy enough to promote?" — an evidence quality question. Those are different axes. An operator-commissioned Perplexity deep research report citing 30 academic papers has higher evidence density than most ideas that independently appear in 2 operational handoffs. Deferring it as "n=1 single source" is epistemically wrong — the evidence density within the conversation is the signal, not the count of sessions it appeared in. This connects to the broader epistemic system design in [[epistemic-knowledge-system-design-2026]] — confidence should reflect evidence quality, not just repetition.

## The two-path promotion gate

| Path | Qualifies when | Verification label | Catches |
|------|---------------|-------------------|---------|
| **Corpus-frequency** (original) | ≥2 independent receipted instances across handoffs/AARs/sessions | `multi-source-verified` | Recurring operational patterns |
| **Evidence-density** (new) | Operator-commissioned research with ≥10 cited external sources in one conversation | `evidence-density-verified` | High-value novel findings that haven't recurred yet |

**Operator-commissioned research types** that qualify: Perplexity deep research, multi-turn LLM consultation, /www output, ChatGPT/Gemini consultation.

## Counting rule for "≥10 cited external sources"

- Count distinct URLs cited within the originating conversation's response text
- A single aggregator URL (e.g., one Perplexity response containing 30 footnote references) counts as **N sources** where N = distinct cited URLs, NOT 1
- Multi-turn conversations count the union of URLs across all assistant turns
- Wiki concepts already in the vault do NOT count (internal, not external)
- The concept's own `sources:` frontmatter is the canonical citation list

## Why a distinct verification label (not single-source-verified)

The specialist review caught that labeling evidence-density promotions as `single-source-verified` would conflate evidence quality with source count — the exact error the path was designed to fix. A `/www` output is `multi-source-verified` by /www's own contract; re-labeling it `single-source-verified` on dream promotion would be a regression. The `evidence-density-verified` label distinguishes: high intra-source density (one conversation, many citations) from both cross-source confirmation (multi-source-verified) and single-instance-low-density (single-source-verified).

## What this means for our workspace

1. **Operator-commissioned research no longer gets trapped behind a frequency gate.** When you ask ChatGPT or Perplexity for deep analysis and they cite 10+ sources, the dream can promote the findings without waiting for independent corroboration.

2. **The evidence-density path has test coverage.** 12 tests at `~/.grok/skills/dream/tests/test_pass1_promotion.py` cover: threshold boundary (9 vs 10 sources), source-type gating (operator-commissioned vs casual), verification label assignment, counting rules (aggregator URL = N not 1, internal URLs excluded, multi-turn union).

3. **The corpus-frequency path is unchanged.** Operational patterns that appear in ≥2 handoffs still auto-promote as before. The evidence-density path is purely additive — it catches a category the original gate missed. This aligns with [[persistent-kb-architecture-model-sunset-survivability]] — the canonical store should accumulate knowledge from diverse evidence types, not just recurring operational patterns.

4. **The promotion is still non-destructive.** Auto-promoted concepts can be deleted post-hoc by the operator. The `evidence-density-verified` label makes them easy to find and audit.

## Steelman (rejected alternative)

**Lower the 2-instance floor to 1 instance for all sources.** Simpler — no source-type classification, no counting rule, no new verification label. Any single-source finding would auto-promote. **Why rejected:** this would flood the wiki with single-handoff observations that haven't been corroborated. The 2-instance floor exists for a reason — fleet operational chatter produces many one-off observations that aren't wiki-worthy. The evidence-density path is more selective: it requires both operator commissioning AND ≥10 cited external sources, which filters out casual mentions while letting through high-density research.

## Falsifier

This decision is wrong if:
- Evidence-density-promoted concepts consistently need retraction or correction (the threshold is too low)
- The counting rule (aggregator = N, not 1) is exploited by sources that pad citation counts without adding evidence quality
- The `evidence-density-verified` label is ignored by downstream tools (contradiction scanner, /tp reviewers) that treat it as equivalent to `single-source-verified`
- The test stubs at `test_pass1_promotion.py` don't match the actual dream implementation when it's coded (the stubs test the logic contract, not the real `__lib/` functions — which don't exist yet). See [[research-system-novel-ideas-external-synthesis]] for how the belief ledger schema faces a similar implementation gap.

## Receipts

- Dream SKILL.md: `~/.grok/skills/dream/SKILL.md` lines 50-85 (promotion gate definition + counting rule)
- Test file: `~/.grok/skills/dream/tests/test_pass1_promotion.py` (12 tests, all PASS)
- Operator trigger: session 2026-08-05, operator said "4 deferred candidates... how problematic is this? we are also deliberately ignoring potentially useful info"
- Specialist finding #6: verification label downgrade risk (ship review, session 019fce56)

## Sources

- Session 2026-08-05 operator feedback ("how problematic is this?")
- Ship specialist review (finding #5: threshold counting undefined, finding #6: verification label downgrade)

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[llm-dreaming-memory-consolidation]]
- [[conversation-distillation-review-packet-export]]
- [[parallelizing-design-doc-generation-what-works]]

