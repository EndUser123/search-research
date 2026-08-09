---
title: Orchestrator-controlled analysis phases in ship-py
title_short: orchestrator-controlled-ship-py-phases
date: 2026-08-09
verified_date: 2026-08-09
tags: [ship-py, orchestration, anti-fabrication, pipeline-design]
host: both
---

# Orchestrator-controlled analysis phases in ship-py

## The pattern

All 6 analysis phases in ship-py's 20-phase pipeline are now orchestrator-controlled:
the Python orchestrator (NOT the LLM) spawns a cross-family model via `pi` subprocess,
captures structured JSON output, and writes findings FROM that output. The LLM is
removed from the evidence-production path.

| Phase | Dispatch module | Lane | Gate |
|-------|----------------|------|------|
| cross-validate | validator_dispatch.py | critic | disputed ≥1 → BLOCK-eligible |
| risk | risk_dispatch.py | critic | HIGH + irreversible → BLOCK |
| check | check_dispatch.py | critic | verdict=FAIL → BLOCK |
| review | review_dispatch.py | critic | all agents failed → BLOCK |
| refactor | refactor_dispatch.py | critic | P0 (silent data loss) → BLOCK |
| trace | trace_dispatch.py | critic | logic-error → BLOCK |

Only **fix** remains as a pause phase — it requires creative bug-fixing, not analysis.

## Why this exists

The original pause-phase pattern depended on the LLM choosing to run the skill.
The pipeline phases were recording stubs: they read findings files that the LLM
was supposed to produce by running /check, /review, /risk, /refactor, or /trace.
In practice, the LLM frequently skipped the skill invocation and either:

1. Wrote empty/stub findings JSON manually (specification gaming)
2. Left the phase incomplete, stalling the pipeline
3. Produced findings without the rigor the standalone skill provides

The gap was demonstrated empirically: standalone `/risk` found 8 real findings on
a diff, while the pipeline risk phase found zero because the LLM never ran /risk.

## How it works

Each dispatch module follows the same 4-function pattern:

```
select_*_model()          → pick_model.py receipt (critic lane, cross-family)
build_*_prompt(state)     → structured prompt with diff summary
invoke_*_scan(prompt)     → pi subprocess (temp-file for shell-quoting safety)
parse_*_response(raw)     → JSON extraction (markdown-fence stripping, regex fallback)
```

Each `cmd_*` phase function:
1. Tries orchestrator dispatch first (`_try_orchestrator_*_scan`)
2. Falls back to findings file if dispatch fails (`_try_findings_file`)
3. Gates on the findings content (not schema — orchestrator output may vary)
4. Fails-open: dispatch failures don't block, they fall back

The fail-open fallback preserves backward compatibility with the pause-phase
pattern. If `pi` is unavailable, quota is exhausted, or the model is unresolvable,
the phase falls back to reading a findings file that the LLM can write manually.

## Anti-fabrication guarantee

The orchestrator stamps receipt fields (`_risk_model`, `_check_dispatch_path`,
etc.) from the `pick_model.py` receipt, NOT from the model's JSON output. This
prevents model-name spoofing. The findings content comes from the model's stdout,
which the LLM cannot influence — the LLM never sees the prompt or the response.

## Alternatives considered

1. **Remove pause phases entirely** (no fallback) — rejected: breaks backward
   compatibility and removes the safety net when pi is unavailable.

2. **Independent verification feature flag** (`SHIP_PY_VERIFY_FINDINGS=1`) —
   deferred: would spawn a second model after any phase writes findings to check
   plausibility. Not needed now that all phases produce orchestrator-verified
   findings.

## Reference

- Commit history: `git log --oneline -- ~/.grok/skills/ship-py/__lib/*_dispatch.py`
- Pattern origin: `[[orchestrator-controlled-cross-model-validation-ship-py]]`
- Design decision: `[[specification-gaming-in-llm-agent-pipelines]]`
- Related: `[[making-llm-agents-honestly-execute-skills-solution-stack]]`
