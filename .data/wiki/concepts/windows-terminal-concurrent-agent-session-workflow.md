---
title: "Windows Terminal workflow for concurrent agent sessions"
created: 2026-08-13
source: session-2026-08-13
tags: [windows-terminal, agentic-cli, session-management, scrollback, export, layout]
summary: >
  Windows Terminal is being used as the primary surface for multiple concurrent
  Grok, Claude, Codex, and shell sessions. The chosen workflow combines Alt+T
  searchable tab lookup, a 32767-line scrollback buffer, prompt scroll marks,
  persisted window layout, and Ctrl+Shift+S timestamped buffer export with a
  user-selected destination. The dialog defaults to P:\exports and a
  timestamp-prefixed agent-session text filename. The configuration and
  deterministic helper path
  are locally verified, while the interactive Save As smoke test remains an
  operator-run check.
type: decision
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
tier: warm
confidence: 0.95
last_verified: 2026-08-13
half_life_days: 180
evidence_gaps:
  - "A live Ctrl+Shift+S export has not yet been exercised in the Windows Terminal UI."
relations:
  - target: wiki/concepts/terminal-visual-enhancements-for-agentic-clis.md
    type: related
  - target: wiki/concepts/file-link-format-windows-terminal.md
    type: related
  - target: wiki/concepts/mcp-server-sharing-multi-terminal.md
    type: related
---

# Windows Terminal workflow for concurrent agent sessions

## Decision context

The operator is running many agent sessions at once and found that the main
problem is session lookup, recovery, and retention rather than a missing
terminal replacement. The decision was to improve the existing Windows Terminal
surface before adopting a separate agent manager: reduce lookup cost with
searchable tabs, preserve useful output, make long buffers navigable, and
restore window structure after a restart.

The chosen approach favors built-in Windows Terminal features and one existing
small export helper. This keeps the workflow reversible and avoids making a
terminal manager infer agent state from output. The rejected alternative was
installing a new session-management application immediately; it remains
reasonable if native Terminal features cannot provide reliable attention
signaling or durable transcripts.

## Configuration now in effect

The authoritative settings file is:

`C:\Users\brsth\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`

The current workflow is:

- `Alt+T` opens searchable tab lookup through the built-in `tabSearch` action.
- `firstWindowPreference: "persistedWindowLayout"` enables restoration of
  window positions, names, tabs, panes, profiles, and reported working
  directories. It does not restore running processes or pane contents.
- Profile defaults use `historySize: 32767`, the documented Windows Terminal
  maximum, rather than the earlier attempted value of `100000`.
- `autoMarkPrompts: true` marks prompt boundaries when Enter is pressed.
- `showMarksOnScrollbar: true` displays those marks on the scrollbar.
- `User.exportBufferTimestamped` is bound to `Ctrl+Shift+S`; the former
  `Ctrl+E` binding was removed because that shortcut may have another local use.
  The helper now opens a Save As dialog and prepends a timestamp to the chosen
  filename.

## Buffer export path

The Terminal action first uses the native `exportBuffer` action to write a
staging file, then opens a short-lived PowerShell helper. The helper waits for a
  fresh stable staging file and opens a Save As dialog. The dialog defaults to
  `P:\exports` and a filename shaped like
  `20260813-123456-789_workspace-agent-session.txt`. If the operator chooses
  `P:\exports\yt-grok.txt`, the result is written as something like
`P:\exports\20260813-123456-789_yt-grok.txt`.

The native fallback remains `Ctrl+Shift+A` followed by `Ctrl+C`: select all
content in the terminal buffer, copy it, and paste it into a file or another
LLM workflow. This fallback has been documented by Microsoft, but the custom
`Ctrl+Shift+S` path still needs an interactive Save As smoke test.

## Why this arrangement

