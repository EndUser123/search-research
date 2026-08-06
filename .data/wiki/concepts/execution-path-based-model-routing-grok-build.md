---
title: "Execution-path-based model routing for Grok Build (quota-aware)"
created: 2026-07-30
source: session-20260730 (fleet quota system + model routing research)
tags: [architecture, routing, execution-path, quota-gate, spawn-gate, grok-build, model-selection, pick-model, fleet-models]
summary: >
  Grok Build's PreToolUse hooks can only allow/deny — they cannot modify
  tool input (no `updatedInput`). This means seamless model injection at
  the hook level is impossible. The solution is a three-layer architecture:
  (1) behavioral guidance via pool contracts + pick_model.py, (2) enforcement
  via PreToolUse deny-and-redirect gate, (3) execution-path selection —
  choosing spawn_subagent vs opencode/mmx/agy CLI based on task type. The
  execution-path insight is the key: we control model selection on every
  path except inline-parent, so the real question isn't "which model" but
  "which execution path + which model."
agent: grok
host: grok
cognitive_load: 3
verification: empirically-tested
status: active
sources:
  - "https://docs.x.ai/build/features/hooks (Grok Build hooks docs — PreToolUse allow/deny only)"
  - "https://code.claude.com/docs/en/hooks (Claude Code supports updatedInput)"
  - "https://github.com/workweave/router (WorkWeave Router — proxy-based routing)"
  - "https://www.tamirdresher.com/blog/2026/03/21/rate-limiting-multi-agent (9-agent rate coordination)"
relations:
  - target: wiki/concepts/model-picker-as-failover-not-router.md
    type: refines
  - target: wiki/concepts/fleet-quota-api-discovery-2026.md
    type: extends
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md
    type: complements
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
---

# Execution-path-based model routing for Grok Build

## Decision context

**The problem:** GLM-5.2 quota burned through 1600 prompts/5h in a single
session because every turn — including mechanical formatting, ruff checks,
and code iteration — consumed parent-model inference. When asked "how do we
use the best model automatically with no friction," the initial answer was
an auto-routing hook that injects a model into spawn_subagent calls.

**The blocker:** Grok Build's PreToolUse hooks output only
`{"decision": "allow"}` or `{"decision": "deny", "reason": "..."}`. There is
no `updatedInput` field (unlike Claude Code, Codex CLI, and Cursor). This
was verified by reading the Grok Build hooks documentation at
`~/.grok/docs/user-guide/10-hooks.md` lines 238-249.

**The realization that reframed the problem:** we already have full model
control on every execution path except inline-parent. The problem isn't "we
can't pick models" — it's that skills reflexively use `spawn_subagent` when
other paths (opencode, mmx, agy) would be better for certain task types.

## The three-layer architecture

### Layer 1: Behavioral guidance (pool contracts + pick_model.py)

Pool contracts ([[coding-model-pool]], [[reasoning-model-pool]],
[[mechanical-model-pool]], [[critic-model-pool]]) define tier-1 and tier-2
models per lane. `fleet-models.json` is the machine-readable registry.
`pick_model.py <lane>` returns the best available model filtered by quota
cache + serde-broken set + spawn-broken set.

**This is a recommendation, not enforcement.** The LLM follows it most of
the time but can ignore it. See [[model-picker-as-failover-not-router]]
for the original distinction between recommendation and enforcement.

### Layer 2: Enforcement (PreToolUse deny-and-redirect)

`PreToolUse_spawn_model_gate.py` blocks serde-broken models and
quota-exhausted providers. The deny message includes a lane-aware fallback
recommendation. This is the safety net — one extra inference turn cost when
the LLM picks wrong.

### Layer 3: Execution-path selection (the new insight)

This is the architectural decision. Different task types should use
different execution paths, not just different models. This extends
[[delegation-optimization-chunking-output-backend-discipline]] with
execution-path awareness.

| Task type | Best path | Why |
|-----------|-----------|-----|
| Read-only exploration | `spawn_subagent(type=explore, model=...)` | Fast, native, no context overhead |
| Write-capable implementation | `opencode run --model=X "..."` | Avoids serde bug, avoids AGENTS.md context bloat |
| Mechanical bulk work | `mmx text chat --model=MiniMax-M3` | Free-tier, no spawn overhead |
| Cross-model second opinion | `/agy`, `/codex`, `/mmx` skills | Already built, model-aware |
| Deep reasoning / critique | `spawn_subagent(model=reasoning)` | Needs full Grok context |

**Why this is better than pure spawn routing:** `spawn_subagent` has two
structural weaknesses that CLI tools don't have: (1) the serde bug that
crashes certain models, and (2) the ~26K token AGENTS.md context injection
that causes Mistral to 422. By routing write tasks through opencode or mmx,
we avoid both.

