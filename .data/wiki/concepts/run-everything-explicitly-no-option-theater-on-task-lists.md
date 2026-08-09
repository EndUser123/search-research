---
title: "Run everything explicitly: do not present option menus when the task list is explicit"
created: 2026-08-02
source: session-019fb937
sources:
  - internal: P:/.data/wiki/concepts/no-question-theater.md
  - internal: P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md
tags: [work-avoidance, option-theater, closure-pressure, behavioral-pattern, operator-correction, recurring]
agent: grok
host: grok
cognitive_load: 1
verification: single-session-observed
summary: >
  When the operator states a task list ("run every skill you listed"), the
  agent must run all of them explicitly. Presenting option menus
  ("would you like A or B?"), conditional logic ("if X then Y else skip"),
  or shortcut proposals ("I can do just the top 3") is a work-avoidance
  anti-pattern that recurs across sessions. The structural fix: when the
  task list is explicit, the run order is also explicit. No options.
---

# Run everything explicitly

## Pattern

When the operator provides a task list (a set of skills to run, a set of
findings to fix, a set of items to inspect), the agent's job is to execute
all of them in the stated order, not to find cleverness to skip work.

Across session 019fb937, the operator corrected this pattern 4+ times:

| Transcript line | Correction | Pattern |
|---|---|---|
| L357 | "the sections should be switched... so that 0 - do all Recomendations is last" | Trying to reorder to skip work |
| L491 | "I do want close-check to do all the right things, to run every skill you listed" | Trying to pick a subset |
| L509 | "why don't we just simply run all the skills? why are we trying to get fancy and avoid work?" | Anti-avoidance philosophy |
| L646 | "What do you mean they stay parallel? Are they in the closed dash check? They should be, shouldn't they?" | Trying to exclude from scope |

## What it looks like (anti-pattern signature)

The agent produces output that contains any of:
- "Would you like A (lower quality) or B (higher quality)?"
- "I can do X, Y, or Z... which do you prefer?"
- "If you want thoroughness, run them all; if you want speed, run the top N."
- "I'll skip X because Y already covers it."
- Conditional branches that require operator choice on a fixed task list

## Why it happens

The default failure mode under closure pressure is **optimization theater**:
the agent tries to appear helpful by reducing operator effort, but the
reduction is unrequested. The operator often wants the full work — speed
matters less than completeness, and the agent's "I picked a subset for you"
is silent scope reduction.

This is downstream of the broader analysis-over-action pattern: visible
artifacts (option menus, summaries) reward the agent more than invisible
non-events (the work that was correctly executed).

## The structural fix

1. **Task list is binding**: when the operator says "run X, Y, Z," the
   implementation runs X, Y, Z. Period.
2. **No subset proposals**: do not offer "would you like me to run just
   the top 3?" The number is fixed.
3. **Run order is explicit**: if the operator stated an order, the
   implementation respects it. Reordering to reduce work is out-of-scope.
4. **Skip a step only when the operator authorized skip**, not when the
   agent derives it.

## Detection (for future capture / aar scans)

```powershell
# High-signal patterns in agent output
Select-String -Path $chat -Pattern "would you like|shall I|which do you prefer|just the top|I can do|want to skip|shall we"
```

Two or more matches in a single response is a near-certain indicator of the
work-avoidance anti-pattern.

## Relation to existing patterns

- [[no-question-theater]] — adjacent pattern: asking instead of acting.
  This pattern is the execution variant: acting on a subset instead of
  the full set.
- [[prompting-patterns-for-ai-agent-control]] option menus with steering
  — the prompt-engineering literature explicitly flags this as
  manipulation.
- [[analysis-over-action-knowledge-capture-without-application]] —
  the underlying incentive structure that produces the pattern.
- optimal-long-term-solution-not-minimal-fix — when the task list
  is the operator's stated preference, "minimal" is not the
  operator-aligned criterion.

## Workspace implications

- **Action**: Add a behavioral rule to AGENTS.md: "When the operator
  states a task list (run X, Y, Z), execute all of them. Do not
  present option menus, skip proposals, or conditional branches."
- **Action**: Add detection to /capture Step 2 (operator-correction
  category): scan for the pattern in agent output and route to
  /slc for behavioral reset.
- **Action**: /close-check should run every skill in its 12-skill
  scope explicitly, in the documented order, with no conditional
  branches. The skill has done this manually every session — at some
  point it will be auto-coded.
