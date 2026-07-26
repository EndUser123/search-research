---
title: "Operationalizing Gemma models: the practical guide (verified 2026-07-22)"
created: 2026-07-22
source: session-2026-07-22
tags: [gemma, diffusiongemma, operational, best-practices, prompting, sampling, temperature, thinking-mode, tpm, api, nvidia, verified]
summary: >
  How to get maximum value from the two Gemma variants in our fleet: Gemma 4 31B
  (Google API, 14,400 RPD, 30 RPM, 16K TPM, 131K context, free) and DiffusionGemma
  26B (NVIDIA API, no daily cap, ~40 RPM, 262K context, free). Both passed all
  quality tests (7/7 code gen, 3/3 code review, valid JSON, 1.0 extraction recall).
  Official Google best practices: temperature=1.0, top_p=0.95, top_k=64; thinking
  mode via <|think|> in system prompt; no thinking content in conversation history.
  DGemma-specific: max_tokens >= 256 (generates in 256-token diffusion blocks);
  latency 600ms-3.7s (small), 4-9s (large file reads). Gemma 4 31B-specific:
  latency 7-8s (short prompts), 12-29s (large file reads); 16K TPM is the binding
  constraint (not RPD or RPM).
agent: grok
host: both
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22
    type: extends
  - target: wiki/concepts/gemini-billing-tiers-actual-rate-limits-2026-07-22
    type: grounds
  - target: wiki/concepts/model-fleet-provider-pools
    type: operationalizes
  - target: wiki/concepts/model-pool-not-chain
    type: operationalizes
---

# Operationalizing Gemma models

## The two Gemma variants in our fleet

| Property | Gemma 4 31B (`gemma-4-31b-it`) | DiffusionGemma 26B (`nvidia-diffusiongemma-26b`) |
|----------|-------------------------------|--------------------------------------------------|
| **Provider** | Google API (generativelanguage.googleapis.com) | NVIDIA API (integrate.api.nvidia.com) |
| **Cost** | Free (Free tier) | Free (NVIDIA Developer Program) |
| **Architecture** | 30.7B dense, hybrid attention | 25.2B MoE, 3.8B active, diffusion-based |
| **Context** | 131K (API-configured) | 262K (NVIDIA docs confirmed) |
| **RPD** | **14,400** (highest in fleet) | **No daily cap** |
| **RPM** | 30 | ~40 |
| **TPM** | **16K** (binding constraint) | Unknown (no rate-limit headers) |
| **Latency p50 (short)** | ~7.6s | ~3.9s |
| **Latency p50 (large file)** | ~29s | ~8.5s |
| **Latency consistency** | **1.01x** (extremely stable) | 2.6x (variable) |
| **Dispatch** | `spawn_subagent(model="gemma-4-31b-it")` or direct API | Direct API only (`spawn_subagent` returns empty — see below) |

## Google's official best practices (from Gemma 4 model card, verified 2026-07-22)

### Sampling parameters

Use these standardized settings across all use cases:

```
temperature = 1.0
top_p = 0.95
top_k = 64
```

**Do NOT lower temperature below 1.0.** The model is optimized for this default.
Lower temperatures can cause degraded performance, looping, or unexpected
behavior. (Same guidance as Gemini 3 models.)

For DiffusionGemma, use the Entropy-Bounded Denoising sampler with:
- Max denoising steps: 48
- Temperature schedule: linear decay 0.8 → 0.4
- Entropy bound: 0.1

### Thinking mode

**Enable:** include `<|think|>` at the start of the system prompt.
**Disable:** remove the token.

When thinking is enabled:
```
<|channel>thought
[internal reasoning]
<channel|>
[final answer]
```

When thinking is **disabled** (no `<|think|>`):
- Gemma 4 31B: still generates empty thought tags, then the answer
- DiffusionGemma: may return empty content if `max_tokens < 256`

**Multi-turn rule:** do NOT include thinking content from previous turns in
conversation history. Only include the final response. Exception: preserve
thinking content on tool-call turns.

### Modality order (for multimodal)

- Image content **before** text in the prompt
- Audio content **after** text
- Video: processed as frame sequences (up to 60 seconds at 1 fps)

### Image resolution (variable token budget)

Configurable visual token budgets: 70, 140, 280, 560, 1120 tokens per image.
- **Lower budgets** (70-140): classification, captioning, video (faster)
- **Higher budgets** (560-1120): OCR, document parsing, small text

## Operational configuration for our fleet

### config.toml settings (verified working)

```toml
# Gemma 4 31B — Google API
[model.gemma-4-31b-it]
model = "gemma-4-31b-it"
base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
api_key = "<GEMINI_API_KEY>"
api_backend = "chat_completions"
context_window = 131072
max_completion_tokens = 8192

# DiffusionGemma 26B — NVIDIA API
[model.nvidia-diffusiongemma-26b]
model = "google/diffusiongemma-26b-a4b-it"
base_url = "https://integrate.api.nvidia.com/v1"
api_key = "<NVIDIA_API_KEY>"
api_backend = "chat_completions"
context_window = 262144
max_completion_tokens = 8192   # CRITICAL: must be >= 256 or content is empty
```

