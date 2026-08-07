---
title: "Model pool selection policy: speed + quota over free, except diversity"
created: 2026-07-24
source: session-2026-07-24 (operator refinement during /check model-tiering discussion)
tags: [models, routing, pool, policy, speed, quota, diversity, review, selection]
summary: >
  Three-rule policy for selecting a model from the fleet pool, overriding the
  earlier "free first, always" default. (1) Speed + adequate quota wins over
  free-but-slow. (2) Free is a tiebreaker when speed/quota are comparable, not
  a gate. (3) Model diversity overrides both when the task is adversarial
  review, critique, or cross-checking. Operator decision: M3 is preferred over
  an equivalent free model when M3 is faster with high quota.
agent: grok
host: grok
cognitive_load: 2
verification: operator-stated-preference
relations:
  - target: wiki/concepts/model-fleet-provider-pools
    type: corrects
  - target: wiki/concepts/model-pool-not-chain
    type: extends
  - target: wiki/concepts/model-selection-from-pool-decision-framework
    type: refines
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: complements
---

# Model pool selection policy: speed + quota over free, except diversity

## HARD CONSTRAINT: no paid models from OpenRouter or OpenCode/Zen

**Operator directive (2026-08-07, standing):** NEVER use paid models from
OpenRouter or OpenCode/Zen. Only free, $0, or stealth models from those
providers are allowed.

- **OpenRouter:** only `:free` suffix models (e.g., `nvidia/nemotron-3-nano-30b-a3b:free`).
  All non-`:free` models (e.g., `anthropic/claude-sonnet-4`, `openai/gpt-4o`)
  are **forbidden** — they cost real money per call.
- **OpenCode/Zen:** only models ending in `-free` or explicitly confirmed free.
  Models returning `CreditsError` at inference are paid — do not use them.

This is enforced mechanically by `discover.py`'s `is_model_free()` function,
which filters auto-apply candidates per-model (not per-provider). There is no
`--include-paid` override flag — it was removed because it was a footgun.

## What this corrects

[[model-fleet-provider-pools]] section "Selection flow" step 2 states "Which TIER?
then Free first; subscription only when free pool exhausted." That rule optimizes
for cost-savings on subscription quota. It is **wrong as a default** when a
subscription model is both faster and has quota headroom that dwarfs fleet
demand. Free-first applies *within comparable speed tiers*, not as a gate that
overrides speed.

## The three rules (priority order)

### Rule 1 -- Speed + adequate quota wins

Default to the fastest model with adequate quota for the task.

A subscription model that is faster and has high quota beats a free model
that is slower, even when the free model could do the work. The operator's
time (waiting) is the scarcest resource; subscription quota is abundant.

**Dispatch-path overhead (verified 2026-08-03):** speed is NOT just a model
property — it varies by dispatch path. The same model can be 3-10x slower via
`spawn_subagent` than via PI due to agent context overhead (~35K tokens of
AGENTS.md + skills + system prompt). Always check `dispatch_latency` in
`fleet-models.json` for the measured per-path latency, not just the model's
raw HTTP speed. A model that benchmarks at 2s on HTTP can take 30-70s on spawn
because the agent context triggers deeper reasoning. When `pick_model.py`
recommends `dispatch_path: PI`, use PI — the recommendation is based on measured
data, not assumption.

**Worked example:** `minimax-m3` (subscription, 4,500 calls/5h, fast
instruction-following) is preferred over `gemma-4-31b-it` (free, 625/5h,
unmeasured latency) for `/check` verifiers. M3 could absorb the entire fleet's
verifier traffic (900/hr ceiling vs ~170/hr demand) and still have 5x headroom.

### Rule 2 -- Free is a tiebreaker

When two models are comparable on speed and quota, prefer the free one.

Free-first is the tiebreaker, not the gate. It applies *within* a speed tier,
not across tiers where a paid model is meaningfully faster.

### Rule 3 -- Model diversity overrides both

