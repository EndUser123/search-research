---
title: "Fix agy headless permission denial (jetski auto-deny)"
created: 2026-08-07
status: resolved
assigned_to: grok
assigned_at: ""
assigned_by: ""
priority: high
tags: [agy, antigravity, headless, permissions, tp-panel, cross-model]
---

# Fix agy headless permission denial (jetski auto-deny)

## Goal

Fix the agy (Antigravity CLI) headless permission denial that silently kills the agy lens in `/tp` 3-lens parallel panels. The fix is documented in the wiki but was never applied to the config file.

## Context

**What's happening:** when `/tp` fires its 3-lens panel (spawn + codex + agy), the agy lens returns empty output with the error:

```
jetski: no output produced — a tool required the "command" permission
that headless mode cannot prompt for, so it was auto-denied.
Add an allow-rule under permissions.allow in settings.json
(e.g. command(<target>)).
```

This occurs even when the mandatory headless flags are used (`-p --dangerously-skip-permissions --print-timeout 10m --output-format json`). The flags handle the outer permission layer; `jetski` (agy's internal tool layer) has its own permission gate that auto-denies in non-TTY mode.

**The fix is already documented.** Wiki concept `[[gemini-api-vs-agy-cli]]` line 80 (updated 2026-08-01) prescribes:

> add a `permissions.allow` section to `~/.gemini/settings.json` with entries like `"read_file"`, `"list_directory"`, and `"run_shell_command(read_file)"`.

But this was never applied to the actual config file. The settings file exists at `C:\Users\brsth\.gemini\settings.json` — it has `mcp.allowed` and `security.auth` sections but NO `permissions.allow` section.

## What was done this session

1. The `/tp {3}` panel fired with all 3 lenses. Spawn and codex returned critiques. agy returned `INVOCATION_FAILED` — empty output, jetski auto-deny.
2. The operator flagged this for a handoff.

## What needs to happen

1. **Add `permissions.allow` to `~/.gemini/settings.json`.** The entries needed (per wiki `[[gemini-api-vs-agy-cli]]`):
   ```json
   "permissions": {
     "allow": [
       "read_file",
       "list_directory",
       "run_shell_command(read_file)"
     ]
   }
   ```

2. **Verify by re-firing an agy lens.** After applying the config change, run a simple agy headless dispatch to confirm it produces real output instead of the jetski auto-deny:
   ```powershell
   agy -p --dangerously-skip-permissions --print-timeout 30s --output-format json "Reply: AGY_PERMISSION_TEST_OK"
   ```

3. **Update `[[tool-fallbacks]]` § AGY row** to note that the fix has been applied (change the wiki status from "pending live verification" to "verified fixed").

4. **Update `[[gemini-api-vs-agy-cli]]` line 80** to remove "pending live verification" note once the fix is confirmed working.

## Acceptance criteria

- [ ] `permissions.allow` section exists in `~/.gemini/settings.json` with `read_file`, `list_directory`, and `run_shell_command(read_file)`
- [ ] agy headless dispatch produces non-empty output (not the jetski auto-deny error)
- [ ] `[[tool-fallbacks]]` and `[[gemini-api-vs-agy-cli]]` updated to reflect applied fix

## Why this matters

The agy lens is 1/3 of the `/tp` parallel panel. Without it, every `/tp` critique runs at 2/3 capacity — losing the Gemini family perspective. This has been broken since at least 2026-08-01 (wiki documentation date) and has silently degraded every `/tp` 3-lens invocation since.

## Evidence

- Session 019fd9c9 terminal log: `call_955ca37d37704552b9f7c09a.log` — the jetski auto-deny output
- Wiki: `[[gemini-api-vs-agy-cli]]` line 80 — documented fix, unapplied
- Config: `C:\Users\brsth\.gemini\settings.json` — exists, lacks `permissions.allow`

## Execution Status

Updated: 2026-08-07T00:00:00Z
Session: 019fdc45-15b9-71c0-8c0c-58d000ecd1c8
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | `permissions.allow` in `~/.gemini/settings.json` | ✅ DONE (pre-existing) | Config already contained the section (richer than spec): `read_file`, `list_directory`, `run_shell_command(read_file)` + `cat`/`ls`/`dir`/`grep`/`type`/`Get-Content`/`python`. No edit needed. |
| 2 | agy headless produces non-empty output (no jetski auto-deny) | ✅ DONE | Smoke test: `status: SUCCESS`, `response: SMOKE_OK`, 2.4s. File-read test: `status: SUCCESS`, `response: ZX9Q7` (correct), 2.0s, 16K cache-read tokens. |
| 3 | `[[tool-fallbacks]]` + `[[gemini-api-vs-agy-cli]]` updated | ✅ DONE | `gemini-api-vs-agy-cli.md:80` — "pending live verification" → "Verified fixed 2026-08-07". `tool-fallbacks.md:112` — new row for "command permission auto-deny (jetski)". |

### Key findings during execution

- **Handoff's core premise was already satisfied.** The `permissions.allow` section was already present in `~/.gemini/settings.json` when execution began — applied by a prior session, with 7 more entries than the handoff specified. Verifying the claim before acting avoided overwriting the richer config with the handoff's minimal version.
- **The handoff's verification command was malformed.** It placed `-p` immediately before `--dangerously-skip-permissions`; since `-p` consumes the next argument, that would have treated the flag as the prompt. Used the documented form `agy -p "<prompt>" --dangerously-skip-permissions ...` instead.
- **agy 1.1.11 confirmed working headless with file reads.** OAuth token cached (no 5-min hang); ~18-21K token baseline overhead per request (consistent with wiki Discussion #27307 note).
