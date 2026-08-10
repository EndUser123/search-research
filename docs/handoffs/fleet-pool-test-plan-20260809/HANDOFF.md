---
title: "Fleet pool test plan: per-provider, per-capability, per-method"
sources:
  - date: 2026-08-09
    host: grok
    session: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
provenance: session-observation
last_verified: 2026-08-09
---

# Fleet pool test plan: per-provider, per-capability, per-method

## Principle

Test every model against every capability. Lane assignments are informed by results, not assumptions. A model currently assigned to "reasoning" might be the best coding model — we won't know until we test it.

## Provider status tracker

Updated as testing progresses. Check before running.

| Provider | Models | Capacity | Status | Blocker |
|---|---|---|---|---|
| cerebras | 2 | n/a | SKIP | Provider excluded by operator |
| cohere | 3 | 0% | BLOCKED | Quota exhausted — reset pending |
| groq | 3 | n/a | SKIP | Provider excluded by operator. Free tier TPM cap (6,000-8,000) blocks all production spawns — Grok Build system prompt alone is ~54K tokens. Pool test could work (short prompts) but model can't be promoted to active production use until TPM limit resolved. Verified 2026-07-29: all 3 models fail instantly with HTTP 413. |
| minimax | 1 | 48% | PENDING | |
| nim | 2 | n/a (shares nvidia) | PARTIAL | nim-openai-gpt-oss-20b tested (18/18 pass); nim-deepseek-v4-flash returns 410 Gone |
| nvidia | 6 | n/a | PENDING | |
| opencode | 3 | n/a | PENDING | |
| openrouter | 2 | n/a | BLOCKED | or-ling-3-flash-free moved behind paywall (404) |
| zai | 1 | 69% | PENDING | |
| zen | 3 | n/a | BLOCKED | zen-deepseek-v4-flash-free returns 401 "Model is disabled" |

## Per-provider plans

### Cohere (3 models) — BLOCKED: quota at 0%

Test all 3 capabilities for all 3 models when quota resets.

| Model | tool-loop (18 problems) | reasoning (8 problems) | mechanical (8 problems) |
|---|---|---|---|
| `cohere-north-mini-code` | Run 1 | Run 2 | Run 3 |
| `cohere-command-a-plus` | Run 4 | Run 5 | Run 6 |
| `cohere-command-a-reasoning` | Run 7 | Run 8 | Run 9 |

Total: 34 problems x 3 models = 102 API calls.

Commands (run when quota resets):
```
python pool_test.py --model cohere-north-mini-code --capability tool-loop --method http
python pool_test.py --model cohere-north-mini-code --capability reasoning --method http
python pool_test.py --model cohere-north-mini-code --capability mechanical --method http
python pool_test.py --model cohere-command-a-plus --capability tool-loop --method http
python pool_test.py --model cohere-command-a-plus --capability reasoning --method http
python pool_test.py --model cohere-command-a-plus --capability mechanical --method http
python pool_test.py --model cohere-command-a-reasoning --capability tool-loop --method http
python pool_test.py --model cohere-command-a-reasoning --capability reasoning --method http
python pool_test.py --model cohere-command-a-reasoning --capability mechanical --method http
```

After HTTP baseline: run top performer via --method pi and --method opencode for tool-evidence requirement.

### nim (2 models) — TESTED

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `nim-openai-gpt-oss-20b` | **18/18 PASS** (1.00) | **7/8 PASS** (0.88) | **6/8 PASS** (0.75) | Excellent all-around. 1 reasoning failure was empty response (API hiccup). 2 mechanical failures genuine (word count + JSON types). |
| `nim-deepseek-ai-deepseek-v4-flash` | **DEAD** (HTTP 410) | — | — | Model endpoint retired. Needs lifecycle=retired. |

Commands for nim-openai-gpt-oss-20b remaining:
```
python pool_test.py --model nim-openai-gpt-oss-20b --capability reasoning --method http
python pool_test.py --model nim-openai-gpt-oss-20b --capability mechanical --method http
```

nim-deepseek-ai-deepseek-v4-flash: mark lifecycle=retired (model gone).

### nvidia (now 22 models) — TOOL-LOOP TESTED

Full API discovery + probe + 18-problem coding suite run against all alive models.

