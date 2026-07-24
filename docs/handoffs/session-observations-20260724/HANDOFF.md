---
title: "Session observations 2026-07-24"
session_id: 019f94c9-43c1-7b31-87c4-980fdd3047e8
date: 2026-07-24
status: CLOSED
type: session-observations
---

# Session observations — 2026-07-24

## Major work shipped

- **Model fleet multimodal tags**: all 35 models tagged [T]/[T+I]/[T+I+V]/[T+I+V+A]/[T+I+A] in config.toml
- **Inkling fix**: added max_completion_tokens=16384, resolved serialization error on both HTTP and spawn_subagent paths
- **/tp improvements**: horizon=now domain 5 fix, hybrid session-state carve-out, critique memory (tp_critique_log.py with auto-infer outcomes from git history)
- **model-benchmark overhaul**: quality scoring, cost tracking, parallel execution, multimodal tier, tool-call tier, reliability trend, cli_benchmark.py for agy/codex/mmx
- **AGENTS.md policies**: auto-commit without asking, web_search "last resort only + quota cost", accounting reliability requirement, coverage question triggers
- **Wiki**: multimodal capability filter (46 models), AI thought-partner landscape research

## Key observations

1. **Mistral Medium Latest is the fleet surprise** — fastest on both mechanical (1.1s) and reasoning (1.2s) tiers with perfect quality. Was [T?] unverified; now confirmed [T+I] multimodal.

2. **Zen models pass HTTP but fail spawn_subagent** — zen-deepseek-v4-flash-free and zen-north-mini-code-free both work via direct API but fail Grok's dispatch with "serialization error: missing field `id`". They can't be used as /tp lenses, /check verifiers, or /review specialists.

3. **DiffusionGemma doesn't support tool calling** — the only model that failed the tool-call tier. Diffusion architecture produces different output structure.

4. **GLM-5.2 quality scoring reveals hidden problem** — responds HTTP 200 but content is empty or just thinking tags. Without quality scoring, latency-only benchmarks would hide this. Q=0.0 on both mechanical and reasoning.

5. **NVIDIA NIM serialization bug is fleet-wide** — the `max_tokens: null` → `expected u32` error affects any NIM model without explicit max_completion_tokens in config. Inkling was the first to surface it; Nemotron also had it in spawn_subagent tests.

6. **built-in web_search costs Grok quota** — runs grok-4.20-multi-agent model, not a free API. AGENTS.md updated to "last resort only."

## Seeds for future work

- **model-benchmark telemetry integration**: the telemetry library is ready but no skills actually call log_spawn() yet. Priority targets: /check verifiers, /tp lenses, /review specialists.
- **Quality calibration**: the keyword-based scoring is crude. Could use LLM-as-judge for richer quality assessment on reasoning tier.
- **Zen spawn_subagent fix**: the "missing field id" error might be fixable with a response-format shim or config change. Worth investigating if Zen models are needed as dispatch targets.
- **Cost tracking for paid models**: the pricing table has $0 for all providers since none are paid per-token. When OpenRouter models are tested, the cost data will start populating.
