---
title: "Grok Build hook payload field — lastAssistantMessage, not response/messages"
created: 2026-07-28
source: session-019fa48a (behavioral hook debugging)
tags: [hooks, grok-build, payload, lastAssistantMessage, bug-fix, stop-hook]
host: grok
agent: grok
verification: observed
cognitive_load: 1
summary: >
  Grok Build Stop hooks receive the agent's final response in the `lastAssistantMessage`
  field (camelCase), not `response`, `messages`, or `tool_response`. Two behavioral hooks
  were written with the wrong field name and would have been permanently silent in production.
  The existing working hooks on this host (dbr_language_check.py, quality_gate.py) already
  used the correct field — the new hooks were modeled on generic templates instead.
  Always model payload extraction on existing working hooks, not templates.
relations:
  - target: wiki/concepts/hook-script-capability-derivation-receipt-loop-fix.md
    type: related
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: related
---

# Grok Build hook payload field — lastAssistantMessage

## Decision context

**Why this was needed:** two Stop hooks (`behavioral_check.py`, `wiki_persistence_check.py`) were written and unit-tested but would have been **permanently silent in production**. The `extract_response_text()` function checked `response`, `messages`, and `transcript_path` — but the Grok Build Stop hook payload provides `lastAssistantMessage`.

## The field

The Grok Build Stop hook payload uses camelCase keys throughout. The agent's final response text is at:

```python
payload["lastAssistantMessage"]  # str
```

Not `response`, not `messages[-1].content`, not `tool_response`. Source: `~/.grok/docs/user-guide/10-hooks.md:262`:

> "lastAssistantMessage carries the text of the agent's final response this turn, so hooks can act on it without parsing the transcript."

## The bug pattern

Both new hooks were modeled on generic hook templates rather than existing working hooks on the same host. The existing hooks (`dbr_language_check.py`, `quality_gate.py`) already used `lastAssistantMessage` correctly — only the new hooks had the bug.

## Fix

Add `lastAssistantMessage` as the **first** check in `extract_response_text()`, before falling back to other field names:

```python
def extract_response_text(payload: dict) -> str:
    if "lastAssistantMessage" in payload:
        lam = payload["lastAssistantMessage"]
        if isinstance(lam, str):
            return lam
    # ... fallbacks for other formats ...
```

## Lesson

When writing hooks for Grok Build, model the payload extraction on **existing working hooks on the same host**, not on generic templates. The `lastAssistantMessage` field is documented but easy to miss — the existing hooks are the ground truth.

This is the same pattern as [[hook-script-capability-derivation-receipt-loop-fix]] — a bug introduced because the implementation was modeled on a template rather than existing working code on the host. The general principle: **when adding new infrastructure to a host with existing infrastructure of the same type, read the existing implementation first.**

The broader context is documented in [[agents-md-construction-best-practices]] and [[grok-build-host-authority]] — Grok Build has specific payload formats, hook types, and field names that differ from Claude Code conventions. Generic templates from Claude Code documentation produce silent failures.

## Why silent failures are the worst failure mode

A hook that crashes at least produces an error in the TUI scrollback. A hook that extracts an empty string, checks it for patterns, finds none, and exits 0 — that hook is **invisible**. It ran, it returned success, and it detected nothing. The operator sees "hook fired" in the logs with no indication that the payload field was wrong. This is the same class as the capability derivation bug in [[hook-script-capability-derivation-receipt-loop-fix]] — a structural mismatch between what the hook expects and what the runtime provides, producing silent failure rather than loud failure.

The AGENTS.md rule "evidence-scope discipline" (a hook file existing does not prove the host loaded it) applies here: a hook script that runs without error does not prove it's processing the right data. The verification step must test with a realistic payload, not just check the script runs.

## What this means for our workspace

Any future hook written for Grok Build must check `lastAssistantMessage` first in its `extract_response_text` function. The existing pattern in `behavioral_check.py` and `wiki_persistence_check.py` (after the fix) is the canonical reference. New hooks should be tested with a realistic Stop event payload (not just unit tests with synthetic input) to verify the extraction works end-to-end.

The `behavioral_check.py` hook now logs detections to `~/.grok/hooks/state/behavioral-check-log.jsonl`, giving us production data on true-positive rates. This data was impossible to collect before the fix because the hook was permanently silent.

## Verification protocol for new hooks

The fix reveals a gap in our hook deployment protocol: unit tests passed (they tested `check_behavioral_violations()` directly), but the integration path (stdin JSON → `extract_response_text` → pattern matching) was never tested with a realistic payload. The protocol should be:

1. **Unit test** the detection logic (pattern matching on synthetic text) — we did this
2. **Integration test** with a realistic Stop event payload (pipe JSON to stdin, check stdout) — we did NOT do this initially
3. **Live test** after `/hooks` reload (confirm the hook fires and produces output) — we did this only after the operator pointed out the hooks should be visible

Step 2 is the missing step. It catches payload-format bugs that unit tests cannot. The test is trivial: `echo '{"lastAssistantMessage": "test text"}' | python hook.py`. Adding this to the deployment checklist for all future hooks would prevent this class of silent failure.

## Timeline

1. Hooks written and unit-tested (10/10 pass) — `extract_response_text` used wrong field
2. Operator restarted Grok Build, confirmed hooks visible via `/hooks` → `r`
3. Operator asked to verify hooks fire live — testing with realistic payload revealed the bug
4. Fix applied: added `lastAssistantMessage` as first check
5. Verified: both hooks now produce correct advisory JSON on test payloads
6. The bug would have been invisible indefinitely without the live-payload test — the hooks reported success (exit 0) on every real payload because empty text → no violations → clean exit

## Falsifier

This is wrong if Grok Build changes the payload field name in a future version. Check `~/.grok/docs/user-guide/10-hooks.md` for the current field name before writing new hooks.

## Receipts

- `~/.grok/docs/user-guide/10-hooks.md:262` — documents `lastAssistantMessage` as the field carrying the agent's final response text
- `~/.grok/hooks/scripts/dbr_language_check.py:253-254` — existing working hook using `data.get("lastAssistantMessage", "")`
- `~/.grok/hooks/scripts/quality_gate.py:1042` — existing working hook using `data.get("lastAssistantMessage", "")`
- `~/.grok/hooks/scripts/behavioral_check.py:99-109` — the fix (added `lastAssistantMessage` as first check in `extract_response_text`)
