---
title: "Model fleet: provider pools, access tiers, and selection flow"
created: 2026-07-22
source: session-2026-07-21/22
tags: [models, routing, pool, provider, tier, fleet, zen, go, nvidia, gemini, minimax, glm, ccr, openrouter, access-path]
summary: >
  The fleet has 46 model slugs across 8 access paths (CCR local, NVIDIA direct,
  Google Gemini direct, MiniMax direct, GLM direct, OpenCode Zen, OpenRouter go,
  OpenRouter free). Models within a lane are a POOL, not a chain. The selection
  flow is: (1) lane (Reasoning vs Code), (2) provider preference (free first),
  (3) situational fit (context, speed, multimodal, availability). Provider
  diversity IS a feature — different indices fail at different times. The zen/go/
  or pools are underused backup capacity that should be exercised, not ignored.
agent: grok
host: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/model-pool-not-chain
    type: extends
  - target: wiki/concepts/model-selection-from-pool-decision-framework
    type: complement
  - target: wiki/concepts/model-lanes-vs-roles
    type: corrects
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: refines
---

# Model fleet: provider pools and selection flow

## The 8 access paths

| # | Provider | Base URL | Cost | Quota (per 5h) | Models | Context |
|---|----------|----------|------|-------|--------|---------|
| 1 | **CCR local** | localhost:8010 | Free | **Disabled** (operator, 2026-07-23) | ornith-1.0-9b | 65K |
| 2 | **NVIDIA direct** | integrate.api.nvidia.com | Free | No published cap | Nemotron-3-Ultra, DiffusionGemma-26b, Inkling | 262K-1M |
| 3 | **Google Gemini direct** | generativelanguage.googleapis.com | Free tier | Gemma 4: ~625/5h (14,400 RPD); Flash-Lite: ~104/5h (500 RPD); Flash: ~4/5h (20 RPD) | 10 Gemini + Gemma-4-31b | 131K-1M |
| 4 | **MiniMax direct** | api.minimax.io | Subscription (Plus plan) | **4,500 calls/5h** | M3 | 1M |
| 5 | **GLM direct** | api.z.ai | Subscription (Max-Yearly plan) | **1,600 prompts/5h** | GLM-5.2 | 1M |
| 6 | **OpenCode Zen** | opencode.ai/zen/v1 | Free (free + stealth models work) | Unknown — needs probe | big-pickle, deepseek-v4-flash-free, mimo-v2.5-free, north-mini-code-free, nemotron-3-ultra-free | 128K |
| 7 | **OpenRouter** (go-*) | openrouter.ai | **~$0.005/1M tokens — NOT free** | Pay-per-use | kimi-k3, kimi-k2.7-code, mimo-v2.5, mimo-v2.5-pro, deepseek-v4-pro, deepseek-v4-flash, qwen3-7-max, qwen3-7-plus, qwen3-6-plus | 200K |
| 8 | **OpenRouter :free** (or-*) | openrouter.ai :free | **$0/1M tokens — genuinely free** (corrected 2026-07-29) | Rate-limited: 20 RPM, 50 RPD (or 1,000 RPD with $10+ lifetime credits) | nemotron-ultra-free, nemotron-super-free, hy3-free, laguna-m1-free, laguna-s-2-1-free, laguna-xs-2-1-free, ling-3-flash-free | 262K-1M |

> **Corrected (2026-07-29):** OpenRouter `:free` models (`or-*`) are genuinely
> $0 per 1M tokens — both input and output. The previous claim of `~$0.005/1M`
> was incorrect. The `go-*` models (paid variants without `:free`) DO cost money.
> Sources: openrouter.ai/docs/faq, openrouter.ai/docs/api_reference/limits,
> openrouter.ai/pricing. Rate limits: 20 req/min always; 50 req/day without $10
> credits, 1,000 req/day with $10+ lifetime credits.

**Key insight: paths 2-3 and 6 are all FREE and working.** That's 3 free access paths
(CCR local is currently disabled). Subscription (paths 4-5) provides high per-5h quotas
(GLM: 1,600/5h, MiniMax: 4,500/5h). OpenRouter (paths 7-8) is paid backup.

### agy (Antigravity CLI) measured quota (2026-07-23)

agy uses the Google AI Pro/Ultra subscription quota (separate from direct API key).
Quota is **request-based** (API round-trips), not token-based. Measured via 3-run
experiment on account a.hominidae@gmail.com (Gemini Flash + Pro group):