When the task is adversarial review, critique, or cross-checking, deliberately
select models from **different families** (different providers, different
training corpora). Rules 1-2 do not apply here.

**Why:** different model families catch different blind spots. A faster or
cheaper model from the same family is not a substitute for a slower model from
a different family when the goal is independent perspective. This is the entire
basis of `/review`, `/risk`, `/tp` critique lenses, and cross-model second
opinions (`/agy`, `/codex`, `/mmx`).

**When this fires:** red-team specialists, /tp fresh-lens critique, cross-model
review panels, any "does another model see a problem this one missed?" question.

**When it does NOT fire:** implementation, verification (rule 1 governs),
mechanical extraction, single-model synthesis, routine code generation.

## Corrected quota model (operator-verified 2026-07-24)

The initial draft assumed subscription quota was a binding constraint requiring
5h-window thresholds. The operator corrected this:

| Provider | Actual quota model | Conservation needed? |
|---|---|---|
| **MiniMax M3** | **Weekly-unlimited** (operator: "we can drain it dry") | Only at <10% — reserve for tasks that benefit most from M3 (see below) |
| **DeepSeek V4 Flash** (Zen path) | **150K requests/month** | Very generous (~5,000/day). **Shared pool** with expensive Zen models — using big-pickle / north-mini-code drains the same quota. Prefer DeepSeek/MiMo within this pool. |
| **MiMo V2.5** (Zen path) | **150K requests/month** (same shared pool as DeepSeek) | Same as above. |
| **GLM-5.2** | 1,600 prompts/5h | Monitor; reserve for reasoning. |

**Operator directive (2026-07-24):** "DeepSeek and MiMo should be used for any
mechanical tasks." This makes DeepSeek/MiMo the **mechanical default**, not M3.
M3's role shifts to the domains where instruction-following quality matters.

## Revised task-domain pools (operator-corrected + tool-use + firewall layer)

The domain table now includes three additional dimensions the /tp critique
identified as missing:

- **Domains** — which task types this model is suited for
- **Tool use** — can the model use tools (read files, run commands, iterate)?
  Completion-only models must be called via script, not `spawn_subagent`.
- **Firewall layer** — where in the 3-layer context firewall this model sits
  (see [[context-firewall-architecture]] for the full pattern)

### Model capability matrix

| Model | Provider | Cost | Context | Tool use | Firewall layer | Best domains | Latency (mechanical) |
|---|---|---|---|---|---|---|---|
| `zen-deepseek-v4-flash-free` | Zen | Free (150K/mo shared) | 128K | Yes | Layer 2 (agent) | mechanical, code-reading, code-gen | **2900ms** |
| `zen-mimo-v2.5-free` | Zen | Free (shared pool) | 128K | Yes | Layer 2 (agent) | mechanical, code-reading | 4493ms |
| `minimax-m3` | MiniMax | Sub (weekly-unlimited) | 1M | Yes | Layer 2 (agent) | code-gen, multimodal, structured-output | 4056ms |
| `glm-5-2` | GLM | Sub (1,600/5h) | 1M | Yes | Layer 2 (agent) | reasoning, planning | 6744ms |
| `gemma-4-31b-it` | Google | Free (625/5h) | 131K | Yes | Layer 1 or 2 | mechanical, multimodal | 5094ms |
| `nvidia-nemotron-3-ultra` | NVIDIA | Free (40 RPM) | 1M | Yes | Layer 2 (agent) | reasoning, adversarial | `[UNMEASURED]` |
| `nvidia-diffusiongemma-26b` | NVIDIA | Free (40 RPM) | 262K | **No** (script only) | **Layer 1 (extraction)** | batch-read, extraction | ~600ms-3.7s |
| `gemini-3.5-flash-lite` | Google | Free (500 RPD) | 1M | Yes | Layer 1 or 2 | mechanical, multimodal | `[UNMEASURED]` |
| `nvidia-inkling` | NVIDIA | Free | 1M | Yes | Layer 2 | multimodal (audio) | `[UNMEASURED]` |
| `ccr-ornith` | CCR local | Free | 65K | Yes | Layer 2 (agent) | deep-single-file | `[SLOW: ~956s]` |
| Parent Grok | inherited | -- | -- | Yes | Layer 3 (orchestrator) | synthesis, decisions | -- |

