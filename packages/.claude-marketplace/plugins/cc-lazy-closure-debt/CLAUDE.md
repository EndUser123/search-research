# cc-lazy-closure-debt

Deferral auto-promotion plugin PLUS gate-FP feedback loop (Phase 1+2, 2026-06-03;
Phase 4, 2026-06-19; Phase 5 / Gate Residue v1, 2026-07-10).

**Mission (updated)**: (1) Detect untracked deferral phrases and auto-promote
them to tasks. (2) Surface Stop-hook gate blocks as "residue" so the model
can identify false positives and the developer can inspect the FP rate.

The Stop hook detects untracked deferral phrases ("I'll leave that for now",
"we can address that later", etc.) via the shared `lazy_closure_detector` in
cc-aca-epistemic and appends them to a per-terminal JSONL audit log.
The UserPromptSubmit hook reads that log and injects a `TaskCreate` directive
so each deferral lands in the real task list on the next turn. The PostToolUse
hook watches for `TaskCreate(subject="Deferral: <phrase>")` and appends a
tombstone so the deferral stops re-surfacing after it has been formalized.

**Gate residue (Phase 5 v1)**: The same UserPromptSubmit hook also ingests new
Stop-block rows from `diagnostics.db` and `stop_blocks.jsonl` (incrementally,
by watermark), classifies them against the current turn's transcript, and emits
TaskCreate directives for confirmed_FP blocks. Scope: Stop blocks only
(PreToolUse is a documented v2 gap — they are NOT in diagnostics.db).
Dispatch is via `__lib/router.py` registered in `settings.json` (not hooks.json).

## Responsibility

- **Stop hook** detects deferral phrases via the shared detector and
  appends JSONL lines to the audit log. Never blocks; the detector in
  cc-aca-epistemic already surfaces the user-facing message.
- **UserPromptSubmit hook** reads the JSONL audit log, filters to items
  newer than 24h, dedupes by fingerprint, and emits a directive that
  prompts the model to call `TaskCreate` (one per unique phrase) on the
  next turn. After auto-promotion, the detector's
  `DEFERRAL_TRACKING_MARKERS` exemption prevents the same phrase from
  re-firing the same turn.
- **/debt skill** is a read-only debug view: list, clear, list-all.
  It does NOT call `TaskCreate` (that path was removed in Phase 2).
  The "Press Y to formalize" prompt has been deleted from the skill.
- **Workflow review** can summarize whether the last supervised turn is
  better handled locally, by a subagent, or by an external LLM review.
  It appends a lightweight per-terminal review log so production
  frequency can be inspectable without changing the task flow. The
  visible stats line is opt-in and only appears for `/debt review`.

## Phase History

- **Phase 1 (2026-06-03)**: UserPromptSubmit hook now injects a
  `TaskCreate` directive on the next turn, replacing the manual
  `Run /debt to formalize` flow. Audit log is preserved verbatim.
- **Phase 2 (2026-06-03)**: `/debt` skill demoted to a read-only debug
  view. The `Press Y to formalize` prompt is gone; the skill no
  longer offers to create tasks.
- **Phase 3 (2026-06-03)**: Plugin description and CLAUDE.md updated
  to match the new scope. A future rename (e.g. to
  `cc-deferral-to-task`) is a follow-up if/when the name is causing
  real confusion; it has cross-system blast radius (marketplace,
  hooks.json, any docs that grep for the old name) and is deferred.
- **Phase 4 (2026-06-19)**: Tombstone mechanism added to break the
  duplicate-task loop. PostToolUse hook watches `TaskCreate` with
  "Deferral: " subject and writes a tombstone fingerprint so
  `recent_deferrals()` filters that phrase permanently. Dispatch
  migrated from `hooks.json` to `__lib/router.py` + `settings.json`
  (router-XOR-hooks.json invariant; `hooks/hooks.json` stays `{"hooks": {}}`).
