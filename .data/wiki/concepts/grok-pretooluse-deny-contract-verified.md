---
title: "Grok PreToolUse deny contract — verified end-to-end (Python hook)"
created: 2026-07-19
source: session-2026-07-18
agent: grok
tags: [grok, hooks, pretooluse, deny, enforcement, python, verified]
summary: >
  A Python PreToolUse hook returning {"decision":"deny","reason":"..."} on stdout
  reliably blocks the tool call in Grok Build 0.2.103. The deny reason is surfaced
  to the model as "Hook denied: <reason>". Env vars (GROK_SESSION_ID, etc.) are
  populated. This is the only verified structural enforcement point in Grok Build
  and is the load-bearing mechanism for any exec-gate or authorization design.
cognitive_load: 2
host: both
---

## Summary

Verified by direct probe (canary-e.py) on 2026-07-19: a Python PreToolUse hook
denying a `read_file` call returned `{"decision":"deny","reason":"CANARY E: deny
from Python PreToolUse hook."}` and the tool was blocked. The model received the
reason string in the tool response as `Hook denied: CANARY E: deny from Python
PreToolUse hook.`

## Verified Facts

- **Deny blocks the tool.** Read of `P:/tmp/canary/canary-probe-target.txt` was
  blocked; the model received `Hook denied: <reason>` instead of the file contents.
- **Reason string is surfaced to the model.** This enables informative denial
  messages that tell the model what to do instead (e.g. "Run /exec to authorize
  implementation work").
- **Env vars are populated** for Python hooks: `GROK_SESSION_ID`, `GROK_HOOK_EVENT`,
  `GROK_HOOK_NAME`, `GROK_WORKSPACE_ROOT` all present. This enables per-session
  state files keyed on `GROK_SESSION_ID` — see [[multi-terminal-hook-state-isolation]].
- **Matcher `.*` dispatches.** The hook used `"matcher": ".*"` and fired for both
  `read_file` and `run_terminal_command` tool calls.
- **Multiple concurrent sessions are isolated by `GROK_SESSION_ID`.** During testing,
  a second concurrent Grok session fired the same canary hook; the log showed two
  distinct session IDs (`019f780a-e6ff-7d` and `019f76e8-eae4-7c`). Any stateful
  hook design must key on `GROK_SESSION_ID`, not a shared path.
- **Python invocation works via `python <script>` in the command field.** No
  bash-wrapper, no polyglot wrapper, no `pwsh -File`. Just `python P:/path/script.py`.

## Working Hook JSON Shape

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/path/to/hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Working Python Hook Shape

```python
import json, sys
payload = json.loads(sys.stdin.read() or "{}")
tool_name = payload.get("toolName", "")
# ...your logic...
if should_deny:
    print(json.dumps({"decision": "deny", "reason": "informative reason"}))
    sys.exit(2)
print(json.dumps({"decision": "allow"}))
sys.exit(0)
```

Both `{"decision":"deny"}` on stdout AND exit code 2 are accepted; either alone works.

## What This Enables

The exec-gate architecture is buildable:
1. `/exec` slash command (or any UserPromptSubmit-side detection) writes a session-scoped
   flag file: `~/.grok/.state/exec-grant-${GROK_SESSION_ID}`.
2. PreToolUse Python hook reads the flag; if absent or stale, denies `search_replace`,
   `write`, and mutating `run_terminal_command` calls with a reason like
   *"Dialogue mode — run /exec to authorize implementation."*
3. SessionEnd hook cleans up the session's flag file; startup sweep removes orphans.

## What Does NOT Work (contrasts)

- **Bash hook scripts may have degraded env vars.** Canary A (bash) showed
  `GROK_SESSION_ID=<unset>` in its log while Python canary E showed it populated.
  EVIDENCE_GAP: not cleanly isolated; may be a bash-on-MSYS quirk rather than a
  deterministic bash failure. Until verified, prefer Python for hooks that need
  env vars. See [[grok-hook-python-vs-bash-reliability]].
- **Passive events cannot inject context.** UserPromptSubmit/PostToolUse/Stop
  hooks fire and can write side-effect files, but their stdout is dropped entirely.
  See [[grok-build-hook-host-ceiling]].

## Related

- [[grok-build-hook-host-ceiling]]
- [[grok-hook-diagnostic-method]]
- [[grok-hook-command-env-var-preflight]]
- [[grok-hook-python-vs-bash-reliability]]
- [[multi-terminal-hook-state-isolation]]
- [[grok-pretooluse-matcher-and-readonly-fastpath]] (companion: the failure modes that don't apply once you use Python)

## Sources

- Direct probe 2026-07-19: `P:/tmp/canary/canary-e.py` + `~/.grok/hooks/canary-e-python-deny.json`
- TUI response to read_file probe: `Hook denied: CANARY E: deny from Python PreToolUse hook.`
- `P:/tmp/canary/canary-e.log` (10 invocations logged, `env_present: true` throughout)
- `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md` L189-200 (decision contract)

---

## Recovery note (2026-07-21)

This page was originally written on 2026-07-18 in a worktree session
(`019f7cbb-8f77-72d2-8982-6497e557391c` and sibling `019f7cbb-8f77-72d2-8982-64a470468f6a`).
The write landed in the worktree's `.data/wiki/concepts/` but was never synced
to the canonical `P:/.data/wiki/concepts/`. Multiple subsequent artifacts (the
exec-gate plugin README at `~/.grok/plugins/exec-gate/README.md:80`, the wiki
log at `P:/.data/wiki/log.md:4256`, the enhancement plan at
`P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md`) cited this page;
those citations dangled until 2026-07-21 when the page was finally promoted from
the worktree copy to the canonical location.

**Lesson:** worktree writes do not automatically sync to the parent workspace.
Wiki concepts written from a worktree session must be explicitly copied (or
written via a path that resolves to the parent workspace, not the worktree's
local copy). A future hook enhancement (see exec-gate PR 5) could enforce this
by detecting writes to `*/.data/wiki/concepts/*.md` from worktree-scoped
sessions and warning.
