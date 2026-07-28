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
  commands foreground, OR use a Notification hook for completion events.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - https://docs.x.ai/build/features/hooks (xAI, 2026-07-24)
  - https://github.com/asgeirtj/system_prompts_leaks/blob/main/xAI/grok-build.md (System prompt leak, 2026-07)
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

### Option 2: Notification hook for completion events

Register a hook on the `Notification` event, which fires when background
tasks complete. The hook would read the notification payload and write a
receipt at that point.

**Limitation:** requires understanding the notification payload format
for background-task completion, which is not well-documented.

### Option 3: Marker file + Stop hook

The backgrounded command writes a marker file when done. The Stop hook
reads marker files and writes receipts.

**Limitation:** requires modifying the command to write markers, which
isn't possible for arbitrary pytest invocations.

## What this means for our workspace

1. **The Stop hook obligation system will keep blocking** on code changes
   where pytest was auto-backgrounded. The manual obligation-clearing
   workaround (`quality-obligation-*.json` → `status: SATISFIED`) is the
   current fallback.

2. **The LLM should pass `timeout=180000` when running pytest** to keep
   it foreground. This is a behavioral rule, not a structural fix — it
   depends on the LLM remembering to set the parameter. This is the same
   class of problem as [[causal-mechanism-claims-require-source-receipts-before-durable-write]]:
   a rule that works when followed but has no mechanical enforcement.

3. **The `_parse_exit_code` fix is still valuable** — it handles the case
   where commands DO run foreground (short tests, `py_compile`, script
   runs). It just doesn't help for auto-backgrounded commands. See
   [[verification-claim-admissibility]] for the broader framework of
   what counts as admissible verification evidence.

4. **A structural fix would require a Notification hook** that captures
   background-task completion and writes receipts at that point. This is
   future work.

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
