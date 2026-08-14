---
title: "in codex cli, how do I enter mulit line edits.  I try shift-enter and / and those don't work."
date: "2026-01-18"
mode: "COPILOT"
uuid: "56810b39-f7de-44f2-ba5a-9b2c8d8538cc"
entry_count: 5
---

## Human

in codex cli, how do I enter mulit line edits.  I try shift-enter and / and those don't work.

## Assistant

Codex CLI does support multi-line edits, but the keybinding is very dependent on your terminal, and Shift+Enter often gets intercepted so it falls back to “submit” instead of “newline”.[1][2]

## How to enter multi-line input

Try these, in roughly this order:

- Press **Alt+Enter** in the Codex prompt; this is the common alternative binding for inserting a newline without submitting on many terminals.[3]
- If that fails, try **Alt+Shift+Enter**; some terminal setups wire multi-line input to that combo instead.[3]
- If none of those work, switch to a different terminal app (e.g., plain Windows Terminal, iTerm2, or your OS’s default terminal) and test again; Codex CLI itself supports Shift+Enter, but some terminals (and some IDE-embedded terminals like Cursor) swallow or remap it.[2][1]

## Workarounds if keys are blocked

- Paste multi-line text directly into Codex; recent versions handle multi-line paste correctly on Windows and other platforms.[4]
- Configure your terminal to map a shortcut (like Shift+Enter) to insert `\n` instead of sending an Enter keypress; this is possible in many terminal/IDE keybinding settings.[5][6][2]

If you tell which OS and terminal (e.g., Windows Terminal, VS Code, Cursor, iTerm2), it’s possible to give an exact keybinding setting that will make multi-line input work smoothly.

## Human

powershell 7.5.4

## Assistant

In PowerShell 7.5.4 on Windows, use **Ctrl+J** to insert a newline for multi-line edits in Codex CLI prompts.[1]

## Why Shift+Enter fails here

PowerShell 7+ intercepts Shift+Enter for its own multi-line command continuation, preventing Codex CLI from receiving it as a raw newline.[2]
Ctrl+J sends the ASCII line feed (LF) directly, bypassing the interception.[3][1]
This works reliably in Windows Terminal or plain PowerShell windows hosting Codex CLI.[4]

## Additional tips for PowerShell

- Paste multi-line text; recent Codex CLI updates handle non-ASCII and multi-line pastes correctly in PowerShell.[5][4]
- If Ctrl+J doesn't suit, try Alt+Enter as a fallback (works in some Windows Terminal setups).[6]
- For persistent setup, ensure PowerShell runs in UTF-8 mode via `$OutputEncoding = [System.Text.Encoding]::UTF8` before launching Codex.[4]

## Human

does ctrl J work in Claude Code the same way?

## Assistant

Yes, Ctrl+J works in Claude Code the same way as in Codex CLI—for inserting a newline during multi-line input in prompts or interactive mode.[1][2][3]

## Official keybindings

Claude Code explicitly lists Ctrl+J as the "line feed character for multiline" input, making it a reliable cross-platform fallback.[2][4]
It functions independently of terminal-specific issues like Shift+Enter interception in PowerShell or Windows Terminal.[3][5]
Docs confirm it works in all terminals, alongside alternatives like `\` + Enter (quick escape).[6][2]

## PowerShell specifics

In PowerShell 7.5.4, Ctrl+J bypasses the native Shift+Enter handling, just like in Codex CLI.[7]
For customization, edit `~/.claude/keybindings.json` to remap or add bindings like Shift+Enter if your terminal supports it.[8]
Run `/keybindings` in Claude Code to open the config file directly.[8]

## Human

how can I get codex to stop asking me if it can read a file?

## Assistant

Use the `--ask-for-approval never` (or `-a never`) flag when launching Codex CLI to disable all file read prompts.[1]

## Command-line options

Launch with full auto-approval for reads and writes in your workspace: `codex --sandbox workspace-write --ask-for-approval never "your prompt"`. This allows file reads/edits without asking but keeps network/commands safer.[2][1]
For unrestricted access (use cautiously): `codex --sandbox danger-full-access -a never` or `codex --yolo`.[3][4][1]
Read-only mode without prompts: `codex --sandbox read-only -a never`.[1]

## Persistent config

Edit `~/.codex/config.toml` (create if missing) and add:
```
approval_policy = "never"
sandbox_mode = "workspace-write"
```
This sets defaults globally or per-project; relaunch Codex to apply.[5][6][2]
For project-specific: Add `[projects."/path/to/repo"]` section with `trust_level = "trusted"`. Review changes before committing.[2]

## Human

what about if I alrady have codex running?

## Assistant

Type `/approvals never` (or `/approvals auto`) directly in the running Codex CLI session to disable file read prompts on the fly.[1][2]

## Available slash commands

Run `/approvals` alone to list modes: `never` (no prompts), `auto` (workspace auto-approve), `readonly` (reads only), or `full` (max access).[3][1]
Confirmation appears in chat confirming the switch, e.g., "Approval policy changed to never".[1]
`/approvals auto` is safest for daily use—it auto-approves repo files/commands but prompts for network/external.[4][1]

## Verification and alternatives

Type `/status` to confirm active policy and sandbox mode.[5]
If slash commands fail (rare bug), restart with `--ask-for-approval never` or edit `~/.codex/config.toml` for `approval_policy = "never"` and relaunch.[6][3]
Changes apply immediately to new requests but may not retroactively affect queued ones.[7]
