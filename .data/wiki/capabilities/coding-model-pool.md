# coding-model-pool

## Inputs
- task_type: "code-generation" | "code-review" | "code-exec" | "general-coding"

## Outputs
- model_slug: string (selected model slug from config.toml)
- fallback_chain: string[] (ordered list of fallback models)

## Procedure

1. Select first available model from tier-1 pool:
   - mistral-medium-latest
   - nim-openai-gpt-oss-20b
   - minimax-m3
2. If all tier-1 unavailable, select from tier-2:
   - glm-5-2
   - nvidia-nemotron-3-super-120b
   - zen-deepseek-v4-flash-free
3. Return model_slug + remaining models as fallback_chain

## Tier-1 (verified 2026-07-29, 5-problem HumanEval)
mistral-medium-latest (5/5, 2s, Mistral free)
nim-openai-gpt-oss-20b (4/5, 8s, NVIDIA free)
minimax-m3 (4/5, 6s, MiniMax subscription)

## Tier-2 (fallback when tier-1 exhausted)
glm-5-2 (4/5, 7s, GLM subscription)
nvidia-nemotron-3-super-120b (4/5, 17s, NVIDIA free)
zen-deepseek-v4-flash-free (4/5, 17s, OpenCode free)

## Excluded
Groq models: rate-limited on multi-call sequences
gemma-4-31b-it: 1/5 code-exec pass rate
Models <8B params: insufficient code quality

## Quality gate
Re-run `benchmark.py --tier code-exec --skip-paid` monthly.
Tier-1 model must maintain ≥4/5 pass rate.
