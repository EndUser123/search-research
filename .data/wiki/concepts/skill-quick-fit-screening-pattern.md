---
title: "Skill quick-fit screening: a 30-second triage before skill execution"
created: 2026-07-21
source: session-2026-07-21
tags: [skill-design, screening-pattern, agent-routing, triage, design-pattern, agent-cost]
summary: >
  Every skill should run a 30-second fit assessment at invocation: is this
  task a good fit for the skill, or would a different skill do it better? The
  assessment is advisory (the user can override) but surfaces the
  recommendation before the skill burns tokens on the wrong task. The
  pattern: each skill declares "good fit" criteria, "better fit" alternatives,
  and a one-sentence surface format for the screening output. When the
  same user sees the same surface format across all skills, they build
  intuition for which skill to invoke on which task.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/compound-skill-improvement-patterns
    type: refines
  - target: wiki/concepts/skill-enforcement-layers
    type: related
---

## Summary

The cost of invoking the wrong skill is high: tokens spent on an output the user doesn't want, plus the user's time to redirect. A 30-second screening pass at skill invocation prevents this by surfacing the recommendation when the task is a poor fit for the skill invoked.

The pattern: every skill declares upfront what it's good for, what it's not good for, and where to redirect. The screening is advisory (the user can override) but its presence means a future agent reading the skill knows both the use case and the alternative.

## The pattern (concrete)

Every skill should have a **Quick-fit screening** section near the top, formatted consistently:

```markdown
## Quick-fit screening (runs at invocation; 30-second assessment)

When `/<skill>` is invoked, do this 30-second check:

**Good fit for /<skill>:**
- <3-5 specific criteria>

**Better fit:**
- `/<other-skill>` if <criteria that distinguish>

If the task is clearly a poor fit, surface ONE sentence before proceeding:

> "This task looks like a better fit for `/<other-skill>` because <one-line reason>. Proceed with `/<skill>` anyway?"

This is advisory, not blocking. The user can override. Skipping the screening
on a poor-fit task burns the user's tokens for an output that doesn't serve
their actual goal.
```

The four elements:

1. **Good fit criteria** — specific, falsifiable. "User asked for X" is good. "Good for any task" is not.
2. **Better fit alternatives** — name the other skill + what distinguishes the boundary. Without this, the user can't decide.
3. **One-sentence surface format** — quoted text the skill's preamble should print. Consistency across skills lets users recognize the pattern.
4. **Advisory, not blocking** — explicit. The user can override. Without this, the screening becomes theater (user invokes skill → skill refuses → user re-invokes).

## Why this works

The screening surfaces the routing decision **before** the skill body executes. Without it:

- The skill runs the body and produces an output.
- The user reads it, realizes it's the wrong shape, redirects.
- Tokens spent on the body are wasted.

With it:

- The skill surfaces a one-line recommendation.
- The user can either accept the override or redirect to a better skill.
- Tokens saved: the entire skill body (often 30–60% of total session tokens for substantive skills).

The screening cost is one print statement + one user read. The benefit is the saved tokens from running a 100K-token skill body that doesn't match the task.

## Adoption examples

The four skills `/plan`, `/design`, `/go`, `/tp` each have this pattern in their current SKILL.md:

- **`/plan`** declares its good fit as "≥3 distinct decisions to triage, durable artifact, multi-decision triage" and surfaces alternatives (`/tp quick`, `/design`, `/go`) before the Fire rule.
- **`/design`** declares its good fit as "design question with uncertainty, polished durable doc, ~5+ source files" and surfaces `/plan`, `/tp`, `/go` as alternatives.
- **`/go`** declares its good fit as "multi-step engineering, ≥1 file change, user wants execution" and surfaces `/plan`, `/design`, `/tp`, "just do it" as alternatives.
- **`/tp`** declares its good fit as "question with multiple valid answers, framing needs challenging, critical-friend lens" and surfaces `/plan`, `/design`, `/go`, "just answer" as alternatives.

When the user sees "This task looks like a better fit for..." in a skill's preamble, they immediately know the alternative is named and they can override. Without it, they have to read the skill body to discover whether it was the right choice.

## When NOT to apply this pattern

Don't apply the pattern when:

1. **The skill is unambiguous** — e.g., `/wiki search "X"` has one clear use case; screening would be noise.
2. **The skill is a primitive** — e.g., `/read_file`, `/grep`, `/run_terminal_command`; these are building blocks, not task-routing skills.
3. **The skill is a one-shot** — e.g., `/handoff close <path>`; the user knows what they want.

Apply the pattern when:

1. **The skill is a substantive workflow** — `/plan`, `/design`, `/go`, `/tp`, `/review`, `/red-team`.
2. **The skill's output is durable** — the output outlives the conversation (a plan, a design doc, a code change). Mistakes are costly.
3. **Adjacent skills exist** — if `/go` and `/plan` both could apply, the screening names which is preferred for which task shape.

## Adoption

Verified in session 2026-07-21: the four Grok meta-skills (`/plan`, `/design`, `/go`, `/tp`) all carry this pattern in their SKILL.md. The pattern is repeatable: copy the template, customize the criteria, run the skill to verify.

## EVIDENCE_GAP

The exact phrasing of the surface format ("This task looks like a better fit for...") is one of several viable alternatives. Alternatives considered:

- "I notice this might be better served by `/<other>` — proceed with `/<this>` anyway?"
- "Heads up — `/<other>` could be a better fit here. Continue with `/<this>`?"
- (silent screening — no surface, just internal recommendation)

The chosen phrasing was selected for being direct without being presumptuous. Empirical data on which phrasing leads to the highest user-override rate (i.e., the right amount of friction) is not yet collected.

## Auto-related

- [[skill-enforcement-deep-dive]]
- [[skill-enforcement-layers]]
- [[claude-code-verify-builtin-skill]]
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
