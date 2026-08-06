---
title: "Model delegation: using cheap models for mechanical code edits to preserve expensive-model quota"
created: 2026-08-06
source: /www research session 019fd8dc
tags: [model-routing, cost-aware-delegation, coding-model-pool, oh-my-pi, frugalgpt, cascade-routing, glm-5-2, quota-management]
summary: >
  GLM-5.2 quota was being consumed by mechanical code edits that cheaper models
  handle as well or better. Research covers: (1) our existing but underused
  delegation infrastructure (codex-external-delegation bridge with role-scored
  model selector), (2) free tier-1 coding models already in the pool
  (or-ling-3-flash-free, nim-openai-gpt-oss-20b), (3) oh-my-pi (omp) as a
  potential upgrade with role-based model routing and hashline edits, (4)
  FrugalGPT cascade routing research (up to 98% cost reduction). Recommendations:
  immediate behavioral fix (use tier-1 free models for code subagents), medium-term
  (wire external delegation bridge from Grok Build), long-term (evaluate omp).
agent: grok
host: grok
cognitive_load: 2
verification: research-verified
relations:
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: applies
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: extends
  - target: wiki/concepts/cost-aware-delegation.md
    type: related
  - target: capabilities/coding-model-pool.md
    type: implements
  - target: wiki/concepts/tool-fallbacks.md
    type: related
---

# Model delegation: using cheap models for mechanical code edits

## Decision context

**The problem:** GLM-5.2 (Z.ai subscription) hit rate limits because it was being
used for mechanical code edits — lint fixes, placeholder renames, scanner
patches — that cheaper or free models handle as well or better. The operator
flagged: "these code edits are EASILY done by M3 and other models."

**What the research changed:** confirmed that the workspace already has the
infrastructure to route code edits to cheaper models (role-scored model selector,
coding-model-pool with free tier-1 models), but the behavioral gap is that the
parent agent (Grok) does edits inline instead of dispatching. The fix is partly
behavioral (use what we have) and partly infrastructural (wire external
delegation from Grok Build).

## Evidence

### Our existing model selector already knows the answer

The `codex-external-delegation` package (`P:\packages\codex-external-delegation\src\model-selector.mjs`)
scores models by role:

| Model | Provider | Mechanical | Coding | Verification | Reasoning | Quota class |
|---|---|---|---|---|---|---|
| DeepSeek-v4-flash | OpenCode Go | **96** | 88 | 92 | — | shared_subscription |
| DeepSeek-v4-flash | NVIDIA NIM | **94** | 86 | 90 | — | unlimited_with_rate_limit |
| MiniMax-M3 | MiniMax | 76 | **98** | 84 | — | dedicated_regenerating |
| GLM-5.2 | Z.ai | 70 | 86 | 90 | **100** | dedicated_regenerating |
| DeepSeek-v4-flash | OpenCode Zen | 88 | 82 | 84 | — | rate_limited_free |

GLM-5.2 scores **lowest on mechanical** (70) and **lowest-tier on coding** (86).
It's the right model for reasoning (100) but the wrong model for code edits.

### Free tier-1 coding models already verified

From `[[coding-model-pool-tier-1-tier-2]]` (benchmark-verified 2026-07-29/31):

| Model | Provider | Code-exec | Reasoning | Speed | Cost |
|---|---|---|---|---|---|
| or-ling-3-flash-free | OpenRouter | 5/5 | 13/13 | 2.2s | **$0/M** |
| nim-openai-gpt-oss-20b | NVIDIA NIM | 4/5 | 13/13 | 7.7s | **free** |

These are already declared as the coding-model-pool for `/go` H4 parallel
dispatch. The `/go` SKILL.md says to use them. The gap is behavioral compliance.

### FrugalGPT cascade routing (external research)

FrugalGPT (Chen et al., Stanford 2023, arXiv:2305.05176) demonstrated:
- **Up to 98% cost reduction** through cascade routing
- 60-80% of production queries are simple enough for a small/cheap model
- The cascade: try cheap model first → escalate to expensive only when quality
  threshold not met
- Price spread across model tiers is 15-100× in 2026

Three routing strategies from the literature:
1. **Rule-based** (query length, code presence, context size) — simple, brittle
2. **Classifier-based** (small model classifies complexity → routes to tier) — accurate
3. **Cascade** (try cheap → escalate on uncertainty) — elegant, adds latency

**Caveat (I-CALM):** an independent benchmark found a commercial router doing
worse than no routing at all (Sean Geng, "The honest guide to LLM model routing").
Routing quality matters — a bad router wastes more than it saves.

### Oh-My-Pi (omp)

**can1357/oh-my-pi** — a Pi fork (from badlogic/pi-mono) by Can Bölük.
Repository: https://github.com/can1357/oh-my-pi

