---
title: "Automated result plausibility checking — sanity-check background task output before reporting"
created: 2026-08-11
source: session-019fdf47
tags: [validation, plausibility, background-tasks, narrative-sufficiency, anomaly-detection, automated-testing, trust-but-verify]
summary: >
  When a background task (pool test, benchmark, orchestrator run) completes,
  the agent must sanity-check the output for plausibility before reporting
  results to the operator. Three checks: duration plausible? success rate
  plausible given known baselines? failure pattern systematic (provider-level)
  or scattered (model-level)? Without these checks, the agent trusts obviously
  wrong output and reports invalid results as fact.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://waxell.ai/blog/ai-agent-output-validation-production (Waxell, 2026)
  - https://genai.owasp.org/llmrisk/llm06-sensitive-information-disclosure/ (OWASP, 2025)
  - https://blog.jztan.com/the-most-dangerous-llm-is-the-one-that-sounds-confident/ (jztan, 2026)
  - https://www.cegeka.com/en/blogs/the-pitfalls-of-test-automation (Cegeka, 2025)
  - https://www.functionize.com/blog/watching-out-for-false-positives-and-false-negatives-in-software-testing (Functionize, 2025)
---

# Automated result plausibility checking

## The class of error

This is a specific instance of **narrative sufficiency** — the agent treats
structured output from a background task as valid because it *looks* complete,
without checking whether the content is *plausible*. The research literature
calls this several related names:

| Name | Source | Description |
|------|--------|-------------|
| **Blind trust in tool outputs** | OWASP LLM06:2025, Waxell 2026 | Agents treat tool results as ground truth without plausibility checks |
| **Confident hallucination** | jztan 2026 | Schema-valid but factually wrong output — 67% of verifiable facts fabricated in one case study |
| **False acceptance rate** | Keysight/Functionize 2025 | Test suite passes but defective code ships because assertions are too weak or coverage gaps exist |
| **Pesticide paradox** | Cegeka 2025 | Automated tests lose effectiveness over time; green dashboards create false confidence |
| **Narrative sufficiency** | [[plausible-narratives-substitute-for-verification]] | Agent treats plausible-looking output as verified without checking |

## The specific failure mode in our workspace

When a background task completes and returns data, the agent's instinct is to
"read results and report." This skips three critical plausibility checks:

### Check 1: Is the duration plausible?

A pool test of 18 problems × 14 models via PI should take hours, not seconds.
When the orchestrator reported `33.8s` for 3 PI cells, that was obviously
impossible — each PI call alone takes 5-30s. The agent should have immediately
said "that's wrong, something broke" before reading the log.

### Check 2: Is the success rate plausible given known baselines?

A model that scored 18/18 via HTTP scoring 0/18 via PI is a 100% gap. Real
capability gaps between methods are 10-30%, not 100%. A 100% gap means the test
infrastructure failed, not the model. The agent should compare against the
HTTP baseline before accepting PI results as valid.

### Check 3: Is the failure pattern systematic or scattered?

All 18 probes failing on OpenRouter is a **provider-level** failure (wrong
API key, wrong PI provider config, rate limit exhaustion), not a model-level
finding. The agent should check: if N% or more of models fail identically,
it's infrastructure, not capability.

## How others mitigate this

### AI agent research (2025-2026)

The industry is shifting from "agents that can act" to "agents whose actions
are verifiable" (Waxell 2026). Key mitigations:

1. **Multi-layer validation** — deterministic checks (schema, ranges) +
   semantic checks (LLM-as-judge, consistency) + policy enforcement (risk-context)
2. **Ground-truth spot-checks** — sample a few verifiable claims against
   authoritative sources to catch systematic failures
3. **Provenance tracing** — record typed graphs of tool calls → outputs → claims
4. **Uncertainty as first-class** — schemas that force "N/A" or confidence levels
5. **Runtime enforcement, not just observation** — dashboards that only observe
   are insufficient; enforcement must sit in the execution path

### Software engineering (CI/CD pipelines)

1. **Anomaly detection on test metrics** — detect sudden spikes in failures,
   unusual durations, coverage drops using statistical/ML methods
2. **Flaky test management** — quarantine and investigate tests that pass/fail
   unpredictably
3. **Never ship solely on "tests passed"** — require risk-based human review
   for critical paths
4. **Treat test suite as a product** — maintain, evolve, and monitor it

## What this means for our workspace

The agent must perform a **plausibility gate** before reporting any background
task results to the operator:

```
Background task completes
    ↓
Read results
    ↓
PLAUSIBILITY GATE:
  1. Duration plausible? (compare to expected range)
  2. Success rate plausible? (compare to known baseline)
  3. Failure pattern systematic? (>50% identical = infra)
    ↓
Pass → Report results
Fail → Investigate before reporting; label as [INVALID] if confirmed
```

This gate is behavioral (agent judgment) not mechanical (code), because the
"plausible" threshold depends on context. But it should be as mandatory as
the edit-then-verify pattern for file writes.

## Falsifier

This check is unnecessary if background tasks never return obviously wrong
data. In practice, they do — rate limits, configuration mismatches, and
infrastructure failures produce 0-scores that look like valid results.

## Related

- [[plausible-narratives-substitute-for-verification]] — parent pattern
- [[narrative-sufficiency-external-approaches]] — external mitigations
- [[diagnostic-logging-by-default-in-fleet-tooling]] — failure mode breakdown
- [[claims-require-receipts]] — the receipt rule applied to task results

## Receipts

- Pool test HTTP scorer: `benchmark_tiers.py:CodeExecTier.score()` (line 715) — scores by executing code in sandbox
- Pool test failure breakdown: `pool_test.py:run_pool_test()` summary section (line 830) — classifies failures into infra:* vs quality:*
- PI dispatch module: `~/.grok/skills/model-quota/scripts/pi_dispatch.py:dispatch()` — shared dispatch with retry
- Orchestrator sequential fix: `benchmark_orchestrator.py:_run_provider_cells()` — runs capabilities sequentially per provider
- Background task completion notifications: Grok Build harness delivers `<system-reminder>` with task ID, duration, exit code
- HTTP rate-limit retry: `pool_test.py:_call_via_http()` (line 503) — retries on 429 with Retry-After header
- PI rate-limit classification: `pi_dispatch.py:_classify_pi_error()` (line 110) — classifies 429 as quota_exhausted (transient)

## Auto-related

- [[skill-graph]]
- [[checkpoint-bundle-skills]]
- [[skill-catalog]]
- [[close-scanner-verification-gap-stale-read]]
- [[scope-matching-verification-discipline]]