| Model | Score | In registry? | Notes |
|---|---|---|---|
| `deepseek-ai/deepseek-v4-flash-0731` | 18/18 (1.00) | NEW | Replacement for dead v4-flash |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 18/18 (1.00) | NEW | Reasoning nano |
| `nvidia/nemotron-3-super-120b-a12b` | 18/18 (1.00) | existing | Was active, now confirmed |
| `openai/gpt-oss-120b` | 18/18 (1.00) | NEW | Larger GPT-OSS |
| `openai/gpt-oss-20b` | 18/18 (1.00) | existing | Previously tested |
| `meta/llama-3.1-70b-instruct` | 17/18 (0.94) | NEW | |
| `nvidia/llama-3.3-nemotron-super-49b-v1` | 17/18 (0.94) | NEW | |
| `nvidia/nemotron-3-nano-30b-a3b` | 17/18 (0.94) | NEW | |
| `google/gemma-4-31b-it` | 16/18 (0.89) | NEW | |
| `meta/llama-3.2-90b-vision-instruct` | 16/18 (0.89) | NEW | Vision-capable |
| `nvidia/nemotron-nano-12b-v2-vl` | 16/18 (0.89) | existing | Was candidate |
| `nvidia/nvidia-nemotron-nano-9b-v2` | 15/18 (0.83) | existing | Was candidate |
| `thinkingmachines/inkling` | 15/18 (0.83) | NEW | |
| `mistralai/mistral-nemotron` | 14/18 (0.78) | NEW | |
| `nvidia/llama-3.1-nemotron-nano-vl-8b-v1` | 14/18 (0.78) | NEW | |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 14/18 (0.78) | existing | |
| `nvidia/nemotron-3-ultra-550b-a55b` | 14/18 (0.78) | existing | |
| `meta/llama-3.1-8b-instruct` | 13/18 (0.72) | NEW | |
| `meta/llama-3.2-11b-vision-instruct` | 13/18 (0.72) | NEW | |
| `meta/llama-3.2-3b-instruct` | 13/18 (0.72) | NEW | |
| `google/diffusiongemma-26b-a4b-it` | 11/18 (0.61) | NEW | Known spawn issues |
| `stepfun-ai/step-3.7-flash` | 11/18 (0.61) | existing | Was candidate |
| `minimaxai/minimax-m3` | 2/18 (0.11) | existing | 429 rate-limited during batch; scored 17/18 individually |
| `nvidia/nemotron-mini-4b-instruct` | 0/18 (0.00) | not added | Cannot code |

**Next steps for nvidia:** reasoning + mechanical tests for the 22 promotable models. Method-aware testing (pi, opencode) for tool-evidence requirement.

Commands (4 candidates x 3 capabilities + 2 active x 3 capabilities = 18 runs):
```
# Per model, run all 3 capabilities
python pool_test.py --model <model-id> --capability tool-loop --method http
python pool_test.py --model <model-id> --capability reasoning --method http
python pool_test.py --model <model-id> --capability mechanical --method http
```

### minimax (1 model) — TESTED

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `minimax-m3` | **17/18 PASS** (0.94) | **8/8 PASS** (1.00) | **4/8 PASS** (0.50) | Policy=excluded. Strong coder + reasoner. Mechanical format-compliance gap. |

**Analysis:** minimax-m3 is an excellent coder (17/18 including all 5 hard problems) and perfect reasoner (8/8). Mechanical is borderline (4/8) — genuine instruction-following gaps where the model adds verbose text. Initial 0/8 reasoning was a scorer bug (think tags); fixed in commit c0c0f88.

**Recommendation:** eligible for tool-loop and reasoning if un-excluded. Not eligible for mechanical.

### zai (1 model) — PENDING

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `glm-5-2` | TODO | TODO | TODO | Policy=excluded but operator wants test data |

Capacity at 69% — should be testable.

### opencode (3 models) — PENDING

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `zen-laguna-s-2-1-free` | TODO | TODO | TODO | Candidate |
| `zen-longcat-2-0-free` | TODO | TODO | TODO | Candidate |
| `zen-ling-3-0-tiny-free` | TODO | TODO | TODO | Candidate |

### zen (3 models) — BLOCKED

| Model | Status | Notes |
|---|---|---|
| `zen-deepseek-v4-flash-free` | HTTP 401 "Model is disabled" | Endpoint issue |
| `zen-north-mini-code-free` | TODO | |
| `zen-big-pickle` | TODO | |

### openrouter (2 models) — BLOCKED

| Model | Status | Notes |
|---|---|---|
| `or-ling-3-flash-free` | HTTP 404 — moved behind paywall | |
| `or-arcee-ai-trinity-large-thinking` | TODO | |

## Post-test actions

1. Update lane assignments in fleet-models.json based on test results
2. Mark retired models (410 Gone, 401 disabled) as lifecycle=retired
3. Promote candidates that pass the floor (>=5 problems) to active
4. Run discrimination report (--report flag) once 2+ models tested
5. Run method-aware testing (pi, opencode) for tool-evidence requirement
6. **Fix selector recommending dead models** — or-ling-3-flash-free (404 paywalled), zen-deepseek-v4-flash-free (401 disabled), nim-deepseek-v4-flash (410 gone) are still in the active pool and get recommended by pick_model.py. Need either: (a) per-model health probe that detects 4xx as model-level failure, or (b) mark these lifecycle=retired in fleet-models.json, or (c) add a model-availability gate alongside the capacity gate. The /review skill hit this in production: "Both model slugs failed."
7. **Fix exact-match scorer for verbose models** — minimax-m3 wraps output in `<think>` tags. The scorer can't extract the answer. Need a `<think>` stripper or "last line / last number" extraction before exact-match comparison.

## Falsifier

This plan is wrong if the pool test problems don't discriminate between models (all pass or all fail) or if the lane assignments after testing don't improve fleet selection quality.
