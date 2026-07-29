# reasoning-model-pool

## Inputs
- task_type: "planning" | "architecture" | "rca" | "thought-partner" | "delegation-packet"

## Outputs
- model_slug: string (selected model slug from config.toml)
- fallback_chain: string[] (ordered list of fallback models)

## Procedure

1. Check pool health (same mechanism as coding pool).
2. Select from tier-1 based on task subtype:
   - thought-partner / planning / delegation: glm-5-2 (Tau2 #1 globally, agentic #21)
   - deep-reasoning (free): or-ling-3-flash-free (13/13 our benchmark, 2.2s)
   - deep-reasoning (if reasoning tokens needed): nvidia-nemotron-3-ultra (13/13, IFBench #2)
3. If tier-1 unavailable, fall to backup (zen-deepseek-v4-flash-free).

## Tier-1 (verified 2026-07-29)
### Thought-partner / planning / delegation
glm-5-2 (Tau2 99.1 #1 world, coding #12/130 91st pct, agentic #21/129, knowledge #9/55, spawn OK)
  - Use for: multi-turn dialogue, planning, architecture, delegation packets
  - Quota: 1,600 prompts/5h (GLM Max-Yearly). At 1,000s of requests/month,
    this is sustainable: ~288K/month theoretical max, no per-token dollar cap.

### Deep reasoning (free-first)
or-ling-3-flash-free (13/13 deep-reasoning, $0/M, 2.2s, spawn untested)
  - Use for: math, logic, single-shot analysis
or-arcee-ai-trinity-large-thinking (13/13, 4.6s, $0/M)
  - Use for: reasoning-model tasks (has thinking trace)

### Institutional reasoning
nvidia-nemotron-3-ultra (13/13, IFBench #2 globally at 81.4%, 32s avg)
  - Use for: instruction-constrained reasoning, structured analysis

## Backup (when GLM-5-2 unavailable)
zen-deepseek-v4-flash-free (Tau2 95.6, 13/13 reasoning, 7.4s median, $0)
  - Same provider as go-deepseek-v4-flash (opencode.ai/zen/go/v1), but zen
    billing path is $0 free tier vs go subscription quota
  - Coding rank: #84/130 (36th pct) vs GLM-5.2's #12/130 (91st pct) —
    significant quality drop for coding tasks, acceptable for reasoning
  - Quota: no published RPM/TPM limits. $0 during OpenCode free promotion.
  - At 1,000s of requests/month this is sustainable at zero cost.
    If the free promotion ends, switch to go-deepseek-v4-pro ($60/month
    shared Go budget, ~30K requests/month capacity).

## Fallback chain after backup exhausted
1. glm-5-2 (Tau2 99.1, coding #12, subscription, no dollar cap)
2. zen-deepseek-v4-flash-free (Tau2 95.6, coding #84, $0 free)
3. go-deepseek-v4-pro (Tau2 96.2, shares $60/mo Go budget, ~6K req/5hr)
4. go-qwen3-7-max (Tau2 94.7, IFEval 94.3%, shares $60/mo Go budget)

## Excluded
minimax-m3: #97/129 agentic (25th pct). Good at bounded math (13/13) but
  cannot sustain multi-turn reasoning or follow complex instructions.
  NOT a thought partner. Use for bounded tasks only.
groq-*: TPM cap blocks spawn_subagent. Direct-API-only, burst-capable.

## Selection criteria
Thought-partner quality is measured by Tau2 (multi-turn agent coherence)
and agentic benchmark rank — NOT by competition math scores. See
[[model-role-assignment-public-vs-custom-benchmarks]] for the full
justification of why GLM-5.2 beats M3 for this role.

## Quality gate
Re-verify GLM-5.2 Tau2 score quarterly via benchlm.ai/models/glm-5-2.
Re-run `benchmark.py --tier deep-reasoning` monthly for infrastructure validation.

