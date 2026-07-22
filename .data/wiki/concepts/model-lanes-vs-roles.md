---
title: "Model lanes vs roles: the 2-lane routing framework"
created: 2026-07-21
source: session-2026-07-21
tags: [models, routing, lanes, roles, fleet, grok-build, ccr-ornith, diffusiongemma, gemini, quality-latency, pareto, architectural]
summary: >
  Two model lanes (Reasoning vs Code/everything-else) replace seven cognitive
  modes. Personas/roles still specialize behavior; models follow the lane.
  Multimodal is a capability filter, not a third lane. Free local + NVIDIA
  first when they clear the quality floor; subscription escalate after.
  ccr-ornith is the Code lane primary (65K context, fast, free, but misreads
  Windows file attributes and times out on large reviews). DiffusionGemma is
  the Code lane fallback (262K context, 42x faster than ornith, but produces
  less detailed output and fails via spawn_subagent with "empty content").
  Gemini 3.x Flash is the new multimodal-capable free option.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: refines
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: related
  - target: wiki/concepts/gemini-google-api-models-2026-07
    type: related
  - target: wiki/concepts/gemini-api-vs-agy-cli
    type: related
---

# Model lanes vs roles: the 2-lane routing framework

## Why this page exists

The `/go` skill has a spawn recipe that routes work to different models. The
logic was captured in the skill file (`~/.grok/skills/go/SKILL.md` § Spawn recipe)
but never distilled into its own wiki concept. This page is the durable reference
for the lane framework and the model-specific knowledge that informs lane choice.

## The framework: lanes, not modes

**Decision rule — quality–latency Pareto with a quality floor:**

1. **Quality floor first.** Never pick a model that cannot do the job reliably,
   even if it is free and fast. Floor is role-relative.
2. **Among models that clear the floor, prefer free / local / NVIDIA** when
   quality is good enough — save subscription quota for work that needs it.
3. **Latency is secondary.** ~2σ slower is fine if ~2σ+ higher quality. Hurry
   only when latency is bad relative to the quality premium.
4. **Do not over-split roles.** Practical work collapses to two lanes.

### Two lanes

| Lane | When | Persona / type | Effort | Primary (free) | Escalate |
|------|------|----------------|--------|----------------|----------|
| **Reasoning** | Plan, architecture, RCA, adversarial critic, hard trade-offs | `plan` + `sdlc-plan`; `sdlc-debug`; `sdlc-critic` | **high** | `nvidia-nemotron-3-ultra` | `glm-5-2`; parent `grok-4.5` if needed |
| **Code / everything else** | Implement, discover, tests, mechanical work | `sdlc-code`; `sdlc-discover`; test | low–**medium** | `ccr-ornith` (local) | `nvidia-diffusiongemma-26b`; then `minimax-m3`; then `gemini-3.6-flash` |

**Multimodal is a capability filter, not a third lane.** When the packet needs
images/audio, pick a multimodal-capable model that still fits the lane: `gemini-3.6-flash`,
`minimax-m3`, `nvidia-inkling`.

**zen/OR free models:** backup, perspective diversity, research failover — not
default coding path.

### Personas vs models — what each layer owns

| Layer | Owns | Example |
|-------|------|---------|
| **Role / mode** (persona) | Behavior specialization (what the agent attends to) | discover, plan, code, critic |
| **Model lane** | Which provider runs the inference | Reasoning vs Code |
| **Picker** | Transport failover mid-failure | `/model <slug>` or Ctrl+M |
| **Fusion** | Opt-in multi-model synthesis (async only) | OpenRouter Fusion, MoA panel |

## ccr-ornith — Code lane primary

### What it is

Local llama-server via CCR. Model: `ornith-1.0-9b`. Fast, free, no quota, no
network dependency.

### Capabilities (verified 2026-07-21)

| Property | Value |
|----------|-------|
| Context window | 65K (rated) — effective ~30-40K under tool-heavy agents |
| Speed | Fast for small tasks; **956s observed on a large githook review** (cancelled by timeout) |
| Cost | Free (local) |
| Code quality | Strong — produced most complete answer in binary-search test (including assertions) |
| Network | None (localhost) |

