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

1. **Check quota first.** Run `python ~/.grok/skills/model-quota/scripts/pick_model.py --json --lane mechanical` to get quota-eligible models. This filters out any model whose provider is below the quota floor. The quota-aware picker returns only models that won't be denied by the spawn gate.
2. Check pool health.
3. Select from tier-1 (fastest free models that pass mechanical tier):
   - For speed: nim-openai-gpt-oss-20b
   - For IFBench-constrained formatting: minimax-m3
3. If tier-1 unavailable, fall to tier-2.

## Tier-1 (verified 2026-08-08)
nim-openai-gpt-oss-20b (7.7s, free, spawn OK — fastest remaining tier-1 after ling-3 moved to paid)
minimax-m3 (7.3s, sub, IFBench #1 globally at 82.9%)
  - Use specifically for: formatting, structured output, constraint adherence
  - NOTE: fails on tasks with large output budgets — see tool-fallbacks.md (max_tokens_truncation)

## Broken via spawn_subagent (do NOT dispatch)
mistral-medium-latest — HTTP 422 on every spawn_subagent attempt on this host.
  Root cause: this host's AGENTS.md context injection (~26K tokens) exceeds
  Mistral's input limit. Verified 2026-07-21 and re-confirmed 2026-07-29 (4/4
  /www research subagents failed identically). Works via direct API only.
  See ~/.grok/tool-fallbacks.md.

## Tier-2 (fallback)
nvidia-nemotron-3-super-120b (6.1s, free, 13/13 reasoning)
zen-big-pickle (7.2s, $0, 13/13 reasoning)
or-mistralai-codestral-2508 (4.3s, $0/M, 13/13 reasoning but 2 wrong on harder problems)

## Excluded
or-ling-3-flash-free: now paid-only as of 2026-08-08. Returns 404 "This model
  is unavailable for free" on spawn_subagent. Was the fastest fleet model
  (2.2s) but the free tier was removed by the provider. Removed from Tier-1.
  (Receipt: session 019fe25d /www run — 4/4 first-batch subagents failed identically.)
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
