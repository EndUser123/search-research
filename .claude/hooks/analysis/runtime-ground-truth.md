# Runtime Ground Truth — freshness-ruled verified facts

**Status:** Phase 2 deliverable, Close-the-Loop batch (2026-07-07).
**Purpose:** Inject a small, explicit set of session-start verified facts that the
model can cite without re-fetching (paths, IDs, manifest contracts). Each fact
is paired with a `verification_command` and `last_verified` date; if a fact
goes stale past its `expiry_trigger`, it renders as
`[STALE — reverify: <cmd>]` rather than being dropped or silently trusted.

**Injection surface:** `cc-aca-session` SessionStart router (entry
`aca_session_ground_truth_inject.py`), pending HARD PAUSE before router.py
registration (Rule 4b).

**Cumulative injection budget:** protected slots — `ground_truth` + the
existing `mechanism_manifest` UPS injector render in full; if other injectors
would push total > budget, recall/segment content truncates first. See
`runtime_ground_truth.py::BUDGET_PROTECTED_CHARS`.

## Schema (per row)

| Column | Meaning |
|--------|---------|
| fact | The short claim injected to the model |
| source | Where the fact was first asserted (file:line, doc, prior verification) |
| verification_command | Re-runnable command that proves the fact right now |
| last_verified | ISO date the verification was last run |
| expiry_trigger | When this fact must be re-verified (event or elapsed time) |

## Rows

| fact | source | verification_command | last_verified | expiry_trigger |
|------|--------|----------------------|---------------|----------------|
| Gold corpus canonical path = `P:/.data/evals/` | close-the-loop-plan.md verified-facts block (relocation 2026-07-07) | `ls P:/.data/evals/ && ls P:/.data/evals/gold/` (4 fixtures + 3 .py + misses.jsonl) | 2026-07-07 | any `evals/` relocation — re-run manifest check + update this row + the verified-facts block |
| Append-only block log = `P:/.claude/hooks/logs/diagnostics/stop_blocks.jsonl` | close-the-loop-plan.md verified-facts block | `ls -la P:/.claude/hooks/logs/diagnostics/stop_blocks.jsonl` | 2026-07-07 | log rotation or path change |
| CC-aca-session dispatches SessionStart via `__lib/router.py` | cc-aca-session router.py line 25 (DISPATCH dict) | `grep -n "DISPATCH" P:/packages/.claude-marketplace/plugins/cc-aca-session/__lib/router.py` | 2026-07-07 | router.py rewritten, or plugin splits into multiple dispatchers |
| Hook state directory = `P:/.claude/state/` | aca_state_paths.get_state_dir() (P:/packages/.claude-marketplace/plugins/cc-aca-session/__lib/aca_state_paths.py:42) | `python -c "import sys; sys.path.insert(0,'P:/packages/.claude-marketplace/plugins/cc-aca-session/__lib'); from aca_state_paths import get_state_dir; print(get_state_dir())"` | 2026-07-07 | env-var override or path relocation |
| Knowledge cutoff for THIS Claude session = 2026-01 | model_id `claude-sonnet-4-6` family (system identity) | `date` (today is 2026-07-07; 6mo drift → re-baseline facts) | 2026-07-07 | calendar 2027-01 (12mo; then check whether model family changed) |
| Today is 2026-07-07 | `<system-reminder>` `currentDate` field | n/a — system-provided at session start | 2026-07-07 | next session start (re-emitted by harness) |