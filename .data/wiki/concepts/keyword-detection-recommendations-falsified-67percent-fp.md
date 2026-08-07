---
title: "Keyword detection of recommendations falsified at 67% FP (assertion-vs-discussion confusion)"
created: 2026-08-07
source: session-019fdc43
tags: [falsification, keyword-detection, enforcement-strategy, retrodiction-technique, empirical-calibration, structural-enforcement]
summary: >
  A keyword classifier designed to detect unvalidated external recommendations
  achieved 0% FP on a 20-item hand-curated corpus but 67% FP on real session
  data (retrodiction over 1385 turns). The root cause is structural: regex
  cannot distinguish assertion ("I recommend Aider") from discussion ("the agent
  said 'recommend Aider'"). This falsifies keyword-only detection for this
  problem class. The wiki concept also documents the retrodiction technique
  (run hook logic over historical transcripts to measure FP before shipping)
  and the 3 genuine catches the classifier did find.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/advisory-vs-blocking-enforcement-decision-2026.md
    type: extends — confirms the regex FP concern with empirical data
  - target: wiki/concepts/reasoning-first-search-never-claim-without-checking.md
    type: refines — the recommendation validation design was the structural fix path for Instance 5
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related — enforcement strategy that hit its precision ceiling
  - target: wiki/concepts/self-clearing-enforcement-hooks-design-pattern.md
    type: related — the hook was evaluated against this pattern
---

# Keyword detection of recommendations falsified at 67% FP

## Decision context

Session 2026-08-07 implemented a recommendation-validation capability:
a keyword classifier (`needs_external_validation.py`) + Stop hook designed
to detect when the agent makes architectural recommendations about external
tools without validating them via `/www`. The design doc
(`P:/docs/handoffs/recommendation-validation-design-20260807/grok-design-doc.md`)
chose keyword-based detection over LLM-based (DEC-02) for speed and
determinism.

After implementation, retrodiction testing over 40 historical sessions
(1385 assistant turns) revealed a 67% false-positive rate — well above
the workspace's own falsifier threshold of >50% FP for regex-based
enforcement (`advisory-vs-blocking-enforcement-decision-2026.md:35`).

## The falsification

### Unit 0a: synthetic corpus (misleading)

A 20-item hand-curated corpus (`validation_corpus.json`) with 5
external-architectural, 5 internal-workspace, 5 pure-reasoning, and 5
mixed recommendations achieved 0% FP and 0% FN. This **looked like a
pass** but was a false positive by construction: the corpus cleanly
separated "external architectural" vs "internal/reasoning" items —
exactly the axis keyword lists handle well. It contained near-zero of
the ambiguous *assertion-vs-discussion* text that real sessions are
full of.

**Lesson:** a synthetic corpus that cleanly separates the categories
your keyword lists are designed to distinguish will always pass. The
test must include the ambiguous cases that cause real false positives.

### Retrodiction: real session data (the actual measurement)

Running the hook's `scan_message()` logic over 1385 assistant turns
from 40 recent sessions produced 9 advisory fires (after initial tuning
reduced from 22). Labeling each:

| # | TP/FP | Why |
|---|---|---|
| 1 | TP | "Industry standard is EDD" — genuine consensus claim |
| 2 | TP | "Research says flat is optimal" — genuine research claim |
| 3 | FP | "A recommendation like 'Adopt Aider'" — quoting a hypothetical |
| 4 | TP | "CircleCI validates two-hook pattern" — genuine validation claim |
| 5 | FP | Describing a design option, not recommending |
| 6 | FP | "Researched pre-commit patterns" — retrospective summary |
| 7 | FP | Quoting wiki title containing "research says" |
| 8 | FP | Discussing event sourcing/CQRS as examples |
| 9 | FP | "GitHub Actions but for internal pipeline" — internal comparison |

**3 TP, 6 FP. FP rate = 67%.**

### Root cause: assertion vs discussion

The false positives share one pattern: the recommendation vocabulary
("recommend", "optimal", tool names) appears in text that *discusses*
or *critiques* recommendations rather than *making* them. Examples:

- **Assertion:** "I recommend adopting Aider for repo mapping." → needs validation
- **Discussion:** "The agent said 'recommend Aider' but that was wrong." → does not
- **Meta-analysis:** "Option B is a hook that scans for 'recommend' patterns." → does not

No keyword list can separate these reliably. The words are identical;
only the semantic context differs. This is the same finding reached
independently by the `/maintain` risk scan in session 019fcdd2:
*"regex can't tell assertion from discussion apart."*

## The retrodiction technique (transferable)

The method that produced this measurement is itself valuable and
transferable to any future enforcement hook:

**Retrodiction = run the hook's detection logic over historical session
transcripts to measure FP/TP rates before shipping (or before promoting
advisory → blocking).**

The harness (`P:/.agents/scripts/retrodiction_hook_measure.py`) imports
the hook's `scan_message()` function, iterates over
`~/.grok/sessions/P%3A%5C/*/chat_history.jsonl`, extracts assistant
turns, and reports each fire with session ID, turn index, and the
triggering sentence. The operator then labels each fire as TP or FP.

This converts "wait weeks for live data" into "know the FP rate in
5 minutes." It should be the standard pre-ship validation step for
any detection-based hook.

## The 3 genuine catches

The classifier did find 3 real cases where `/www` would have added
value:

1. **"The industry standard is Eval-Driven Development"** — a consensus
   claim about external practice. Whether EDD is actually the industry
   standard needs external evidence.
2. **"Research says flat one-level disclosure is optimal"** — cites
   external research. The citation (arxiv 2607.17598) turned out to
   be accurate, but the claim needed checking.
3. **"CircleCI validates the two-hook pattern"** — an external validation
   claim. Whether CircleCI actually uses a two-hook pattern needed
   verification.

These are genuine catches. But at 3 per 1385 turns (~0.2%), the
keyword classifier's precision is too low for the noise to be worth it.

## Relationship to the advisory-vs-blocking decision

The workspace's `[[advisory-vs-blocking-enforcement-decision-2026]]`
documented: *"If Phase 3 measurement shows PGM's regex prefilter has
>50% FP rate on labeled data, the entire hook-based approach is
suspect and Phase 4 should re-evaluate whether prompt-level is the
right ceiling."*

This measurement (67% FP) crosses that threshold. The falsifier has
fired for keyword-based recommendation detection specifically. The
broader lesson: keyword-only detection for semantic classification
problems (where the same words appear in different intent contexts)
has a precision ceiling that makes it unsuitable for enforcement.

## What this means for the workspace

1. **Do not re-attempt keyword-only detection for recommendation
   validation.** The 67% FP rate is structural (assertion-vs-discussion
   confusion), not fixable with more keywords. This was tested
   empirically: 14 meta-discussion suppression phrases dropped the fire
   count 59% but the FP rate barely moved (68% → 67%).

2. **If detection is revisited, use a two-layer approach** (regex
   pre-filter + LLM judge for assertion-vs-discussion). This is the
   PGM pattern. The design doc rejected it (DEC-02) for latency/cost,
   but that rejection was made before the data showed keyword-only
   doesn't work.

3. **The retrodiction technique should be standard pre-ship validation
   for detection-based hooks.** It catches the synthetic-corpus
   false-confidence problem before the hook ships.

4. **The design doc is preserved** at
   `P:/docs/handoffs/recommendation-validation-design-20260807/grok-design-doc.md`
   as the full architecture record. The code has been deleted (it was
   re-derivable standard Python with no unique value beyond what this
   concept and the design doc capture).

## Falsifier

This finding is wrong if:
- A future keyword list achieves >70% precision on real session data
  (would mean the assertion-vs-discussion confusion was narrower than
  measured — possible if the problem space narrows to a specific skill
  rather than all-session scanning)
- An LLM-judge layer is tested and also hits <50% precision (would
  mean the problem is harder than "assertion vs discussion" — perhaps
  the distinction itself is subjective)
- The 3 genuine catches turn out to be noise (all 3 were already
  validated in the originating session, so this is unlikely)

## Sources

- Session 019fdc43 transcript: implementation, retrodiction, 3-lens /tp critique
- Design doc: `P:/docs/handoffs/recommendation-validation-design-20260807/grok-design-doc.md`
- Handoff: `P:/docs/handoffs/recommendation-validation-design-20260807/HANDOFF.md`
- `[[advisory-vs-blocking-enforcement-decision-2026]]` — the enforcement-strategy decision whose falsifier fired
- `[[reasoning-first-search-never-claim-without-checking]]` — the 5 instances that motivated the design (only 1/5 was an external recommendation)
- `[[self-clearing-enforcement-hooks-design-pattern]]` — the hook pattern this was evaluated against

## Receipts

The code is deleted (commit `a20e6bb`), but the findings are grounded in
tool output from session 019fdc43. The evidence artifacts:

- **67% FP rate:** retrodiction output captured at `P:/tmp/retrodiction_v2.txt`
  (9 fires, 3 TP, 6 FP, across 1385 turns). The retrodiction was produced by
  `P:/.agents/scripts/retrodiction_hook_measure.py` (surviving harness) which
  imported the deleted `scan_message()` function from
  `Stop_validate_recommendations.py`.
- **0% FP on synthetic corpus:** Unit 0a run output, this session turn 1.
  Corpus was `validation_corpus.json` (20 items, deleted with the code).
- **67% > 50% falsifier threshold:** `advisory-vs-blocking-enforcement-decision-2026.md`
  line 35 (the falsifier statement).
- **3-lens critique findings:** subagent outputs from session 019fdc43:
  MiniMax (019fdd8a-6ac9), DeepSeek (019fdd87-e2ef), GLM-5.2 (019fdd8a-6acb).
- **1/5 incident coverage:** `reasoning-first-search-never-claim-without-checking.md`
  § "The five instances" — Instances 1-4 are internal-knowledge assertions;
  Instance 5 is the only external-recommendation case.
- **`/maintain` risk scan reaching the same conclusion independently:**
  session 019fcdd2, documented in that session's transcript.

The deleted implementation files (for git-history recovery if needed):
- `needs_external_validation.py` — the keyword classifier (commit `fc21996`)
- `Stop_validate_recommendations.py` — the Stop hook (commit `fc21996`)
- `classifier_prototype.py` — the Unit 0a prototype (commit `fc21996`)
- `external_validation_signals.json` — keyword config (commit `fc21996`)
- `validation_corpus.json` — 20-item test corpus (commit `fc21996`)
- `test_needs_external_validation.py` — test suite (commit `fc21996`)

## Auto-related

- [[skill-graph]]
- [[refactor-verification-gap-keyword-checks-form-not-content]]
- [[predictable-code-problems-detection-python-314-ai-generated]]
- [[model-fit-and-post-hoc-behavioral-detection]]
- [[run-all-lifecycle-skills-unconditionally-conditional-detection-is-the-gap]]

