---
title: "Model Routing Implementations: Community Comparison (2026-07-31)"
created: 2026-07-31
source: session-20260731
tags: [model-routing, model-selection, agent-harness, pool-contracts, spawn-gate, comparison]
summary: >
  Four community implementations of per-task model routing for agentic CLIs,
  compared against our three-layer spawn protection + pool contract system.
  The Hermes model-router plugin (5-tier classifier with auto-escalation) is
  the closest analogue. Claude Code subagent routing via .claude/rules is the
  simplest. Tokenless (YC S26) is a commercial proxy gateway. Our approach
  is unique in using PreToolUse hooks for enforcement rather than config or
  proxy.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://github.com/open-world-project/model-router (open-world-project, 2026)
  - https://github.com/NousResearch/hermes-agent/issues/5508 (NousResearch, Apr 2026)
  - https://news.ycombinator.com/item?id=49099143 (Tokenless YC S26, Jul 2026)
  - https://gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd (peragwin, Jul 2026)
  - https://docs.openclaw.ai/gateway/config-agents (OpenClaw Docs, 2026)
relations:
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: complements
  - target: wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md
    type: related
  - target: docs/designs/2026-07-30-quota-aware-model-routing.md
    type: related
---

# Model Routing Implementations: Community Comparison

## Decision context

Session 20260730/31 built a three-layer spawn protection system (PreToolUse
gate + PostToolUseFailure error learner + UserPromptSubmit injector) with
pool contracts as the model-selection guidance layer. The operator asked:
"find the exact implementations, I want to capture and compare to what we
have." This concept captures the four community implementations found and
compares each to our system.

## Implementation 1: Hermes Agent model-router plugin

