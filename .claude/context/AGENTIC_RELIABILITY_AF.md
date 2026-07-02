# Agentic-Reliability Work — A–F Summary

_This is a documentation-only summary commit. The actual implementation is
spread across prior auto-commits because the auto-commit hook fired mid-session.
This file exists so the A–F unit has one descriptive record._

## Scope shipped (A–F)

| Step | What | Key files (in prior auto-commits) |
|------|------|-----------------------------------|
| **A** | Repaired the **dead read-before-edit gate**. Two co-existing bugs made `PreToolUse_existence_gate.py` silently inert: it read top-level `session_id` (real payload nests it under `session.id`), and its `run_read_tracker` was never wired into PostToolUse. Now uses `resolve_session_id`; tracker wired inline in `PostToolUse.py` (the registry skips Read). | `PreToolUse_existence_gate.py`, `PostToolUse.py` |
| **B** | Tests proving the repair against the **real nested payload** (resolve, Read→sidecar, Edit→allow, missing-Read→telemetry + no block), plus a regression guard for the gated block path. | `tests/test_existence_gate_repair.py`, `tests/test_existence_gate.py` |
| **C** | **Telemetry-only rollout**: detect logs + allows by default. Original `sys.exit(2)` block preserved behind `EXISTENCE_GATE_BLOCK=1` for promotion once FP rate is measured. New shared sink `__lib/agentic_reliability_telemetry.py`. | `PreToolUse_existence_gate.py`, `__lib/agentic_reliability_telemetry.py` |
| **D** | **Generated repo map** (`regen_repo_map.py`, reusing `active_hook_inventory.build_inventory`): flat structural inventory — 26 plugins, 81 router-expanded hooks. Outputs `repo_map.generated.{md,json}` + `canonical_paths.generated.md`. | `regen_repo_map.py` |
| **E** | **SessionStart mtime-guarded regen**: auto-discovered hook, skips when outputs are newer than generator + newest manifest. | `SessionStart_repo_map.py` |
| **F** | **Search-before-create telemetry**: logs when a new helper/util/hook/skill file is Written without a prior Grep/Glob in session. Telemetry-only; never blocks. | `PreToolUse_search_before_create.py`, `PreToolUse.py` (dispatch), `PostToolUse.py` (Grep/Glob tracking) |

## Rollout discipline

All gates ship **telemetry-only**. None block by default. The rule:

> Observe first (PreToolUse probes + reliability sink). Block or warn only after
> measured signal shows an acceptable false-positive rate.

Enable telemetry with `AGENTIC_RELIABILITY_TELEMETRY=1`. Promote read-before-edit
to blocking with `EXISTENCE_GATE_BLOCK=1` only after reviewing the
`missing_read` events in `.claude/state/shared/agentic_reliability_telemetry.jsonl`.

## Generated artifacts (gitignored — regenerate locally)

`repo_map.generated.*` and `canonical_paths.generated.md` live under
`.claude/state/shared/` (gitignored). They regenerate on SessionStart when stale,
or via `python .claude/hooks/regen_repo_map.py`. They are intentionally NOT
committed — they are derived, not source.

## Parked — G

Task #1033: extend existing claim/validation gates for two gaps (positive
"registered/exists" structural claims; "not-run" validation claims). Decision
deferred: telemetry probe (low blast, recommended) vs in-place Stop-gate edit
(high blast: model-tier-gated quality machinery). Not started; out of scope for
A–F.

## Verification at ship time

- `tests/test_existence_gate.py` + `tests/test_existence_gate_repair.py`: 22/22 pass.
- Self-checks: `__lib/agentic_reliability_telemetry.py` round-trip; `PreToolUse_search_before_create.py` self-check.
- Dispatch imports: `PreToolUse`, `PostToolUse`, both new probes, `regen_repo_map`, `SessionStart_repo_map` all import clean.
- End-to-end chain smoke (nested payload): Read→sidecar→Edit allow; Grep→sidecar→Write-no-fire; no-search→Write-helper→telemetry.
