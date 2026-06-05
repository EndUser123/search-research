# cc-lazy-closure-debt

Persistent technical-debt tracker built on the cc-aca-epistemic lazy_closure
detector. Records untracked deferral phrases ("I'll leave that for now",
"we can address this later", etc.) to a per-terminal JSONL store, then
surfaces them as `additionalContext` on the next prompt so the model is
aware of untracked debt from previous turns.

## Responsibility

- **Stop hook** detects deferral phrases via the shared detector and
  appends JSONL lines to the debt store. Never blocks; the existing
  detector in cc-aca-epistemic already surfaces the user-facing message.
- **UserPromptSubmit hook** reads the JSONL store, filters to items
  newer than 24h, and emits a compact "You have N pending deferral items
  from previous turns" message as `additionalContext`.
- **/debt skill** lists, clears, and (on explicit user Y) formalizes
  items as tasks via the TaskCreate tool.
- **Workflow review** can summarize whether the last supervised turn is
  better handled locally, by a subagent, or by an external LLM review.
  It also appends a lightweight per-terminal review log so production
  frequency can be inspected without changing the task flow. The visible
  stats line is opt-in and only appears for `/debt review`.

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
