---
title: "TUICommander silent three-location MCP registration"
created: 2026-08-13
source: session-20260813
tags: [mcp, config, tuicommander, uninstall, grok-build, codex, claude-code]
summary: >
  TUICommander's installer registered itself as an MCP server in three
  separate config files across three different coding-assistant ecosystems
  (~/.grok/config.toml, ~/.codex/config.toml, ~/.claude.json) without asking
  permission. Removing it from config.toml alone left a live registration in
  ~/.claude.json that Grok Build reads at session start. The standard
  diagnostic pattern of searching config directories missed the top-level
  config file. grok mcp doctor is the definitive tool for finding all MCP
  registrations.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - https://github.com/sstraus/tuicommander/releases (sstraus/tuicommander, 2026)
relations:
  - target: wiki/concepts/claude-code-mcp-server-configuration.md
    type: related
---

# TUICommander silent three-location MCP registration

## Decision context

TUICommander was being evaluated as a passive tool without integrations. After
evaluation, the `tuic.exe` stub was removed from `%LOCALAPPDATA%\Microsoft\WindowsApps`.
But every fresh Grok Build session continued reporting `tuicommander (connection
failed)` in its MCP connection status — the application binary was gone, but
the MCP registration pointing at a nonexistent `tuic-bridge.exe` persisted.

The problem: finding and removing all registration sites required three
diagnostic rounds, each revealing a config location the previous search
had missed. The standard "search the `.claude/`, `.codex/`, `.grok/`
directories" pattern was structurally blind to the top-level `~/.claude.json`
file.

## What happened

TUICommander's installer (downloaded as `TUICommander-setup.exe` into
`%LOCALAPPDATA%\Temp\`) registered itself as a stdio MCP server in three
locations, all pointing at `C:\Users\<user>\AppData\Local\TUICommander\tuic-bridge.exe`:

1. **`~/.grok/config.toml`** — `[mcp_servers.tuicommander]` table with a
   `command` key. Grok Build's primary config.
2. **`~/.codex/config.toml`** — `[mcp_servers.tuicommander]` table with
   `command` and `env_vars = ["TUIC_SESSION"]`. Codex CLI's config.
3. **`~/.claude.json`** — `mcpServers.tuicommander` object with `command`,
   `args`, `env`, `type`. Claude Code's primary config, which Grok Build
   also reads as an MCP config source at session start.

This is the same failure class as [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]]: a tool registers itself silently, and the standard diagnostic pattern doesn't cover the registration location. The third location (`~/.claude.json`) was the hardest to find. The initial
diagnostic searched *inside* the `.claude/`, `.codex/`, and `.grok/`
directories recursively — but `~/.claude.json` is a standalone file at the
profile root, not inside any of those directories. It was invisible to the
recursive directory search.

## The diagnostic blind spot

The failure pattern:

```
Get-ChildItem "$HOME\.claude", "$HOME\.codex", "$HOME\.grok" -Recurse -File |
  Select-String -Pattern 'tuicommander'
```

This searches the **contents of directories** but not **standalone config
files at the profile root**. `~/.claude.json` sits at `C:\Users\<user>\.claude.json`
— outside all three searched directories.

The correct diagnostic for MCP registration is `grok mcp doctor`, which
lists all config sources and every server registered in each:

```
Config sources
  ~/.grok/config.toml          5 servers
  ~/.claude.json               2 servers
  ...
```

This output immediately reveals `~/.claude.json` as a config source that
filesystem directory searches miss.

## What this means for our workspace

- **When cleaning up any MCP server registration**, check all three locations:
  `~/.grok/config.toml`, `~/.codex/config.toml`, and `~/.claude.json`. Do not
  assume the server was registered in only one place.
- **Use `grok mcp doctor` as the definitive MCP registration diagnostic.**
  It enumerates every config source Grok reads and lists each server per source.
  Filesystem searches are a supplement, not a substitute.
- **When evaluating a new tool that claims to "integrate with your coding
  assistants,"** inspect what it writes during installation. TUICommander
  modified three separate config files across three ecosystems without
  prompting. The evaluation record: TUICommander gets two strikes — (1) broken
  `\\?\P:\` CWD handling from native PowerShell, (2) silent three-location MCP
  registration despite a passive evaluation intent. This connects to
  [[chronic-workspace-health-debt-inventory-2026-08-01]]: silent config
  modifications accumulate across sessions if not caught at install time.
- **Search known config files at the profile root explicitly**, not just the
  directories that contain them. The pattern:
  ```powershell
  Select-String -Path "$HOME\.claude.json","$HOME\.grok\config.toml","$HOME\.codex\config.toml" -Pattern '<server-name>'
  ```

## TUICommander evaluation summary

Two independent failure modes in this environment:

1. **Broken CWD**: native PowerShell CWD handling produced a broken
   `\\?\P:\` path that TUICommander couldn't navigate.
2. **Silent MCP registration**: the installer wrote to three MCP config files
   (`~/.grok/config.toml`, `~/.codex/config.toml`, `~/.claude.json`) without
   asking. The `tuic-bridge.exe` it pointed to was never actually placed at
   the registered path (`AppData\Local\TUICommander\tuic-bridge.exe`), making
   even the registration half-baked — it registered a server whose binary
   didn't exist.

Not worth revisiting unless these behaviors materially change upstream. This
connects to [[predictable-enforcement-for-recommendation-commitment]] and the
broader principle that tool installations should declare their side effects
rather than spreading them silently across multiple config ecosystems.

## Falsifier

If a future TUICommander release (a) fixes the `\\?\P:\` CWD issue and
(b) either asks before registering MCP servers or consolidates to a single
config location, this evaluation verdict should be revisited. The three-location
registration pattern is specific to the version evaluated (1.7.4-era setup
executable, August 2026); upstream changes could eliminate both strikes.

## Receipts

- `grok mcp doctor` output (this session): listed `~/.claude.json` as a config
  source with 2 servers, including `tuicommander` pointing at
  `C:\Users\brsth\AppData\Local\TUICommander\tuic-bridge.exe` (command not found).
- `~/.claude.json` line 948 (pre-edit): `"tuicommander": {"args": [], "command": "C:\\Users\\brsth\\AppData\\Local\\TUICommander\\tuic-bridge.exe", ...}`.
- `~/.grok/config.toml` line 112 (pre-edit): `[mcp_servers.tuicommander]` table.
- `~/.codex/config.toml` line 104 (pre-edit): `[mcp_servers.tuicommander]` table.
- All three blocks removed and verified via `grok mcp doctor` (0 tuicommander
  references, `~/.claude.json` dropped from 2 to 1 server).

## Sources

- [TUICommander releases](https://github.com/sstraus/tuicommander/releases) (sstraus/tuicommander) — confirms `TUICommander_1.7.4_x64-setup.exe` is the Windows artifact used by the current installer.

## Auto-related

- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]]
- [[chronic-workspace-health-debt-inventory-2026-08-01]]
- [[predictable-enforcement-for-recommendation-commitment]]
- [[hook-failure-mode-taxonomy]]