**Repo:** [github.com/open-world-project/model-router](https://github.com/open-world-project/model-router)
**License:** MIT | **Status:** Active (4 commits)

**How it works:**
- 5-tier model contract (T1-T5), each tier maps to a specific model
- Per-turn classifier (separate small model) classifies each turn's
  difficulty BEFORE the main model runs
- Auto-escalation: after 2 consecutive tool errors, bumps up one tier
- Auto-de-escalation: drops back to base tier after turn completes
- Manual pinning: `/t1` to `/t5` pins session to a specific tier
- Config via `model_router.yaml` with per-profile support
- Patches Hermes core files (commands.py, cli.py) to intercept model calls
- WebUI integration: patches API routes + static UI for tier controls

**Default tiers:**

| Tier | Model | Purpose |
|------|-------|---------|
| T1 | qwen3.5-flash | triage, acks, cheap helper |
| T2 | deepseek-v4-flash | default daily-driver |
| T3 | minimax-m2.7 | creating, coding, review |
| T4 | deepseek-v4-pro | planning, architecture |
| T5 | claude-sonnet-4.6 | high-stakes reasoning |

**Compared to ours:**

| Aspect | Hermes model-router | Our system |
|--------|-------------------|------------|
| Tier system | 5 tiers (T1-T5) | 2 tiers (tier1, tier2) × 4 lanes |
| Classification | Per-turn classifier (separate model) | Behavioral (LLM reads pool contract) |
| Enforcement | Patches Hermes core (intercepts model call) | PreToolUse hook (blocks, doesn't modify) |
| Escalation | Auto (2 errors → bump tier) | None (deny-and-redirect only) |
| De-escalation | Auto (drops after turn completes) | None |
| Config | YAML with per-profile | Markdown pool contracts |
| Pinning | `/t1`-`/t5` slash commands | `--model` flag on spawn_subagent |
| Manual override | `/auto` resumes automatic | `--model` override skips gate |

**What they do better:** auto-escalation on errors and per-turn
classification. Our system blocks but doesn't escalate.

**What we do better:** quota-awareness (their system doesn't check quota
before routing). Our spawn gate reads a live quota cache; theirs doesn't.

## Implementation 2: Hermes Agent per-skill model config (issue #5508)

**Issue:** [github.com/NousResearch/hermes-agent/issues/5508](https://github.com/NousResearch/hermes-agent/issues/5508)
**Status:** Closed (feature request)

**Three mechanisms proposed:**
1. `delegate_task(model=..., provider=...)` — per-call model override
2. Skill frontmatter `model:` field — skill declares its own model
3. Config aliases — `supervisor_model` + `execution_model` in config

**Compared to ours:** This is EXACTLY our pool contract pattern but baked
into the harness config rather than wiki markdown. The skill frontmatter
`model:` field is the cleanest version — the model is part of the skill
definition, not a runtime decision.

**What they do better:** the `model:` frontmatter field means the model is
deterministic per skill, not dependent on LLM behavioral compliance. We
can't do this in Grok Build (subagent types don't support per-type model
defaults).

## Implementation 3: Claude Code subagent routing via .claude/rules

**Gist:** [gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd](https://gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd)

**How it works:**
- A markdown rules file in `.claude/rules/` that instructs the orchestrator
  on model selection per task type
- Five model tiers: Haiku (mechanical), Sonnet (workhorse), Opus
  (judgment-dense), GPT-5.6 Sol (specialist escalation), Fable (planner)
- Explicit delegation rules: "keep quick targeted changes in main
  conversation, delegate bounded side tasks"
- Routing by: ambiguity, coupling, decision density, verification difficulty
- Hard rules: "Always set model explicitly per invocation. Never rely on
  default inherit."

**Compared to ours:** This is a PURE BEHAVIORAL approach — no mechanical
enforcement at all. It's the same as our pool contracts without the spawn
gate. The rules file is the pool contract; the difference is they trust the
LLM to follow it.

**What they do better:** simplicity. One markdown file, no hooks, no cache,
no infrastructure. The LLM reads the rules and picks.

**What we do better:** mechanical enforcement. Their system has no fallback
when the LLM ignores the rules.

## Implementation 4: Tokenless (YC S26)

**HN:** [news.ycombinator.com/item?id=49099143](https://news.ycombinator.com/item?id=49099143)
**Status:** Commercial product, launched Jul 2026

**How it works:**
- API gateway proxy that sits between agent and model providers
- Per-turn routing: fans out to multiple models in parallel, watches their
  progress, picks the winner early
- Custom foundation models predict LLM confidence on each turn
- Cuts off unconfident expensive models early to save tokens
- Works with Claude Code, Codex CLI, and any OpenAI-compatible agent
- Claims Claude Fable 5 quality at 50% cost

**Key HN discussion insights:**
- HN commenters challenge cache invalidation: "most agentic work involves
  long strings of successive tool calls that benefit from a hot cache"
- Competing gateway builder (vancouvermatt): "most of our savings came
  from stopping our own code from invalidating [the cache prefix], not from
  the routing decision"
- brandall10: "seems like it might be more advantageous to just adjust
  reasoning effort to retain cache" — but Claude's cache breaks with
  reasoning effort adjustment
- verdverm: "model routing seems like a piece of the AI stack that will
  quickly distill into industry if it is even that useful. More likely you
  want to evaluate some and then settle on the model-agent-task pairings"

**Compared to ours:** Tokenless is a proxy gateway — it intercepts HTTP
traffic. Our system operates at the hook level inside Grok Build. The proxy
approach can modify requests (their `updatedInput` equivalent); our hooks
can only block.

**What they do better:** can modify requests mid-flight. Can race multiple
models and pick the best output. Has a classifier model, not just rules.

**What we do better:** no external dependency. No proxy latency. Works
within Grok Build's architecture without modifying API traffic. Our quota
cache is our own data, not a gateway's.

## What we're missing (actionable gaps)

1. **Per-turn classifier.** Hermes model-router uses a separate small model
   to classify each turn's difficulty before routing. We rely on the
   orchestrator LLM's judgment, which is behavioral. A lightweight classifier
   (even a rule-based one using token count + tool-call type) would add
   mechanical routing intelligence.

2. **Auto-escalation.** Hermes escalates on 2 consecutive errors. Our gate
   only blocks. Adding "if spawn fails twice, recommend a higher-tier model"
   would be a simple PostToolUseFailure extension.

3. **Skill-level model declaration.** Hermes issue #5508 proposes `model:`
   in skill frontmatter. Claude Code uses `.claude/rules/` for the same
   purpose. We have `consumes:` declarations but no `model:` field. Adding
   `model:` to SKILL.md frontmatter would bake the model into the skill
   definition.

4. **Cache-awareness.** Tokenless and the HN discussion both highlight that
   KV-cache invalidation is the dominant cost factor, not per-token pricing.
   Our system doesn't consider cache state when routing.

## What we do that nobody else does

1. **Quota-aware routing.** None of the four implementations check quota
   before routing. Our system reads a live quota cache from 15+ providers
   and blocks exhausted providers mechanically. This is unique.

2. **Serde-broken model detection.** None of the four handle platform-specific
   model incompatibilities (like Grok Build's serde deserialization failures).
   Our learned-serde-broken file self-corrects when new models break.

3. **Three-layer enforcement.** The community uses either config (Hermes),
   rules (Claude Code), or proxy (Tokenless). Nobody uses a three-layer
   system (proactive injector + enforcement gate + reactive error learner).
   Our architecture is more defensive but also more complex.

## Honest assessment

Our system is the most defensive of the four — it prevents failures that the
others don't encounter (serde crashes, quota exhaustion). But it's also the
least intelligent — no classifier, no escalation, no per-turn routing. The
pool contracts are behavioral guidance, same as Claude Code's rules file.

The Hermes model-router plugin is the most complete implementation: 5-tier
contract + per-turn classifier + auto-escalation + manual pinning. If we
could add their classifier + escalation to our quota-aware gate, we'd have
the best of both worlds.

## Falsifier

This comparison is wrong if:
- The Hermes model-router or Tokenless implementations have changed
  significantly since July 2026 (both are active)
- Grok Build adds `updatedInput` support, making the proxy approach viable
  for us
- A new implementation emerges that combines quota-awareness with
  per-turn classification (currently nobody does both)

## Receipts

- Hermes model-router: [github.com/open-world-project/model-router](https://github.com/open-world-project/model-router) — 5-tier system with auto-escalation, MIT, 4 commits, read full README
- Hermes issue #5508: [github.com/NousResearch/hermes-agent/issues/5508](https://github.com/NousResearch/hermes-agent/issues/5508) — per-skill model config feature request, closed
- Tokenless HN: [news.ycombinator.com/item?id=49099143](https://news.ycombinator.com/item?id=49099143) — 61 comments, YC S26 launch, read full thread
- Claude Code rules: [gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd](https://gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd) — behavioral routing via .claude/rules/, read full gist
- AgentPatterns.ai: [agentpatterns.ai/patterns/agent-design/auto-model-selection/](https://www.agentpatterns.ai/patterns/agent-design/auto-model-selection/) — comprehensive pattern catalog, read full page

## What this means for our workspace

- Our quota-aware gate is unique — no community implementation checks quota
  before routing. This is a genuine differentiator, not a gap.
- The Hermes model-router plugin's auto-escalation pattern (2 errors → bump
  tier) could be added to our PostToolUseFailure hook as a follow-up.
- The `model:` frontmatter field from Hermes issue #5508 is the cleanest
  model-selection mechanism — we should add it to our SKILL.md frontmatter
  if Grok Build ever supports per-type model defaults.
- Our pool contracts are functionally equivalent to Claude Code's
  `.claude/rules/` approach — both are behavioral guidance without
  mechanical enforcement. The spawn gate is our differentiator.
- Cache invalidation is the dominant cost factor in real agent workloads
  (per HN discussion) — something to consider when evaluating Tokenless or
  any proxy approach.

## Related concepts

- [[execution-path-based-model-routing-grok-build]] — our three-layer architecture
- [[model-role-assignment-public-vs-custom-benchmarks]] — why GLM-5.2 is orchestrator
- [[delegation-decision-rule-context-dependency]] — when to delegate vs keep on orchestrator
- [[agentic-harness-seven-components-2026]] — system prompt is only component that regresses alone

## Sources

- [Hermes model-router](https://github.com/open-world-project/model-router) (open-world-project, 2026) — 5-tier auto-routing plugin
- [Hermes issue #5508](https://github.com/NousResearch/hermes-agent/issues/5508) (iRonin, Apr 2026) — per-skill model config proposal
- [Tokenless HN](https://news.ycombinator.com/item?id=49099143) (rohaga, Jul 2026) — YC S26 proxy gateway launch
- [Claude Code subagent routing](https://gist.github.com/peragwin/13de94e77fce9c9ccb60e3968292e4bd) (peragwin, Jul 2026) — behavioral rules file
- [AgentPatterns.ai: Auto Model Selection](https://www.agentpatterns.ai/patterns/agent-design/auto-model-selection/) — comprehensive pattern reference