| Pattern | Tool reads | Quota used (5h) | Est. runs/5h |
|---|---|---|---|
| Single merged file | 1 | ~1.6% | ~50 |
| Multi-file (separate reads) | 3-4 | ~15.6% | ~5 |
| Light review (1 small file) | 1-2 | ~1.9% | ~40 |

**Optimization:** always merge target files into a single temp file before
dispatching to agy. Reduces cost 9x (15.6% → 1.6%). Windows command-line
length limit (~32K chars) prevents inlining via `-p` for large files —
use a merged temp file + single tool read instead.

## Lane → pool → provider mapping

### Code lane pool (implementation, discovery, tests, mechanical reads)

**Free tier (prefer first):**

| Model | Provider | Context | Strength | Limitation |
|-------|----------|---------|----------|------------|
| `ccr-ornith` | CCR local | 65K | Deep single-file; no network dependency | Context limit; slow on large reviews (~40s+ per task); latency unmeasured |
| `nvidia-diffusiongemma-26b` | NVIDIA | 262K (verified) | Fast (~600ms-3.7s measured); large ctx; batch reads; 3.8B active params (efficient MoE) | spawn_subagent fails (use direct API); shallower output than ornith; transient 500s (~1 in 8 calls) |
| `gemini-3.6-flash` | Google | 1M | Multimodal; large ctx | 20 RPD (~4/5h) — reserve only |
| `gemini-3.5-flash-lite` | Google | 1M | High-throughput | 500 RPD (~104/5h) |
| `gemini-2.5-flash` | Google | 1M | Proven; responded OK in single probe | 20 RPD (~4/5h) — reserve only |
| `gemma-4-31b-it` | Google | 131K | Open weights via Gemini API | 14,400 RPD (~625/5h) — massive headroom |

**Subscription tier (escalate when free pool exhausted):**

| Model | Provider | Context | Quota (per 5h) | Strength |
|-------|----------|---------|-------|----------|
| `minimax-m3` | MiniMax direct (Plus plan) | 1M | **4,500 calls/5h** | Instruction-following; multimodal; high quota |
| `glm-5-2` | GLM direct (Max-Yearly plan) | 1M | **1,600 prompts/5h** | Strong reasoning; "FAR better at planning" |

**Exception-only (manual picker, NOT default routing):**

| Model | Provider | Cost | When |
|-------|----------|------|------|
| `go-kimi-k2-7-code` | OpenRouter | ~$0.005/1M | Operator manually selects; code-specialized |
| `go-mimo-v2-5` | OpenRouter | ~$0.005/1M | Operator manually selects; verified spawn_subagent OK |
| `go-deepseek-v4-pro` | OpenRouter | ~$0.005/1M | Operator manually selects; strong reasoning |
| `or-*` (7 models) | OpenRouter :free | **$0/1M (free)** | Rate-limited: 20 RPM, 50-1000 RPD. Corrected 2026-07-29 — these are genuinely free. |
| `zen-*` (5 models) | OpenCode Zen | Free | **Working** (corrected 2026-07-23): big-pickle, deepseek-v4-flash-free, mimo-v2.5-free, north-mini-code-free, nemotron-3-ultra-free all function when properly configured |

> **OpenRouter `:free` models ARE free** ($0/1M tokens). The `go-*` paid variants
> cost ~$0.005/1M. Corrected 2026-07-29 — verified via openrouter.ai/docs/faq
> and openrouter.ai/docs/api_reference/limits.

### Reasoning lane pool (plan, architecture, RCA, critic)

**Free tier (prefer first):**

| Model | Provider | Context | Strength | Limitation |
|-------|----------|---------|----------|------------|
| `nvidia-nemotron-3-ultra` | NVIDIA | 1M | Deep reasoning; long ctx | Token-hungry thinking trace |
| `gemini-3.1-pro-preview` | Google | 1M | Pro-tier reasoning | Free-tier quota often limit=0 |
| `zen-nemotron-3-ultra-free` | Zen | 128K | Same model via Zen path | Zen quota; 128K context |
| `or-nemotron-ultra-free` | OR free | 1M | Same model via OR :free | Rate-limited |

**Subscription tier (escalate when free pool exhausted):**