### Known limitations (verified this session)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **65K context limit** | Handoff reviews / large file dumps fail with `exceed_context_size_error` | Use Nemotron (1M) or DiffusionGemma (262K) for large-context work |
| **Windows file attribute false-positives** | Githook review reported "hook not executable" as critical — empirically refuted; the hook ran fine | Treat ornith's Windows-specific claims as `[INFERENCE]` until verified |
| **Slow on large reviews** | 956s for partial review (cancelled) | Split large reviews into smaller chunks; or use DiffusionGemma for breadth-first reads |
| **spawn_subagent serialization errors** | Sometimes fails with serialization error on certain model slugs | Fall back to parent-inherited model for spawn |

### When to use

- Default Code lane primary for implementation, discovery, tests
- Small-to-medium context tasks (<30K effective)
- When you need free + fast + local

### When NOT to use

- Large-context work (>30K effective) → use DiffusionGemma or Nemotron
- Windows file attribute analysis → verify claims independently
- Reviews requiring >10 min → split or use faster model for breadth

## nvidia-diffusiongemma-26b — Code lane fallback

### What it is

NVIDIA-hosted `google/diffusiongemma-26b-a4b-it`. Free, 262K context, diffusion-LLM hybrid.

### Capabilities (verified 2026-07-21)

| Property | Value |
|----------|-------|
| Context window | 262K |
| Speed | **42x faster than ccr-ornith** for file reads (~1-3.5s per call) |
| Cost | Free (NVIDIA) |
| Code quality | Less detailed than ornith; 17/20 vs 20/20 on blind comparison (T4 test) |
| Network | NVIDIA API (no quota competition with subscription) |

### Known limitations (verified this session)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **spawn_subagent "empty content"** | Fails via `spawn_subagent(model="nvidia-diffusiongemma-26b")` with "Empty content not allowed for assistant messages" | Use **direct Python API calls** via `diffusiongemma_read.py` instead of spawn_subagent. Root cause: spawn_subagent sends parameters that conflict with thinking mode. |
| **API 400 errors** | Sometimes returns 400 on trivial calls | Retry once; fall back to ornith or minimax-m3 |
| **Shallower output** | Less detailed summaries than ornith | Use fan-out multi-pass: 3-4 calls with different prompts, then merge. See `compensating-for-weaker-models-ensemble-multi-pass` |
| **Temperature untested** | Temperature parameter not verified via NVIDIA endpoint | Test before relying on temperature-controlled sampling |

### When to use

- Large-context file reads (>30K effective) — 262K window
- Breadth-first mechanical scanning (fast, cheap)
- Multi-pass fan-out reads (42x faster → 3-4 calls still faster than 1 ornith call)
- When ornith's context limit is the bottleneck

### When NOT to use

- Via `spawn_subagent` (use direct API instead)
- For high-precision single-pass analysis where ornith's depth is needed
- For tasks requiring Windows file attribute analysis

### The direct API workaround

The `spawn_subagent` failure means DiffusionGemma can't be used as a
`spawn_subagent(model=...)` target. Instead, use the Python script:

```python
# P:/.data/wiki/scripts/diffusiongemma_read.py
# Single mode:
python diffusiongemma_read.py --file path/to/file.py
# Enhanced mode (3-perspective fan-out):
python diffusiongemma_read.py --file path/to/file.py --enhanced
# Batch mode (multiple files):
python diffusiongemma_read.py --batch path/to/dir/ --pattern "*.py"
```

This is a **critical routing fact**: DiffusionGemma is a Code lane model but
cannot be dispatched via the normal `/go` spawn recipe. It must be called
via `run_terminal_command` + the Python script, not via `spawn_subagent`.

## Gemini 3.x Flash — the new free multimodal option

Added to picker 2026-07-21. See `gemini-google-api-models-2026-07` for the
full catalog. Key models for lane routing:

| Model | Lane fit | Notes |
|-------|----------|-------|
| `gemini-3.6-flash` | Code lane (multimodal) | Current stable Gemini; fast; free-tier friendly |
| `gemini-3.5-flash-lite` | Code lane (mechanical) | Cheapest/fastest; high-throughput |
| `gemini-3.1-pro-preview` | Reasoning lane (when quota allows) | Free-tier Pro quota often limit=0 |
| `gemini-2.5-flash` | Code lane (fallback) | Proven free-tier fallback |

**Quota caveat:** Pro-class models (`gemini-3.1-pro-preview`, `gemini-2.5-pro`)
have free-tier limit 0 on this host's keys. Use Flash/Lite for default; reserve
Pro for when quota exists.

