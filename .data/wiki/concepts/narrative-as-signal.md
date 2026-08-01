---
title: "Narrative-as-signal: plausible narrative is the trigger to investigate"
concept_type: "anti-pattern"
created: 2026-07-27
agent: grok
host: both
cognitive_load: 2
verification: session-verified
sources:
  - P:/AGENTS.md § "Narrative-as-signal (anti-dismissal rule)"
  - session 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e (close-check broken-wikilink fix)
tags: [narrative, anti-pattern, anti-dismissal, verification, false-negative, closure-pressure, llm-behavior]
summary: >
  When an LLM constructs a plausible narrative for why something "can't
  be done," "doesn't exist," or "is already handled," that narrative is
  the signal to investigate — not the answer. The moment the model thinks
  "this can't be done because X," the next action should be to check
  documentation, grep the codebase, or read the obvious config locations.
  The narrative feels sufficient (it has internal logic, it explains the
  observation), but narrative sufficiency is not verification. This is
  the anti-dismissal rule: treat the plausible story as a hypothesis to
  disconfirm, not as a conclusion to accept.
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: related — both describe plausible narratives substituting for evidence
  - target: wiki/concepts/fabricated-fatigue-llm-session-end-recommendations
    type: related — same family: plausible-sounding LLM output that exceeds its evidence
  - target: wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns
    type: related — same family
  - target: wiki/concepts/fix-introduces-regression-by-trading-properties
    type: related — fix author constructs narrative for why the fix is safe
  - target: wiki/concepts/evidence-scope-discipline
    type: complements — that rule covers scope inflation; this covers narrative sufficiency
---

# Narrative-as-signal: plausible narrative is the trigger to investigate

## Decision context

**Why this knowledge was needed:** across multiple sessions (2026-07-20
through 2026-07-27), the model repeatedly dismissed correct findings
because it constructed a plausible story for why the finding was wrong,
invalid, or already handled. The story felt sufficient; the model stopped
investigating; the story turned out to be wrong. Every instance traced
back to the same pattern: **plausible narrative substituted for
verification.**

## The anti-pattern

```
model observes: "X doesn't work" or "X is missing"
model constructs narrative: "X can't work because Y" (Y is plausible, internally consistent)
model accepts narrative as answer: stops investigating
reality: X exists, works, or is handled — the narrative was wrong
```

The narrative is not random — it has internal logic, explains the
observation, and feels like understanding. That's what makes it
dangerous: **the feeling of understanding is not the act of verifying.**

## Observable symptoms

1. **"This can't be done because X"** — the model concludes
   impossibility from a single plausible reason without checking
   alternatives.

2. **"This doesn't exist"** — the model concludes absence from a
   failed search in one location without checking sibling locations.

3. **"This is already handled"** — the model concludes coverage from
   the existence of a mechanism without verifying it's wired or firing.

4. **"This is a known limitation"** — the model labels something as
   structural without verifying whether the limitation is current or
   documented.

## The rule

**The moment you think "this can't be done because X":**

1. Have you read the documentation for the system in question?
2. Have you checked the obvious config locations the docs name?
3. Are you conflating the finding with the proposed fix? (A wrong fix
   does not invalidate a correct finding.)
4. Is your narrative grounded in observed evidence, or in inference?

If the answer to (1) or (2) is "no," read the docs first. **The
narrative is the trigger to investigate, not the substitute for it.**

## Reference incidents

- **2026-07-20 session:** another LLM reported that MCP servers weren't
  being enumerated from `[mcp_servers]` in config.toml. The model
  checked config.toml, found no `[mcp_servers]` section, and concluded
  "the data doesn't exist in any static config." It then constructed a
  narrative ("the hook fires before MCP servers connect, so enumeration
  is structurally impossible"). Both were wrong: MCP config IS in static
  files — `~/.claude.json` and `~/.claude/.mcp.json`. The model didn't
  read the documentation until the user told it to.

- **2026-07-27 session:** the model declared Workstream B "DONE" after
  a single-module AST audit returned "zero function-body references to
  module-level constants." The narrative ("AST clean = hermetic") felt
  sufficient. The operator caught that `continuation_coverage.py` (an
  imported sibling module) still used globals and wrote to the real
  workspace. The narrative was plausible but exceeded its evidence —
  the audit scope was narrower than the claim.

## What this means for our workspace

- **AGENTS.md rule:** `P:/AGENTS.md` § "Narrative-as-signal" codifies
  this as a behavioral rule for all agents.
- **Operationalized in `/tp`:** the critic-phase asks "which of these
  outputs is a plausible narrative substituting for evidence?" — turning
  the behavioral rule into a structural check.
- **Related to [[reactive-pattern-matching-and-closure-pressure]]:**
  the narrative is often a closure-pressure artifact (the model wants
  to feel done, so it constructs a story that supports done-ness).

- **Connected to [[cross-module-call-graph-audit-false-negative]]:** the
  AST-clean narrative that exceeded its evidence is a direct instance.

- **Connected to [[single-repo-verification-false-negative-on-multi-repo-workspace]]:**
  the wrong-repo-search narrative is another direct instance.

## Falsifier

This pattern is wrong if plausible narratives are always correct — i.e.,
if every time the model says "this can't be done because X," X turns
out to be true. Empirical observation across multiple sessions shows
the opposite: plausible narratives exceed their evidence ~30-50% of
the time in this workspace. The pattern holds.

## Receipts

- `P:/AGENTS.md:141-145` — the governing behavioral rule ("Narrative-as-signal
  (anti-dismissal rule)")
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — `/tp` Step 3 verification
  synthesis: the spot-check gate that catches narrative-as-signal
  (originally after the cc-council incident, per `~/.grok/AGENTS.md`
  § "Subagent synthesis → report gate")
- `P:/AGENTS.md:141` — the exact line: "When you construct a plausible
  narrative for why something 'can't be done' or 'doesn't exist,' treat
  that as the **signal to read documentation** — not as the answer."

## Sources

- `P:/AGENTS.md` § "Narrative-as-signal (anti-dismissal rule)" — the
  governing behavioral rule
- Session 019fa111 (2026-07-27): cross-module audit false-negative —
  AST-clean narrative exceeded its evidence
- Session 019f821c (2026-07-20): MCP enumeration narrative — wrong repo
  search produced false absence claim
- `adhd-parallel-frame-divergent-ideation-integration.md` — maps this
  pattern to ADHD-trap detection as a critic-phase step
- `fabricated-fatigue-llm-session-end-recommendations.md` — same family:
  plausible-sounding LLM output exceeding its evidence