| Model | Provider | Context | Strength |
|-------|----------|---------|----------|
| `glm-5-2` | GLM direct | 1M | "FAR better at planning"; strong reasoning |
| `minimax-m3` | MiniMax direct | 1M | Fallback reasoning (weak at planning, OK at execution) |

### Multimodal capability filter (all 46 models, researched 2026-07-24)

**Multimodal = accepts image input (at minimum).** All multimodal models output
text only — none generate images/audio. OpenRouter and Zen pass through image
input to models that natively support it; the practical question is whether the
underlying model accepts images, not which access path you use.

#### Multimodal models (accept image input)

| Model | Fleet slugs | Modalities | Confidence |
|-------|-------------|------------|------------|
| NVIDIA Inkling (Thinking Machines) | `nvidia-inkling` | Text + image + audio | `[FACT]` — model card, NVIDIA NIM |
| MiniMax M3 | `minimax-m3` | Text + image + video (up to 30 min) | `[FACT]` — MiniMax blog, OR, HuggingFace |
| Gemini 3.6 Flash | `gemini-3.6-flash` | Text + image + video | `[FACT]` — Gemini API docs |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | Text + image + video | `[FACT]` — Gemini family (all variants) |
| Gemini 2.5 Flash | `gemini-2.5-flash` | Text + image + video | `[FACT]` — Gemini API docs |
| Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | Text + image + video + audio | `[FACT]` — Gemini family |
| Kimi K3 (Moonshot) | `go-kimi-k3` | Text + image (natively multimodal) | `[FACT]` — Moonshot homepage |
| Kimi K2.7 Code | `go-kimi-k2-7-code` | Text + image | `[FACT]` — Moonshot platform docs |
| MiMo V2.5 (Xiaomi) | `go-mimo-v2-5`, `zen-mimo-v2.5-free` | Text + image + video + audio (omnimodal) | `[FACT]` — HuggingFace, Xiaomi blog |
| MiMo V2.5-Pro | `go-mimo-v2-5-pro` | Text + image + video + audio (omnimodal) | `[FACT]` — HuggingFace |
| Qwen3.7-Plus (Alibaba) | `go-qwen3-7-plus` | Text + image + video | `[FACT]` — OpenRouter, Alibaba docs |
| Gemma-4-31B-IT (Google) | `gemma-4-31b-it` | Text + image | `[FACT]` — HuggingFace, Google AI docs |
| DiffusionGemma-26B (NVIDIA) | `nvidia-diffusiongemma-26b` | Text + image + video | `[FACT]` — NVIDIA NIM docs (also noted §architecture) |

#### Text-only models

| Model | Fleet slugs | Confidence | Evidence |
|-------|-------------|------------|----------|
| Nemotron-3-Ultra | `nvidia-nemotron-3-ultra`, `zen-nemotron-3-ultra-free`, `or-nemotron-ultra-free` | `[FACT]` text-only | NVIDIA NIM docs: "This text-only, reasoning-capable model" |
| Nemotron-3-Super | `or-nemotron-super-free` | `[INFERENCE]` text-only | Pre-trained on text tokens only; no vision mentioned in any source |
| GLM-5.2 (Zhipu) | `glm-5-2` | `[FACT]` text-only | glm5.app: "GLM 5.2 is text-in, text-out only." Vision = separate GLM-5V-Turbo |
| big-pickle (= GLM-4.6) | `zen-big-pickle` | `[FACT]` text-only | pi.dev: "Input: text"; community-confirmed GLM-4.6 |
| Ornith-1.0-9B (DeepReinforce) | `ccr-ornith` | `[INFERENCE]` text-only | Coding model; one aggregator claims multimodal but unverified |
| Laguna M1 (Poolside) | `or-laguna-m1-free` | `[FACT]` text-only | HuggingFace: "Input: text"; agentic coding model |
| North Mini Code (Cohere) | `zen-north-mini-code-free` | `[INFERENCE]` text-only | 30B MoE coding model; no vision mentioned |
| HY3 (Tencent) | `or-hy3-free` | `[INFERENCE]` text-only | 295B MoE reasoning model; no vision mentioned |
| DeepSeek V4-Flash | `go-deepseek-v4-flash`, `zen-deepseek-v4-flash-free` | `[INFERENCE]` text-only | cloudbase: "V4-Flash does not accept image_url" |

#### Conflicting / ambiguous

