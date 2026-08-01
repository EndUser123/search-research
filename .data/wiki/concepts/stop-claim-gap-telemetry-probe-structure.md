---
title: "Stop_claim_gap_telemetry_probe.py — verified internal structure"
created: 2026-07-20
source: session-2026-07-20
tags: [hook-infrastructure, claim-gap, telemetry, stop-hook, verified-facts, host-internals]
summary: >
  Verified internal structure of P:/.claude/hooks/Stop_claim_gap_telemetry_probe.py —
  the active telemetry-only Stop hook that detects structural/validation claims
  without evidence. Documents the reusable infrastructure (markers, evidence regexes,
  ±2-line window), the non-obvious gaps (probe does NOT read its own rollout env var,
  log_event hardcodes decision="telemetry", dedup key includes marker so different
  markers on the same line produce separate records), and the circular import risk
  when extending it. Verified by direct file inspection 2026-07-20.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
relations:
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: related
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/fabricated-causal-chain-receipt-required
    type: related
---

# Stop_claim_gap_telemetry_probe.py — verified internal structure

## Summary

`Stop_claim_gap_telemetry_probe.py` is the active telemetry-only Stop hook that
detects structural and validation claims without evidence. It has reusable
infrastructure (markers, evidence regexes, ±2-line window) that future extensions
can build on. It also has three non-obvious gaps that any extension must account
for: it does NOT read its own rollout env var, its `log_event` call hardcodes
`decision="telemetry"` regardless of escalation, and its dedup key includes the
marker name so different markers on the same line produce separate records.

## Key Findings (all verified by direct file inspection 2026-07-20)

### File stats

- **Total lines: 371** (verified via `splitlines()` and `(Get-Content).Count`)
- **Non-empty lines: 325** (verified via `Measure-Object -Line`)
- **WARNING: `Measure-Object -Line` counts non-empty lines, NOT total lines.**
  Do not use it to report total line count. Use `.Count` or `splitlines()`.
  This caused a wrong "correction" (371 → 325) in a design review this session —
  see [[plausible-narratives-substitute-for-verification]] Disguise 7.

### Registration in Stop.py