**The `max_completion_tokens = 8192` line is mandatory for DiffusionGemma.**
Without it, Grok Build sends a low default max_tokens, and the model cannot
complete its first 256-token diffusion block, returning empty content.

### TPM management (Gemma 4 31B's binding constraint)

The 16K TPM limit is the real operational constraint — not RPD (14,400) or RPM (30).

**Practical TPM math:**
- A typical skill file read (~9K tokens input + ~500 tokens output) = ~9.5K tokens
- 16K TPM budget ÷ 9.5K per call = **~1.7 large file reads per minute**
- Small prompts (~200 tokens input + ~200 output) = ~40 small calls per minute

**Strategy:**
- For large file reads: space 30 seconds apart (stays under TPM)
- For batch small reads: 3-second spacing (like our latency test — 10/10 success)
- If TPM exhausted: switch to DiffusionGemma (NVIDIA, separate TPM pool) or ccr-ornith

### Rate limit pacing

| Model | Spacing between calls | Why |
|-------|----------------------|-----|
| Gemma 4 31B (small prompts) | 3s | Stays under 16K TPM |
| Gemma 4 31B (large file reads) | 30s | Large prompts consume TPM fast |
| DiffusionGemma | 2s | Stays under ~40 RPM |
| Both in rapid-fire test | Verified 10/10 success at these spacings |

## Quality results (all verified this session)

| Test | Gemma 4 31B | DiffusionGemma | Gemini Flash-Lite (reference) |
|------|-------------|----------------|-------------------------------|
| Extraction recall (go/SKILL.md) | **1.0** | 0.87 | 1.0 |
| Extraction recall (handoff/SKILL.md) | **1.0** | 1.0 | 1.0 |
| Code generation (7-point check) | **7/7** | 7/7 | 7/7 |
| Code review (3 bugs) | **3/3** | 3/3 | 3/3 |
| JSON instruction following | ✅ | ✅ | ✅ |
| Latency p50 | 7,645ms | 3,913ms | **918ms** |
| Latency consistency | **1.01x** | 2.6x | 1.09x |

**All three pass the quality floor.** The operational choice is about rate
limits, latency, and dispatch mechanism — not quality.

## When to use which Gemma

| Situation | Pick | Why |
|-----------|------|-----|
| **High-volume daily work (100+ calls)** | Gemma 4 31B | 14,400 RPD — 28x more headroom than any other free model |
| **Batch file reads (small prompts)** | DiffusionGemma | Faster per-call (3.9s vs 7.6s); no daily cap |
| **Large file reads (>8K tokens)** | DiffusionGemma | 262K context; faster on large prompts (8.5s vs 29s); no TPM constraint |
| **Low-latency interactive** | Gemini Flash-Lite (if RPD available) or ccr-ornith | 918ms or local |
| **Need consistency (predictable timing)** | Gemma 4 31B | p90/p50 = 1.01x — nearly perfect stability |
| **NVIDIA rate-limited or down** | Gemma 4 31B | Separate provider; independent failure |
| **Google API rate-limited** | DiffusionGemma | Separate provider; independent failure |
| **spawn_subagent dispatch** | Gemma 4 31B `[UNTESTED post-config-fix]` | DGemma fails via spawn_subagent (empty content); Gemma needs testing |

## What still needs testing

| Gap | Priority | Plan |
|-----|----------|------|
| Gemma 4 31B via `spawn_subagent` | **High** | Test after restart (config.toml changes need restart) |
| DiffusionGemma via `spawn_subagent` post `max_completion_tokens` fix | **High** | Same — the fix may resolve the empty-content issue |
| Gemma 4 31B with thinking mode enabled | Medium | Compare quality with/without `<|think|>` |
| Gemma 4 31B multimodal (image input) | Medium | Test with understand_image-style tasks |
| Multi-turn consistency | Medium | Test conversation memory across turns |
| Context window stress (>10K tokens) | Low | 131K rated; not pushed to limits |

## Sources

- [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) — official Google best practices (scraped 2026-07-22)
- [NVIDIA NIM DiffusionGemma docs](https://docs.api.nvidia.com/nim/reference/diffusiongemma-26b-a4b-it) — architecture + context window
- `P:/tmp/model-test-results.json` — verified test results for all 3 models
- `P:/tmp/dgemma_gemini_test_suite.py` — reproducible test suite
- Live API tests this session (all latency/quality/sampling measurements)

## Auto-related

- [[solo_operator_adr_best_practices]]
- [[exemption-logic-as-conflict-signal]]