| Model | Fleet slug | Status | Detail |
|-------|------------|--------|--------|
| DeepSeek V4-Pro | `go-deepseek-v4-pro` | `[FACT]` text-only | HuggingFace model card: "language models"; API docs no image input. Third-party "vision" claims are OCR wrappers, not native. |
| Qwen3.7-Max | `go-qwen3-7-max` | `[INFERENCE]` text-primary | apidog: "Max keeps a small text-only edge"; "For mixed or vision work, Plus is the only option" |

#### Resolved (updated 2026-07-24)

| Model | Fleet slug | Was | Now | Evidence |
|-------|------------|-----|-----|----------|
| Qwen3.6-Plus | `go-qwen3-6-plus` | `[UNKNOWN]` | `[FACT]` multimodal (T+I+V) | Official Qwen blog: "multimodal capabilities, visual analysis, video reasoning" |
| Mistral Medium 3.5 | `mistral-medium-latest` | `[UNKNOWN]` | `[FACT]` multimodal (T+I) | mistral.ai/models: tagged "Multimodal" explicitly |
| DeepSeek V4-Pro | `go-deepseek-v4-pro` | `[CONFLICTING]` | `[FACT]` text-only | HuggingFace: "language models"; API docs no image input; Reddit confirms no native vision |

#### Research notes

- **Nemotron 3 family:** Only **Nano Omni** is multimodal (text+vision+audio). Ultra and Super are text-only reasoning models. Nano Omni is not in the fleet.
- **GLM family:** GLM-5.2 is text-only. The multimodal variant is **GLM-5V-Turbo** (separate model, not in fleet). GLM-4.6 (big-pickle) is also text-only.
- **DeepSeek V4:** The "Thinking with Visual Primitives" paper describes a research direction, not a shipped capability. Vision support is provider-dependent and unconfirmed natively.
- **OpenRouter pass-through:** OpenRouter has a unified image-input API that works with any model that natively supports images. The go-*/or-* prefixes don't strip multimodal capability — if the model accepts images, OpenRouter passes them through.

### Synthesis / parent (judgment, cross-referencing, final output)

| Model | When |
|-------|------|
| Parent Grok (inherited) | Default — the orchestrator's own model |
| `glm-5-2` | When parent is unavailable or a different reasoning family is wanted |

## Selection flow (the decision tree)

```
1. Which LANE? → Reasoning or Code (or multimodal filter)
2. Which TIER? → Free first; subscription only when free pool exhausted
3. Which PROVIDER? → Pick by situational fit within the tier:
   - Context fit: does input fit effective budget (~40-50% of rated)?
   - Availability: is the provider responding?
   - Speed: is the operator waiting? (interactive vs batch)
   - Special needs: multimodal? batch? code-specialized?
   - Provider diversity: if one provider is down, use a DIFFERENT provider, not the same provider's next model
4. Pool member fails? → Pick ANOTHER pool member (same tier, different provider if possible)
5. Free pool exhausted? → Escalate to subscription tier
6. Subscription exhausted? → Parent model (last resort)
```

**Critical: provider diversity IS a feature.** When NVIDIA is down, switch to
Google — not to another NVIDIA model.

## Delegation gate: when to dispatch vs keep in parent

Before selecting from the pool, decide **whether to delegate at all.** The pool
exists for work that benefits from dispatching; not everything does.

### Hard gate — delegate ONLY when ALL are true

| # | Condition | If false |
|---|-----------|----------|
| 1 | Task is **mechanical** (read, extract, run command, apply patch, compare) not judgment-heavy | Keep in parent |
| 2 | Result is **verifiable** from files, command output, or artifacts | Keep in parent |
| 3 | Scope **fits one bounded packet** with disjoint files or read-only target | Keep in parent or split first |
| 4 | Parent can **name the exact success criteria** before starting | Narrow the task first |
| 5 | Likely **savings outweigh** packet-writing and verification overhead | Do it locally |

If any one is missing, keep the work in the parent thread.

### Keep with the parent (never delegate)

- Task framing and decomposition
- Model selection and cost/risk tradeoffs
- Experiment design and benchmark interpretation
- Security, destructive, external, or user-visible decisions
- Final synthesis and recommendations
- Integration, commits, PRs, and handoff docs
- Ambiguous root-cause diagnosis before the question is narrowed
- Broad architecture choices or final conclusions

### Good delegation targets (send to the pool)