### Domain → default model routing (rules applied)

| Domain | Default | Why | Fallback | Layer |
|---|---|---|---|---|
| Mechanical / extractive | `zen-deepseek-v4-flash-free` | Fastest (2900ms), free, code-capable | `minimax-m3` | Layer 2 |
| Code reading + verification | `zen-deepseek-v4-flash-free` | Code-specialized, adequate for "is this stubbed?" | `minimax-m3` | Layer 2 |
| Code generation | `minimax-m3` | Instruction-following + speed. `[INFERENCE: uncalibrated for code quality]` | `zen-deepseek-v4-flash-free` | Layer 2 |
| Reasoning / planning | `glm-5-2` | "FAR better at planning" (operator assessment) | `nvidia-nemotron-3-ultra` (free) | Layer 2 |
| Adversarial / critique | Parent Grok + diverse specialists | **Diversity override (rule 3)** — mix families | -- | Layer 3 + Layer 2 |
| Multimodal (image/video) | `minimax-m3` | M3 is multimodal; most free code models are text-only | Gemini Flash-Lite / Inkling | Layer 2 |
| **Bulk extraction / batch reads** | `nvidia-diffusiongemma-26b` | Fastest (600ms-3.7s), free, 262K ctx, batch-capable | `gemma-4-31b-it` / `gemini-3.5-flash-lite` | **Layer 1** |

### The Extraction pool (Layer 1 — script-called, completion-only)

Separate from the agent pool. These models are called via **Python scripts**
(not `spawn_subagent`). The script reads files, constructs the prompt, calls
the API, parses the response, returns JSON. The orchestrator never sees the
raw file content — only the extracted facts. See
[[context-firewall-architecture]] for the full pattern.

| Member | Provider | Context | Speed | Role |
|---|---|---|---|---|
| `nvidia-diffusiongemma-26b` | NVIDIA | 262K | ~600ms-3.7s | Primary — fastest, batch-capable, free |
| `gemma-4-31b-it` | Google | 131K | 5094ms | Fallback 1 — if NVIDIA is down/429 |
| `gemini-3.5-flash-lite` | Google | 1M | `[UNMEASURED]` | Fallback 2 — large context needs |
| `nvidia-nemotron-3-ultra` | NVIDIA | 1M | `[UNMEASURED]` | Fallback 3 — reasoning-quality extraction (token-hungry) |

**Defining property:** you pass everything in the prompt and get one response.
No tool use, no iteration, no file access by the model. The script IS the
firewall — it handles file reading + API call + response formatting.

**Existing implementation:** `P:/.agents/scripts/models/dgemma_read.py`
(modes: single, `--enhanced` 3-perspective merge, `--batch` multiple files).

### What tasks benefit most from M3 (when quota drops below 10%)

The operator asked specifically what to reserve M3 for. Based on M3's profile
(strong instruction-following, multimodal, fast, reliable availability):

1. **Multimodal tasks** — M3 accepts image/video input. Most free code models
   (DeepSeek, GLM, ornith) are text-only. If a task needs vision, M3 is the
   reliable path (Gemini quota is too low for routine use).
2. **Structured output precision** — JSON extraction, exact format compliance,
   tabular data generation where instruction-following quality directly affects
   correctness. DeepSeek can do this but M3 is more reliable on edge cases.
3. **Speed-critical interactive work** — when the operator is actively watching
   and latency matters. M3 is fast and always available (no rate-limit risk).
4. **Code generation that needs judgment** — implementation waves where the
   model must make design decisions, not just follow a spec. DeepSeek is strong
   on mechanical code; M3's instruction-following helps on ambiguous specs.

