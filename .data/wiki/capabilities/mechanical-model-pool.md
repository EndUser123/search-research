---
title: "mechanical-model-pool"
domain: model-pool
version: "1.0"
---
# mechanical-model-pool

## Inputs
- task_type: "extraction" | "formatting" | "bulk-read" | "summarization" | "classification"

## Outputs
- model_slug: string
- fallback_chain: string[]

## Procedure

1. Check pool health.
2. Select from tier-1 (fastest free models that pass mechanical tier):
   - For speed: or-ling-3-flash-free or mistral-medium-latest
   - For IFBench-constrained formatting: minimax-m3
3. If tier-1 unavailable, fall to tier-2.

## Tier-1 (verified 2026-07-29)
or-ling-3-flash-free (2.2s, $0/M, 13/13 reasoning — fastest fleet model)
mistral-medium-latest (6.9s, free, 5/5 code-exec)
minimax-m3 (7.3s, sub, IFBench #1 globally at 82.9%)
  - Use specifically for: formatting, structured output, constraint adherence
nim-openai-gpt-oss-20b (7.7s, free, spawn OK)

## Tier-2 (fallback)
nvidia-nemotron-3-super-120b (6.1s, free, 13/13 reasoning)
zen-big-pickle (7.2s, $0, 13/13 reasoning)
or-mistralai-codestral-2508 (4.3s, $0/M, 13/13 reasoning but 2 wrong on harder problems)

## Excluded
Groq models: TPM cap. Usable for single-shot only, not for bulk operations.
nvidia-nemotron-nano-vl-8b: 0.38 score on deep-reasoning (5/13 wrong)
or-mistralai-mistral-small-3-1-24b-instruct: 0.00 (all 13 wrong)
or-morph-morph-v3-*: reject multi-turn API (no system message support)
or-arcee-ai-virtuoso-large: provider endpoint down

## Selection criteria
Mechanical tasks prioritize speed and cost. Quality floor is lower than
coding or reasoning pools — the task is extraction/formatting, not
generation or analysis. Use the fastest free model that is reachable.
For formatting tasks with strict constraints (JSON schema, word count,
content rules), use minimax-m3 (IFBench #1 globally).

## Quality gate
Re-run `benchmark.py --tier mechanical` monthly.
Tier-1 models must maintain reachability (no provider-side 410/404).