- Read-only code or log searches with exact questions
- Extracting tables, metrics, or file references from existing artifacts
- Running predefined tests or commands and reporting exact output
- Comparing two artifacts against a checklist
- Small patches in one or two files with a complete spec and tests
- Independent review of a focused diff or plan
- Batch file reads for breadth-first scanning

### The cost test

- If a task type repeatedly costs more to delegate than to do directly, stop delegating that class
- If a task is often small enough for one local command, do it locally
- **If the packet is larger than the task, the task is too small for delegation**

### Delegation packet structure (when dispatching to the pool)

Every `spawn_subagent` dispatch should include:

1. **Objective** — one concrete outcome
2. **Context** — only facts needed to avoid rediscovery (include session transcript path + search terms per `/go` H4)
3. **Scope** — cwd, allowed files, forbidden files, edit permission
4. **Do** — numbered tasks
5. **Don't** — explicit forbidden actions
6. **Stop if** — conditions that prevent stale, destructive, or non-discriminating work
7. **Verification** — exact commands, evidence, or checks required
8. **Final packet** — required output fields: commands run, files read/changed, key observations, blockers, uncertainty, git status

### Parent verification (after delegate returns)

- Changed files stayed within scope
- Required commands actually ran
- Outputs match the requested shape
- Tests or diff checks passed when requested
- No skipped stop condition invalidated the result
- The delegate's conclusion matches the artifacts

**If verification cost is high, the task probably should not have been delegated.**

> Source: adapted from `cost-aware-delegation` skill (`P:/.agents/skills/cost-aware-delegation/SKILL.md`), originally Codex-oriented. Principles transfer to our pool model; the local PI worker / LM Studio specifics do not (we use CCR + ccr-ornith, not LM Studio + qwen2.5-coder).

## DiffusionGemma verified data (2026-07-22)

### Live API tests (this session, directly verified)

| Test | Prompt size | Result | Latency |
|------|-------------|--------|---------|
| Basic completion | 22 tokens in, 6 out | OK | **867ms** |
| Code reading task | ~30 tokens in, 64 out | OK (1 transient 500; succeeded on retry) | **3,727ms** |
| Summarization | 319 tokens in, 64 out | OK | **1,806ms** |
| Rapid-fire (5 sequential) | 8 tokens out each | 5/5 OK, 0 failed | **628-1,491ms** (avg ~1,095ms) |

### NVIDIA API rate limit (verified from NVIDIA sources)

- **~40 RPM** (staff-confirmed on NVIDIA Developer Forums)
- **No daily cap** — rate-based, not credit-based
- At 40 RPM sustained = ~57,600/day. Actual fleet (~170/hr x 5 terminals) = ~7% of ceiling

### Model architecture (NVIDIA NIM docs)

- 25.2B total / 3.8B active params (MoE)
- Parallel 256-token block generation via diffusion; 1,100+ tok/s on H100
- Context: 262,144 tokens (confirmed)
- Supports text+image+video; function calling; 35+ languages
- Long-context retrieval weaker (MRCR v2 8-needle 128K = 32.0%)

### What is NOT verified

| Claim | Status |
|-------|--------|
| "42x faster than ccr-ornith" | `[UNVERIFIED]` — other session; no ornith measurement this session |
| Gemini 3.x speed on this host | `[UNMEASURED]` |
| Gemini free-tier daily quota | `[UNMEASURED]` |
| spawn_subagent failure | Documented earlier this session; not re-tested |
| ccr-ornith average latency | `[UNMEASURED]` — 1 data point (956s on large review) |

## Selection strategy

**Key insight from research (Digital Applied 2026, RouteLLM ICLR 2025):** route to
the cheapest capable model per request, not the smartest. Most production traffic
is routine and never needed a frontier model. The savings live in the traffic split
between cheap and expensive — not in which specific cheap model you pick.

### The decision factors (ranked)

| Factor | Question | Weight |
|--------|----------|--------|
| **1. Quality floor** | Can this model do the job at all? | Hard gate — if no, skip |
| **2. Cost tier** | Free vs subscription? | Free first, always |
| **3. Context fit** | Does input fit effective budget (~40-50% of rated)? | Hard gate for large inputs |
| **4. Latency sensitivity** | Is the operator waiting (interactive) or can it run background? | High weight for interactive |
| **5. Task volume** | Single call or batch (50+ calls)? | High weight for batch — burn free quota, not subscription |
| **6. Quality requirement** | Mechanical (extraction, formatting) vs judgment (reasoning, synthesis)? | Mechanical = any free; judgment = best free reasoning model |
| **7. Provider diversity** | Has this provider been failing recently? | Switch providers on failure, not models within same provider |

