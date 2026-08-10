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

### nim (2 models) — PARTIAL

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `nim-openai-gpt-oss-20b` | DONE: 18/18 pass | TODO | TODO | Already has production evidence |
| `nim-deepseek-ai-deepseek-v4-flash` | BLOCKED: HTTP 410 Gone | BLOCKED | BLOCKED | Model endpoint retired — needs registry cleanup |

Commands for nim-openai-gpt-oss-20b remaining:
```
python pool_test.py --model nim-openai-gpt-oss-20b --capability reasoning --method http
python pool_test.py --model nim-openai-gpt-oss-20b --capability mechanical --method http
```

nim-deepseek-ai-deepseek-v4-flash: mark lifecycle=retired (model gone).

### nvidia (6 models) — PENDING

| Model | tool-loop | reasoning | mechanical | Notes |
|---|---|---|---|---|
| `nvidia-nemotron-3-super-120b` | TODO | TODO | TODO | Has production evidence |
| `nvidia-nemotron-3-ultra` | TODO | TODO | TODO | Has production evidence (n=1) |
| `nvidia-laguna-xs-2-1` | TODO | TODO | TODO | Candidate — needs promotion |
| `nvidia-nemotron-nano-9b-v2` | TODO | TODO | TODO | Candidate |
| `nvidia-nemotron-nano-12b-v2-vl` | TODO | TODO | TODO | Candidate |
| `nvidia-stepfun-3-7-flash` | TODO | TODO | TODO | Candidate |

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
| `minimax-m3` | **17/18 PASS** (0.94) | **0/8 FAIL** (0.00) | **2/8 PASS** (0.25) | Policy=excluded. Strong coder, terrible at exact-match reasoning/mechanical. |

**Analysis:** minimax-m3 is an excellent coding model (17/18, including all 5 hard problems) but fails reasoning and mechanical tasks. The reasoning/mechanical failures are likely an output-formatting issue — the model produces `<think>` tags and verbose explanations instead of just the number/answer. The exact-match scorer can't extract the answer from the verbose output. This is a scoring problem, not necessarily a capability problem — but for production, if the model can't follow "return ONLY the number" instructions, it IS a capability gap for those lanes.

**Recommendation:** eligible for tool-loop (coding) if un-excluded. Not eligible for reasoning or mechanical.

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