- **Import:** `Stop.py:176` — `from Stop_claim_gap_telemetry_probe import run as _run_claim_gap_telemetry_probe`
- **Gate registration:** `Stop.py:4288` — `("claim_gap_telemetry_probe", _run_claim_gap_telemetry_probe)` in `IN_PROCESS_GATES`
- **Metadata:** `Stop.py:4190` — declares `"rollout_mode": RolloutMode.ADVISORY` (metadata-only; see gap #1 below)

### Reusable infrastructure (all in the probe file)

| Component | Purpose | Approximate line |
|-----------|---------|-----------------|
| `_STRUCTURAL_MARKERS` | Phrases like "is registered", "is wired", "safe to delete" | ~54 |
| `_VALIDATION_MARKERS` | Phrases like "tests pass", "is verified", "is fixed" | ~68 |
| `_HEDGE_PHRASES` | Suppresses telemetry on "not verified", "assumption", "unverified" | ~100 |
| `_PATH_LIKE` / `_COMMAND_LIKE` / `_CITATION` / `_FIRST_PERSON_ACTION` | Evidence regexes: path-like tokens, command tokens, citations, action verbs | ~142 |
| `_window_lines(text, idx, before=2, after=2)` | ±2-line window around each detected claim | ~166 |
| `_line_has_evidence(line)` | Returns True if line contains an evidence token (path, command, citation, action verb) | ~174 |
| `_scan_marker` | Iterates markers, detects matches per line, checks evidence in window | ~184 |
| `find_claim_gaps` | Orchestrates scan across all marker types, deduplicates results | ~230 |
| `_has_tool_verification_evidence(data)` | Checks if the tool transcript contains verification evidence (pytest, grep, etc.) | ~267 |
| `run(data)` | Main entry point — scans response, emits telemetry, returns warn/block decision | ~287 |
| Phase 2 promotion | Returns `{"decision": "warn"}` when `has_validation_gap and not _has_tool_verification_evidence` | ~333 |

### Gap #1: probe does NOT read any env var

The probe's `run()` function does **not** read `STOP_GATE_ROLLOUT_CLAIM_GAP_TELEMETRY_PROBE`
or any other env var. Grep for `STOP_GATE_ROLLOUT`, `_get_rollout_mode`, `os.environ`
against the probe file returns **zero matches**. The metadata at `Stop.py:4190`
declares `RolloutMode.ADVISORY` but this is metadata-only — nothing in the probe's
code consults it. The env var is also not set anywhere in `settings.json`.

**Implication for extensions:** if you want rollout-mode-aware behavior (shadow →
advisory → block staging), you must add the env-var read yourself. The canonical
convention is `STOP_GATE_ROLLOUT_<NAME>` at `Stop.py:3724-3734` (`_get_rollout_mode`).
Values: `shadow` / `advisory` / `disabled` / `block` / `on`.

### Gap #2: `log_event` hardcodes `decision="telemetry"`

At line 318, the `log_event` call uses `decision="telemetry"` unconditionally.
The escalation decision (`{"decision": "warn", ...}`) is returned from `run()`
separately — it goes to the LLM as a `systemMessage` but the telemetry sink
records `decision="telemetry"` for every gap regardless of escalation.

**Implication for metrics:** filtering `agentic_reliability_telemetry` by
`decision="warn"` will match zero records. Either change the `log_event` call
to pass the actual escalation decision, or filter by a different field.

### Gap #3: dedup key includes marker name

At line ~250, the dedup key is `(c["claim_text"].lower(), c["marker"])`. Because
the marker name is part of the key, **different markers on the same line do NOT
deduplicate**. A line containing `"stub-quality"` produces 2 gap records if both
`"stub"` and `"stub-quality"` are in the markers list. Sorting longest-first
does NOT fix this — you need per-line matching with `break` after first match.

### `stop_blocks.jsonl` only logs blocks

`_log_stop_block_event` at `Stop.py:289-310` is the function that persists Stop
decisions to `stop_blocks.jsonl`. Verified: it only uses `action="block"`.
Warn decisions are NOT persisted to `stop_blocks.jsonl` — they go to the LLM as
`systemMessage` but do not enter the canonical block log.

**Implication for metrics:** do not filter `stop_blocks.jsonl` for warn-rate
metrics. Use `agentic_reliability_telemetry` instead.

### Circular import risk

`Stop.py:176` imports the probe at module-load time. If the probe imports back
from `Stop.py` (e.g., `from Stop import _get_rollout_mode`), the import chain
becomes circular. **Fix:** re-implement the needed helper locally in the probe
(e.g., read `os.environ.get("STOP_GATE_ROLLOUT_CLAIM_GAP_TELEMETRY_PROBE", "advisory")`
directly) rather than importing from `Stop.py`.

### `CATEGORIES` constant is documentation, not enforcement

`__lib/agentic_reliability_telemetry.py` has a `CATEGORIES` frozenset for
discoverability/tests. It does NOT include `"claim_gap_telemetry"`. But the sink
accepts arbitrary category strings — the probe uses `"claim_gap_telemetry"` at
line 313 without issue. The constant is advisory; the sink is untyped.

## Related

- [[plausible-narratives-substitute-for-verification]] — the cognitive pattern this hook detects
- [[external-state-cross-check-as-structural-fix]] — the design pattern for extending this hook structurally
- [[fabricated-causal-chain-receipt-required]] — the receipt-required defense this hook partially implements

## Sources

- Session 2026-07-20 — design loop for closing the exploration-failure loop (4 review rounds)
- Direct file inspection: `P:/.claude/hooks/Stop_claim_gap_telemetry_probe.py`, `P:/.claude/hooks/Stop.py`, `P:/.claude/hooks/__lib/agentic_reliability_telemetry.py`
- Design artifacts: `C:/Users/brsth/.grok/design-runs/grok-design-43e11106/`
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