### When to use free-fast vs free-slow vs subscription-high-quota

| Situation | Pick | Why |
|-----------|------|-----|
| **Interactive, single file, small context** | `ccr-ornith` (local, 65K) | No network dependency; deep single-file analysis. Latency: ~40s+ per task `[MEASURED: slow on reviews]` |
| **Batch breadth reads (20+ files)** | `nvidia-diffusiongemma-26b` via direct API (262K) | Verified: ~600ms-3.7s per call; 5/5 rapid-fire OK; 40 RPM ceiling = 2,400/hour (far above demand). Free. |
| **Large context needed (>65K)** | `nvidia-diffusiongemma-26b` (262K verified) or `gemini-3.6-flash` (1M rated) | Ornith's 65K is too small; switch to larger-context model |
| **Reasoning, planning, architecture** | `nvidia-nemotron-3-ultra` (free, 1M) | Free reasoning model; deep thinking trace |
| **Reasoning, Nemotron quality insufficient** | `glm-5-2` (subscription, 4.3K req/mo) | "FAR better at planning" — ration for when free reasoning misses floor |
| **High-volume mechanical work** | Free pool — NVIDIA has massive headroom (40 RPM = 2,400/hr vs ~170/hr actual) | Save subscription quota |
| **Subscription quota abundant (start of month)** | `minimax-m3` for instruction-following (16K req/mo) | Use quota while fresh; doesn't roll over |
| **All free providers down or rate-limited** | `minimax-m3` or `glm-5-2` (subscription) | Subscription is the escalation tier |
| **Exception: OpenRouter paid needed** | Manual picker selection of go-* | NOT default routing; ~$0.005/1M; operator approves. Note: or-* (`:free`) models are genuinely free ($0/M) — corrected 2026-07-29 |

### The quota arithmetic (corrected with verified data)

| Provider | Rate limit / quota | Source | Daily ceiling (estimated) |
|----------|-------------------|--------|--------------------------|
| **CCR local** | Unlimited | Local process | Unlimited |
| **NVIDIA** | **~40 RPM** (no daily cap) | NVIDIA Developer Forums (staff-confirmed) | ~57,600/day if sustained |
| **Google Gemini** | Per-model free-tier quotas | Google rate-limits page | `[UNMEASURED]` — not scraped |
| **MiniMax** | 16,000 req/month | Operator account | ~530/day |
| **GLM** | 4,300 req/month | Operator account | ~143/day |

**Actual session usage (verified):** 271 model calls in 8 hours = ~34/hour for one terminal.
**At 5 terminals:** ~170/hour = ~1,360/8-hour-day.

**NVIDIA at 40 RPM = 2,400/hour.** Actual load (170/hour across 5 terminals) is **7% of the NVIDIA ceiling.** NVIDIA is NOT the bottleneck for this fleet's usage pattern.

**Subscription is the bottleneck for high-volume reasoning:** GLM at 143/day and MiniMax at 530/day are consumed quickly under heavy multi-terminal use. Free pool (NVIDIA especially) has massive headroom.

### The "subscription with a lot of quota" question

When would you prefer MiniMax M3 (16K req/mo subscription) over a free model?

1. **When the free pool is rate-limited.** If NVIDIA and Google are both returning
   429s, MiniMax with its 16K/month quota is the reliable path.
2. **When instruction-following quality matters more than cost.** M3 is "very good
   at following clear instructions" (operator assessment). For structured output,
   JSON extraction, or precise formatting, M3 may outperform free models.
3. **When multimodal is needed and free multimodal models are unavailable.** Gemini
   Pro quota is often 0; Inkling is NVIDIA-dependent. M3 is always available with
   its subscription quota.
4. **When you're at the start of the month and quota is fresh.** Unused quota
   doesn't roll over. If you have 16K requests available and the task is
   volume-heavy, using M3 now is free opportunity cost later.

