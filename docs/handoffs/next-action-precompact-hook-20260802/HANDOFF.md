---
thread_id: next-action-precompact-hook-019fa8f8
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: console_019fa8f8
produced_at: 2026-08-02T00:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: efac5a42fb93d25224ca4bf0c9237c8afc236073
---

# Handoff: Next-action precompact hook — implementation

## Objective

Implement a PreCompact hook that scans the transcript for uncaptured improvement opportunities and injects a structured count into the compaction context, so that `/capture` can pick up operator corrections and friction patterns automatically before compaction discards the working memory.

## Status

OPEN — triaged as READY_FOR_HANDOFF by harvest on 2026-08-02. No handoff existed until this one was created.

## Producing context

- Harvest source: `P:/.data/harvest/triaged/next-action-precompact-hook.json` (status: READY_FOR_HANDOFF, triaged by session 019fb177)
- Harvest pending: `P:/.data/harvest/pending/tp-session-019fb926.json` (1d old, 3 unresolved obligations)
- Session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
- The precompact hook addresses the gap where operator corrections and friction patterns are lost at compaction time because `/capture` only runs at `/close` and `/handoff`, not at compaction boundaries.

## Read-first list

1. `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check lifecycle context
2. `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — I/O safety patterns for hook authors
3. `P:/docs/handoffs/close-check-blocked-019fa8f8-20260801/HANDOFF.md` — the close-check remediation handoff that motivated this hook
4. `P:/.claude/hooks/PreToolUse.py` — dispatch chain reference for hook registration
5. `P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md` — ruff invocation pattern for hooks

## Verified facts

- [FACT] Harvest triage item `next-action-precompact-hook.json` has status=READY_FOR_HANDOFF (source: `P:/.data/harvest/triaged/next-action-precompact-hook.json`)
- [FACT] The hook needs to scan `chat_history.jsonl` for operator correction patterns (pushback, redirect, "you didn't", "that's wrong", "revert") and friction patterns (tool retries, repeated failures, timeout events)
- [FACT] The hook must write its output to the PreCompact additionalContext injection point (source: harvest triage item — two assumptions need verification: PreCompact additionalContext injection, chat_history.jsonl accessibility at PreCompact time)
- [FACT] The hook must be registered via `settings.json` router.py dispatch pattern, NOT via `hooks.json` directly (per plugin-development rule: plugin hooks MUST be registered in settings.json via router.py dispatch pattern)
- [FACT] The hook file should be at `~/.grok/hooks/PreCompact_improvement_capture.py` with registration in `~/.grok/hooks/improvement-capture-precompact.json` (source: harvest triage target_skill and affected_files)

## Task packets

### T1: Verify PreCompact additionalContext injection mechanism

- **id:** PAC-01
- **goal:** Confirm that PreCompact hooks receive additionalContext and that chat_history.jsonl is accessible at PreCompact time
- **in scope:** PreCompact hook spec, `~/.grok/hooks/` directory, `settings.json` router.py
- **acceptance:** Either (a) confirmed that additionalContext injection works and chat_history.jsonl is readable at PreCompact time, OR (b) documented as a blocking assumption with a workaround (e.g., read transcript from the session directory instead)
- **falsifier:** if PreCompact does not support additionalContext or chat_history.jsonl is not accessible, the hook design needs revision
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 15 minutes

### T2: Implement PreCompact_improvement_capture.py

- **id:** PAC-02
- **goal:** Write the hook script that scans chat_history.jsonl for operator corrections and friction patterns, counts them, and outputs a structured summary
- **in scope:** `~/.grok/hooks/PreCompact_improvement_capture.py`
- **acceptance:** script runs without errors on a sample chat_history.jsonl, produces structured JSON output with correction_count, friction_count, and top_5_patterns
- **falsifier:** if the script crashes or produces no output on a valid chat_history.jsonl
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR
- **estimate:** 2 hours

### T3: Register the hook via settings.json router.py

- **id:** PAC-03
- **goal:** Register PreCompact_improvement_capture.py in settings.json via the router.py dispatch pattern (NOT hooks.json)
- **in scope:** `~/.grok/settings.json`, `__lib/router.py`
- **acceptance:** hook fires at PreCompact events and is listed in the dispatch chain
- **falsifier:** if the hook does not fire at PreCompact time or is not in the dispatch chain
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 30 minutes

### T4: Test the hook end-to-end

- **id:** PAC-04
- **goal:** Run the hook against a real session transcript and verify the output is structured and useful
- **in scope:** any session with operator corrections and friction patterns
- **acceptance:** hook produces a non-empty correction/friction summary that a future session could act on
- **falsifier:** if the output is empty or malformed
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 30 minutes

## Hard constraints

- AGENTS.md auto-commit: stage only files you changed; surgical `git add <paths>`
- AGENTS.md destructive-git ban: no force-push, no reset --hard, no rebase -i, no clean -fd
- Hook must follow the `{plugin_name}_{EventName}.py` naming convention (PreCompact_improvement_capture.py)
- Hook must use `_bootstrap.py` for path setup (import pattern from plugin-development rules)
- Hook must not modify existing files — only create new ones
- All I/O must use atomic writes (tmp+replace) per the fmea findings for this session

## Acceptance criteria for closing this handoff

T1-T4 complete. The PreCompact hook fires at compaction boundaries and produces a structured correction/friction summary. The harvest triage item is marked resolved. The close-check-blocked handoff can reference this as a completed improvement stream.
