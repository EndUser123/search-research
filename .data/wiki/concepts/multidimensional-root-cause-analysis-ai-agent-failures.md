---
title: "Multi-dimensional root cause analysis for AI agent failures: Ishikawa fan-out adapted for LLM reasoning errors"
created: 2026-07-25
source: session-019f94c9
tags: [root-cause-analysis, ishikawa, fishbone, fault-diagnosis, multi-dimensional, five-whys, methodology, ai-agent-failure]
summary: >
  When an AI agent makes a wrong diagnostic conclusion (e.g., "hooks not
  registered" from incomplete evidence), single-cause root cause analysis
  (Five Whys) misses contributing factors. The Ishikawa/fishbone method,
  adapted from manufacturing and medical diagnosis, fans out across
  dimensions (mechanical, measurement, behavioral, process, environmental)
  and finds multiple contributing causes simultaneously. Applied to the
  receipt-system diagnostic error of 2026-07-25: four dimensions
  contributed (measurement bug, schema ambiguity, sampling bias, behavioral
  narrative closure). No single "why" chain would have found all four.
  Includes the adapted Ishikawa category table for AI agent failures, the
  prompt-level technique for applying it, and when to use each method
  (linear vs. fan-out).
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/ (Webster 2021, cognitive biases in diagnosis)
  - https://en.wikipedia.org/wiki/Ishikawa_diagram (Ishikawa/fishbone reference)
  - https://www.opm.gov/policy-data-oversight/human-capital-management/closing-skills-gaps/root-cause-analysis.pdf (OPM Ishikawa methodology)
relations:
  - target: wiki/concepts/problem-first-systems-decomposition.md
    type: complements — decomposition before solutions; this is decomposition of causes before fixes
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: applies-to — the root cause methodology was applied to diagnose this pattern
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — both target the same failure class from different angles
---

# Multi-dimensional root cause analysis for AI agent failures

## Decision context

**Why this methodology was needed:** session 2026-07-25 produced a multi-dimensional failure (the agent wrongly concluded "hooks not registered" from incomplete evidence). The operator asked for the causal chain to root cause. A linear Five Whys analysis would have found ONE cause and stopped; the actual failure had four contributing dimensions. This page documents the fan-out methodology that found all four, adapted from the Ishikawa/fishbone tradition for AI agent failures.

## The problem with single-cause analysis on multi-dimensional failures

**Five Whys** assumes a linear causal chain: each "why" drills deeper into a single cause. This works when there IS one root cause. It fails when multiple independent factors contribute:

```
Five Whys on the receipt-system failure:

Why did the agent say "hooks not registered"?
→ Because evaluation summaries showed hook_registration_status: not_registered
Why did the summaries show not_registered?
→ Because the evaluation script checks the wrong registration path
Why does it check the wrong path?
→ Because it was written for a different hook discovery mechanism
STOP. Root cause: evaluation script bug.

BUT THIS MISSES:
- The agent sampled subagent sessions (sampling bias)
- Zero-completion looks identical to zero-activity (schema ambiguity)
- The agent didn't check raw files (behavioral narrative closure)
```

The linear chain found the evaluation script bug (dimension 1) and stopped. It missed three other contributing causes. Any fix based solely on the linear chain would leave three dimensions unaddressed.

## Ishikawa/fishbone adapted for AI agent failures

The Ishikawa diagram (fishbone) from manufacturing quality control addresses this by fanning out across categories simultaneously. Instead of drilling down one path, you enumerate ALL plausible cause categories and investigate each.

**Adapted category table for AI agent systems:**

| Category | Question | AI-agent-specific examples |
|----------|----------|---------------------------|
| **Mechanical** (code/tool/config) | Is the tool actually working? Is the config correct? Is there a bug? | Hook not registered in JSON; script exits with error; config path wrong; API returns unexpected format |
| **Measurement** (how we observe) | Is what we're measuring actually what we think? Is the metric derived correctly? | Evaluation script checks wrong path; metric conflates two states; counter increments on wrong event; unit mismatch |
| **Behavioral** (model/agent reasoning) | Did the agent reason from evidence or from narrative? Did it verify before claiming? | Narrative closed before evidence checked; claim stated as fact without receipt; confirmation bias; premature closure |
| **Process** (workflow/skill design) | Does the process have a verification gate at the right point? Does it allow skipping? | No gate for mid-session diagnostic claims; receipt rule is advisory not structural; verification targets wrong claim class |
| **Environmental** (host/platform) | Is there a race condition, path mismatch, or platform-specific behavior? | Multi-agent transcript race; env vars not exported to shell; glob discovery vs. config-path check; Windows path encoding |

**How to apply it:**

1. State the observed failure in one sentence
2. For each category, ask: "could a problem in this dimension have contributed to the failure?"
3. For each "yes," investigate that dimension independently
4. Classify each found cause as structural (fixable in code/config) or behavioral (probabilistic mitigation only)
5. Fix structural causes first (permanent); design probabilistic mitigations for behavioral causes (may decay)
6. Name the falsifier: "if this cause were the only cause, would fixing it prevent the failure from recurring?" If no, there are other dimensions.

## Worked example: the receipt-system diagnostic error (2026-07-25)

**Observed failure:** the agent concluded "receipt system hooks are not registered" from evaluation summaries showing `completion_attempts: 0` and `hook_registration_status: not_registered`. The conclusion was wrong — the hooks were already firing via `verification-receipts.json` and had produced 31 receipt files with real data.

**Ishikawa fan-out:**

| Dimension | Cause found | Structural or behavioral? | Fix |
|-----------|------------|--------------------------|-----|
| **Mechanical** | Evaluation script checks a config-path registration mechanism that doesn't match Grok Build's glob-based `*.json` discovery | Structural | Fix `receipt_shadow_evaluation.py` to check whether receipt files exist, not whether a config key matches |
| **Measurement** | `hook_registration_status: not_registered` is derived from the wrong check; it reports registration status that doesn't reflect actual hook firing | Structural | Derive registration status from actual receipt-file existence or shadow-log activity |
| **Schema** | `completion_attempts: 0` is ambiguous — it means "no completion claims evaluated" but looks identical to "hooks didn't fire at all" | Structural | Add `shadow_entries_total` and `receipts_written_total` fields to distinguish no-claims from no-activity |
| **Sampling** | The agent sampled 5 most-recent evaluation summaries, all from subagent sessions that naturally have zero completion claims (subagents don't make completion claims) | Behavioral + structural | Behavioral: agent should check parent session, not just most-recent. Structural: add session-type field to summaries |
| **Behavioral** | The agent treated the plausible narrative ("zeros → not registered") as sufficient without checking raw evidence (one `ls` of the receipt directory) | Behavioral | Receipt rule extension: cover diagnostic claims about system state, not just causal claims about runtime behavior. Plus: diagnostic claim gate (see handoff) |

**Key insight:** 4 of 5 causes are structural (fixable in code). Only the behavioral dimension is probabilistic. If the structural causes are fixed, the behavioral cause becomes much less likely to recur — because the misleading signals that triggered it would no longer exist.

## When to use linear (Five Whys) vs. fan-out (Ishikawa)

| Method | When to use | When it fails |
|--------|------------|--------------|
| **Five Whys** (linear) | Single-cause failures; mechanical bugs; clear causal chain | Multi-dimensional failures; systemic issues; when multiple independent factors contribute |
| **Ishikawa** (fan-out) | Multi-dimensional failures; systemic issues; when the failure could have mechanical + behavioral + process causes | Simple bugs where one cause is obvious; time pressure (fan-out takes longer) |

**Rule of thumb:** if the first "why" produces a cause that feels like "the answer," ask "is this the ONLY cause?" If you're not sure, switch from linear to fan-out. The cost of fan-out on a single-cause problem is ~5 extra minutes of analysis. The cost of linear-only on a multi-cause problem is missing causes that produce recurrence.

## Connection to our existing root-cause infrastructure

Our `/aar` skill (Phase 4) has a layered root-cause model:
```
OBSERVED_FAILURE → IMMEDIATE_TRIGGER → PROXIMATE_CAUSE → CONTRIBUTING_CONDITIONS → SYSTEMIC_REUSABLE_CAUSE
```

This is the linear model. It's strong for tracing a single failure chain to depth. The Ishikawa fan-out is the complement: it's weak at depth but strong at breadth. Using both:
1. **Ishikawa first** to find all contributing dimensions
2. **Five Whys on each dimension** to trace each to its root

This gives both breadth (no dimension missed) and depth (each dimension traced to its structural root cause).

## The prompt-level technique

When the operator catches a diagnostic error, the most effective prompt is the Ishikawa fan-out in question form:

> "The evaluation summaries show all zeros. Before concluding the hooks aren't registered, verify across dimensions:
> - **Mechanical:** are the hook scripts registered in the dispatch JSON?
> - **Measurement:** is `hook_registration_status` derived from actual firing or from a config check?
> - **Behavioral:** did you check the raw files, or just the summary?
> - **Process:** does any verification gate target diagnostic claims made mid-session?
> - **Environmental:** could a platform-specific discovery mechanism explain the discrepancy?"

This forces the agent to investigate multiple dimensions simultaneously rather than locking onto the first plausible narrative. It's the medical diagnosis field's "differential diagnosis" applied to AI agent reasoning — force the consideration of alternatives before commitment.

## Falsifier

This methodology is wrong if, after applying it to 5+ multi-dimensional failures, the Ishikawa fan-out consistently finds only one real cause (the other dimensions are always false positives). In that case, the linear method is sufficient and the fan-out is overhead.

If the fan-out consistently finds ≥2 real contributing causes per failure, the methodology is validated.

**Current evidence:** 1 application (receipt-system failure, 2026-07-25). Found 5 causes across 5 dimensions. 4 were structural. The methodology was validated for this case. Needs 4+ more applications before generalizing.

## Sources

- [Webster: Cognitive biases in diagnosis and decision making](https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/) (2021, 88 citations) — premature closure in medical diagnosis; the #1 cognitive error
- [Ishikawa diagram (Wikipedia)](https://en.wikipedia.org/wiki/Ishikawa_diagram) — the original fishbone method from manufacturing quality control
- [OPM: Ishikawa Root Cause Analysis Methodology](https://www.opm.gov/policy-data-oversight/human-capital-management/closing-skills-gaps/root-cause-analysis.pdf) — US Office of Personnel Management's guide; "In cases of human error, people are rarely the true root cause. Seek the system, policy, or process that allowed the error to occur."
- [Chattopadhyay: Cognitive Biases in Software Development](https://cacm.acm.org/research/cognitive-biases-in-software-development/) (CACM) — confirmation bias mapping to software engineering
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
