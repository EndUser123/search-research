---
title: "Model benchmark testing quirks: gotchas that affect accuracy"
created: 2026-07-29
source: session-2026-07-28/29 (discovered during fleet benchmark development)
tags: [benchmark, testing, quirks, gotchas, reasoning-tokens, reasoning-effort, groq, tpm, glm, config, prompt-design]
summary: >
  Practical gotchas discovered during fleet benchmarking that affect test
  accuracy or cause false failures. Each quirk has a specific fix. Topics:
  reasoning tokens consuming output budget, reasoning_effort truncating
  content, Groq TPM limits on max_tokens and spawn_subagent, per-provider
  effort vocabularies, config flags affecting parent model behavior, prompt
  ambiguity in code-exec problems, and warm-up calls for cold-start latency.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-verified
sources:
  - "Session 2026-07-28/29 fleet benchmark sweeps"
relations:
  - target: wiki/concepts/parameter-aware-benchmark-tier-system.md
    type: complements
  - target: wiki/concepts/fleet-benchmark-results-2026-07-29.md
    type: companion
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: related
  - target: wiki/concepts/groq-free-tier-tpm-limit-6000.md
    type: related
---

# Model benchmark testing quirks

## Decision context

During fleet benchmarking, multiple models appeared to "fail" code-exec
or produce empty output. Investigation revealed that most failures were
test-infrastructure issues, not model capability issues. This page
documents every quirk discovered, its root cause, and the specific fix —
so the next benchmarking session doesn't re-derive them.

## Quirk 1: Reasoning tokens consume max_tokens budget

**Symptom:** Model returns empty content or truncated code. `finish_reason:
"length"` with very few output tokens.

**Cause:** GLM-5.2, MiniMax-M3, MiMo, DeepSeek, and other reasoning
models consume `max_tokens` on internal chain-of-thought thinking before
producing visible content. At small budgets (1024 tokens), reasoning
eats the entire budget, leaving nothing for the actual answer.

**Verified example:** GLM-5.2 used 1064 reasoning tokens on a simple
code-exec prompt at `max_tokens=1024` — zero tokens left for code output.

**Fix:** `CodeExecTier.get_budget()` returns the model's full
`max_completion_tokens` from config (no artificial cap). For models
without config capacity, default to 8192.

**Do NOT do:** Add `reasoning = true` to config.toml to fix benchmark
budgets. This flag affects the parent model's behavior in Grok Build and
caused a production max_tokens truncation (see [[groq-free-tier-tpm-limit-6000]]).
Detect reasoning by provider instead (glm, minimax, opencode).

## Quirk 2: reasoning_effort parameter truncates content on some models

**Symptom:** GLM-5.2 produces shorter, truncated code output when
`reasoning_effort: "medium"` is sent.

**Cause:** The `reasoning_effort` parameter changes how models allocate
reasoning vs content budget. On GLM-5.2, `reasoning_effort: "medium"`
caused it to truncate code mid-function — the code block never closed,
extraction failed, quality scored 0.0.

**Fix:** The benchmark does NOT send `reasoning_effort` by default. Models
that need reasoning use it internally regardless. Per-model
`reasoning_effort` can be set in config.toml for specific cases (e.g.,
Groq Qwen3.6 needs `"default"` not `"high"`).

## Quirk 3: Per-provider reasoning_effort vocabularies differ

**Symptom:** `reasoning_effort: "high"` rejected by Groq Qwen3.6 with
400 error: "must be one of `none` or `default`."

**Cause:** Different providers use different effort vocabularies.

| Provider/Model | Accepted values |
|---|---|
| Groq gpt-oss-120b | low, medium, high |
| Groq qwen3.6-27b | none, default |
| NVIDIA Nemotron | low, medium, high |
| GLM-5.2 | max, xhigh, high, medium, low, minimal, none (default: max) |
| MiniMax-M3 | low, medium, high |

**Fix:** Per-model `reasoning_effort` field in config.toml. CLI flag
`--reasoning-effort <value>` overrides all models for a run.

## Quirk 4: Groq TPM limit (6000) blocks large max_tokens

**Symptom:** All Groq models fail with HTTP 413 "Request too large ...
TPM: Limit 6000, Requested 8238."

**Cause:** Groq's free tier (`on_demand` service tier) enforces a 6000
Tokens Per Minute limit. Any request where `max_tokens > 6000` is
rejected before inference — regardless of actual output size.

**Fix:** The benchmark's retry/error layer handles HTTP 413 gracefully
(classified as `request_too_large`). Models with large
`max_completion_tokens` will fail on Groq; this is expected behavior, not
a test bug. The pool health monitor tracks success rate and can flag Groq
as degraded.

**Do NOT do:** Cap all models to 6000 to protect Groq. That starves
non-Groq models of output tokens (see Quirk 1).

