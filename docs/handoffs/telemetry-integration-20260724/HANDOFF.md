---
thread_id: a7c1f2e3-8b4d-4e9a-b6f1-3c2d4e5f6a7b
parent_handoff_path: none
current_session_id: 019f94c9-43c1-7b31-87c4-980fdd3047e8
current_terminal_id: console_9d8ef5b2-9187-4432-a2a8-47ce
produced_at: 2026-07-24T17:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 356f255
---

# Telemetry integration into skills

## Objective

Wire `log_call()` / `log_spawn()` from the model-benchmark telemetry library into the skills that dispatch subagents or make direct model API calls. This is the #1 priority from AAR 019f94c9 — the benchmark and telemetry infrastructure is built (commit `756ec4c`) but no skills feed it live data yet. Without this, the routing decisions that depend on per-model latency/quality/cost data have no empirical basis.

## Context

The telemetry library at `~/.grok/skills/model-benchmark/scripts/telemetry.py` provides two functions:

```python
import sys
sys.path.insert(0, r"C:\Users\brsth\.grok\skills\model-benchmark\scripts")
from telemetry import log_call, log_spawn

log_call(model="minimax-m3", provider="minimax",
         task_domain="code-verification", latency_ms=1234, success=True,
         caller="/check verifier", quality_score=0.8, cost_usd=0.0)
```

Data accumulates at `P:/.artifacts/model-telemetry/usage.jsonl`. Analysis via `python ~/.grok/skills/model-benchmark/scripts/analyze.py`.

## Priority integration targets

1. **`/check` verifiers** — `P:/.grok/skills/check/` — log each verifier spawn with `log_spawn(model=<slug>, task_domain="verification", ...)`
2. **`/tp` critique lenses** — `~/.grok/skills/tp/SKILL.md` Step 2 — log each spawn_subagent pool attempt with `log_spawn(model=<slug>, task_domain="critique", ...)`
3. **`/review` specialists** — `~/.grok/skills/review/` — log each specialist spawn
4. **`/go` H4 parallel waves** — log each implementation/test/critic subagent
5. **DiffusionGemma direct API scripts** — `P:/.agents/scripts/models/dgemma_read.py` — already logs via benchmark; verify it uses the new `quality_score` and `cost_usd` fields

## What NOT to do

- Don't add telemetry to every single model call — only skills that dispatch subagents or make multi-model API calls
- Don't block on telemetry failures — wrap in try/except so a logging error never blocks the skill
- Don't log the parent (inherited) model — only explicit model selections

## Status

OPEN — not started

## Evidence

- Telemetry library: `~/.grok/skills/model-benchmark/scripts/telemetry.py` (commit `756ec4c`)
- Benchmark scripts: `~/.grok/skills/model-benchmark/scripts/benchmark.py` (quality + cost + parallel + multimodal + tool-call)
- CLI benchmark: `~/.grok/skills/model-benchmark/scripts/cli_benchmark.py` (agy/codex/mmx)
- Analyze script: `~/.grok/skills/model-benchmark/scripts/analyze.py` (cost + trend + temporal)
- Session observations: `P:/docs/handoffs/session-observations-20260724/HANDOFF.md`
- AAR report: `P:/.artifacts/console_9d8ef5b2/grok-aar/20260724-165010/AAR_REPORT.md`

## Read first

- `~/.grok/skills/model-benchmark/SKILL.md` — the telemetry data model and integration plan
- `~/.grok/skills/model-benchmark/scripts/telemetry.py` — the `log_call` / `log_spawn` API
- `P:/.data/wiki/concepts/model-fleet-provider-pools.md` — the fleet inventory + multimodal tags

## Next steps

1. Start with `/tp` Step 2 — it's the simplest integration (one `log_spawn` call after the pool selection)
2. Then `/check` verifiers — wrap each `spawn_subagent` call
3. Then `/review` specialists — wrap each specialist dispatch
4. After 1 week of accumulated data, run `analyze.py --trend` to see if patterns emerge

## Falsifier

If after integration the telemetry data shows <10 entries per model after a full week of active use, the integration is too shallow — skills aren't actually calling the logging functions. Check whether the `import telemetry` path resolves correctly from each skill's working directory.
