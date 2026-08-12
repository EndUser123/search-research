---
title: "Grok hook command env-var preflight — what it rejects and why"
created: 2026-08-12
source: session-019ff472
agent: grok
host: both
tags: [grok, hooks, env-var, preflight, plugin-porting, claude-mem]
summary: >
  Grok's hook runner pre-validates ${VAR} references in hook command strings
  before spawning the process. If a referenced env var isn't set at spawn time,
  the hook is not executed and the TUI shows "hook not executed: required env
  var(s) not set: ${VAR}." This bites plugins designed for Claude Code whose
  hook commands use bash shell variables (not env vars) that are assigned at
  runtime inside the command string. The fix: use host-injected vars
  (GROK_PLUGIN_ROOT) directly instead of discovery loops with shell scratch vars.
---

## Decision context

**When this matters:** porting Claude Code plugins to Grok Build, or writing
hooks that use shell-native variable syntax.

**Host difference:** Claude Code passes hook `command` strings to bash as-is.
Grok Build pre-expands `${VAR}` / `$VAR` references at the host level before
the shell sees them. This is documented in
`~/.grok/docs/user-guide/10-hooks.md` but easy to miss.

## What Grok rejects

Grok scans the `command` field for `${VAR}` patterns. If a referenced env var
isn't set in Grok's process environment at spawn time, the hook fails preflight
with:

```
✗ plugin/<name>/hooks:<event>[0].hooks[0] (0ms)
    hook not executed: required env var(s) not set: ${VAR1}, ${VAR2},
```

**Affected patterns:**
- `${VAR}` where VAR is a shell-local variable (assigned later in the command)
- `${VAR:-default}` where VAR is not a real env var (Grok may expand the default, but unset bare vars fail)
- Bare `$VAR` references to shell scratch variables (less reliably rejected — depends on Grok version)

**Not affected:**
- `${GROK_PLUGIN_ROOT}` — Grok injects this for plugin hooks
- `${GROK_SESSION_ID}`, `${GROK_HOOK_EVENT}`, etc. — runner-injected, always present
- `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PROJECT_DIR}` — Grok sets these as aliases

## Instance 1: canary test (2026-07-18)

Canary C used inline `pwsh -Command "..."` with PowerShell variable syntax like
`${d}` and `$env:USERPROFILE`. Grok's preflight rejected `${d}` as an unset env
var. Source: [[grok-pretooluse-matcher-and-readonly-fastpath]].

## Instance 2: claude-mem plugin port (2026-08-12)

claude-mem v13.15.0's hook commands use a bash discovery one-liner that
assigns shell scratch variables (`_G`, `_R`, `_T`, `_M1`, `_M2`, `_M3`, etc.)
at runtime. Grok's preflight sees `${_G}` / `${_R}` / `${_T}` references in
the command string, can't find them as process env vars, and refuses to execute.

**Error:**
```
✗ plugin/claude-mem/hooks:post_tool_use[0].hooks[0] (0ms)
    hook not executed: required env var(s) not set: ${_G}, ${_R}, ${_T},
```

**Fix:** replace the bash discovery one-liner with direct node invocation
using `${GROK_PLUGIN_ROOT}`:

```json
{
  "type": "command",
  "command": "node \"${GROK_PLUGIN_ROOT}/scripts/bun-runner.js\" \"${GROK_PLUGIN_ROOT}/scripts/worker-service.cjs\" hook claude-code observation"
}
```

No scratch vars, no discovery loop, no preflight rejection.

## Root cause chain

1. Claude Code plugins assume shell owns `$var` expansion
2. Grok pre-expands `${VAR}` at the host level (for MCP-style secret injection)
3. Shell scratch vars in hook commands are not env vars → preflight rejects
4. Hook is never executed (0ms, fail-open) — silent failure, no hook output

## How to diagnose

1. **Check TUI scrollback** for "hook not executed: required env var(s) not set"
2. **Read the command field** of the failing hook in `hooks.json`
3. **Look for `${...}` references** — are they env vars or shell locals?
4. **Check process env:** `Get-ChildItem Env:` — is the referenced var set?

## Prevention

- **Use `${GROK_PLUGIN_ROOT}` for plugin hooks** — always injected, always real
- **Avoid bash one-liners with shell scratch vars** — use script files or node
- **For `shell: "bash"` hooks:** Grok does NOT skip preflight for bash — it
  still scans the command string for `${VAR}`. Use a `.sh` script file with
  the command field as `bash "${GROK_PLUGIN_ROOT}/scripts/hook.sh"` instead
- **For PowerShell hooks:** use single-quoted strings to avoid `${var}` being
  treated as env-var references

## Related

- [[grok-pretooluse-matcher-and-readonly-fastpath]] — instance 1 (canary C)
- [[hook-failure-mode-taxonomy]] § B3 — env-var preflight failure mode
- [[tool-fallbacks]] — claude-mem / Codex preflight instances

## Falsifier

This concept is wrong if Grok changes the preflight to:
- Skip `${VAR}` validation when `shell: "bash"` is set, OR
- Only expand a whitelist of runner-injected vars (not arbitrary `${VAR}`), OR
- Pass `${VAR}` through to the shell when the var is unset (bash treats unset
  vars as empty by default, which would be safe)

## Sources

- TUI scrollback, session 019ff472 (2026-08-12)
- `~/.grok/docs/user-guide/10-hooks.md` L156, L352-354
- `grok.exe` binary string: `hook not executed: required env var(s) not set:`
  in `crates/codegen/xai-grok-hooks/src/runner/command.rs`
