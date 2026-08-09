---
title: "Model role assignment: public benchmarks vs custom benchmarks, and fleet composite ranking"
created: 2026-07-29
source: session-2026-07-29 (public benchmark integration + fleet composite analysis)
tags: [model-selection, public-benchmarks, ifeval, ifbench, tau2, agentic, thought-partner, role-assignment, fleet-ranking]
summary: >
  Decision: use public benchmarks (IFEval, IFBench, Tau2, Agent Planning Benchmark)
  for instruction-following, multi-turn agent, and planning assessment. Use our
  custom benchmark only for infrastructure validation (does the model work through
  our API paths?) and math/code-exec capacity. Composite ranking shows GLM-5.2
  is the correct thought-partner model (Tau2 #1 globally, agentic #21, knowledge
  #9) despite MiniMax M3 having a higher overall BenchLM score and beating GLM-5.2
  on our math benchmark. M3 is the correct bounded-task model (IFBench #1 globally).
  No fleet-available model beats GLM-5.2 for the thought-partner role.
agent: grok
host: grok
cognitive_load: 3
verification: empirically-grounded
sources:
  - "BenchLM instruction-following leaderboard (benchlm.ai, refreshed 2026-07-29)"
  - "PricePerToken benchmark leaderboards (pricepertoken.com, accessed 2026-07-29)"
  - "Fleet benchmark sweeps 2026-07-29: 780 calls, 60 models, 13 deep-reasoning problems"
  - "Tau2 multi-turn agent benchmark (pricepertoken.com/leaderboards/benchmark/tau2)"
relations:
  - target: wiki/concepts/fleet-benchmark-results-2026-07-29.md
    type: extends
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: related
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: related
  - target: wiki/concepts/parameter-aware-benchmark-tier-system.md
    type: companion
---

# Model role assignment: public vs custom benchmarks, fleet composite ranking

## Decision

**Public benchmarks own the capability-assessment axis.** Our custom benchmark
owns the infrastructure-validation axis. Neither substitutes for the other.

| What we want to know | Source | Why |
|---|---|---|
| Can the model follow instructions? | **IFEval / IFBench** (public) | Peer-reviewed, standardized, already scored for our models |
| Can the model plan and decompose? | **Agent Planning Benchmark, Tau2** (public) | Tau2 tests multi-turn agent coherence directly |
| Can the model sustain thought-partner dialogue? | **Tau2** (public) | Multi-turn agent benchmark = best proxy for sustained dialogue |
| Is the model reachable through our API paths? | **Our benchmark** (custom) | Only we can test config.toml, provider endpoints, dispatch |
| Can the model do math through our infrastructure? | **Our benchmark** (custom) | Tests through actual API paths with our config |

**Why not build custom instruction-following tests:**
IFEval has 541 test prompts across 25 constraint types, validated by Google
(arXiv:2311.07911), with scores already published for GLM-5.2, MiniMax M3,
Nemotron Ultra, Qwen3.7, and other fleet models. Any custom test we build would
be smaller, less validated, and less reproducible.

## The key finding: GLM-5.2 vs MiniMax M3 across axes

The operator's lived experience — "GLM-5.2 is a useful thought partner, M3 is
madness contained in an LLM" — is confirmed by every relevant public benchmark.

### Thought-partner axes (where GLM-5.2 dominates)

| Benchmark | What it measures | GLM-5.2 | MiniMax M3 |
|---|---|---|---|
| **Tau2** | Multi-turn agent coherence (airline, retail) | **#1 globally (99.1)** | Not scored |
| **Agentic** (BenchLM) | Autonomous task completion | **#21/129 (84th pct)** | #97/129 (25th pct) |
| **Knowledge** (BenchLM) | Research, analysis, factual Q&A | **#9/55 (85th pct)** | Not measured |
| **Coding** (BenchLM) | Code generation | **#12/130 (91st pct)** | #72/130 (45th pct) |
| **ARC Challenge** | Reasoning from grade-school science | **96.0 (#2-3)** | Not ranked |

### Bounded-task axes (where M3 can win)

| Benchmark | What it measures | GLM-5.2 | MiniMax M3 |
|---|---|---|---|
| **IFBench** | Formatting constraint adherence | Not scored | **#1 globally (82.9)** |
| **Our math benchmark** | Competition math (13 problems) | 12/13 (92%) | 13/13 (100%) |
| **Overall BenchLM** | Weighted all categories | 63.0 (#41) | **68.8 (#18)** |

M3's higher overall score (68.8 vs 63.0) is real but misleading for our use case.
The overall score weights multimodal and categories where M3 has coverage and
GLM-5.2 doesn't. In the categories that matter for thought partnership (agentic,
knowledge, multi-turn), GLM-5.2 is dramatically stronger.

**Conclusion: no fleet-available model beats GLM-5.2 for thought partnership.**
GLM-5.2 is #1 in the world on Tau2 — the most relevant proxy for sustained
multi-turn reasoning. The operator's trust in GLM-5.2 as a thought partner is
empirically grounded.

## Fleet composite ranking by role

### Thought-partner tier (multi-turn reasoning, planning, delegation)

Rank models by: Tau2 > Agentic > Knowledge > IFEval

| Model | Tau2 | Agentic rank | Knowledge rank | IFEval | Verdict |
|---|---|---|---|---|---|
| **GLM-5.2** (`glm-5-2`) | **99.1 (#1 world)** | #21/129 | #9/55 | 92.6% | **Primary thought partner** |
| **Qwen3.7 Max** (`go-qwen3-7-max`) | — | — | — | 94.3% | Potential alternate (higher IFEval, no Tau2 data) |
| **Qwen3.7 Plus** (`go-qwen3-7-plus`) | — | — | — | 94.6% | Potential alternate |
| **Nemotron 3 Ultra** (`nvidia-nemotron-3-ultra`) | — | — | — | — (IFBench 81.4) | Reasoning model, no multi-turn data |
| **MiniMax M3** (`minimax-m3`) | Not scored | #97/129 | Not measured | — (IFBench 82.9) | **Not suitable** — 25th percentile agentic |

### Bounded-task tier (specific role in skill graph composition)

Rank models by: the benchmark relevant to their assigned role.

| Role | Best fleet model | Evidence | Runner-up |
|---|---|---|---|
| **Math computation** | `minimax-m3` | 13/13 our benchmark, 85.7% provider-reported | `glm-5-2` (12/13, MATH 92.5%) |
| **Instruction formatting** | `minimax-m3` | IFBench #1 globally (82.9) | `nvidia-nemotron-3-ultra` (#2, 81.4) |
| **Code generation** | `mistral-medium-latest` | 5/5 HumanEval our benchmark, BenchLM coding #72 | `nim-openai-gpt-oss-20b` (5/5, faster) |
| **Fast free coding** | `or-ling-3-flash-free` | 5/5 code-exec, 13/13 math, $0/M, 2.2s | `zen-deepseek-v4-flash-free` (5/5, $0) |
| **Deep reasoning (free)** | `or-ling-3-flash-free` | 13/13 at 2.2s | `or-arcee-ai-trinity-large-thinking` (13/13 at 4.6s) |
| **Tool calling** | `glm-5-2` | BFCL v3 #1 (GLM family) | `minimax-m3` |
| **Knowledge retrieval** | `glm-5-2` | BenchLM Knowledge #9/55 | Not measured for others |

### Infrastructure tier (our custom benchmark only)

These are verified through our actual API paths. Public benchmarks can't answer
"does this work through config.toml + provider endpoint + dispatch chain?"

| Check | Result | Source |
|---|---|---|
| Spawn_subagent viable? | mistral, minimax, nim-gpt-oss, glm-5-2 = yes; groq = no (TPM) | Our spawn tests |
| Streaming metrics | TTFT/ITL captured for 10 models | Our stream benchmark |
| API reachability | 60 models tested, 718/780 calls OK | Our deep-reasoning sweep |

## Why our math benchmark showed M3 > GLM-5.2 (and why it doesn't matter)

Our 13-problem math benchmark showed M3 at 13/13 and GLM-5.2 at 12/13. This is
real — M3 is a slightly better competition-math solver. But:

1. **Math solving ≠ reasoning quality.** Competition math rewards pattern-matching
   to known problem templates. Thought partnership rewards deliberation, honest
   uncertainty, and contextual reasoning. These are different axes.

2. **GLM-5.2's Tau2 score (99.1, #1 globally) is the more relevant signal.**
   Tau2 tests whether a model can sustain coherent multi-turn agent interactions
   — exactly what a thought partner does. M3 doesn't even have a Tau2 score.

3. **Agentic rank gap is enormous.** GLM-5.2 is #21/129 (84th percentile) on
   agentic benchmarks. M3 is #97/129 (25th percentile). That 60-percentile gap
   directly reflects the operator's experience: "M3 doesn't follow skills or
   instructions well."

4. **Our math benchmark is an infrastructure validation tool**, not a general
   capability assessment. Its correct interpretation: "both models are reachable
   through our API and can solve math at high accuracy." It should not be used
   to rank thought-partner quality.

## Models that might challenge GLM-5.2 (not yet in fleet)

From public leaderboards, these models score higher than GLM-5.2 on multiple axes
but are not available in our current provider pool:

| Model | Why notable | Availability gap |
|---|---|---|
| **GPT-5.6 Sol** | #1 on agentic (91.9%), #1 on TerminalBench | Available via codex CLI only, not in config.toml |
| **Claude Opus 4.8** | #3 on Humanity's Last Exam (45.7%) | Subscription required, not in config.toml |
| **Gemini 3.1 Pro Preview** | #1 on GPQA (94.1%), #1 on LiveCodeBench | API key exists but no config.toml entry |
| **Kimi K3** | #1 on IFEval (92.6%), GPQA #4 (93.5%) | In config as go-kimi-k3 but excluded (operator directive) |
| **Qwen3.5-27B** | IFEval 95% (#2 globally) | Not in fleet; open weight, could add via NIM |

Of these, **Gemini 3.1 Pro Preview** is the most actionable on paper — API key
exists, just needs a config.toml entry. **GPT-5.6 Sol** is viable via codex CLI
(verified passing both coding and reasoning in this session).

**Operator directive (2026-07-29):** Do NOT prioritize adding Gemini 3.1 Pro to
config.toml. Current Gemini usage is too low to justify the integration effort.
Record for future reference only — revisit if Gemini fleet usage increases or if
GLM-5.2 quality degrades.

## Falsifier

These rankings become stale when:
- BenchLM/PricePerToken update their leaderboards (daily)
- Provider models are updated or replaced
- New benchmarks emerge that better measure thought-partner quality
- Our fleet config changes (models added/removed)

Re-verify by checking benchlm.ai/models/<model> quarterly and re-running the
infrastructure benchmark when config.toml changes. The public benchmark data
should be re-fetched from source URLs, not trusted from this page.

See [[fleet-benchmark-results-2026-07-29]] for the raw sweep data.
See [[coding-model-pool-tier-1-tier-2]] for the coding pool contract.
See [[model-fleet-provider-pools]] for the full fleet inventory.
See [[parameter-aware-benchmark-tier-system]] for the benchmark infrastructure.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."

## Update: dual basis for model selection (session 20260730)

The original framing above presents task-fit as validated primarily by public
benchmarks. This is incomplete. **Task-fit is validated by direct operator
experience** — the most relevant evidence we have:

> "M3 drives me nuts as an orchestrator. GLM-5.2 is the right thought partner."

This is stronger than any benchmark score because it measures exactly what
matters: sustained multi-turn orchestration quality in real workspace
conditions. The benchmark data (Tau2 #1, agentic 84th pct) *confirms* the
lived experience; it doesn't *replace* it.

### The dual basis for using different models

Model selection in our fleet rests on two independent, composable reasons:

| Basis | Evidence | What it justifies |
|-------|----------|-------------------|
| **Task-fit** | Operator experience + public benchmarks | GLM-5.2 orchestrates; M3 formats; DeepSeek codes — different models are genuinely better at different roles |
| **Quota isolation** | Mechanical: GLM has ~1600 calls/5h, every tool call burns one | Delegate execution work to preserve orchestrator quota for orchestration |

Both apply. Task-fit says "use the right model." Quota isolation says "don't
burn GLM quota on work any model can do." They compose: delegate to a model
that is both task-appropriate AND on a separate quota pool.

### What tasks the orchestrator should keep vs delegate

**Keep on GLM-5.2 (orchestration + reasoning):** planning, decomposition,
framing decisions, composing subagent results, writing durable artifacts
(wiki, handoffs), any task needing conversation history.

**Delegate to subagents (quota isolation + parallelism):** research/search
(already delegated via /www, /web), code implementation, mechanical bulk work,
parallel read-only exploration.

**The gap:** the parent often does mechanical work inline (formatting, running
ruff, fixing test assertions) that could be delegated. Each inline tool call
burns GLM quota. Delegating these to a free-tier subagent preserves GLM quota
for the work only it can do well.

### pick_model.py and pool contracts — corrected framing

The picker (`pick_model.py`) is an **availability checker**, not a selector.
Pool contracts are the source of truth for task-fit judgment (they contain
benchmark data, known issues, quota recovery speed, fallback rationale).
`pick_model.py` filters the pool by current availability (quota cache + serde
compatibility) and returns a ready-to-use slug. The skills were reverted from
"run pick_model.py" back to "read the pool contract" because the pool contains
richer context for making a judgment call than a greedy first-available
algorithm. See [[execution-path-based-model-routing-grok-build]] for the full architecture.

## What this means for our workspace

- GLM-5.2 remains the orchestrator (validated by both benchmarks and lived
  experience). Do not switch to M3 for orchestration regardless of overall
  benchmark scores.
- Delegation discipline matters: inline mechanical work on GLM burns quota
  that could be spent on orchestration. This is the primary lever for quota
  conservation.
- Pool contracts remain the source of truth for model selection judgment.
  `pick_model.py` is a tool for checking availability, not for making decisions.
- The spawn gate (PreToolUse hook) and UserPromptSubmit injector remain the
  mechanical enforcement layers — they catch quota-exhausted and serde-broken
  models regardless of what the skills say.

## Receipts

- Operator direct experience: M3 as orchestrator = "drives me nuts" (session 20260730, operator statement)
- GLM-5.2 quota: ~1600 calls per 5h window (observed in session 20260730 via `/model-quota` dashboard)
- Pool contract files: `P:/.data/wiki/capabilities/coding-model-pool.md`, `reasoning-model-pool.md`, `mechanical-model-pool.md`, `critic-model-pool.md`
- pick_model.py: `~/.grok/skills/model-quota/scripts/pick_model.py` — returns first available tier-1 model filtered by quota cache + serde set (greedy, no task-fit judgment)
- Spawn gate: `~/.grok/hooks/PreToolUse_spawn_model_gate.py` — reads serde set from registry, reads quota cache, blocks exhausted providers
- Skill wiring reverted: commit `72ddee6` — skills restored to pool-contract-read instructions after pick_model.py wiring proved to remove judgment from the process