## The full fleet — model picker (as of 2026-07-21)

| Slug | Lane | Provider | Cost | Context | Notes |
|------|------|----------|------|---------|-------|
| `ccr-ornith` | Code | Local | Free | 65K | Primary; 65K limit; Windows attr issues |
| `nvidia-diffusiongemma-26b` | Code | NVIDIA | Free | 262K | Fallback; use direct API not spawn_subagent |
| `nvidia-nemotron-3-ultra` | Reasoning | NVIDIA | Free | 1M | Primary reasoning; token-hungry thinking trace |
| `nvidia-inkling` | Multimodal | NVIDIA | Free | 1M | Native text+image+audio |
| `gemini-3.6-flash` | Code/multimodal | Google | Free | 1M | New; current stable Flash |
| `gemini-3.5-flash-lite` | Code/mechanical | Google | Free | 1M | Cheapest Gemini |
| `gemini-2.5-flash` | Code/fallback | Google | Free | 1M | Proven free-tier |
| `glm-5-2` | Reasoning | Z.ai | Subscription | 1M | "FAR better at planning"; ration (4300 req/mo) |
| `minimax-m3` | Code/execution | MiniMax | Subscription | 1M | "Good at instructions, weak planning"; 16K req/mo |
| `gemma-4-31b-it` | Code/diversity | Google | Free | 131K | Open Gemma 4 via Gemini API |
| zen/OR free models | Backup/research | OpenCode/OpenRouter | Free | varies | Not default coding path |

## Wave table (from `/go` spawn recipe)

```text
Role       Persona / type          Effort    Lane → model pick
─────────  ──────────────────────  ────────  ──────────────────────────────────
discover   explore + sdlc-discover low–med   Code → ccr-ornith → diffusiongemma → m3
plan       plan + sdlc-plan        high      Reasoning → nemotron → glm-5-2
debug      general + sdlc-debug    high      Reasoning → nemotron → glm-5-2
code       general + sdlc-code     medium    Code → ccr-ornith → diffusiongemma → m3
test       general-purpose         medium    Code → ccr-ornith → m3
critic     read-only + sdlc-critic high      Reasoning → nemotron → glm-5-2
```

## Context fit (dispatch check)

Rated context windows are not fully usable under tool-heavy agents. Rule of
thumb: **effective budget ≈ 40-50% of rated**.

Before dispatch, rough check: `(input + expected_output) × ~2.5` against
that budget.

| Model | Rated | Effective (~40%) | Wrong for |
|-------|-------|-------------------|-----------|
| ccr-ornith | 65K | ~26-32K | Huge dumps, multi-file reviews |
| nvidia-diffusiongemma-26b | 262K | ~105-131K | (rarely the bottleneck) |
| nvidia-nemotron-3-ultra | 1M | ~400-500K | (rarely the bottleneck) |
| gemini-3.6-flash | 1M | ~400-500K | (rarely the bottleneck) |

## Relationship to existing concepts

- **Refines** [[model-picker-as-failover-not-router]] — skills recommend lane
  primaries; the picker handles transport failure.
- **Related** [[compensating-for-weaker-models-ensemble-multi-pass]] — the
  fan-out/multi-pass recipes for closing DiffusionGemma's quality gap.
- **Related** [[gemini-google-api-models-2026-07]] — the Gemini catalog.
- **Related** [[gemini-api-vs-agy-cli]] — Gemini surface decision.

## Sources

- Session 2026-07-21: binary-search test (ornith vs diffusiongemma), T4 blind
  comparison, context-limit failures, spawn_subagent failures, timing measurements
- `~/.grok/config.toml` — verified model entries (46 total)
- `~/.grok/tool-fallbacks.md` — documented failure modes
- `~/.grok/skills/go/SKILL.md` § Spawn recipe — the executable routing logic

## Staleness

Model capabilities change fast. Re-verify:
- ccr-ornith context limit if CCR updates the loaded model
- DiffusionGemma spawn_subagent compatibility if Grok Build updates
- Gemini free-tier quotas quarterly
- Nemotron thinking-trace token consumption if NVIDIA updates the model

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[exemption-logic-as-conflict-signal]]
- [[solo_operator_adr_best_practices]]
- [[handoff-pre-compact-problems]]

