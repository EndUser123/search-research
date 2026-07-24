---
thread_id: cascade-pattern-2026-07-24
parent_handoff_path: none
current_session_id: 019f91d3-2741-7f83-af68-211796180474
current_terminal_id: console_b7ba7bf3-2403-437a-b44a-c5c9
produced_at: 2026-07-24T19:40:00Z
status: open
handoff_type: architectural
accurate_as_of_head: non-git-session
---

# Cascade pattern: try cheap, score, escalate

## Objective

Implement the FrugalGPT-style cascade pattern for verification and extraction tasks: try the cheapest model first, score the output with deterministic signals, escalate to a stronger model only if quality is insufficient. This eliminates the need to define the "quality floor" (Rule 0) upfront — the floor emerges from the scoring step.

## Status

OPEN — design identified, not started. The `/tp` and red-team both identified cascade as the optimal approach. No code exists.

## Producing context

- Date: 2026-07-24
- Session: 019f91d3-2741-7f83-af68-211796180474
- Origin: red-team GATE-2 (quality floor undefined), GATE-4 (confidence calibration uncalibrated), /tp unifying insight #1

## Read-first list

1. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md:347-354` — the wiki already documents cascade as "superior but not implemented"
2. `P:/.agents/scripts/models/extract.py` — the Layer 1 extraction utility that would benefit from cascade scoring
3. `P:/.data/wiki/concepts/context-firewall-architecture.md` — how cascade fits into the 3-layer firewall
4. FrugalGPT paper: `https://arxiv.org/abs/2305.05176` — the academic foundation (98% cost reduction matching GPT-4)

## Verified facts

- [FACT] The wiki acknowledges cascade as superior: "External research (FrugalGPT, UCCI) shows sequential escalation can outperform upfront selection" (`model-pool-selection-policy-speed-quota-diversity.md:350-352`)
- [FACT] Rule 0 (quality floor) is undefined and cannot be evaluated — the policy's own epistemic state acknowledges "M3, GLM, DeepSeek have no quality data" (red-team GATE-2, LOGIC-016)
- [FACT] extract.py's self-confidence rating is uncalibrated — DiffusionGemma may always say "high" (red-team GATE-4)
- [FACT] FrugalGPT cascade achieves up to 98% cost reduction at GPT-4 quality (paper, not independently verified)
- [FACT] Deterministic scoring signals are available: JSON parse success, output length vs expected, response time vs median

## Current state

- No cascade implementation exists
- extract.py uses self-reported confidence (uncalibrated, may be dead code)
- The quality floor (Rule 0) is decorative — undefined and unmeasurable
- The domain table uses upfront selection (pick one model per domain)

## Task packets

### CS-01: Define deterministic scoring signals

- **Goal:** Replace model self-reported confidence with deterministic, measurable quality signals
- **In scope:** a scoring function that takes (model_output, expected_shape) → score
- **Signals to implement:**
  | Signal | What it detects | Weight |
  |---|---|---|
  | JSON parse failure | Model didn't produce valid structured output | Auto-fail (score=0) |
  | Output length << expected | Model extracted almost nothing | Heavy penalty |
  | Output length >> expected | Model hallucinated or padded | Moderate penalty |
  | Response time > 2× median | Model struggled | Light penalty |
  | Required fields missing | Schema validation failure | Auto-fail |
  | Anomaly field non-empty | Model found something unexpected | Flag for review (not auto-fail) |
- **Files:** `P:/.agents/scripts/models/scorer.py`
- **Acceptance:** scorer produces a 0-1 score for any extraction output; auto-fails on JSON parse failure or missing required fields
- **Falsifier:** scorer gives high score to garbage output; or scorer gives low score to correct output

### CS-02: Implement cascade in extract.py

- **Goal:** extract.py tries DiffusionGemma first, scores output, escalates to DeepSeek/M3 if score < threshold
- **In scope:** `extract.py` — add cascade logic after the DiffusionGemma call
- **Flow:**
  ```
  1. Try DiffusionGemma (Layer 1, ~2s, free)
  2. Score output with scorer.py
  3. If score >= 0.7: return extraction (done, cheap path)
  4. If score < 0.7: log "cascade escalation: DGemma score=X"
  5. Escalate to DeepSeek via spawn_subagent (Layer 2, tool-use, ~3s)
  6. Return DeepSeek output (or original if DeepSeek also fails)
  ```
