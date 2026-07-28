---
title: "PostToolUse fires on tool-call completion, not process completion — auto-backgrounded commands skip receipts"
created: 2026-07-28
source: session-2026-07-28
tags: [hooks, PostToolUse, auto-background, verification, receipt, grok-build, timeout]
summary: >
  Grok Build's PostToolUse hook fires when the tool call itself completes
  (returns a result), NOT when a backgrounded process finishes. When
  run_terminal_command auto-backgrounds a command (exceeds 120s default
  timeout), the tool call "completes" immediately by returning a task ID.
  PostToolUse fires at that point with incomplete output. The actual pytest
  exit code and output arrive later via get_command_or_subagent_output —
  but no second PostToolUse fires. Fix: pass timeout=180000+ to keep
  commands foreground (behavioral), OR use a Stop hook with
  backgroundTasks awareness (structural — Notification event is
  metadata-only and cannot capture exit codes).
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://docs.x.ai/build/features/hooks (xAI, 2026-07-24)
  - https://github.com/asgeirtj/system_prompts_leaks/blob/main/xAI/grok-build.md (System prompt leak, 2026-07)
  - https://github.com/anthropics/claude-code/issues/65169 (PostToolUse does not fire for Agent completions)
  - https://github.com/anthropics/claude-code/issues/23386 (Expose background tasks to hooks — closed)
  - https://github.com/anthropics/claude-code/issues/52917 (claude -p exits before background subagents complete)
  - https://code.claude.com/docs/en/hooks (Notification payload is metadata-only)
  - https://code.claude.com/docs/en/hooks-guide (Agent-based hooks pattern)
  - https://ona.com/guides/background-agents (Production verification patterns)
relations:
  - target: wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md
    type: extends
  - target: wiki/concepts/built-in-grep-tool-over-shell-ripgrep-for-wiki-search.md
    type: related
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: complements
---

# PostToolUse fires on tool-call completion, not process completion

## Decision context

**Why this research was needed:** Session 2026-07-28 spent significant
effort trying to make the verification receipt writer capture pytest
results. The `_parse_exit_code` function was fixed to infer exit codes
from "59 passed" patterns. But receipts were still never written for
pytest commands — because the PostToolUse hook fires BEFORE pytest
finishes, not after.

**The problem:** `run_terminal_command` with default timeout (120s)
auto-backgrounds commands that exceed it. But even commands that finish
in 16-20s get auto-backgrounded by the tool wrapper if they exceed a
shorter internal default. When auto-backgrounded, the tool call returns
immediately with a task ID. PostToolUse fires at that moment — the
`toolResult` contains "automatically moved to background", not the test
output. The receipt writer sees no exit code and skips writing.

## The mechanism (documented behavior)

From the Grok Build hooks documentation and system prompt:

| Situation | When PostToolUse fires |
|-----------|----------------------|
| Foreground command (runs to exit) | After the command finishes |
| Auto-backgrounded or `background: true` | Right after launch (task ID returned) |
| Real process exit later | **No second PostToolUse** — completion is a separate notification/task path |

This is **expected behavior**, not a bug. PostToolUse is a tool-call
lifecycle event, not a process lifecycle event. This relates to
[[grok-build-stop-hook-patterns-and-feedback-mechanism]] and
[[hook-evidence-collection-cost-vs-timeout-tradeoff]] — both document
the tension between hook timing and evidence capture.

## What this means for verification receipts

The verification receipt writer (`verification_receipt_writer.py`) is a
PostToolUse hook that reads `toolResult` to determine exit codes and
write receipts. For auto-backgrounded commands:

1. PostToolUse fires → `toolResult` = "automatically moved to background"
2. Receipt writer calls `_parse_exit_code("automatically moved to background")` → returns `None`
3. Receipt writer skips: `exit_code is None → don't write receipt`
4. pytest finishes 16s later → model calls `get_command_or_subagent_output` → gets results
5. No PostToolUse fires for the completion → receipt never written

**The `_parse_exit_code` fix (inferring from "N passed") is correct but
irrelevant** — the function never receives pytest output because the
hook fires before pytest produces output.

## The fix

### Option 1: Keep commands foreground (simplest)

Pass a high `timeout` parameter so the tool call doesn't auto-background:

```
run_terminal_command(command="python -m pytest ...", timeout=180000)
```

With `timeout=180000` (3 minutes), pytest runs in foreground, PostToolUse
fires after completion with the real output, and the receipt writer can
parse the exit code.

**Limitation:** the timeout parameter is on the `run_terminal_command`
tool call, which the LLM controls. If the LLM forgets to set it, the
default 120s applies and auto-backgrounding can still happen.

### Option 2: ~~Notification hook~~ (WRONG — metadata-only payload)

**Research finding (2026-07-28 /www run):** the `Notification` event
payload is **metadata-only** — it carries `message`, `title`, and
`notification_type` (Claude Code) or `kind`, `title`, `body` (Grok
Build). It does NOT include structured exit codes, test results, or task
output. Background-task completion appears as a human-readable message
string like "Background command '...' completed (exit code 0)", which a
hook would have to regex-parse from the message text — not a reliable
contract for a verification receipt.

