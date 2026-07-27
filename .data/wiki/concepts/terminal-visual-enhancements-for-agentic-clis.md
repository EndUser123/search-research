---
title: "Terminal visual enhancements for agentic CLIs: what works, what people want"
created: 2026-07-27
source: session-019fa276 (/www research on terminal visuals + implementation in nlm-to-wiki report)
tags: [terminal, visual-enhancement, agentic-cli, unicode, sparkline, bar-chart, clickable-links, rich, progressive-disclosure, report-design]
summary: >
  Three pure-Unicode visual enhancements that work in agentic CLI terminals
  (Grok Build, Claude Code, Codex) without external dependencies: ASCII bar
  charts for distribution data, Unicode sparklines for histograms, and
  clickable file:/// links for cross-referencing output files. Research
  from Zaalouk (Feb 2026), David Min (Mar 2026), and the wiki's existing
  TUI/rendering concepts converged on: task-dependent modality (CLI for
  CRUD, GUI for visualization), dual-mode output (human-readable default +
  --json for agents), and progressive disclosure (outcome-first). Implemented
  in nlm-to-wiki's report.py with zero external dependencies.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "https://adelzaalouk.me/2026/feb/22/terminals-agents-and-the-control-plane-nobody-built/" (Zaalouk, Feb 2026 — CLI vs GUI is task-dependent, not expertise-dependent)
  - "https://medium.com/@dminhk/designing-clis-for-ai-agents-patterns-that-work-in-2026-29ac725850de" (David Min, Mar 2026 — dual-mode CLIs for humans + agents)
  - "P:/.data/wiki/concepts/markdown-mermaid-rendering-agentic-clis-windows-11.md" (what renders in Grok Build)
  - "P:/.data/wiki/concepts/clickable-file-links-grok-tui-windows.md" (OSC8 file:/// links work in Grok Build)
  - "P:/.data/wiki/concepts/close-report-design-user-centric-progressive-disclosure.md" (outcome-first report format)
  - "P:/.data/wiki/concepts/tui-frameworks-for-personal-scripts.md" (Rich → Textual upgrade arc)
relations:
  - target: wiki/concepts/close-report-design-user-centric-progressive-disclosure.md
    type: extends
  - target: wiki/concepts/markdown-mermaid-rendering-agentic-clis-windows-11.md
    type: related
  - target: wiki/concepts/clickable-file-links-grok-tui-windows.md
    type: applies
  - target: wiki/concepts/video-to-wiki-pipeline-report-metrics-and-framework.md
    type: implements
---

# Terminal visual enhancements for agentic CLIs

## Decision context

**Why this was needed:** the nlm-to-wiki pipeline report used plain-text
tables and numbers. The operator asked whether there are visual
enhancements that work in our terminal (Grok Build on Windows 11 /
PowerShell 7) and that people actually want to see more often. The question
bridges two concerns: what renders reliably in agentic CLI terminals, and
what makes output more useful without adding complexity.

## What works in our terminal

Based on the wiki's existing rendering tests
([[markdown-mermaid-rendering-agentic-clis-windows-11]],
[[clickable-file-links-grok-tui-windows]]) and the Rust-CLI renaissance:

| Enhancement | Mechanism | Works in Grok Build? | Notes |
|---|---|---|---|
| **Unicode block characters** | `█░▁▂▃▄▅▆▇` | ✅ Yes | PowerShell 7 + Windows Terminal render these correctly |
| **Color emoji** | ✅ ⚠️ ❌ | ✅ Yes | Used for status indicators in reports |
| **Clickable file:/// links** | OSC8 hyperlinks | ✅ Yes (verified) | `file:///P:/...` with forward slashes |
| **ASCII box drawing** | `═══ ───` | ✅ Yes | Section separators in reports |
| **Rich tables** | `rich` library | ✅ Yes (with dep) | Borders, alignment, color — but adds a dependency |
| **Progress bars** | `rich.progress` | ✅ Yes (with dep) | Live-updating; needs a running process, not a post-run report |
| **Mermaid diagrams** | JS-based | ❌ No | CLI terminals have no JS runtime |
| **True color (24-bit)** | ANSI 24-bit | ⚠️ Depends | Windows Terminal yes; older terminals no |

## The three highest-value enhancements (implemented)

### 1. ASCII horizontal bar chart

```
  ████████████████████████  95  Claude Skills Overview
  █████░░░░░░░░░░░░░░░░░░░  20  AI-Powered Video Editing
  ███░░░░░░░░░░░░░░░░░░░░░  13  Claude Code Usage Patterns
```

**Why it works:** the 24x cluster imbalance is visible instantly without
reading numbers. The bar is proportional (`value / max * width`). Uses
`█` for filled and `░` for unfilled. Pure Unicode, no dependency.

**Implementation:** 6 lines — a `bar_chart(value, max_val, width)` function
that returns a string. Called once per row in the cluster distribution table.

### 2. Unicode sparkline

```
  ▆▅█▅▄▂▁▁▁▁ ▁   ▁
  Min: 2 words   Max: 14,889 words   Median: 2,412 words
```

**Why it works:** shows the distribution shape in one line — the peak at
the left (many short transcripts), the long tail (few very long ones). The
operator sees "most transcripts are short-to-medium with a long tail"
without parsing a histogram.

**Implementation:** 12 lines — bins the values into N buckets, maps each
bucket's count to a block character `▁▂▃▄▅▆▇█`. Pure Unicode.

### 3. Clickable file:/// links

```
  Claude Skills Overview
    file:///P:/.data/wiki/concepts/claude-skills-overview.md
```

**Why it works:** the operator Ctrl+Clicks the link to open the concept
page in their editor directly from the terminal report. No copy-paste, no
"where is that file?" The OSC8 protocol is verified to work in Grok Build
on Windows ([[clickable-file-links-grok-tui-windows]]).

**Implementation:** 2 lines — a `file_link(slug)` function returning
`file:///P:/.data/wiki/concepts/<slug>.md`. The terminal renders it as a
hyperlink.

## Research findings: what people want in agentic CLIs

**[HIGH confidence — 2 independent sources + wiki convergence]**

### The task-dependent modality principle

Zaalouk (Feb 2026, citing Coleman et al. 2022): "The preference is
task-dependent, not expertise-dependent." Developers prefer CLI for CRUD
operations and debugging; GUI for monitoring and visualization. This isn't
"experts prefer CLI, beginners prefer GUI" — it's "different tasks pull
you in different directions."

**Implication for our reports:** the report should be scannable (CLI
strength) for the "did it work?" question, and link to deeper views
(GUI/browser/editor strength) for the "let me inspect this page" question.
The clickable file:/// links implement exactly this — scan in terminal,
drill in via editor.

### The dual-mode output principle

David Min (Mar 2026): agents need `--json` flags, stable exit codes, and
machine-parseable stderr. Humans need visual output. Every visual output
should have a `--json` twin. The nlm-to-wiki report already implements
this: default is human-readable with visuals, `--json` produces structured
metrics for programmatic consumption.

**The key insight from Min's article:** "agents hate your CLI" — they
can't parse pretty tables, choke on interactive prompts, waste tokens on
verbose help text. Every design decision that makes the CLI pleasant for
humans makes it hostile to agents. The solution is dual-mode, not
choosing one over the other.

### Progressive disclosure for reports

[[close-report-design-user-centric-progressive-disclosure]] (2026-07-26
research): Level 1 = outcome (2s scan), Level 2 = drill-in, Level 3 =
full data. The nlm-to-wiki report implements this with its three-tier
structure: default (Level 1), --verbose (Level 2+3), --json (structured).

### The Rust-CLI renaissance

Zaalouk documents the parallel trend: ripgrep, bat (syntax-highlighted
cat), eza (colorized ls), fd (fast find), zoxide (smart cd). These tools
prove that developers want *better* terminal output — colors, formatting,
speed — not less of it. The visual enhancements we added follow this
tradition: make the terminal more useful, not less visual.

## What does NOT work (avoid)

| Pattern | Why it fails | Where documented |
|---|---|---|
| Mermaid diagrams in terminal | No JS runtime; renders as raw text | [[markdown-mermaid-rendering-agentic-clis-windows-11]] |
| Interactive prompts in pipeline scripts | Agents can't respond; blocks CI | David Min, Mar 2026 |
| Color-only indicators (no text) | Breaks in terminals without color support; agents can't parse | — |
| Live-updating dashboards in reports | Reports are post-run summaries, not live monitors | Our design decision |
| External library dependencies (Rich/Textual) for simple reports | Adds install burden; pure Unicode achieves 90% of the value at zero cost | [[tui-frameworks-for-personal-scripts]] |

## Receipts

All claims about terminal rendering are from verified wiki concepts or
live tests in this session:

- **Unicode blocks render in Grok Build:** verified by the functional test
  output of `report.py --verbose` (bar chart + sparkline rendered correctly
  in this session's terminal output).
- **Clickable file:/// links work in Grok Build:** verified by
  [[clickable-file-links-grok-tui-windows]] (OSC8 `file:///` URIs are
  Ctrl+Click-able in Grok Build TUI on Windows).
- **`--json` dual-mode:** implemented in `report.py:main()` (the `--json`
  flag switches to structured JSON output; verified by functional test).
- **Progressive disclosure format:** implemented in `report.py:render_report()`
  (Level 1 = 4-line summary; Level 2 = --verbose with bar chart + sparkline;
  Level 3 = per-cluster detail with clickable links).

## What this means for our workspace

- **Pure-Unicode visuals are the right default.** No external dependency,
  works in every terminal we use (PowerShell 7, Windows Terminal, tmux
  over SSH). Rich/Textual are available when interactivity or color is
  needed ([[tui-frameworks-for-personal-scripts]]), but for post-run
  reports, Unicode is sufficient and more portable.
- **Every skill that generates reports should follow this pattern:**
  Level 1 outcome summary → Level 2 visual drill-in → Level 3 clickable
  detail → `--json` for agents. The nlm-to-wiki report is the reference
  implementation.
- **Clickable file:/// links are underused in our workspace.** They work
  in Grok Build (verified), they cost zero lines of real code (just format
  the path as a URI), and they eliminate the "where is that file?" friction.
  Other skills that reference files (handoff, wiki, review) should use them.

## Falsifier

These enhancements are unnecessary if:
- The terminal doesn't render Unicode block characters (unlikely —
  PowerShell 7 + Windows Terminal both support them natively)
- The operator never uses --verbose (Level 1 alone is sufficient)
  — measurable: add a counter for --verbose invocations
- The visual layer adds maintenance burden without user value
  — testable: A/B test with and without visuals on the same report

## Sources

- [Your terminal is an AI runtime now](https://adelzaalouk.me/2026/feb/22/terminals-agents-and-the-control-plane-nobody-built/)
  (Zaalouk, Feb 2026) — task-dependent modality principle, Rust-CLI
  renaissance, cognitive load theory applied to CLI vs GUI
- [Designing CLIs for AI Agents: Patterns That Work in 2026](https://medium.com/@dminhk/designing-clis-for-ai-agents-patterns-that-work-in-2026-29ac725850de)
  (David Min, Mar 2026) — dual-mode output (human + --json for agents),
  agents hate pretty tables, need stable exit codes
- `P:/.data/wiki/concepts/clickable-file-links-grok-tui-windows.md` —
  OSC8 `file:///` URIs verified to work in Grok Build TUI on Windows
- `P:/.data/wiki/concepts/markdown-mermaid-rendering-agentic-clis-windows-11.md`
  — what renders reliably in Grok Build (markdown yes, Mermaid no)
- `P:/.data/wiki/concepts/close-report-design-user-centric-progressive-disclosure.md`
  — outcome-first, detail-on-request report design
- `P:/.data/wiki/concepts/tui-frameworks-for-personal-scripts.md` —
  Rich → Textual upgrade arc; Rich for beautiful output, Textual for
  full-screen interactive apps

## Auto-related

- [[close-report-design-user-centric-progressive-disclosure]] — the report-design principle this implements
- [[markdown-mermaid-rendering-agentic-clis-windows-11]] — what renders in our terminal
- [[clickable-file-links-grok-tui-windows]] — OSC8 links verified in Grok Build
- [[video-to-wiki-pipeline-report-metrics-and-framework]] — the report that uses these visuals
- [[tui-frameworks-for-personal-scripts]] — Rich/Textual for when Unicode isn't enough
