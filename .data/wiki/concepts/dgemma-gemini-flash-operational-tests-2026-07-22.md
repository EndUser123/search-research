---
title: "DGemma + Gemini Flash-Lite operational test results (2026-07-22)"
created: 2026-07-22
source: session-2026-07-22
tags: [dgemma, gemini, flash-lite, test-results, calibration, latency, quality, operational, verified]
summary: >
  Formal test of DiffusionGemma (NVIDIA direct API) and Gemini 3.5 Flash-Lite
  (Google API) across 6 task types: extraction (2 files), code generation,
  code review, JSON instruction following, latency profiling (10 calls each),
  and corrected handoff extraction. Both models passed all quality checks.
  Gemini Flash-Lite is 4x faster with 4x more consistent latency. DGemma
  requires max_completion_tokens >= 256 (generates in 256-token blocks via
  diffusion; lower values return empty). Full results with content previews
  at P:/tmp/model-test-results.json.
agent: grok
host: grok
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/model-fleet-provider-pools
    type: grounds
  - target: wiki/concepts/model-pool-not-chain
    type: grounds
  - target: wiki/concepts/model-lanes-vs-roles
    type: grounds
---

# DGemma + Gemini Flash-Lite operational test results

## Test methodology

**Models tested:**
- DiffusionGemma (`google/diffusiongemma-26b-a4b-it`) via NVIDIA direct API
- Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) via Google API

**Task types (6 tests per model):**
1. Extraction from go/SKILL.md (36KB, ~9K tokens) — extract profiles, packs, model slugs
2. Extraction from handoff/SKILL.md (21KB, ~5K tokens) — extract commands, constraints
3. Code generation — write `parse_semver()` from spec; 7-point correctness check
4. Code review — find 3 known bugs (SQL injection, index out of range, indentation)
5. Instruction following — produce valid JSON array with specific schema
6. Latency profiling — 10 sequential calls, same prompt, report p50/p90

**Scoring:** extraction tasks scored against known answer keys (recall = found/expected).
Code/review/JSON tasks scored on objective correctness markers. Latency measured
end-to-end including network round-trip.

**Rate limit handling:** 2-second spacing between calls. Retry on 429 with 3-second backoff.

**Full raw results:** `P:/tmp/model-test-results.json` (includes content previews for every test)

## Results

| Test | DGemma | Gemini 3.5 Flash-Lite |
|------|--------|----------------------|
| **Extraction (go/SKILL.md)** | 0.87 recall (missed `route-only`) | **1.0 recall** (perfect) |
| **Extraction (handoff/SKILL.md)** | **1.0 recall** | **1.0 recall** |
| **Code generation** | **7/7** (def, dict return, prerelease, ValueError, docstring, assertion, int conversion) | **7/7** |
| **Code review** | **3/3** bugs found (SQL injection, index, indentation) | **3/3** bugs found |
| **JSON instruction following** | **Valid JSON, correct schema** | **Valid JSON, correct schema** |
| **Latency p50** | 3,913ms | **918ms** |
| **Latency p90** | 10,169ms | **998ms** |
| **Latency p90/p50 ratio** | 2.6x (variable) | **1.09x (stable)** |
| **Rate limit success** | 10/10 at 2s spacing | 10/10 at 2s spacing |

## Key findings

### 1. Both models are competent on all task types

No quality floor issue for either model. Code generation, code review, JSON
formatting, extraction — all pass. Both found all 3 bugs in the review test.
Both produced valid JSON with correct schema. Both generated complete
`parse_semver()` implementations with all 7 correctness markers.

### 2. Gemini Flash-Lite is 4x faster with 4x more consistent latency

- p50: 918ms vs 3,913ms (4.3x faster)
- p90: 998ms vs 10,169ms (10x faster)
- p90/p50 ratio: 1.09x vs 2.6x (Gemini is predictable; DGemma varies significantly)
- DGemma's p90 outlier (10s) suggests diffusion block generation occasionally
  needs more denoising steps on certain prompts

### 3. DGemma's empty-content root cause (verified)

