# coding-model-pool

## Inputs
- task_type: "code-generation" | "code-review" | "code-exec" | "general-coding"

## Outputs
- model_slug: string (selected model slug from config.toml)
- fallback_chain: string[] (ordered list of fallback models)

## Procedure

0. **Check quota first.** Run `python ~/.grok/skills/model-quota/scripts/pick_model.py --json --lane coding` to get quota-eligible models before reading tier lists. This filters out any model whose provider is below the quota floor.
1. Check pool health: read `P:/.data/wiki/capabilities/coding-model-pool-health.json`.
   Skip any model with `status: "degraded"`. Models with `status: "recovering"`
   are usable but not preferred.
2. **Single subagent:** select first available from tier-1 (not degraded):
   - or-ling-3-flash-free
   - nim-openai-gpt-oss-20b
3. **Parallel wave (≥2 subagents):** use **round-robin provider assignment**
   to spread concurrent requests across providers and avoid rate-limit congestion.
   Alternate between tier-1 providers, then fall to tier-2 for additional slots:
   ```
   Subagent 1: or-ling-3-flash-free    (OpenRouter)
   Subagent 2: nim-openai-gpt-oss-20b  (NVIDIA)
   Subagent 3: or-ling-3-flash-free    (OpenRouter)
   Subagent 4: nim-openai-gpt-oss-20b  (NVIDIA)
   Subagent 5: zen-deepseek-v4-flash-free (Zen)  ← tier-2 to add a 3rd provider
   Subagent 6: minimax-m3              (MiniMax) ← tier-2 to add a 4th provider
   ```
   Rule: never assign the same provider to more than 2 concurrent subagents
   unless all other providers are degraded or rate-limited.
4. If all tier-1 unavailable or degraded, select from tier-2 (not degraded):
   - go-deepseek-v4-flash
   - minimax-m3
   - zen-deepseek-v4-flash-free
   - glm-5-2
5. Return model_slug + remaining models as fallback_chain

## Provider diversity table

| Model | Provider | Quota pool | Rate limit risk |
|---|---|---|---|
| or-ling-3-flash-free | OpenRouter | Free tier | Medium (shared free pool) |
| nim-openai-gpt-oss-20b | NVIDIA NIM | Free tier | Low (dedicated NIM endpoint) |
| zen-deepseek-v4-flash-free | OpenCode/Zen | Free tier | Low (Zen dedicated) |
| minimax-m3 | MiniMax | Subscription (4500/5h) | Low (high quota) |
| go-deepseek-v4-flash | OpenCode Go | Subscription | Low |
| glm-5-2 | Z.ai/GLM | Subscription | Low (ration for reasoning) |

**Parallel wave strategy:** maximize provider diversity. For N subagents,
use ceil(N/2) different providers. Never stack all subagents on one provider.

## Tier-1 (verified 2026-07-29, 5-problem HumanEval + 13-problem deep-reasoning;
re-verified 2026-07-31 with live code review quality tests)
or-ling-3-flash-free (5/5 code-exec, 13/13 reasoning, 2.2s, $0/M, spawn OK)
  - Live test 2026-07-31: 7-8s latency on review tasks, 10 findings (most thorough),
    found all critical issues across 4 test cases, zero fabricated findings.
  - Best default for single subagent and odd-numbered parallel slots.
nim-openai-gpt-oss-20b (4/5 code-exec, 13/13 reasoning, 7.7s, free, spawn OK)
  - Live test 2026-07-31: 9-13s latency on review tasks, 7-9 findings,
    found all critical issues across 4 test cases, zero fabricated findings.
  - Best for even-numbered parallel slots (different provider from or-ling).
  - NOTE: mistral-medium-latest was tier-1 (5/5 code-exec) but is now spawn-broken
    (422 context-too-large on this host). Moved to excluded. See fleet-models.json.

## Tier-2 (fallback when tier-1 exhausted; tested 2026-07-31)
minimax-m3 (4/5 code-exec, 13/13 reasoning, 7.3s nominal, 30-60s live test)
  - Live test: deepest analysis (9-12 findings), but 4-8× slower. Use when
    quality matters more than speed. Subscription (4500/5h quota).
zen-deepseek-v4-flash-free (4/5 code-exec, 13/13 reasoning, 7.4s nominal, 28-50s live test)
  - Live test: 6-10 findings with correct root-cause analysis. Provided full
    corrected implementations. Different provider from tier-1 (Zen). Free.
go-deepseek-v4-flash (5/5 code-exec, 13/13 reasoning, 6.4s, OpenCode sub)
  - Not live-tested in this session. Available as fallback.
glm-5-2 (4/5 code-exec, 12/13 reasoning, 7.9s nominal, 8.1s live test)
  - Live test: correct, concise. REASONING LANE ONLY — ration subscription quota.
  - Use for plan/debug/critic roles, not general code execution.

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