## Steelman: the proxy pattern (rejected)

The industry standard for seamless model routing is a proxy —
claude-code-router (10k+ stars) and WorkWeave Router (685 commits) both
sit between the CLI tool and the model providers, intercepting every API
call and routing per-request using ML-based task classification.

**Why we chose against it:** Grok Build's parent model talks to xAI's API
directly — there's no proxy point we can insert. Subagent spawns go through
Grok's internal dispatch, not an HTTP API we control. A proxy would only
help for opencode/codex/mmx CLI traffic, which is Layer 3's domain. Adding
Docker + Postgres (WorkWeave's requirements) for a subset of our traffic
isn't worth the infrastructure overhead.

The proxy pattern becomes viable when Grok Build adds `updatedInput` support
to PreToolUse hooks (matching Claude Code). At that point, the hook can
inject a model directly into spawn_subagent calls, making Layer 1 + Layer 2
fully seamless. Until then, the three-layer approach is the best we can do.

## What this means for our workspace

**Infrastructure built this session:**
- `fleet-models.json` — machine-readable registry (4 lanes × 2 tiers)
- `pick_model.py` — model picker with quota + serde awareness
- `fleet_quota.py` — quota dashboard covering 15+ providers
- `PreToolUse_spawn_model_gate.py` — deny-and-redirect gate
- `PostToolUseFailure_spawn_quota.py` — error-based cache updater
- Scheduled 30-min cache refresh (full opencode-quota refresh)

**The gap that remains:** no skill currently calls `pick_model.py` before
spawning. The `consumes:` frontmatter declarations point at pool contracts,
but nothing enforces that skills read them. The behavioral discipline of
"call pick_model.py before spawning" is the single biggest lever for
reducing wasted quota.

**The deeper gap:** skills default to `spawn_subagent` reflexively. Shifting
to execution-path-aware dispatch (Layer 3) requires updating skill design
patterns — each skill should classify its task type and pick the path, not
just the model.

## Receipts

- **PreToolUse output contract (allow/deny only):** `~/.grok/docs/user-guide/10-hooks.md` lines 238-249.
  Output vocabulary: `{"decision": "allow"}` or `{"decision": "deny", "reason": "..."}`. No `updatedInput` field.
- **Claude Code supports updatedInput:** `code.claude.com/docs/en/hooks` — confirmed via web research, not local inspection.
- **Grok Build does NOT support updatedInput (re-verified 2026-08-06):** Falsifier test in session 019fd8dc. Hook fired (confirmed via log), hook emitted valid JSON with `hookSpecificOutput.updatedInput` swapping `model: minimax-m3` → `model: nim-openai-gpt-oss-20b`, Grok Build ignored the modification — subagent ran on original model, no swap marker in prompt. The documented limitation still holds as of 2026-08-06.
- **serde-broken model set:** `~/.grok/skills/model-quota/scripts/fleet-models.json` → `serde_broken` array.
  Source: `PreToolUse_spawn_model_gate.py` function `get_serde_broken()`.
- **spawn gate implementation:** `~/.grok/hooks/PreToolUse_spawn_model_gate.py` — reads registry, checks serde-broken + quota cache, returns deny with lane-aware fallback.
- **pick_model implementation:** `~/.grok/skills/model-quota/scripts/pick_model.py` function `pick()` — reads `fleet-models.json` + quota cache + learned-broken, returns best available model per lane.
- **AGENTS.md context injection (~26K tokens):** [INFERENCE] observed as Mistral 422 error cause in session 2026-07-29. Not directly measured but consistently reproduced.

## Falsifier

This architecture is wrong if:
- Grok Build adds `updatedInput` support to PreToolUse hooks (makes the
  proxy-pattern-at-the-hook-level possible, obsoleting Layer 2's
  deny-and-redirect approach)
- The serde bug is fixed (removes the need for execution-path selection —
  all models work via spawn_subagent)
- The AGENTS.md context injection is reduced below 4K tokens (makes
  spawn_subagent viable for Mistral and other context-sensitive models)

## Sources

- [Grok Build Hooks](https://docs.x.ai/build/features/hooks) — PreToolUse output contract: allow/deny only
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks) — supports `updatedInput` for argument modification
- [WorkWeave Router](https://github.com/workweave/router) — proxy-based routing with opencode integration
- [Tamir Dresher: 9 AI Agents, One API Quota](https://www.tamirdresher.com/blog/2026/03/21/rate-limiting-multi-agent) — rate coordination patterns for multi-agent fleets
- [Avengers-Pro (arXiv:2508.12631)](https://arxiv.org/abs/2508.12631) — performance-efficiency optimized routing
