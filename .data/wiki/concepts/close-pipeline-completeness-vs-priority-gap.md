---
title: "Close pipeline completeness-vs-priority gap: why /close + /aar miss forward-looking actions"
created: 2026-07-29
source: session-20260728 (/why analysis of why /tp do? finds what /close doesn't)
tags: [close, tp, pipeline, forward-looking, completeness, priority, skill-design, close-gap]
summary: >
  The /close pipeline (/close + /aar) is backward-looking: it checks whether
  artifacts exist (completeness) and what was learned (retrospective). It does
  not surface what should be done next (priority). /tp do? fills this gap — it
  scans the same session evidence but through an action lens, producing a
  numbered list of next steps. Session 019fa5a1 proved this empirically: /close
  ran 15+ times and never surfaced "execute the v5 plan" as a next step; /tp do?
  surfaced it in one pass. The fix: /close Step 4 now calls /tp do? instead of
  /tp session, giving the pipeline both backward-looking completeness and
  forward-looking actionability.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - C:/Users/brsth/.grok/skills/close/SKILL.md (Step 4, commit 16dd79d)
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/fabrication-ceremony-tax-compounding-cost.md
    type: related
  - target: wiki/concepts/spec-driven-development-tools-and-planning-workflows.md
    type: related
---

# Close pipeline completeness-vs-priority gap

## Decision context

**Why this was needed:** session 019fa5a1 ran `/close` 15+ times across the
session. The scanner correctly resolved gate after gate (retrospective, wiki,
handoffs, temp files, referenced files). But it never surfaced the most
important next action: execute the v5 close-authority plan. The plan existed
on disk, committed, with a handoff — all gates could be satisfied. But "will
anyone execute this plan?" is not a close question. It's a `/tp do?` question.

The operator asked: "why does `/tp do?` keep finding stuff that `/close + /aar`
doesn't find?" The `/why` analysis revealed the structural gap.

## The three questions, and who asks them

| Skill | Question | Direction | Output |
|---|---|---|---|
| `/close` | "Is everything persisted?" | Backward (completeness) | Gate states |
| `/aar` | "What should be learned?" | Backward (retrospective) | Lessons, opportunities |
| `/tp do?` | "What should we do?" | Forward (actionable) | Numbered action list |

`/close` and `/aar` are necessary but not sufficient. A session can close
cleanly with all gates satisfied and the most important work unstarted. The
gates check *existence*, not *priority*. A committed plan file satisfies the
`handoffs` gate. Whether anyone will execute that plan is not a close question.

## The empirical evidence

This session proved the gap:

- `/close` ran 15+ times, resolved 14 gates, never said "execute the v5 plan"
- `/tp do?` ran once, surfaced 3 actionable items in seconds:
  1. Execute v5 plan
  2. Run /skill-dev improve plan-writer
  3. Push commits to origin

The `/close` scanner has 14 gates. All can be satisfied and the session can be
"complete" while the highest-value next action is unstarted. The scanner is
not broken — it's answering a different question.

## The fix

**`/close` Step 4 now calls `/tp do?` instead of `/tp session`.** Commit
`16dd79d` in the close skill.

The change is one section of one skill file. The `/tp do?` variant produces
an actionable numbered list with effort estimates and a `0 - Proceed`
confirmation. The `/tp session` variant produced observations. The close
pipeline needs actions, not observations.

This connects to [[reactive-pattern-matching-and-closure-pressure]] — the
model under closure pressure treats "complete" as "done" rather than "ready
for the next step." The `/tp do?` step forces the forward-looking question
before the session actually ends. It also relates to
[[spec-driven-development-tools-and-planning-workflows]] — Böckeler's
critique that SDD tools create elaborate workflows but miss the
forward-looking action question, leaving the operator with "a lot of
markdown files to review" but no clear next step.

It also connects to [[fabrication-ceremony-tax-compounding-cost]] — the
ceremony layer has grown to 15 gates, 4+ validators, and multiple receipt
rules. Adding one more step (`/tp do?`) is justified because it fills a
structural gap (forward-looking), not because it adds more ceremony
(backward-looking). The test: does this step prevent a real failure mode?
Yes — the failure mode is "session closes cleanly, plan sits unexecuted."

## What this means for our workspace

The close pipeline is now: `/wiki` → `/handoff` → `/aar` → `/close` (with
`/tp do?` at Step 4). This produces:
- Backward-looking: are artifacts persisted? (scanner gates)
- Reflective: what was learned? (AAR report)
- Forward-looking: what should we do next? (`/tp do?` actionable list)

All three are necessary. The pipeline was missing the third.

## Falsifier

This fix would be wrong if:
1. `/tp do?` adds latency without value (the scanner already finds everything
   worth doing). Falsified empirically: this session proved it finds items
   the scanner doesn't.
2. `/tp do?` produces noise (low-quality recommendations the operator ignores).
   Monitor: track whether the operator acts on the recommendations. If the
   hit rate drops below 50%, the step is adding ceremony without value.
3. The forward-looking question should be a separate skill invocation, not
   embedded in `/close`. This is a design preference — embedding it in `/close`
   ensures it fires every session. Making it separate means it might be skipped.

## Receipts

- **Close skill Step 4 change:** `C:/Users/brsth/.grok/skills/close/SKILL.md`
  line ~370, commit `16dd79d`. [OBSERVED: read the file after commit]
- **Empirical evidence:** session 019fa5a1 — `/close` ran 15+ times without
  surfacing "execute v5 plan"; `/tp do?` surfaced it in one pass. [OBSERVED]
- **`/why` analysis:** the root cause analysis identified completeness
  (backward) vs priority (forward) as the structural distinction. [OBSERVED]