## Quirk 5: Groq can't do spawn_subagent (system prompt too large)

**Symptom:** `spawn_subagent(model="groq-gpt-oss-120b")` fails with
HTTP 413: "Requested 53781" vs TPM limit 8000.

**Cause:** Grok Build's `spawn_subagent` sends a ~54K token system
prompt. Groq's free tier TPM cap (8000 for spawn path) can't accommodate
it.

**Fix:** None possible. Groq models are excluded from all spawn-based
pools (coding, reasoning). They can only be used via direct HTTP API
calls (burst-only, single-shot).

## Quirk 6: reasoning = true in config.toml affects parent model

**Symptom:** Production `max_tokens_truncation` error on GLM-5.2 as
parent orchestrator. Only 235 output tokens produced on a 58K input turn.

**Cause:** Adding `reasoning = true` to GLM-5.2's config entry (done to
fix benchmark code-exec budget) caused Grok Build to allocate reasoning
budget differently for the parent model. The flag was meant for the
benchmark but config.toml is the live production config — it affects
every session.

**Fix:** Reverted `reasoning = true` from GLM-5.2 config. The benchmark
now detects reasoning models by provider (glm, minimax, opencode) in
`CodeExecTier.get_budget()` instead of relying on the config flag.

**Lesson:** NEVER add fields to config.toml model entries to fix benchmark
behavior. Config.toml is production infrastructure. The benchmark must
adapt to config as it exists.

## Quirk 7: Code-exec prompt ambiguity causes non-deterministic failures

**Symptom:** Model passes code-exec on one run, fails on another. Same
model, same prompt.

**Cause:** The original HumanEval problem docstring said "Ignore whitespace
between groups" which models interpreted as "groups are whitespace-
separated." When adjacent groups (`()()()`) appeared in tests, models
that used `.split()` failed.

**Fix:** Added explicit second doctest example: `separate_paren_groups("()()()")`
returns `['()', '()', '()']`. This makes adjacent-group handling
unambiguous in the prompt itself.

**Lesson:** Any test prompt that produces non-deterministic results across
runs likely has an ambiguity. Investigate the prompt, not the model.

## Quirk 8: Warm-up call eliminates cold-start latency inflation

**Symptom:** First model tested on each provider shows artificially high
latency (2-3x normal).

**Cause:** Provider-side cold start — first request to a provider's
infrastructure may be slow due to connection setup, model loading, or
cache warming.

**Fix:** Per-provider warm-up call before the timed benchmark. The
benchmark sends an untimed `"Reply: OK"` probe to each provider once per
run (tracked via `_warmed_providers` set).

## Quirk 9: Windows subprocess timeout doesn't kill child processes

**Symptom:** Code-exec subprocess times out but orphaned processes
continue running, consuming resources.

**Cause:** `subprocess.run(timeout=5)` on Windows uses
`TerminateProcess()` which only kills the parent Python process, not
children spawned by model-generated code.

**Fix:** Added `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` on
Windows in `CodeExecTier.score()`.

## Quirk 10: OpenRouter :free models are genuinely free

**Symptom:** `--skip-paid` excluded OpenRouter `:free` models from
sweeps, preventing testing of potentially strong coding models (Laguna
S2.1, Ling 3.0 Flash).

**Cause:** The wiki incorrectly stated `:free` models cost `~$0.005/1M`
tokens. The `--skip-paid` flag filtered them out based on this claim.

**Verified reality:** OpenRouter `:free` models are $0/M input and $0/M
output. Rate limited: 20 RPM, 50 RPD (or 1000 RPD with $10+ lifetime
credits). Sources: openrouter.ai/docs/faq, openrouter.ai/docs/api_reference/limits.

**Fix:** Updated `[[model-fleet-provider-pools]]` to correct the pricing.
The `go-*` paid variants DO cost money; the `or-*` `:free` models do not.

## Quirk 11: Zen free models' data privacy caveat

**Symptom:** Not a test failure — a privacy risk.

**Cause:** Zen free models (big-pickle, deepseek-v4-flash-free, mimo-v2.5-
free, laguna-s-2.1-free, ling-3.0-flash-free) may use submitted data for
model training during the free period. North Mini Code Free (Cohere)
and Nemotron 3 Ultra Free (NVIDIA) have explicit data-logging warnings.

**Fix:** Do not send sensitive/proprietary data to Zen free models.
They're fine for benchmark probes (public HumanEval problems) but should
not receive production code or internal documents.

## Falsifier

These quirks are session-specific findings. They become stale if:
- Providers change their API behavior (reasoning token counting, TPM limits)
- Grok Build changes how config.toml flags affect parent model behavior
- OpenRouter changes `:free` tier pricing or rate limits
- HumanEval problems become contaminated (models trained on them)

Re-verify by running a fresh fleet sweep and comparing results to
[[fleet-benchmark-results-2026-07-29]].
