---
title: "Skill Auto-Invocation Reliability: Does It Work, Does the Host Matter?"
created: 2026-07-23
source: session-2026-07-23 (/www research on skill activation reliability)
tags: [skill-enforcement, progressive-disclosure, auto-invocation, cross-host, reliability, activation-failure, execution-failure]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://medium.com/@marc.bara.iniesta/claude-skills-have-two-reliability-problems-not-one-299401842ca8 (Marc Bara, Mar 2026 — 650-trial experiment analysis)
  - https://medium.com/@ivan.seleznov1/why-claude-code-skills-dont-activate-and-how-to-fix-it-86f679409af1 (Seleznov, Mar 2026 — 650-trial experiment, source data)
  - https://paddo.dev/blog/claude-skills-controllability-problem/ (paddo.dev, Jan 2026 — controllability analysis)
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (Claude platform docs)
  - wiki/concepts/skill-enforcement-layers (our 3-layer analysis)
  - wiki/concepts/skill-step-downgraded-from-action-to-note (execution failure mode)
  - wiki/concepts/rule-not-fired-vs-rule-doesnt-exist (trigger vs rule)
  - wiki/concepts/grok-build-runtime-docs-divergence (host divergence)
relations:
  - target: wiki/concepts/skill-enforcement-layers
    type: refines
  - target: wiki/concepts/skill-step-downgraded-from-action-to-note
    type: related
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: related
  - target: wiki/concepts/rule-not-fired-vs-rule-doesnt-exist
    type: related
---

# Skill Auto-Invocation Reliability

## Decision context

**Why this research was needed:** the operator asked whether skills work
as automatic behavior, and whether the host platform (Claude Code vs Grok
Build vs Codex vs AGY) matters for skill enforcement reliability. This
determines whether skills can be trusted to fire on their own or whether
explicit invocation (slash commands) is always necessary.

**What the research changed:** confirmed quantitatively that
auto-invocation is unreliable with default descriptions (77%), fixable
to 100% with directive descriptions, but execution (step-following)
remains an unsolved reliability problem. The host matters enormously
for enforcement layers but not for the invocation mechanism itself.

## Two reliability problems (not one)

| Problem | What happens | Fix | Reliability after fix |
|---------|-------------|-----|----------------------|
| **Activation failure** | Skill never loads — model answers directly | Directive descriptions ("ALWAYS invoke... Do not X directly") | 100% (Seleznov 650-trial) |
| **Execution failure** | Skill loads but steps get skipped (especially late-stage verification) | Rewrite steps to require visible output | `[UNKNOWN]` — no structural fix proven |

Both look identical to the user: output that missed something the skill
was supposed to catch.

## Quantitative evidence (Seleznov 650-trial experiment, Mar 2026)

| Description style | Activation rate | Notes |
|-------------------|----------------|-------|
| Passive ("Use when creating Dockerfiles") | **77%** | Anthropic's default recommendation |
| Directive ("ALWAYS invoke... Do not write directly") | **100%** | 20x higher odds (p < 0.0001) |
| Passive + scoring hook | **37%** | Hooks made it WORSE — added noise |

Key insight: "Use when" is a suggestion that competes with the base
behavior and loses. "Do not X directly" blocks the base behavior, leaving
the skill as the only path.

## Why execution failures are harder

Even when a skill loads, the model deprioritizes procedural steps that
delay output without producing visible content. A verification step at
the end of a skill is:

- Far from the user's prompt (recency disadvantage)
- Meta-level (describes HOW, not WHAT to produce)
- Opposes the RL-trained "be helpful and responsive" pattern
- Produces no visible content (easy to skip silently)

Fix direction: rewrite critical steps to require **visible output** that
makes skipping detectable. No controlled experiment has proven this works
at scale yet.

## Does the host matter?

**For invocation mechanism: no.** All LLM-based agents (Claude Code,
Grok Build, Codex, AGY) use the same fundamental approach: model reads
skill description, semantically matches against user request, decides
whether to invoke. The reliability depends on how language models work,
not on platform code.

**For enforcement layers: yes, enormously.**

| Layer | Claude Code | Grok Build |
|-------|-------------|------------|
| Slash commands (explicit) | ✅ | ✅ |
| Skill auto-invocation | ✅ ~77%/100% | ✅ same mechanism |
| PreToolUse hooks | ✅ | ✅ (Grok-native only) |
| Stop hooks | ✅ | ✅ (Grok-native only) |
| Claude-side cc-aca-* suite (28 plugins) | ✅ | ❌ `compat.claude.hooks=false` |
| Permission deny rules | ✅ | ✅ (via compat layer) |

The critical gap: on Grok Build, the entire Claude-side enforcement
suite is disabled. Skills that assume Claude hooks fire will not have
that backstop.

## Cross-host skill design rules

1. **Never rely on auto-invocation alone.** Use directive descriptions.
2. **Always provide explicit slash-command invocation.** Works on every platform.
3. **Assume execution failures happen.** Rewrite critical steps to require visible output.
4. **Host-specific enforcement is not portable.** Skill *content* is portable; *enforcement* is not.
5. **The skill is a starting point for a process, not a guarantee the process was followed.** (Marc Bara)

## What Claude Code 2.1 changed

Anthropic merged skills and slash commands — skills now appear in the
slash menu by default, giving explicit `/skill-name` invocation. This
confirms auto-invocation was unreliable enough to require explicit
invocation as the primary path. (paddo.dev, Jan 2026)

## Falsifier

This concept is wrong if:
- Seleznov's 650-trial results don't replicate at scale (check for larger studies)
- Claude Code 2.1+ skills achieve >95% auto-invocation without directive descriptions
- Execution failures prove fixable with a structural mechanism (check for step-compliance experiments)
- Host platform proves irrelevant to enforcement (check if Grok Build adds native enforcement equivalent to cc-aca-*)