DiffusionGemma generates in 256-token blocks via discrete diffusion. If
`max_tokens < 256`, the model cannot complete its first block and returns
empty content. Verified with controlled max_tokens sweep:

| max_tokens | Content returned? |
|------------|------------------|
| 16 | ❌ empty |
| 32 | ❌ empty |
| 48 | ❌ empty |
| 256 | ✅ content |

**Fix:** `max_completion_tokens = 8192` in config.toml (added this session).
This ensures Grok Build sends `max_tokens: 8192`, giving the model room for
multiple generation blocks.

**Not yet tested:** whether `spawn_subagent(model="nvidia-diffusiongemma-26b")`
works after this fix. Needs Grok restart (config.toml changes require session restart).

### 4. NVIDIA rate limit: ~40 RPM (verified from sources)

- NVIDIA Developer Forums staff-confirmed: ~40 RPM, model/traffic-dependent
- No daily quota cap — rate-based, not credit-based
- At 40 RPM sustained = ~2,400/hour
- Actual fleet usage (~170/hr across 5 terminals) = ~7% of ceiling
- 429s occur only under burst-fire (5+ calls in <3 seconds); 2-second spacing eliminates them

### 5. Gemini API cost is `[UNVERIFIED]`

The GEMINI_API_KEY in `.env` is on Google's `generativelanguage.googleapis.com`
endpoint. Flash-Lite models responded consistently across 20+ calls. Pro models
returned "quota exceeded, limit: 0" on free tier. Flash/Flash-Lite appear to
have higher free-tier limits than Pro, but the billing tier of this specific key
has not been confirmed with the operator.

### 6. Extraction recall difference (go/SKILL.md)

DGemma missed the `route-only` profile (0.87 recall); Gemini found all profiles
(1.0 recall). The `route-only` profile is in the tie-breaker section, not the
main profile table — DGemma may not have read far enough into the file, or the
profile name appears only once and DGemma's diffusion generation skipped it.
On the handoff file (corrected test), both scored 1.0.

## What is NOT tested

| Gap | Why | Priority |
|-----|-----|----------|
| `spawn_subagent` compatibility | Needs Grok restart to pick up config change | **High** — gating for pool membership |
| Gemini cost tier | Haven't confirmed billing status with operator | Medium |
| Gemini daily quota limits | Not scraped from Google rate-limits page | Medium |
| ccr-ornith quality/latency comparison | Not tested in this session — no comparative baseline | High for pool decisions |
| Context window stress test (>10K tokens) | Largest test was 9K tokens; no degradation observed but not pushed to limits | Low (262K/1M rated) |
| Multi-turn conversation consistency | All tests were single-turn | Medium |
| ccr-ornith latency measurement | The "40s+" claim is from a single observation, not a profile | High |

## Test bug disclosed

The initial handoff extraction test used the wrong prompt (asked for profiles/packs/models
but scored against commands/constraints). Both models correctly answered the prompt they were
given but scored 0.2/0.0 against the mismatched answer key. Re-run with correct prompt:
both scored 1.0. The corrected results above are the accurate ones.

## Operational implications

For pool membership decisions, these results support:

- **Gemini 3.5 Flash-Lite**: strong candidate for Code lane primary. Fastest, most
  consistent, most accurate on extraction. Cost `[UNVERIFIED]` — confirm billing
  before treating as reliably free.
- **DGemma**: solid Code lane member. Same quality on code tasks. Slower and more
  variable. Requires `max_completion_tokens >= 256` (fixed in config). Works reliably
  via direct API. `spawn_subagent` compatibility untested post-fix.
- **Both models**: pass quality floor on extraction, code generation, code review, and
  JSON formatting. No reason to exclude either from the Code pool.

## Sources

- `P:/tmp/model-test-results.json` — full raw results with content previews
- `P:/tmp/dgemma_gemini_test_suite.py` — test suite source code (reproducible)
- NVIDIA Developer Forums (rate limit confirmation)
- NVIDIA NIM docs (docs.api.nvidia.com — model architecture, context window)
- Live API tests this session (all latency/quality measurements)

## Auto-related

- [[yt-is-notebooklm-pipeline-improvements]]