- **Acceptance:** extract.py returns DiffusionGemma output for high-score cases; escalates to DeepSeek for low-score cases; logs the cascade decision to telemetry
- **Falsifier:** cascade never escalates (DGemma always scores ≥0.7 — dead code); or cascade always escalates (DGemma always scores <0.7 — no savings)

### CS-03: Implement cascade in /check verifiers

- **Goal:** /check tries DeepSeek first, scores verifier output, escalates to M3 if uncertain
- **In scope:** `P:/.grok/skills/check/SKILL.md` — add cascade guidance to the verifier protocol
- **Scoring for verification:** a verifier PASS with no issues → score high; a verifier with issues → score is irrelevant (issues are the signal); a verifier that errors or times out → score 0, escalate
- **Acceptance:** /check uses DeepSeek for routine verification; escalates to M3 for complex or uncertain cases

## Open decisions

- **Score threshold for escalation?** 0.7 is a guess. Should be calibrated: run extract.py on a held-out corpus, measure where correct extractions score vs incorrect ones. Recommendation: start at 0.7, adjust after 100 calls of telemetry data.
- **Should cascade be in route.py or in each skill?** If route.py (routing library handoff) handles cascade, every skill gets it for free. Recommendation: put the cascade logic in route.py, not per-skill. This means the cascade handoff DEPENDS on the routing library handoff.
- **What model for the escalation tier?** DeepSeek → M3 for code tasks; Nemotron → GLM for reasoning tasks. The domain table already defines the fallback chain — cascade reuses it.

## Hard constraints

- The cheap model must run first (never skip to the expensive model)
- The scoring must be deterministic (no model self-report — that's what we're replacing)
- Every cascade decision (escalate or not) must be logged to telemetry
- The cascade must not add more than 1 extra round-trip (cheap model + at most 1 escalation)

## Cross-reference couplings

- **Depends on:** routing library handoff (`P:/docs/handoffs/routing-library/HANDOFF.md`) — cascade logic should live in route.py
- **Resolves:** red-team GATE-2 (quality floor undefined — cascade replaces the need for it), GATE-4 (confidence uncalibrated — deterministic scoring replaces self-report)
- **Resolves:** wiki `model-pool-selection-policy-speed-quota-diversity.md:347-354` (cascade acknowledged as superior but not implemented)
- `extract.py:425-441` — current escalation logic (self-reported confidence) will be replaced by scorer.py

## Explicit non-goals

- Do NOT build a learned router (RouteLLM-style ML model) — deterministic scoring is sufficient for the first version
- Do NOT implement cascade for /go waves (too complex; /go manages its own effort/m persona system)
- Do NOT calibrate the threshold before shipping — start at 0.7, let telemetry data drive calibration

## Resumption protocol

1. Read FrugalGPT paper sections on cascade scoring (or use the wiki summary)
2. Create `scorer.py` with the deterministic signal table
3. Add cascade logic to extract.py (try DGemma → score → escalate to DeepSeek)
4. Test on a held-out file: verify cascade returns cheap output for simple extractions, escalates for complex ones
5. Log cascade decisions to telemetry for calibration

## Suggested next invocation

```
/go implement cascade pattern: scorer.py (deterministic quality signals) + cascade logic in extract.py (try DiffusionGemma, score, escalate to DeepSeek if <0.7). Depends on route.py from routing-library handoff for per-skill integration. See P:/docs/handoffs/cascade-pattern/HANDOFF.md.
```

## Last user message (verbatim)

> "/handoff please create for each open and paused workstream."

## Epistemic labels

- [FACT] FrugalGPT cascade results cited from the paper (not independently replicated)
- [FACT] Deterministic scoring signals are standard techniques (JSON validation, length checks, timing)
- [INFERENCE] 0.7 threshold is a starting guess — needs calibration data from 100+ calls
- [INFERENCE] Cascade eliminates the need for Rule 0 quality floor definition — this is the /tp's unifying insight, not yet independently verified