**What M3 should NOT be reserved for** (DeepSeek/MiMo are adequate):
- File reading and grep-equivalent verification
- Running pytest and reporting results
- Breadth scans across many files
- Mechanical code generation with a complete spec

## The quota arithmetic that makes this safe

At ~170 model calls/hour across 5 terminals:

| Pool | Ceiling | Daily capacity | Fleet demand share |
|---|---|---|---|
| DeepSeek/MiMo (Zen) | 150K/month | ~5,000/day | 3.4x total fleet demand |
| MiniMax M3 | Weekly-unlimited | Unlimited | Unlimited |
| GLM-5.2 | 1,600/5h | ~7,680/day | 45x single-terminal demand |

DeepSeek/MiMo at 5,000/day covers the mechanical workload (~3,400/day estimated)
with headroom. M3 is effectively unlimited. **Quota is not a constraint for the
default-pool use case.** The constraint is choosing the right model per task.

## Dynamic quota thresholds (simplified — operator-corrected 2026-07-24)

The initial draft had a 4-tier threshold model (>50%, 25-50%, 10-25%, <10%).
With the corrected quota understanding (M3 weekly-unlimited, DeepSeek/MiMo
150K/month), this simplifies:

| Provider | When to conserve | What to do |
|---|---|---|
| **MiniMax M3** | Only if weekly quota drops below 10% | Reserve for multimodal, structured-output precision, speed-critical interactive work (see "What tasks benefit most from M3" above) |
| **DeepSeek/MiMo** (Zen) | If shared Zen pool drops below 20% (150K/mo shared with expensive models) | Avoid big-pickle / north-mini-code; DeepSeek/MiMo only |
| **GLM-5.2** | If 5h quota drops below 25% | Escalate to free reasoning pool (Nemotron) |

The operator's position on M3 is explicit: "I don't care about usage until it's
under 10%." For DeepSeek/MiMo, the constraint is the **shared pool** — expensive
Zen models drain the same 150K/month. Prefer DeepSeek/MiMo within the Zen pool;
avoid big-pickle/north-mini-code unless their specific capability is needed.

### Open question: pool-use priority weighting

Not all pool uses have equal priority. A first pass at priority tiers:

| Priority | Example tasks | Quota-scarce behavior |
|---|---|---|
| **Critical** | Live implementation the operator is watching; blocking fix | Gets subscription quota even in conservation mode |
| **Standard** | Routine verifiers, code generation waves, planning | Subject to tier-shift rules above |
| **Background** | Batch breadth scans, speculative research, calibration trials | First to lose subscription quota; always uses free pool |

**Unresolved:** whether background tasks should *ever* use subscription quota,
or whether the free pool is always correct for them. Operator question: is
there a case where a background task needs M3/GLM speed? (Likely no -- if it's
background, latency tolerance is high.)

## First measured latency data (benchmark run 2026-07-24)

The `/model-benchmark` skill (built this session) ran a mechanical-tier prompt
("list even numbers 1-20") across 5 key models. Results:

| Model | Provider | Latency | Cost tier | Notes |
|---|---|---|---|---|
| `zen-deepseek-v4-flash-free` | OpenCode/Zen | **2900ms** | Free | Fastest; 150K/mo shared pool |
| `minimax-m3` | MiniMax | 4056ms | Sub (weekly-unlimited) | 2nd; verbose output (think trace) |
| `zen-mimo-v2-5-free` | OpenCode/Zen | 4493ms | Free | 3rd; same shared pool as DeepSeek |
| `gemma-4-31b-it` | Google | 5094ms | Free | 4th; 625/5h quota |
| `glm-5-2` | GLM | 6744ms | Sub (1,600/5h) | Slowest; most verbose (202 output tokens) |

