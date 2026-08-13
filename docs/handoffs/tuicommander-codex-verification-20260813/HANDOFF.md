---
title: "Verify Codex session is clean of TUICommander MCP registration"
created: 2026-08-13
session: 019ffbb9-bc18-7db3-a81a-71b467367375
status: ready-to-implement
assigned_to: ""
assigned_at: ""
assigned_by: ""
priority: low
effort: S
---

# Verify Codex session is clean of TUICommander MCP registration

## Goal

Confirm that a fresh Codex session does not report `tuicommander` in its MCP
server list, closing the verification gap from the TUICommander cleanup session.

## Context

Session 019ffbb9 removed TUICommander MCP registrations from three locations:
`~/.grok/config.toml`, `~/.codex/config.toml`, and `~/.claude.json`. The Grok
Build side was verified clean via `grok mcp doctor` (0 tuicommander references).
The Codex side was edited but never verified with a fresh session.

Codex reads MCP servers from `~/.codex/config.toml`. It may or may not also
read `~/.claude.json` — this was not confirmed. If Codex does read
`~/.claude.json`, the edit we made there covers it. If it doesn't, the
`~/.codex/config.toml` edit stands on its own. Either way, unverified.

## What was done this session

1. Searched all standard install locations for TUICommander — nothing found
2. Found `TUICommander-setup.exe` in `%LOCALAPPDATA%\Temp\` — deleted
3. Found MCP registrations in `~/.grok/config.toml` and `~/.codex/config.toml` — removed
4. Fresh Grok session still showed `tuicommander (connection failed)` — diagnosed via `grok mcp doctor` which revealed a third registration in `~/.claude.json`
5. Removed the `~/.claude.json` registration — Grok verified clean
6. Deleted `~/.grok/logs/mcp/tuicommander.stderr.log` and two `~/.codex/config.toml.bak-*` files
7. Wrote wiki concept: `tuicommander-silent-three-location-mcp-registration`

## Acceptance criteria

- [ ] Launch a fresh Codex session
- [ ] Check whether `tuicommander` appears in connected or failed MCP servers
- [ ] If it does NOT appear: verification complete, close this handoff
- [ ] If it DOES appear: search for additional Codex MCP config sources beyond `~/.codex/config.toml`, remove the registration, re-verify

## Next steps for the picking-up agent

1. Launch Codex (`codex` CLI)
2. Look at the MCP connection status at startup
3. If clean, close this handoff with a one-line resolution note
4. If not clean, run `Select-String -Path "$HOME\.codex\config.toml" -Pattern 'tuic'` to confirm the edit persisted, then search for other Codex MCP config locations

## Verification receipts (from this session)

- `Select-String -Path "$HOME\.codex\config.toml" -Pattern 'tuicommander'` → no output (clean)
- `grok mcp doctor` → `~/.claude.json` dropped from 2 servers to 1, no tuicommander anywhere
- Codex session verification: NOT DONE (this handoff)

## Verbatim last user message

> /wiki + /handoff

## Resolution

unanswered
