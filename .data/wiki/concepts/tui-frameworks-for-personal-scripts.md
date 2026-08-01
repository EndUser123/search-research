---
title: "TUI Frameworks for Personal Scripts — Python and PowerShell"
created: 2026-07-22
source: session-2026-07-22
tags: [tui, terminal, python, powershell, textual, rich, terminal-gui, cli]
summary: >
  Comparison of TUI frameworks for wrapping personal CLI scripts. Python's Rich
  (rendering) and Textual (full app framework) dominate. PowerShell uses
  Terminal.Gui (gui-cs) via ConsoleGuiTools or PSTuiTools. Most scripts benefit
  from Rich-style output first; full interactive TUIs are a later upgrade.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
---

## Summary

Two separate TUI ecosystems exist for the two languages in `D:\.code`. Python has
**Rich** (beautiful output, zero interactivity) and **Textual** (full-screen
interactive apps built on Rich). PowerShell has **Terminal.Gui** (a .NET port of
Turbo Vision) accessed via Microsoft's `ConsoleGuiTools` module or the community
`PSTuiTools` reference module. The recommended upgrade path for any script is
incremental: improve output formatting first (Rich for Python, colored
Write-Host for PowerShell), then add interactive selection, then graduate to a
full-screen TUI only if the workflow demands it.

## Key Findings

### Python TUI landscape

| Library | Type | Interactive | Best for |
|---|---|---|---|
| **Textual** | Full app framework (App + Widgets + CSS + reactive state + async event loop) | Yes | Interactive full-screen apps: DataTable, Input, panes, forms |
| **Rich** | Rendering library (tables, progress bars, syntax highlighting, panels) | No | Beautiful output in any script — most projects start here |
| **prompt-toolkit** | Input/REPL toolkit | Yes | Line editors, autocompletion, REPLs (powers IPython, pgcli) |
| **urwid** | Widget toolkit (callback-based, mature) | Yes | Legacy apps, multiple event loops |
| **Typer** | CLI framework | No | Type-checked CLI args + help screens; pairs with Rich |

**Default recommendation:** Start with Rich, graduate to Textual. Both by Will
McGugan / Textualize.io. Textual is the consensus default pick for new
interactive Python TUIs as of 2025-2026.

### PowerShell TUI landscape

| Tool | Type | Best for |
|---|---|---|
| **Microsoft.PowerShell.ConsoleGuiTools** | Official MS module: `Out-ConsoleGridView`, `Show-ObjectTree` | Quick interactive selection from pipeline output |
| **Terminal.Gui** (gui-cs/Terminal.Gui) | .NET cross-platform TUI toolkit | Building custom full-screen TUIs in PowerShell |
| **PSTuiTools** (jdhitsolutions) | Reference module: 11 sample TUIs (process viewer, service monitor, MP3 player, credential dialog) | Learning how to build PowerShell TUIs from real examples |
| **terminal-gui-designer** (ironmansoftware) | Visual designer that outputs PS Terminal.Gui scripts | Designing TUI layouts visually |

**⚠️ Assembly conflict:** `ConsoleGuiTools` uses Terminal.Gui v1.16, `PSTuiTools`
uses v1.19. Loading both in the same session causes version-conflict errors.
Pick one per session. Terminal.Gui v2 (alpha) will fix this but isn't stable yet.

### The 8-pattern upgrade arc (script → TUI app)

From Nexumo (Medium, Oct 2025):
1. CLI scaffold (Typer + Rich, or parameterized PS with colored output)
2. Progress bars (Rich `Progress` for long operations)
3. Tables/trees (Rich `Table` instead of walls of text)
4. Layouts (Textual Horizontal/Vertical panes)
5. Background jobs (Textual `Worker` API for non-blocking async)
6. Forms + validation (Input, Select, inline feedback)
7. State persistence (Pydantic → JSON/TOML in user config dir)
8. Theming + packaging (.tcss stylesheet, `pipx install` command)

Most scripts stop at step 2-3 and are dramatically better. Full TUI (step 4+) is
only worth it for workflows that need live interaction (dashboards, file managers,
monitoring consoles).

### Concrete application to D:\.code scripts

| Script | Language | Quick win | Full TUI |
|---|---|---|---|
| `index_videos.py` | Python | `rich.progress` during drive scan; `rich.table.Table` for results | Textual: live DataTable + Input filter |
| `Keep-Smaller-Copy.ps1` | PowerShell | Already has good colored output | `Out-ConsoleGridView` to preview/override before moving |
| `Download-Videos.ps1` | PowerShell | Already shows progress | `Out-ConsoleGridView` to pick URLs per session |

## Related

- [[cli-canonical-invocation-silent-failure-class]]@related — CLI invocation patterns
- [[git-worktree-multi-terminal-best-practices]]@related — multi-terminal workflows

## Sources

- https://botmonster.com/coding/build-tui-apps-python-textual-rich/ (May 2026) — authority=2, recency=3, evidence=3, bias=2 → score 10
- https://medium.com/@Nexumo_/8-tui-patterns-to-turn-python-scripts-into-apps-ce6f964d3b6f (Oct 2025) — authority=2, recency=3, evidence=2, bias=2 → score 9
- https://www.scriptrunner.com/blog-admin-architect/creating-cross-platform-tui-interfaces (June 2025) — authority=3, recency=3, evidence=2, bias=1 → score 9
- https://github.com/jdhitsolutions/PSTuiTools (Apr 2026) — authority=2, recency=3, evidence=3, bias=2 → score 10
- https://github.com/textualize/textual — official Textual repo
- https://github.com/textualize/rich — official Rich repo
- https://github.com/gui-cs/Terminal.Gui — Terminal.Gui toolkit
- https://www.powershellgallery.com/packages/Microsoft.PowerShell.ConsoleGuiTools — official MS module
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
