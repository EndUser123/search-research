---
title: Dispatch provenance accounting at verdict time
date: 2026-08-10
status: approved
---

# Design: Dispatch provenance accounting

## Problem

The ship-py analysis phases (check, review, refactor, risk, trace, cross-validate) must both prevent specification gaming AND gracefully handle real dispatch failures. The current per-phase provenance gate (shipped) blocks hand-authored fallback findings unless `SHIP_PY_ALLOW_FALLBACK=1`. But it has two gaps:

1. The provenance stamp (`_dispatch_path`) can be forged by writing the field into a hand-authored findings file.
2. Per-phase blocking crashes the pipeline on legitimate dispatch failures (quota, network) with no graceful degradation path.

## Solution: verdict-level dispatch accounting

Instead of (or in addition to) gating per-phase, record which path produced each phase's findings and report it at verdict time. The operator sees the full dispatch/fallback breakdown and decides whether the verdict is acceptable.

### Honest security boundary

Within a single Python process, no provenance stamp is cryptographically unforgeable — the LLM triggers all code execution. The dispatch log is "harder to forge than a JSON field, and transparent at verdict time." It catches lazy specification gaming (writing `_dispatch_path` into findings) and provides operator visibility. It does not catch a determined adversary with full code execution — that's a different threat model.

## Components

### 1. Dispatch log (in try_orchestrator_dispatch)

`try_orchestrator_dispatch` in `dispatch_base.py` appends to `state["_dispatch_log"]` after a successful dispatch (before returning findings to the caller):

```python
import hashlib
from datetime import datetime, timezone

if not response.skipped_reason:
    state.setdefault("_dispatch_log", []).append({
        "phase": phase_name,
        "model": model_receipt.get("model", "unknown"),
        "exit_code": response.exit_code,
        "stdout_hash": hashlib.sha256(
            response.raw_stdout.encode("utf-8")
        ).hexdigest()[:16],
        "invoked_at": datetime.now(timezone.utc).isoformat(),
    })
    # Save state so the log persists
    session_id = state.get("_session_id", "")
    if session_id:
        from phases._shared import save_state
        save_state(session_id, state)
```

This writes the log entry from inside the dispatch path — after `invoke_scan` returns successfully but before the parse function runs. The LLM doesn't directly trigger this write; it's part of the dispatch infrastructure.

### 2. try_orchestrator_dispatch needs state write access

Currently `try_orchestrator_dispatch(state, build_prompt_fn, parse_fn, phase_name)` receives state but doesn't write to it. The change: after successful invoke_scan, append to `_dispatch_log` in state and save.

The session_id comes from `state["_session_id"]` (set by detect phase).

### 3. Verdict phase reads _dispatch_log

The verdict phase (phases/verdict.py) reads `state.get("_dispatch_log", [])` and builds a provenance report:

```python
dispatch_log = state.get("_dispatch_log", [])
dispatched_phases = {entry["phase"] for entry in dispatch_log}
analysis_phases = {"review", "risk", "check", "refactor", "trace", "cross-validate"}

provenance_report = {}
for phase in analysis_phases:
    if phase in dispatched_phases:
        entry = next(e for e in dispatch_log if e["phase"] == phase)
        provenance_report[phase] = f"dispatch (model: {entry['model']})"
    else:
        provenance_report[phase] = "fallback (no dispatch log entry)"

dispatch_count = len(dispatched_phases & analysis_phases)
fallback_count = len(analysis_phases) - dispatch_count
```

### 4. Verdict types

| Condition | Verdict | Meaning |
|-----------|---------|---------|
| All analysis phases have dispatch log entries | SHIP DONE | Full model-verified |
| Some phases used fallback | SHIP VERIFIED (PARTIAL) | Includes which phases and why |
| Any phase missing findings entirely | SHIP BLOCKED | Same as current |

SHIP VERIFIED (PARTIAL) is a new verdict type. Downstream consumers (merge, publish) treat it the same as SHIP VERIFIED — the operator decides whether partial is acceptable. The verdict output makes the breakdown visible:

```
DISPATCH PROVENANCE:
  review:         dispatch (model: nim-openai-gpt-oss-20b)
  risk:           dispatch (model: nim-openai-gpt-oss-20b)
  check:          dispatch (model: nim-openai-gpt-oss-20b)
  refactor:       dispatch (model: nim-openai-gpt-oss-20b)
  trace:          fallback (no dispatch log entry)
  cross-validate: fallback (no dispatch log entry)

Verdict: SHIP VERIFIED (4/6 dispatch-proven, 2/6 fallback)
```

### 5. Interaction with existing provenance gate

The per-phase provenance gate (check_provenance, already shipped) stays in place. It blocks hand-authored fallback findings unless `SHIP_PY_ALLOW_FALLBACK=1`. This is the first line of defense.

The verdict-level accounting is the second line: even if the agent sets `SHIP_PY_ALLOW_FALLBACK=1` (or health-check mode), the verdict still reports which phases ran dispatch vs fallback. The operator sees the full picture at the decision point.

The two layers complement:
- Per-phase gate: prevents the agent from silently using fallback without authorization
- Verdict accounting: reports the authorization usage so the operator can judge the result

## What stays the same

- Fallback path still works (when authorized or health-check mode)
- pi PATH resolution (shipped fix #1)
- Per-phase provenance gate (shipped fix #2)
- All phase cmd_* functions unchanged (they don't need to know about the dispatch log)
- All test assertions unchanged (the dispatch log is additive state)

## Files changed

| File | Change |
|------|--------|
| `dispatch_base.py` | `try_orchestrator_dispatch` writes to `_dispatch_log` after successful invoke_scan |
| `phases/verdict.py` | Reads `_dispatch_log`, builds provenance report, emits verdict type based on dispatch coverage |
| `ship_orchestrator.py` | No change needed (verdict phase already reads state) |
| Tests | New test: verdict with partial dispatch reports SHIP VERIFIED (PARTIAL) |

## Falsifier

This design is wrong if:
- The dispatch log entry can be trivially forged by the LLM (it can — but it's harder than forging a JSON field, and the verdict transparency makes it visible)
- The new verdict type breaks downstream consumers (it won't — SHIP VERIFIED (PARTIAL) is treated same as SHIP VERIFIED by merge/publish)
- The operator doesn't look at the provenance report (possible — but the verdict output makes it the first visible line, not buried in JSON)