**Key finding:** DeepSeek V4 Flash (free) is **1.4x faster than M3 (paid)** on
mechanical tasks. This partially validates the operator's directive ("DeepSeek
and MiMo should be used for any mechanical tasks") and corrects the initial
draft which had M3 as the mechanical default. DiffusionGemma (not in this run,
but previously measured at 600ms-3.7s) is likely faster still.

**Token verbosity matters:** GLM-5.2 generated 202 output tokens for a trivial
prompt vs DeepSeek's 68. M3 generated a think trace (95 tokens) before the
answer. For mechanical work where output is consumed programmatically, verbose
models add downstream processing cost without value.

Full benchmark + telemetry tooling: `/model-benchmark` skill at
`~/.grok/skills/model-benchmark/`. Run periodically for temporal pattern data.

## Corrections from /tp critique and /www research (integrated 2026-07-24)

A /tp critique and /www research pass on this policy produced 9 actionable
corrections. They are tracked here rather than silently rewritten into the
policy body, so the decision trail is visible.

### Correction 1: Quality floor must precede speed (Rule 0)

The original inventory (`[[model-fleet-provider-pools]]`) listed "Quality floor"
as Factor #1 with "Hard gate -- if no, skip." This policy dropped it. A faster
model that gives wrong answers wastes operator time, not saves it.

**Correction:** add Rule 0 before Rule 1: "The model must clear the quality
floor for the task. If it cannot do the job reliably, speed and cost are
irrelevant." This is a hard gate, not a tiebreaker.

### Correction 2: Mechanical default should be DeepSeek, not M3

The initial draft (before operator correction) had M3 as the mechanical default.
The operator corrected to DeepSeek/MiMo. The benchmark confirms: DeepSeek
(2900ms, free) beats M3 (4056ms, paid) on mechanical latency. The corrected
domain table already reflects this.

### Correction 3: Context window must be a selection factor

The policy drops context-fit entirely. With ccr-ornith at 65K and most models
at 128K-1M, a 90K input rules out ornith. Add as a pre-check: if input exceeds
~80% of rated context, route by context first, speed second.

### Correction 4: Multimodal needs a domain row

The inventory documents 13+ multimodal models. The policy has zero mention.
Add: "Multimodal (image/video input) -> Inkling (free) / Gemini 3.5 Flash-Lite
(free, 500 RPD) / M3 (paid, reliable) -- pick by quota and availability."

### Correction 5: Code generation default needs quality calibration

M3 as code-generation default is `[INFERENCE]`, not `[FACT]`. The inventory says
M3 is "instruction-following" -- that's formatting precision, not code quality.
Code-specialized models (DeepSeek V4 Flash, Kimi K2.7 Code) should be considered
before M3 for code generation until quality calibration exists.

### Correction 6: Diversity applies to provider resilience too

Rule 3 fires only for "adversarial review." But the inventory says "provider
diversity IS a feature -- when NVIDIA is down, switch to Google." That's
resilience, not adversarial. Expand Rule 3: diversity also fires for provider
resilience (provider brownout/429 -> switch providers, not just switch models
within the same provider).

### Correction 7: Quota thresholds need per-provider denominators

The initial 4-tier model (>50%, 25-50%, 10-25%, <10%) applied the same buckets
to 5h rate caps, monthly totals, and weekly aggregates. Different time horizons
need different threshold models. The simplified table above (operator-corrected)
addresses this partially but may need further refinement.

### Correction 8: Speed-primary is an inversion of industry default

The /www research found that the dominant academic framing is **cost-quality**
(RouteLLM, FrugalGPT, OmniRouter), not speed. Our speed-primary policy is
**unusual but defensible** for a single-operator fleet where subscription quota
is abundant and operator wait time is the binding constraint. This should be
noted as a deliberate inversion, not an oversight.

