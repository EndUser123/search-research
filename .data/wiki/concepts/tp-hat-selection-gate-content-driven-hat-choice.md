---
title: "TP hat selection gate: content-driven hat choice replaces default-all-on"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [tp, thinking-partner, hat-selection, design-decision, architecture]
summary: >
  The /tp thinking-partner skill's hat framework was redesigned so
  that hat selection is content-driven (analyze the question first,
  then select only relevant hats) rather than default-all-on with
  a horizon matrix to skip some. This is a fundamental mechanism
  change that affects how the subagent prompt is constructed and
  what the operator experiences.
agent: grok
host: grok
cognitive_load: 4
verification: observed
sources:
  - P:/.grok/skills/tp/SKILL.md (the /tp skill being redesigned)
  - Session transcript lines 486-532 (critical friend review rounds)
relations:
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: complements
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: related
  - target: wiki/concepts/agent-config-directory-taxonomy.md
    type: related
  - target: wiki/concepts/cdp-auth-contention.md
    type: related
---

# TP hat selection gate: content-driven hat choice replaces default-all-on

## Decision context

**Why this matters:** The `/tp` skill is one of the most frequently
invoked meta-skills in the workspace. Its hat framework determines
what lenses a subagent applies when critiquing a proposal. The
original design defaulted all hats on and used a horizon matrix to
skip some — meaning the subagent always loaded every hat's
instructions even when irrelevant. The redesign changes the core
mechanism: the model analyzes the specific question first, then
selects only the hats that are relevant and valuable for that
question.

**The operator's intent:** When the operator said "intelligently
used when they can add value, and I rather err on the side of use
them than not," the original design interpreted "err on the side"
as "default-on for all hats." The operator's actual intent was
per-invocation judgment, not blanket firing. The critical friend
caught this inversion and the design was reframed accordingly.

## The selection-criterion shift

| Aspect | Old design | New design |
|--------|-----------|------------|
| Hat activation | Default all on, matrix skips some | Analyze question, select relevant hats only |
| Operator control | Horizon matrix (pre-set) | Per-invocation judgment (dynamic) |
| Prompt complexity | All hat instructions always loaded | Only selected hat instructions loaded |
| Latency | Higher (more instructions to process) | Lower (fewer instructions for simple questions) |
| Coverage risk | Matrix may skip needed hats | Selection may miss hats if analysis is wrong |

## Rationale for content-driven selection

1. **Matches the operator's stated intent** — "intelligently used"
   means selected, not defaulted.
2. **Reduces prompt density** — fewer instructions per subagent
   call means better focus on the actual task.
3. **Lowers latency** — skipping irrelevant hat instructions
   reduces token processing and subagent turnaround time.
4. **Aligns with the "pattern recognition" principle** — the
   model's analysis of what's needed is itself a form of
   intelligence, not just a filter.

## Steelman (rejected alternative)

The alternative is to keep the default-all-on design but make the
horizon matrix more fine-grained (more dimensions, better
thresholds). This would preserve the "always loaded" behavior and
avoid the coverage risk of dynamic selection. However, it doesn't
address the operator's core complaint — that hats should be
selected based on the question, not defaulted. A finer matrix is
still a coarse filter; it can't match per-question judgment.

## Falsifier

This decision is wrong if:
- Dynamic hat selection consistently misses hats that would have
  caught real problems (measured by post-hoc review of rejected
  proposals).
- The coverage risk of content-driven selection produces worse
  outcomes than the horizon matrix on a statistically significant
  sample of design reviews.
- The operator explicitly prefers the old default-all-on behavior
  after experiencing the new approach.

## What this means for our workspace

- The `/tp` SKILL.md needs to be updated to reflect the Hat
  Selection Gate as the core mechanism (Step B.5 in the design
  doc).
- The critical friend's remaining concerns (Pattern Recognition
  scope, Tier 5 A/B protocol, latency ceiling) should be tracked
  as open design questions — they are not resolved by this
  mechanism change alone. The Pattern Recognition discussion connects to [[blind-spot-detection-methods]] and the auto-commit authority pattern in [[auto-commit-authority-isolation]]. The Pattern Recognition discussion connects to [[blind-spot-detection-methods]] and the auto-commit authority pattern in [[auto-commit-authority-isolation]].
- This decision pattern (content-driven selection over
  default-all + filter) may apply to other skill frameworks where
  optional lenses or modes exist.

## Receipts

- `P:/.grok/skills/tp/SKILL.md` -- the /tp skill being redesigned (verified by read_file, 673 lines)
- Session transcript lines 486-532 -- critical friend review rounds showing the framing challenge
- Session transcript lines 489-493 -- operator correction on "intelligently used" interpretation
- Design doc at `C:/Users/brsth/AppData/Local/Temp/grok-design-fe4bd161/grok-design-doc-fe4bd161.md` (109KB, 16 sections) -- verified by listing temp directory
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` -- existing lifecycle architecture concept referenced in design

## Sources

- Session transcript, lines 486-532 (critical friend review)
- Session transcript, lines 489-493 (operator correction on
  "intelligently used" interpretation)
- Design doc at `C:\Users\brsth\AppData\Local\Temp\grok-design-fe4bd161\grok-design-doc-fe4bd161.md` (109KB, 16 sections)

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[code-orchestrates-model-judges-skill-scale]]
- [[wiki-captures-decisions-by-default]]
- [[video-to-wiki-pipeline-transcript-extraction-multimodal]]