Key features relevant to our delegation problem:
- **Ten model roles** that route by intent: `smol` (cheap fan-out), `slow` (deep
  reasoning), `default`, `plan`, `commit`, `vision`, `designer`, `task`,
  `advisor`, `tiny`. This is exactly the tiered routing pattern our workspace needs.
- **Hashline edits** — content-hash anchors instead of retyping lines. Reduces
  output tokens by 61% on Grok 4 Fast. MiniMax pass rate 2.1× with same weights.
- **Advisor model** — a second model watches every turn on its own context/model
- **RPC mode** (`omp --mode rpc`) + Node SDK for programmatic control
- **60+ providers, 1000+ models** — one `/model` command to switch
- **Fallback chains** per role; round-robin credentials per provider
- Native Windows support (no WSL bridge)
- MIT licensed, TypeScript + Rust core

Related Pi ecosystem tools:
- **monopi** (ifiokjr) — one-click setup, like oh-my-zsh for pi
- **agent-pi** (ruizrica) — multi-agent orchestration extension
- **pi-orchestration** (0xKobold) — subagent orchestration with worktree isolation
- **oh-my-openagent / lazycodex** (code-yeongyu) — Codex/OpenCode variant

## Recommendations

### Immediate (behavioral fix — this session)

**Use coding-model-pool tier-1 for code subagents instead of parent Grok or GLM-5-2.**
When dispatching code-edit subagents via `spawn_subagent`, pass `model="or-ling-3-flash-free"`
or `model="nim-openai-gpt-oss-20b"`. These are free, benchmark-verified, and
already declared in the pool. [SUPPORTED — multi-source: benchmark + capability contract]

**Reserve GLM-5-2 for reasoning-only roles** (plan, debug, critic).
Its role score of 100 on reasoning justifies the quota cost. Its 70 on mechanical
does not. [SUPPORTED — model-selector role scores]

### Medium-term (infrastructure)

**Wire the external delegation bridge from Grok Build.** The
`codex-external-delegation` package can dispatch to PI workers with automatic
model selection. The model selector already ranks candidates by role fit, quota
headroom, and reliability. What's missing: a Grok-side invocation path that
calls `node P:\packages\codex-external-delegation\bin\external-delegation.mjs run`
from within a skill or /go phase. [INFERENCE — bridge exists for Codex, not yet wired for Grok]

**Add `/model-benchmark` evidence for omp models.** The omp harness claims
significant model performance lifts (MiniMax 2.1×, Grok 4 Fast -61% tokens).
Our `/model-benchmark` skill can verify these claims on our workload.
[UNTESTED — requires live benchmark run]

### Long-term (evaluate upgrade)

**Evaluate oh-my-pi (omp) as a replacement for the current PI setup.** omp's
role-based model routing, hashline edits, and advisor model directly address
the quota waste problem. The RPC mode allows Grok Build to drive omp
programmatically. [UNTESTED — requires installation and evaluation]

**Consider omp's `smol` role for mechanical fan-out.** This is the cascade
routing pattern from FrugalGPT: cheap model first, escalate only when needed.
omp implements this as a first-class role. [INFERENCE — based on omp docs]

## Workspace-counterexample check

- **Tool-fallbacks:** `[[tool-fallbacks]]` documents known model failures.
  or-ling-3-flash-free and nim-openai-gpt-oss-20b are not in the exclusion list.
  ✅ No counterexample.
- **Nemotron routing policy:** AGENTS.md says nemotron via PI/opencode CLI for
  reasoning, not Grok spawn. This doesn't conflict — we're recommending
  or-ling/nim for code, not nemotron for reasoning. ✅ No conflict.
- **Context firewall:** `[[context-firewall-architecture]]` — each subagent runs
  in its own context. Using cheaper models as subagents is the intended pattern.
  ✅ No conflict.

## Falsifier

If or-ling-3-flash-free or nim-openai-gpt-oss-20b produce incorrect code edits
on our actual workload (skill scripts, Python lint fixes), the recommendation to
use them for code subagents is wrong. Test with a sample of real edits before
trusting the benchmark scores on our specific codebase.

## Sources

- FrugalGPT: Chen et al., 2023, arXiv:2305.05176 — cascade routing, 98% cost reduction
- Pristren blog (2026-05): model routing guide, 50-70% cost reduction
- Sean Geng (2026): "The honest guide to LLM model routing" — commercial router caveat
- can1357/oh-my-pi GitHub — omp feature set, model roles, hashline edits
- Workspace: `P:\packages\codex-external-delegation\src\model-selector.mjs` — role scores
- Workspace: `P:/.data/wiki/capabilities/coding-model-pool.md` — tier-1/tier-2 pool
- Workspace: `[[coding-model-pool-tier-1-tier-2]]` — benchmark evidence