Searchable tabs scale better than repeatedly cycling through tabs when the
number of concurrent sessions grows. Persisted layout addresses reboot and
crash recovery for the workspace structure without pretending that a terminal
can resume an agent process. Prompt marks and a large bounded scrollback buffer
make long agent conversations easier to navigate. Timestamped export creates a
portable artifact for handoffs, postmortems, and continuation without requiring
continuous transcript capture.

This is intentionally a layered, low-coupling design. Tab lookup and layout
are Terminal concerns; export is a discrete user-triggered artifact; agent
attention notifications and continuous transcript capture remain separate
future investigations because their lifecycle and ANSI/TUI fidelity have not
been established across all three agent hosts.

## Receipts

- **Windows Terminal settings:**
  `C:\Users\brsth\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json:47`
  records `firstWindowPreference`; lines 58-59 record `Alt+T`; lines 82-83
  record `Ctrl+Shift+S`; lines 100-102 record the scrollback and scroll-mark
  defaults.
- **Export helper:** `P:\scripts\terminal-buffer-export-finalize.ps1:3-5,54-88`
  defines the staging path, waits for fresh stable output, opens the Save As
  dialog, defaults to a context-shaped `.txt` filename, and creates a
  timestamp-prefixed filename from the selected path.
- **Deterministic helper test:** on 2026-08-13, a selected test path produced a
  timestamp-prefixed output file with the expected contents; the test artifact
  was removed. The real Windows Terminal dialog flow remains untested here.
- **Local verification:** PowerShell `ConvertFrom-Json` parsing and assertions
  on 2026-08-13 confirmed the layout setting, mark settings, 32767 history
  size, `Alt+T` binding, and the `Ctrl+Shift+S`/no-`Ctrl+E` export binding.
- **Interactive boundary:** no Windows Terminal UI automation was used; the
  custom export remains operator-smoke-test pending.

## What this means for our workspace

- Use `Alt+T` and deliberate tab names such as `yt-main:Grok` or
  `yt-review:Codex` for active session lookup.
- Treat persisted layout as structural recovery, not process recovery; agents
  still need their own resume behavior.
- Use `Ctrl+Shift+S` before closing an important session when a durable text
  artifact is useful; choose the destination and base filename in the dialog.
  The timestamp is prepended automatically. If it fails, use `Ctrl+Shift+A`
  then `Ctrl+C` as the native fallback.
- Keep the default `.txt` format for faithful terminal-buffer capture. Use
  Markdown only after a separate formatter exists that can reliably structure
  ANSI/TUI-heavy output.
- Do not increase `historySize` beyond 32767 without rechecking the current
  Terminal implementation and documentation.
- Investigate agent lifecycle attention signaling or continuous transcripts
  only after observing whether this simpler workflow leaves a real gap.

## Falsifier

Re-evaluate this decision if any of the following occurs: persisted layout
regularly restores stale or incorrect windows; `Ctrl+Shift+S` cannot reliably
produce a fresh complete buffer export; scroll marks add noise without helping
navigation; or the operator still cannot identify which agent needs attention
after using named searchable tabs. A future live test should also check TUI and
ANSI-heavy agent output, not only ordinary shell text.

## Sources

- [Windows Terminal startup settings](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/startup) — persisted layout behavior and limits.
- [Windows Terminal advanced profile settings](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-advanced) — history-size maximum and scroll-mark settings.
- [Windows Terminal actions](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions) — `selectAll`, `copy`, custom actions, and keybindings.
- `P:\scripts\terminal-buffer-export-finalize.ps1` — local timestamped export helper.
- `C:\Users\brsth\AppData\Local\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json` — local authoritative configuration.

## Related

[[terminal-visual-enhancements-for-agentic-clis]]@related
[[file-link-format-windows-terminal]]@related
[[mcp-server-sharing-multi-terminal]]@related

## Auto-related

- [[grok-build-workflows-rhai-orchestration]]
- [[python-windows-architectural]]
- [[open-dynamic-workflow-cross-agent-orchestration]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]

