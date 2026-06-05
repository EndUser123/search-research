---
name: debt
description: Read-only debug view of the JSONL audit log that the Stop hook records when a deferral phrase is detected. Auto-promotion to the task list happens via the UserPromptSubmit hook; this skill exists for inspecting or purging the audit trail. Use when the user invokes /debt list, /debt clear, or /debt list-all.
---

# /debt — review and manage lazy-closure debt

The cc-lazy-closure-debt Stop hook records every untracked deferral phrase
("I'll leave that for now", "we can address that later", etc.) into a per-terminal
JSONL store at `P:/.claude/state/cc-lazy-closure-debt/{terminal_id}.jsonl`.

## Subcommands

- `/debt list` — show all debt items in a table (ts, phrase, age). Default subcommand.
- `/debt clear` — delete the JSONL file for the current terminal.
- `/debt list-all` — show every terminal that has debt (debug only).
- `/debt review` — summarize whether the last supervised workflow should stay local,
  move to a subagent, or be escalated to an external LLM judge.
  The workflow review path also keeps a lightweight per-terminal log so the
  recommendation mix can be inspected in production. The visible stats line
  only appears for `/debt review`.

If no subcommand is given, default to `list`.

## On any subcommand

This skill is **read-only by design**. Deferral phrases are auto-promoted to
the task list by the UserPromptSubmit hook (it injects a `TaskCreate`
directive into the model's context). The JSONL store is now a debug/audit
log; this skill exists to inspect or purge it.

After rendering the table, surface the deprecation note:

> ℹ️ Auto-promotion is now handled by the UserPromptSubmit hook (Phase 1).
> This skill is a debug view of the audit log. To act on a debt item, look
> for it in the task list (it should already be there).

Do NOT call TaskCreate from this skill. Do NOT offer a "press Y to formalize"
prompt. If the user reports that an item is in the audit log but missing
from the task list, that is a hook failure — investigate the
UserPromptSubmit hook chain, do not re-introduce manual formalization.

## List rendering (table)

| ts (UTC) | age | phrase |
|---|---|---|
| 2026-06-01 14:22:11 | 2h ago | "i'll leave that for now" |
| 2026-06-01 09:05:42 | 7h ago | "we can address this later" |

If the same phrase appears multiple times, show `xN` next to the phrase and keep
only one row. This is the deduped taskable view, not the raw append-only log.

Convert `ts` (unix seconds) to a human-readable UTC timestamp. Compute age as
`now - ts` and format as `Xs/Xm/Xh/Xd ago` (reuse the same `_format_age` helper
in `hooks/userpromptsubmit/cc_lazy_closure_debt_UserPromptSubmit.py`).

If the store is empty, print:

```
No deferral items recorded for this terminal. The Stop hook will start
appending entries when you (or your responses) use phrases like
"I'll leave that for now" without an immediate fix.
```

## Clear confirmation

`/debt clear` is destructive — show a one-line confirmation prompt:

```
About to delete N items from P:/.claude/state/cc-lazy-closure-debt/{terminal_id}.jsonl.
Press Enter to confirm, or anything else to abort.
```

Only after confirmation, call the `clear_terminal()` helper from
`__lib/debt_store.py` and report `Cleared N items` (N=0 if no file existed).

## Programmatic helpers

Always import from the plugin's `__lib__` namespace:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("$CLAUDE_PLUGIN_ROOT") / "__lib"))
from debt_store import recent_deferrals, clear_terminal, list_terminals
```

## What this skill does NOT do

- Does not retroactively detect deferrals in past transcripts — only what
  the Stop hook has already recorded.
- Does not block the user. List and clear are pure information/tooling.
- Does not call `claude task add` (that CLI subcommand does not exist).
  Task creation is now auto-prompted by the UserPromptSubmit hook
  (Phase 1) — this skill is a debug view, not a task-creation gateway.
- When reviewing workflow improvements, prefer a subagent for multi-file work,
  an external LLM for comparative or rubric-heavy judgments, and local fixes for
  small repeated debt items.