Key external references (from /www research):
- **RouteLLM** (ICLR 2025): 85% cost reduction at 95% GPT-4 quality
- **llm-d** (Google, production): 43% P50 latency improvement via predicted-latency scheduling
- **FrugalGPT** (2023): cascade pattern (try cheap, score, escalate)
- **OmniRouter** (KDD 2025): constrained optimization, closest academic analogue to our quota thresholds
- **Thompson sampling** (LLM Bandit, 2025): structural answer to "no live telemetry yet" -- online learning replaces manual tier thresholds
- **LiteLLM** (open-source gateway): implements cost/latency/rate-limit-aware routing

### Correction 9: "Model pool" terminology is our coinage

No academic paper uses "model pool" as a defined term. The closest concepts are
"router" (academic), "cascade" (FrugalGPT), "gateway" (production). Our
`[[model-pool-not-chain]]` distinction is directionally correct but novel.

## What is not yet measured (remaining gaps)

The benchmark filled the latency gap for 5 models on the mechanical tier. Still
missing:

1. **Code-reading and reasoning tier latency** -- the benchmark ran mechanical
   only. Need to run all 3 tiers for the full picture (some models may invert
   ranking on reasoning tasks).

2. **Quality calibration.** The T4 blind comparison benchmarked DiffusionGemma
   and ornith only. M3, GLM, DeepSeek, MiMo, gemma-4-31b have no quality data.
   Until calibrated, the domain table's defaults are reasonable bets from known
   families, not verified choices.

3. **Temporal patterns.** The telemetry layer exists (`/model-benchmark`
   `telemetry.py`) but has <1 day of data. Need weeks of accumulation before
   hourly/weekly patterns are detectable.

4. **Cascade vs upfront selection.** External research (FrugalGPT, UCCI) shows
   sequential escalation (try cheap, score, escalate) can outperform upfront
   selection. Our policy does upfront selection. Worth testing whether a cascade
   approach would work for verification tasks (try DeepSeek, if quality unclear
   escalate to M3 or GLM).

## When this policy is wrong (falsifier)

1. **Subscription quota is actually scarce (month-end, heavy multi-terminal use).**
   Then rule 1 burns quota the operator needs for higher-value work, and
   free-first (rule 2 as gate) returns as the correct default. Detect by
   checking `/quota` or the provider dashboard before defaulting to subscription.

2. **The "faster" model is lower quality and the task needs judgment.** Then
   speed is the wrong axis -- quality floor is. This is why reasoning defaults
   to `glm-5-2` (strong reasoning) rather than M3 (instruction-following but
   weak at planning per operator assessment).

3. **Diversity is needed and rule 1 picked the same family as the primary.**
   Then rule 3 overrides, deliberately picking a slower or paid model from a
   different family.

## Relationship to existing concepts

- **Corrects** [[model-fleet-provider-pools]] -- the inventory remains accurate;
  only the "free first, always" default in its selection flow is superseded.
- **Extends** [[model-pool-not-chain]] -- the pool model is unchanged; this
  policy governs *which pool member* to pick, not the pool structure.
- **Refines** [[model-selection-from-pool-decision-framework]] -- adds the
  speed-over-free default and the diversity exception that the earlier
  framework under-specified.
- **Complements** [[compensating-for-weaker-models-ensemble-multi-pass]] --
  that concept is about getting more from cheaper models; this policy is about
  when to stop reaching for the cheaper model at all.

## Source

Operator decision stated during session 2026-07-24, in the context of `/check`
verifiers all defaulting to the parent Grok model: "free is good, high quota is
good, fast response is good. I'd rather pick M3 because it's fast with a high
quota, than an equivalent model that is free but slow" -- refined with "unless we
have a need for model diversity because we need a quality check or review where
a different model viewpoint would help." Further refined: "we need to collect
data on latency over a period of time... there's probably hourly or weekly
patterns that need to be considered" and "when quota starts getting low do we
change our behavior on model pool selection?"

## Auto-related

- [[skill-catalog]] -- skills that dispatch subagents should encode this policy
- [[model-fleet-provider-pools]] -- the inventory this policy operates over
- [[diffusiongemma-direct-api-howto]] -- genuinely-free-and-fast path exception
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
