---
title: "Improving red-team analysis: precision incentives, cross-model specialists, and the over-reporting problem"
created: 2026-07-23
source: session-2026-07-23 (/www research on improving red-team analysis)
sources:
  - https://entelligence.ai/code-review-benchmark-2026 (67-bug benchmark, 8 AI reviewers)
  - https://arxiv.org/abs/2503.13657 (Cemri 2025, "Why Do Multi-Agent LLM Systems Fail?")
  - https://openreview.net/forum?id=fOHvpLs6zp (Cooperative Code Review through Structured Disagreement)
  - https://github.com/addyosmani/adverse (cross-model adversarial review pattern)
  - https://ferz.ai/articles/hidden-weaknesses-shared-blind-spots-llms (shared blind spots across LLMs)
tags: [red-team, precision, false-positives, cross-model, specialist-calibration, llm-as-judge, benchmark]
agent: grok
host: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  Three concrete improvements to red-team analysis, grounded in the 2026
  Entelligence benchmark (best F1 = 47%, precision ranges 16-67%). (1)
  Add a false-positive cost to specialist prompts — specialists over-report
  because there's no penalty for wrong findings. (2) Make one specialist per
  run use a cross-model CLI (/agy, /codex, /mmx) instead of parent-model, to
  decorrelate shared blind spots. (3) Precision tracking via critic verdicts
  (not operator acceptance — operator trust makes acceptance unreliable).
relations:
  - target: wiki/concepts/multi-agent-correlated-errors
    type: extends
---

## Decision context

The operator asked "how can we improve the red-team analysis?" after a /red-team run on /tp produced 52 findings, of which only ~10% were actually actionable. The over-reporting pattern — specialists finding "problems" that aren't real — is the dominant quality issue.

## Key findings from research

### 1. The 2026 benchmark proves precision is the problem, not recall

The Entelligence benchmark tested 8 AI code review tools against 67 real production bugs. Results:

| Tool | F1 | Recall | **Precision** | Found/67 |
|---|---|---|---|---|
| Entelligence | 47.2% | 44.8% | **50.0%** | 30/67 |
| Codex | 45.4% | 40.3% | **51.9%** | 27/67 |
| Claude | 42.8% | 43.3% | **42.3%** | 29/67 |
| Graphite | 13.4% | 7.5% | **66.7%** | 5/67 |

The insight: **Graphite has the highest precision (67%) but lowest recall (7.5%).** It finds almost nothing, but what it finds is real. Most tools trade precision for recall — generating lots of noise to catch more bugs. Our red-team has the same problem: 52 findings, most noise.

### 2. Shared blind spots across model families (FERZ, Oct 2025)

FERZ measured that LLMs from different families share overlapping blind spots — "as models become more similar, their blind spots increasingly coincide, creating systemic monoculture risk." This confirms our wiki concept's claim: N same-family agents barely beat N=1. Cross-model diversity is the highest-leverage decorrelation.

### 3. The cooperative disagreement protocol (OpenReview 2025)

The "Adversarial Review" paper introduces a minimal protocol: builder + reviewer + critic, where the critic's job is to resolve disagreements between builder and reviewer. This is structurally similar to our /red-team critic, but with one key difference: **the critic penalizes the reviewer for non-reproducible findings**, creating a feedback loop that calibrates the reviewer over time.

## Three improvements (operator-approved)

### Improvement 1: False-positive cost in specialist prompts [APPROVED]

Add to every specialist dispatch prompt:

> Each finding that the critic marks `non_reproducible` reduces your
> specialist's quality signal. Prefer fewer high-confidence findings
> over many speculative ones. If you are <70% confident a finding is
> real, either drop it or explicitly label it `[speculative]` so the
> critic can weight it lower. The goal is precision, not volume.

This directly addresses the over-reporting problem by adding a cost to
being wrong. Specialists currently have zero incentive to self-filter
because they never see the critic's verdict.

### Improvement 2: Cross-model specialist per run [APPROVED — non-Anthropic only]

Make one specialist per /red-team run use a cross-model CLI instead of
parent-model. Per operator constraint: use /agy (Antigravity/Gemini),
/codex (OpenAI), or /mmx (MiniMax) — NOT Claude or Anthropic models.

Which specialist gets the cross-model slot: the one with the highest
expected value from independent verification. Typically the correctness
or logic specialist — the one most likely to catch bugs the parent-model
specialists share blind spots for.

Implementation: the orchestrator dispatches the cross-model specialist
via `spawn_subagent` with the appropriate model slug, OR shells out to
the CLI if spawn_subagent doesn't support the model. The specialist's
findings are tagged `[cross-model: <slug>]` in the synthesis.

### Improvement 3: Precision tracking via critic verdicts (NOT operator acceptance) [REVISED]

The operator noted that operator acceptance is unreliable as a ground-
truth signal because "I trust you so I don't always vet properly."

Instead, use the **critic's verdict** as the precision signal:
- critic marks finding `verified` → true positive
- critic marks finding `non_reproducible` → false positive
- critic marks finding `unverified` → uncertain (excluded from precision calc)

Precision = verified / (verified + non_reproducible) per specialist, per run.

Track in the existing telemetry infrastructure
(`P:/.artifacts/red-team/telemetry.jsonl`). After 5+ runs, each specialist
has a precision baseline. Specialists below 30% precision get prompt
revisions in the Phase 3b improvement loop.

This is operator-independent — the critic's verdict is the ground truth,
not the operator's gut. The critic can be wrong, but its verdicts are
consistent and measurable, which is what a precision baseline needs.

## Falsifier

If the false-positive cost doesn't reduce finding volume by ≥20% after
5 runs, the incentive isn't strong enough. If cross-model specialists
don't find issues the parent-model specialists missed in ≥1 of 5 runs,
the cross-model slot isn't adding value. If critic-based precision
tracking shows all specialists at >80% precision, the tracking is too
lenient (the benchmark shows even the best tools cap at ~50%).
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
