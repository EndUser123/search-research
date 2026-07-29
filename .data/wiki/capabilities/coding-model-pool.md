# coding-model-pool

## Inputs
- task_type: "code-generation" | "code-review" | "code-exec" | "general-coding"

## Outputs
- model_slug: string (selected model slug from config.toml)
- fallback_chain: string[] (ordered list of fallback models)

## Procedure

1. Check pool health: read `P:/.data/wiki/capabilities/coding-model-pool-health.json`.
   Skip any model with `status: "degraded"`. Models with `status: "recovering"`
   are usable but not preferred.
2. Select first available model from tier-1 pool (not degraded):
   - or-ling-3-flash-free
   - mistral-medium-latest
   - nim-openai-gpt-oss-20b
3. If all tier-1 unavailable or degraded, select from tier-2 (not degraded):
   - go-deepseek-v4-flash
   - minimax-m3
   - zen-deepseek-v4-flash-free
   - glm-5-2
4. Return model_slug + remaining models as fallback_chain

## Tier-1 (verified 2026-07-29, 5-problem HumanEval + 13-problem deep-reasoning)
or-ling-3-flash-free (5/5 code-exec, 13/13 reasoning, 2.2s, $0/M, spawn OK)
mistral-medium-latest (5/5 code-exec, 12/13 reasoning, 6.9s, free, spawn OK)
nim-openai-gpt-oss-20b (4/5 code-exec, 13/13 reasoning, 7.7s, free, spawn OK)

## Tier-2 (fallback when tier-1 exhausted)
go-deepseek-v4-flash (5/5 code-exec, 13/13 reasoning, 6.4s, OpenCode sub)
minimax-m3 (4/5 code-exec, 13/13 reasoning, 7.3s, MiniMax sub, spawn OK)
zen-deepseek-v4-flash-free (4/5 code-exec, 13/13 reasoning, 7.4s, Zen free)
glm-5-2 (4/5 code-exec, 12/13 reasoning, 7.9s, GLM sub, spawn OK)

## Excluded
Groq models: TPM cap (6000/8000) blocks spawn_subagent entirely
gemma-4-31b-it: 1/5 code-exec. Strong reasoning but poor code generation
nvidia-nemotron-mini-4b: actual context limit < advertised; 4B too small
nvidia-llama-3-1-8b: 2/5 code-exec. Inconsistent code quality
go-kimi-k2-7-code: OpenCode Go upstream failure (all calls fail)
go-kimi-k3: operator exclusion directive

## Quality gate
Re-run `benchmark.py --tier code-exec --skip-paid` monthly.
Tier-1 model must maintain ≥4/5 pass rate.

## Health monitoring
Run `python pool_health.py --show` to check current pool health.
Health file: `coding-model-pool-health.json` (auto-generated).
Reset a flagged model: `python pool_health.py --reset <slug>`.
A degraded model is automatically skipped at dispatch time until it
recovers (5 consecutive healthy calls).