**When NOT to prefer subscription:**
- Single-call interactive work (free models are faster to start)
- Mechanical reads (DiffusionGemma measured ~600ms-3.7s/call; ornith latency `[UNMEASURED]`)
- When free models are available and responding (no reason to burn subscription)
- End of month when quota is scarce

These three access paths (paths 6-8) provide **16 models** that are currently
almost never used. They are:

- **Free** (via OpenCode subscription or OR :free tier)
- **Diverse** (different model families: Kimi, DeepSeek, Qwen, MiMo, Nemotron, HY3, Laguna)
- **Independent** (separate infrastructure from NVIDIA, Google, MiniMax, GLM)

**When to use them:**
- When the primary free pool (CCR, NVIDIA, Gemini) is rate-limited or down
- For cross-family diversity in a Fusion/council panel
- For perspective-diverse second opinions
- `go-kimi-k2-7-code` and `go-mimo-v2-5` are verified working via spawn_subagent

**Why they're underused:** no quality calibration data. The models haven't been
tested against the T4-style blind comparison that DiffusionGemma and ornith went
through. This is a gap to close in future sessions.

## Why "pool not chain" matters even more with this fleet

With 46 models, a chain (`A → B → C → D → ... → Z`) is absurd. The chain
notation was always wrong; with the full fleet visible, it's obviously wrong.

The pool model scales: any free pool member that fits the situation works.
Provider diversity provides resilience — when one provider has an outage,
the pool doesn't shrink meaningfully because there are 5 other free providers.

The chain model doesn't scale: if "A" is the top of the chain and A's provider
is down, you're forced to B regardless of whether C, D, or E would be a better
fit. That's the failure mode the chain notation creates.

## What the /go skill should say (corrected pool language)

The wave table should list the POOL, not a chain:

```text
Code pool (free):     {ccr-ornith, diffusiongemma, gemini-3.6-flash, gemini-3.5-flash-lite,
                       gemini-2.5-flash, gemma-4-31b, zen-north-mini-code-free,
                       go-kimi-k2-7-code, go-mimo-v2-5, or-laguna-m1-free}
Code escalation:      minimax-m3 (subscription, when free pool exhausted)

Reasoning pool (free): {nvidia-nemotron-3-ultra, gemini-3.1-pro-preview (if quota),
                       zen-nemotron-3-ultra-free, or-nemotron-ultra-free}
Reasoning escalation: glm-5-2 (subscription, when free pool exhausted)
```

Selection: pick by **situational fit** (context, speed, availability, provider
diversity), NOT by fixed ordering within the pool.

## What needs exercise (gaps in calibration)

| Model | Provider | Status | Needs |
|-------|----------|--------|-------|
| `go-kimi-k2-7-code` | go | spawn_subagent verified OK | Quality test (T4-style blind comparison) |
| `go-mimo-v2-5` | go | spawn_subagent verified OK | Quality test |
| `go-deepseek-v4-pro` | go | Untested | Quality + spawn_subagent test |
| `go-qwen3-7-max` | go | Untested | Quality + spawn_subagent test |
| `zen-north-mini-code-free` | Zen | Untested | Quality test |
| `zen-big-pickle` | Zen | Untested | Quality test |
| `or-nemotron-ultra-free` | OR free | Untested | Quality test (same model as NVIDIA path?) |
| `gemini-3.6-flash` | Google | Config verified | Quality calibration in coding tasks |

Until these are tested, the pool includes them as "qualified candidates" but
without quality calibration data. Using them is a reasonable bet (they're from
known model families), not a verified choice.

## Relationship to existing concepts

- **Extends** [[model-pool-not-chain]] — adds the full fleet inventory and provider-level pool structure
- **Corrects** [[model-lanes-vs-roles]] — the lane table only named ~5 models; the real pool is 20+
- **Refines** [[model-picker-as-failover-not-router]] — the picker selects from within the pool, choosing provider by fit

## Sources

- `~/.grok/config.toml` — 46 model entries verified directly
- Session 2026-07-21: spawn_subagent verification tests (go-mimo-v2-5 OK, others failed)
- Session 2026-07-22: operator observation that zen/go/or pools are underused backup capacity

## Staleness

Provider availability and quotas change. Re-probe pool members quarterly.
New models added to config.toml should be quality-calibrated before being
trusted as pool members (not just config-verified).

## Auto-related

- [[skill-catalog]]
- [[solo_operator_adr_best_practices]]
- [[exemption-logic-as-conflict-signal]]

