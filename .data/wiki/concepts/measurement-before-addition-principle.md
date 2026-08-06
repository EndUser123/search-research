---
title: "Measurement before addition: audit current output before adding detection capabilities"
created: 2026-08-07
source: session-019fd820
tags: [improvement-cycle, measurement, signal-quality, detection-skills, anti-scarcity-bias]
summary: >
  When improving a detection or finding skill (like /insight, /aar, /notice),
  the default impulse is to add new detection capabilities ("find more").
  But the real bottleneck may be signal overflow (too many findings, low
  action rate) rather than signal scarcity. The principle: measure the
  current output's conversion rate (what % of findings get acted on?) and
  defect rate (what % of outputs have structural issues?) BEFORE adding
  new capabilities. Adding detection to a system with low conversion rate
  makes the problem worse, not better — more findings into a leaky bucket.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/insight-skill-improvement-directions.md
    type: extends
  - target: wiki/concepts/session-derived-improvements-from-insight-work.md
    type: extends
  - target: wiki/concepts/signal-prioritization-for-improvement-detection.md
    type: complements
  - target: wiki/concepts/mechanical-enforcement-of-llm-skill-steps-2026.md
    type: related
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: related
---

# Measurement before addition

## Decision context

**Why this was needed:** during `/www` research on improving `/insight`,
6 directions were proposed — all focused on finding *more* improvements
(signal scarcity assumption). A `/tp` critique caught the blind spot: the
real risk might be signal *overflow*. The skill's own falsifier lists
"operator skips /insight because it's too slow or noisy (over-firing)" as
a failure mode. None of the 6 directions addressed this. This connects to
[[proactive-improvement-opportunity-scanner]] (the original /capture concept)
and [[signal-prioritization-for-improvement-detection]] (the SRE patterns
that formalized the overflow problem).

The principle crystallized when the operator pushed back on abstract
research and asked for concrete, session-derived improvements. The first
concrete action was running a defect audit (`skill_audit.py`) that found
106 structural issues across 72 skills — a *measurement* that confirmed
the problem before proposing a solution. This echoes
[[mechanical-enforcement-of-llm-skill-steps-2026]]: measurement is
mechanical; proposals without measurement are behavioral.

## The principle

**Before adding new detection/finding capabilities to any skill, measure:**

1. **Conversion rate:** what percentage of current findings get acted on
   (committed, handed off, or resolved)? SRE teams target 30-50%
   alert-to-action conversion; below 20% = noise problem.

2. **Defect rate:** what percentage of current outputs have structural
   issues (missing frontmatter, description-body mismatch, broken paths)?
   This is a pure measurement — no judgment needed.

3. **Constraint decay:** is the skill already too complex for the LLM to
   reliably follow all its rules? LLMs lose 30+ accuracy points as
   constraints accumulate (lucidshark 2026). See
   [[compound-skill-improvement-patterns]] for the broader skill-growth
   problem.

**If conversion rate is low:** the bottleneck is signal-to-action, not
signal-to-signal. Adding detection capabilities makes overflow worse.
Fix the routing, filtering, or actionability first.

**If defect rate is high:** the bottleneck is quality, not quantity.
Fix structural validation before adding new content categories.

**Only if both are healthy:** add new detection capabilities. The system
can handle more input without degrading.

## What this means for our workspace

- `/insight`: before adding Direction 3 (missed-skill detection) or any
  new finding category, audit the task backlog for items that originated
  from `/insight` runs. If pickup rate is <30%, the fix is filtering
  (actionability gate, grouping), not addition.

- `/www`: before adding new research rounds or decomposition gates, check
  whether current research output is actually being used. The www-ledger's
  `outcome` field tracks this — use it.

- `/skill-dev`: the `script_scan.py` scanner already found 155 code defects
  (handoff `batch-skill-defect-cleanup-20260806`) and the SKILL.md audit
  found 106 structural defects (handoff `skill-md-structural-validator`).
  Both are measurements that confirmed problems before proposing solutions.
  Receipt: `P:/tmp/skill_audit.py` (40-line Python script, session 019fd820)
  — scanned 72 SKILL.md files, found 106 issues in 2 seconds.

- **General rule for skill improvement sessions:** start with a measurement
  pass (grep audit, conversion-rate check, defect scan), THEN propose
  improvements informed by the measurement. Not: propose improvements →
  implement → discover the problem was different.

## Connection to anti-scarcity bias

The failure mode this principle prevents is **scarcity bias** — the
assumption that more detection is always better. This bias is particularly
strong in LLM agents because:

1. The operator's phrasing often implies scarcity ("find more improvements")
2. External research sources promote addition (the Augment Code flywheel
   describes 4 stages of *more* — execute, coach, distill, improve)
3. Addition feels productive; measurement feels like delay

The `/tp` critique caught this by asking: "does this finding assume signal
scarcity? what if the problem is overflow?" That question should be asked
*before* research, not after.

## Falsifier

This principle is wrong if:
- Conversion rates are consistently high (>50%) across all detection skills,
  meaning the system can handle more findings without degradation
- Adding detection capabilities never increases overflow (each new finding
  category is independently actionable)
- Measurement-before-addition produces worse outcomes than
  addition-before-measurement (the measurement delay costs more than the
  misdirected implementation)

## Receipts

- `P:/tmp/skill_audit.py` — 40-line Python script that scanned 72 SKILL.md
  files and found 106 structural issues (49 missing version, 21 missing host,
  12 over 500 lines). Session 019fd820. This is the measurement that preceded
  the validator proposal.
- `~/.grok/skills/skill-dev/__lib/script_scan.py` — existing AST-level scanner
  that found 155 code defects across 9 skills. Source: handoff
  `batch-skill-defect-cleanup-20260806`. This is the measurement that preceded
  the batch-cleanup work.
- The `/tp` critique output (subagent 019fd85c) explicitly stated: "before
  implementing any direction, audit the task backlog — if pickup rate is <30%,
  the bottleneck is signal-to-action, not signal-to-signal." This is the
  statement that motivated the measurement principle.

## Sources

- Session 019fd820: `/www` → `/tp` → implement cycle on `/insight` improvements
- incident.io SRE alerting research: 2000+ alerts/week, only 3% need action
- lucidshark.com constraint decay research: 30+ accuracy points lost as
  constraints accumulate

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[cross-module-call-graph-audit-false-negative]]
- [[portfolio-deep-read-transferable-techniques]]
- [[skill-techniques-index]]

