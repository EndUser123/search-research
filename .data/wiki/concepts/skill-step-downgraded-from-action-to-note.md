---
title: "Skill Step Downgraded from Action to Note Under Context Momentum"
created: 2026-07-20
source: session-2026-07-20
tags: [skill-execution, close-skill, context-momentum, action-degradation, retrospective]
agent: grok
host: grok
cognitive_load: 2
verification: local-only
summary: >
  When a skill step specifies a user-facing action ("ask the operator: 'Run /aar?'"),
  the model under close-out momentum downgrades it to an inline note ("recommend /aar"
  in a summary table) instead of actually asking. The gate fires correctly; the action
  degrades from interactive to passive. This is structurally different from skipping a
  step — the step runs, the condition is detected, but the verb intensity drops.
relations:
  - target: wiki/entities/skill-review-failure
    type: refines
    reciprocal: related
---

## Summary

A skill step specifies an action directed at the operator: "ask: 'Run /aar (deep) or /debrief (quick)?'" The model detects the condition (retrospective gate = `needs_llm_check`, session had friction), resolves the gate as `needs_llm_check`, and then — instead of posing the question to the operator — writes "Retrospective: none (recommend /aar)" in the summary table and moves on.

The step is not skipped. The gate is not ignored. The condition fires. But the **verb degrades**: "ask" becomes "recommend," the question mark disappears, the interactive moment becomes a passive footnote. The operator never sees a question; they see a line in a table.

## Key Findings

- **The failure is invisible to the model at the time.** Writing "recommend /aar" in a summary table feels like resolving the gate. The model reads its own output and sees the recommendation present. It does not notice that the skill said "ask" and the output said "recommend."

- **The failure is visible to the operator after the fact.** The operator reads the summary, sees "recommend /aar," and correctly asks: "why didn't you actually ask me?" The gap between "ask" and "recommend" is the gap between an interactive decision point and a passive observation.

- **Context momentum is the driver.** The model is in close-out mode — emitting a summary, filling template fields, resolving gates. The momentum toward "fill the field and move to the next one" overrides the momentum toward "stop and ask the operator a question." The step that requires breaking momentum (asking) is the step most likely to be downgraded.

- **This is distinct from "skill step skipped."** Skipping means the step doesn't run. Here the step runs, the condition fires, the gate is resolved — but the resolution is the wrong shape. The gate says `needs_llm_check`; the model resolves it by writing a note instead of by asking.

- **Root cause shared with the session's other failures.** Prose rules (including skill step instructions) do not bind reliably under context momentum. The `/close` skill's instruction to "ask" is a prose rule. The model treats it as advisory under momentum, exactly as it treats "Discovery Before Implementation" as advisory under momentum.

## The Pattern

```
Skill instruction: "ask the operator: X?"
  ↓ (context momentum: close-out mode)
Model output: "recommend X" in a summary table
  ↓ (operator reads summary)
Operator: "why didn't you ask me?"
```

The degradation chain: `ask` → `recommend` → `note in table` → `operator misses it`.

## Detection

The operator catches this by comparing the skill's specified action verb against the model's actual output verb:
- Skill says "ask" → model wrote "recommend" → **degraded**
- Skill says "write" → model wrote "noted" → **degraded**
- Skill says "run" → model wrote "should run" → **degraded**

Any time the skill's imperative verb becomes a suggestive verb in the output, the step has been downgraded.

## Fix Directions

1. **Structural**: skills that require operator interaction should produce a blocking output shape (e.g., the summary cannot be emitted until the question is answered). This is the same principle as PreToolUse blocking vs. advisory prose.

2. **Procedural**: the `/close` skill's summary template could require the retrospective gate to emit either "PASS" or a literal question to the operator — not a free-text field where "recommend" satisfies the template.

3. **Behavioral**: the model should check each gate resolution against the skill's specified action verb before emitting the summary. If the skill says "ask" and the resolution is "recommend," the resolution is invalid.

## Evidence

- Session 019f7e24, `/close` invocation: the `/close` skill's gate guidance for `retrospective` says "ask: 'Run /aar (deep) or /debrief (quick)?'" The model's output wrote "Retrospective: none (recommend /aar)" in the summary table.
- The operator's response: "aar isn't optional..." — confirming the question was never posed.
- The same session had three friction events (premature solutioning × 2, self-preference in `/risks` pre-check × 1) that would have warranted `/aar` capture. None were captured because the question was never asked.

## Related

- [[wiki/entities/skill-review-failure]] — the broader pattern of skill execution failures; this page refines it with a specific failure mode (action-to-note degradation)
- [[wiki/concepts/skill-enforcement-layers]] — why prose-level skill instructions don't bind reliably
- [[wiki/concepts/writing-discipline-not-enforced]] — the same root pattern: prose rules treated as advisory under momentum

## Auto-related

- [[handoff-pre-compact-problems]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
