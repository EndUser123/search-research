---
title: "reasoning-model-pool"
domain: model-pool
version: "1.0"
---
# reasoning-model-pool

## Inputs
- task_type: "planning" | "architecture" | "rca" | "thought-partner" | "delegation-packet"

## Outputs
- model_slug: string (selected model slug from config.toml)
- fallback_chain: string[] (ordered list of fallback models)

## Procedure

**Step 0 (mandatory):** Check quota first. Run `python ~/.grok/skills/model-quota/scripts/pick_model.py --json --lane reasoning` to get quota-eligible models before reading tier lists. GLM-5.2 has ~1600 calls/5h; when Z.ai drops below threshold, the picker returns the backup.

### /tp (critical-friend critique) — diversity-first

The entire point of /tp is a DIFFERENT lens. GLM-5.2 is the parent; spawning
a fresh GLM-5.2 subagent is same-model-lens (fresh context, same blind spots).
Selection prioritizes model-family diversity over raw reasoning power.

1. **2nd lens (spawn_subagent):** zen-big-pickle
   - Zen-hosted, free (cost 0 verified by direct probe 2026-08-14)
   - Reasoning 13/13 (2026-07-29); Tau2 unmeasured; not GLM family
   - Prior pick zen-deepseek-v4-flash-free (Tau2 95.6) config-removed
     2026-08-14; Zen backend had disabled its free tier 2026-08-12 (401)
2. **3rd + 4th lens (CLI parallel dispatch):** /codex (GPT) + /agy (Gemini)
   - Maximum cross-family diversity
   - Run in parallel when stakes are high
   - These are CLI skills, not spawn_subagent — separate quota pools
3. **Last resort:** parent-inherited GLM-5.2 (fresh-context but same-model lens)

### Thought-partner / planning / delegation (orchestrator role)
glm-5-2 (Tau2 #1 globally, agentic #21) — this is the orchestrator, not a pool pick

### Deep reasoning (free-first, non-critique tasks)
zen-big-pickle (13/13 our benchmark 2026-07-29; free — verified 2026-08-14)
or-arcee-ai-trinity-large-thinking (13/13, 4.6s — now paid, ~$0.00005/call as of 2026-08-14)

## Tier-1 (verified 2026-07-29)
### Thought-partner / planning / delegation
glm-5-2 (Tau2 99.1 #1 world, coding #12/130 91st pct, agentic #21/129, knowledge #9/55, spawn OK)
  - Use for: multi-turn dialogue, planning, architecture, delegation packets
  - Quota: 1,600 prompts/5h (GLM Max-Yearly). At 1,000s of requests/month,
    this is sustainable: ~288K/month theoretical max, no per-token dollar cap.

### Deep reasoning (free-first)
zen-big-pickle (13/13 deep-reasoning 2026-07-29, free — cost 0 verified 2026-08-14)
  - Use for: math, logic, single-shot analysis
or-arcee-ai-trinity-large-thinking (13/13, 4.6s — now PAID ~$0.00005/call as of 2026-08-14 probe)
  - Use for: reasoning-model tasks (has thinking trace); tiny per-call cost
or-ling-3-flash-free — REMOVED 2026-08-14: OpenRouter retired the free variant (404 probe receipt)

### Institutional reasoning
nvidia-nemotron-3-ultra (13/13, IFBench #2 globally at 81.4%, 32s avg)
  - Use for: instruction-constrained reasoning, structured analysis

## Backup (when GLM-5-2 unavailable)
zen-big-pickle (13/13 reasoning 2026-07-29, $0 — liveness and cost verified 2026-08-14)
  - Zen free tier; coding rank unmeasured (not a coding pick)
  - Quota: no published RPM/TPM limits. $0 during OpenCode free promotion.
  - Prior backup zen-deepseek-v4-flash-free (Tau2 95.6) was config-removed
    2026-08-14 after the Zen backend disabled the free tier (401, 2026-08-12).

## Fallback chain after backup exhausted
1. glm-5-2 (Tau2 99.1, coding #12, subscription, no dollar cap)
2. zen-big-pickle (13/13 reasoning, $0 free — verified alive 2026-08-14)
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