The `Notification` event is designed for side effects (desktop alerts,
Slack webhooks, logging), not for capturing verification data. Both
Claude Code and Grok Build follow this model. Using it for receipt
capture would be a fragile hack, not a structural fix.

### Option 3: Stop hook with `backgroundTasks` awareness (OPTIMAL structural fix)

The Stop hook input already carries a `backgroundTasks` array (documented
at `~/.grok/docs/user-guide/10-hooks.md:270`):

```json
{
  "hookEventName": "stop",
  "backgroundTasks": [
    {"id": "...", "type": "shell", "status": "running", "command": "python -m pytest ..."}
  ],
  "sessionCrons": [...]
}
```

A Stop hook can:
1. Check if any `backgroundTasks` entry has `status: "running"` — if so, block with "background task still running"
2. When all tasks complete (or after the 8-continuation cap), read the completion data via `get_command_or_subagent_output`
3. Write the verification receipt at that point

**This is the structural fix.** It uses an existing event (Stop, which
is already registered) and an existing payload field (`backgroundTasks`).
No new infrastructure needed — just a hook script that reads the field.

**Related pattern — Claude Code Agent-based hooks:** Claude Code supports
`type: "agent"` hooks that spawn a subagent (up to 50 tool-use turns) to
independently verify conditions before allowing stop. The shipped example
is literally "verify all unit tests pass before allowing Claude to stop."
This is the most powerful verification pattern: an independent subagent
runs the actual check and produces a receipt, rather than relying on the
main agent's self-report. Grok Build does not yet have `type: "agent"`
hooks (only `command` and `http`), but the Stop + backgroundTasks
approach achieves a similar result.

### Option 4: Marker file + Stop hook (fallback)

The backgrounded command writes a marker file when done. The Stop hook
reads marker files and writes receipts. Requires modifying the command
to write markers — not practical for arbitrary pytest invocations.

## Industry context (2026-07-28 /www research)

This is a **well-documented, unsolved problem** across the AI agent
ecosystem:

| Source | Finding |
|--------|---------|
| Claude Code #65169 | "PostToolUse hook does not fire for Agent tool completions" — closed-as-not-planned |
| Claude Code #23386 | Feature request: expose running background tasks to hooks — closed-as-not-planned |
| Claude Code #52917 | `claude -p` exits before background subagents complete — closed-as-not-planned |
| Claude Code #55754 | Stop hook causes infinite loop when waiting on background agent |
| Claude Code #7282 | Background task result lost after compaction / 5-hour limit |
| Claude Code #65925 | Audit-event-source pattern — parallel event log when harness state machine is opaque |
| Mastra framework | Proper event-stream lifecycle (started/running/completed/failed chunks) — the model approach |
| Harvey Spectre | "The durable record is the run, not the agent" — run record IS the receipt |
| Ona (Stripe/Ramp) | "Agents verify their own work" via tests/telemetry — same verification infra as humans |

Feature requests #28221 ("PostTask hook"), #48657 ("Fire hooks on
background task completion"), and #23386 are all closed-as-not-planned.
The industry workaround is **session-scoped state files** (documented
in #23386) — the de-facto pattern until the framework provides native
background-task completion hooks.

## What this means for our workspace

1. **The Stop hook obligation system** can be enhanced to check
   `backgroundTasks` in its input. If any task is still `running`, block
   with a reason. When all complete, the model will have already called
   `get_command_or_subagent_output` to get results — the Stop hook can
   check whether a receipt was written for the modified file scope.

2. **The LLM should pass `timeout=180000` when running pytest** to keep
   it foreground. This is the **behavioral workaround** — simple, correct,
   but depends on the LLM remembering to set the parameter.

3. **The `_parse_exit_code` fix is still valuable** for foreground
   commands (short tests, `py_compile`, script runs).

4. **The structural fix is Option 3** (Stop hook with `backgroundTasks`
   awareness), not a Notification hook. The Notification event exists
   but its payload is wrong for this purpose.

## Falsifier

If a future Grok Build version changes PostToolUse to fire on process
completion (not just tool-call completion), this problem disappears and
the receipt writer works without any changes. Check the changelog for
PostToolUse lifecycle changes.

## Sources

- [Grok Build Hooks documentation](https://docs.x.ai/build/features/hooks) (xAI, 2026-07-24) — documents PostToolUse as a tool-call lifecycle event
- [Grok Build system prompt leak](https://github.com/asgeirtj/system_prompts_leaks/blob/main/xAI/grok-build.md) — confirms "you will receive a task id to check output later" and "notified on completion"
- Web research (2026-07-28): multiple sources confirm PostToolUse fires on tool-call completion, not process completion, for auto-backgrounded commands

## Receipts

- `~/.grok/hooks/verification-receipts.json` — PostToolUse hook registration (timeout bumped to 30s)
- `~/.grok/hooks/scripts/verification_receipt_writer.py:852` — `exit_code is None → don't write receipt`
- Session 019f9f4f: 97 receipts written, 0 for pytest commands, all for `python script.py` commands
