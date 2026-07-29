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
3. If tier-1 unavailable, fall to tier-2.

## Tier-1 (verified 2026-07-29)
### Thought-partner / planning / delegation
glm-5-2 (Tau2 99.1 #1 world, agentic #21/129, knowledge #9/55, spawn OK)
  - Use for: multi-turn dialogue, planning, architecture, delegation packets
  - Quota: 1,600 prompts/5h (GLM Max-Yearly)

### Deep reasoning (free-first)
or-ling-3-flash-free (13/13 deep-reasoning, $0/M, 2.2s, spawn untested)
  - Use for: math, logic, single-shot analysis
or-arcee-ai-trinity-large-thinking (13/13, 4.6s, $0/M)
  - Use for: reasoning-model tasks (has thinking trace)

### Institutional reasoning
nvidia-nemotron-3-ultra (13/13, IFBench #2 globally at 81.4%, 32s avg)
  - Use for: instruction-constrained reasoning, structured analysis

## Tier-2 (fallback when tier-1 exhausted)
go-deepseek-v4-pro (Tau2 96.2, 13/13, IFEval unknown, 7.8s, OpenCode sub)
  - Best available fallback: only 2.9 Tau2 points behind GLM-5.2
deepseek-v4-flash via zen-deepseek-v4-flash-free or go-deepseek-v4-flash
  (Tau2 95.6, 13/13, 7.4s)
  - go- and zen- are the SAME provider (opencode.ai/zen/go/v1), different
    billing path. zen = $0 free tier, go = subscription quota. Use zen first.
go-qwen3-7-max (Tau2 94.7, IFEval 94.3%, 13/13, 19s)
go-qwen3-7-plus (Tau2 93.0, IFEval 94.6%, 13/13, 22s)

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
