# cc-lazy-closure-debt

Deferral auto-promotion plugin (Phase 1+2, 2026-06-03). The Stop hook
detects untracked deferral phrases ("I'll leave that for now", "we can
address that later", etc.) via the shared `lazy_closure_detector` in
cc-aca-epistemic and appends them to a per-terminal JSONL audit log.
The UserPromptSubmit hook reads that log and injects a `TaskCreate`
directive so each deferral lands in the real task list on the next turn.
The JSONL is now a debug/audit log, not a user-facing concept.

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
- **Phase 3 (this change)**: Plugin description and CLAUDE.md updated
  to match the new scope. A future rename (e.g. to
  `cc-deferral-to-task`) is a follow-up if/when the name is causing
  real confusion; it has cross-system blast radius (marketplace,
  hooks.json, any docs that grep for the old name) and is deferred.

## Hooks

| Hook | Lifecycle | Purpose |
|------|-----------|---------|
| `hooks/stop/cc_lazy_closure_debt_Stop.py` | Stop | Detect deferrals, append JSONL |
| `hooks/userpromptsubmit/cc_lazy_closure_debt_UserPromptSubmit.py` | UserPromptSubmit | Surface recent items as context |

## Library

- `__lib/debt_store.py` — `append_deferral()`, `recent_deferrals()`,
  `clear_terminal()`, `list_terminals()`. Pure JSONL I/O with fsync.
- `__lib/workflow_review.py` — workflow classification, review-log append,
  and recent recommendation summary helpers.

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
- **No subprocess for task creation**: the prior design called
  `claude task add` as a subprocess. That CLI subcommand does not exist.
  The skill's "formalize as tasks" path uses the TaskCreate tool only
  after explicit user confirmation.

## Tests

`tests/test_debt_store.py` covers the store layer (round-trip, filtering,
truncation, isolation, clear). `tests/test_stop_hook.py` and
`tests/test_userpromptsubmit.py` cover the hook layers with mocked
dependencies so they are hermetic.