- **Phase 5 — Gate Residue v1 (2026-07-10)**: `__lib/gate_residue.py`
  added. UserPromptSubmit hook now ingests Stop-block rows, classifies
  them as `confirmed_fp`/`disputed`/`unresolved`, and emits a separate
  `TaskCreate` directive for confirmed-FP blocks (one-shot per ledger_id
  via tombstone). Scope: Stop blocks only; PreToolUse blocks are NOT in
  diagnostics.db and are a documented v2 gap. The plugin name
  (`cc-lazy-closure-debt`) no longer captures the full scope (which is now
  BOTH deferral debt AND gate-denial residue), but renaming it at this
  point has cross-system blast radius (marketplace, hooks.json,
  settings.json, docs) and is deferred.

## Hooks

| Hook | Lifecycle | Purpose |
|------|-----------|---------|
| `hooks/stop/cc_lazy_closure_debt_Stop.py` | Stop | Detect deferrals, append JSONL |
| `hooks/userpromptsubmit/cc_lazy_closure_debt_UserPromptSubmit.py` | UserPromptSubmit | Surface recent items as context |
| `hooks/posttooluse/cc_lazy_closure_debt_PostToolUse.py` | PostToolUse | Tombstone deferrals when TaskCreate fires |

## Dispatch

All three hooks are dispatched via `__lib/router.py`, registered in
`C:/Users/brsth/.claude/settings.json` under Stop, UserPromptSubmit, and
PostToolUse event groups (matcher `.*`, timeout 10). The source
`hooks/hooks.json` is `{"hooks": {}}` and must stay empty — the
router-XOR-hooks.json invariant means populating both causes double-dispatch.

## Library

- `__lib/debt_store.py` — `append_deferral()`, `recent_deferrals()`,
  `clear_terminal()`, `list_terminals()`. Pure JSONL I/O with fsync.
- `__lib/workflow_review.py` — workflow classification, review-log append,
  and recent recommendation summary helpers.
- `__lib/gate_residue.py` — gate-FP feedback loop: incremental ingestion from
  `diagnostics.db` + `stop_blocks.jsonl`, `classify_block()`, `recent_residue()`,
  `mark_promoted()`, `promoted_ledger_ids()`. Scope: Stop blocks only. v1.

## Skill

- `skills/debt/SKILL.md` — `/debt list`, `/debt clear`, `/debt list-all`.
  Always offers "Press Y to formalize these as tasks now" before any
  TaskCreate call.

## State Paths

Default: `P:/.claude/state/cc-lazy-closure-debt/{terminal_id}.jsonl`

Review log: `P:/.claude/state/cc-lazy-closure-debt/workflow-reviews/{terminal_id}.jsonl`

Override via env var `CC_LAZY_CLOSURE_DEBT_STATE_DIR` (used by tests).

## Architecture

- **Detector import is canonical**: Stop hook imports `detect_lazy_closure`
  from `cc-aca-epistemic.__lib.anti_sycophancy.lazy_closure_detector`.
  No pattern list duplication.
- **Pattern scope**: this plugin persists ONLY `pattern_type == "deferral"`.
  Other lazy-closure types (lazy_justification, sycophancy_capitulation,
  etc.) are still flagged by the upstream detector but are NOT recorded
  as "debt" — they are different kinds of failures.
- **Deduped view**: repeated matches of the same phrase are grouped into a
  single taskable item with an occurrence count, so the same debt does not
  spawn duplicate follow-up tasks.
- **Tombstone resolution**: `resolve_deferral(terminal_id, fingerprint)` and
  `resolve_deferral_by_phrase(terminal_id, phrase)` in `debt_store.py` append
  a `{"kind": "tombstone", "resolved_fingerprint": "<fp>"}` record to the
  same JSONL. `recent_deferrals()` collects all tombstone fingerprints on
  read and filters matching deferrals before returning. Append-only, so
  concurrent Stop-hook writes never race. Tombstones are honored regardless
  of age — a resolved phrase never re-surfaces even if its deferral record
  is still within the 24h window.

## Tests

`tests/test_debt_store.py` covers the store layer (round-trip, filtering,
truncation, isolation, clear, and tombstone resolution via `TestResolve`).
`tests/test_stop_hook.py` and `tests/test_userpromptsubmit.py` cover the
hook layers with mocked dependencies so they are hermetic. The PostToolUse
hook bootstrap chain is verified by smoke test (subprocess invocation with
a `TaskCreate` payload confirms exit 0 + tombstone written + 0 deferrals
after).
