---
title: "Markdown and Mermaid rendering in agentic CLIs on Windows 11"
created: 2026-07-26
source: session-019f9f48
tags: [markdown, mermaid, terminal-rendering, cli-display, windows-11, grok-build, claude-code, formatting-reference]
summary: >
  Reference for what markdown and diagram rendering works reliably in agentic
  CLI terminals (Grok Build, Claude Code, Cursor CLI, Warp) on Windows 11.
  Key gotchas: adjacent lines without blank lines collapse into one paragraph
  (markdown soft-wrap); Mermaid diagrams don't render in most CLI terminals
  (no JS runtime) — use ASCII/Unicode art in code blocks or pipe through
  termaid. Tables work but should be kept narrow (≤4 columns). Code blocks
  (triple backtick) are the most portable formatting — they preserve
  whitespace, line breaks, and alignment in every renderer.
agent: grok
host: grok
cognitive_load: 1
verification: multi-source-verified
sources:
  - https://github.com/fasouto/termaid (Mermaid → Unicode terminal renderer)
  - https://github.com/charmbracelet/glow (markdown CLI renderer)
  - https://github.com/anthropics/claude-code/issues/13600 (Claude Code markdown renderer feature request)
  - https://cursor.com/changelog/cli-feb-18-2026 (Cursor CLI Mermaid ASCII support)
  - https://www.linkedin.com/posts/imharismehmood_terminal-mermaid-diagrams-now-render-in-unicode (Grok CLI Mermaid Unicode support)
relations:
  - target: wiki/concepts/go-home-narrative-fabricated-session-state-constraints
    type: related — the "Proceed with Recommendations?" line-break collapse that motivated this research
---

# Markdown and Mermaid rendering in agentic CLIs on Windows 11

## Decision context

**Why this was needed:** session 019f9f48 encountered a markdown rendering bug where the `/tp session` recommendation prompt (`Proceed with Recommendations?\n0 - Yes`) collapsed into a single line when rendered by Grok Build. The operator reported the formatting didn't change despite the skill spec showing two lines. Investigation revealed this is a fundamental markdown soft-wrap behavior, not a Grok Build bug. The research expanded to cover Mermaid diagram rendering and general markdown display tricks for agentic CLI terminals on Windows 11.

## What works reliably

### Standard markdown formatting (Grok Build + Claude Code)

| Feature | Syntax | Grok Build | Claude Code | Notes |
|---|---|---|---|---|
| **Bold** | `**text**` | ✅ | ✅ | Most reliable formatting |
| **Italic** | `*text*` | ✅ | ✅ | Easy to confuse with bold |
| **Headers** | `##`, `###` | ✅ | ✅ | Colored/sized in TUI |
| **Code blocks** | ` ``` ` | ✅ | ✅ | Preserves whitespace — most portable |
| **Inline code** | `` `code` `` | ✅ | ✅ | |
| **Tables** | `\|` pipe syntax | ✅ | ⚠️ varies | Keep ≤4 columns for terminal width |
| **Lists** | `-`, `1.` | ✅ | ✅ | |
| **Blockquotes** | `>` | ✅ | ✅ | |
| **Links** | `[text](url)` | ✅ | ✅ | Clickable in both CLIs |

### The critical gotcha: adjacent lines collapse

**Two lines without a blank line between them = one paragraph in markdown.** This is the CommonMark spec (soft wrap). The model's output is rendered as markdown, so:

```
Line 1
Line 2
```

Renders as: `Line 1 Line 2` (single line, space-joined).

**Three fixes, in order of reliability:**

| Fix | Syntax | Reliability | Visual |
|---|---|---|---|
| **Blank line** | `Line 1\n\nLine 2` | Highest — always works | Two separate paragraphs |
| **Double trailing space** | `Line 1  \nLine 2` | Medium — works in most renderers | Hard line break |
| **Code block** | `` ```\nLine 1\nLine 2\n``` `` | Highest — preserves everything | Visually heavy for short text |

**For the `/tp session` "Proceed with Recommendations?" prompt:** blank line is the correct fix (applied in commit `e08c545`).

## Mermaid diagrams in terminals

### The problem

Mermaid is a JS-based diagram renderer. CLI terminals don't have a JS runtime. So ```` ```mermaid ```` code blocks render as raw text in most CLI terminals.

### What the field is doing (2026 state)

| Tool | Mermaid support | How |
|---|---|---|
| **Cursor CLI** (Feb 2026) | ✅ Built-in | Mermaid code blocks render inline as ASCII art |
| **Grok CLI** (open-source, Jul 2026) | ✅ Built-in | "Mermaid to Unicode box art landed" |
| **Warp terminal** | ✅ Built-in | Markdown viewer with Mermaid rendering |
| **VS Code 1.121** (May 2026) | ✅ Preview | Mermaid preview in markdown editor |
| **Claude Code** | ❌ Feature request open | `anthropics/claude-code#13600` (Dec 2025) |
| **Grok Build** (this host) | Unknown | Open-source Grok CLI has it; Grok Build is a different product — not confirmed |

### Three options for diagrams in CLI output

**Option 1: ASCII/Unicode art directly (most portable)**

```text
┌──────────────┐     ┌──────────────┐
│   Skill A    │────▶│   Skill B    │
└──────────────┘     └──────────────┘
```

Works everywhere. No dependencies. Limited to simple diagrams.

**Option 2: `termaid` CLI** (Mermaid → Unicode art)

```bash
pip install termaid
echo 'graph LR; A-->B; B-->C' | termaid
```

Supports 18 diagram types. Auto-compacts narrow terminals. Source: `github.com/fasouto/termaid`

**Option 3: `beautiful-mermaid`** (npm, ASCII art)

```bash
npm install -g beautiful-mermaid
beautiful-mermaid render diagram.mmd
```

## Practical recommendations for this workspace

1. **For line breaks**: blank line between paragraphs. For hard breaks within a paragraph, double trailing space. Never assume two adjacent lines will stay on separate lines. See [[go-home-narrative-fabricated-session-state-constraints]] for the incident that surfaced this rule.

2. **For diagrams**: ASCII/Unicode art in code blocks. Don't rely on Mermaid rendering in Grok Build — it's not confirmed. If Mermaid syntax is needed, pipe through `termaid`. See [[prompting-patterns-for-ai-agent-control]] for how code-block formatting interacts with agent instruction patterns.

3. **For tables**: keep ≤4 columns. Pipe syntax works in Grok Build but can render inconsistently in narrower terminals. For complex data, use code blocks with aligned text. See [[mandatory-step-enforcement-code-over-prose]] for how table-rendered rules interact with the code-over-prose principle.

4. **For maximum formatting reliability**: code blocks (triple backtick) are the universal portability layer. They preserve whitespace, line breaks, and alignment in every terminal renderer.

5. **For the "prompt with options" pattern**: use blank line between the question and the options. The `/tp session` recommendation prompt fix (`e08c545`) is the reference implementation.

## Falsifier

This reference is wrong if:
- Grok Build adds native Mermaid rendering (then the "don't use Mermaid" advice is obsolete)
- A terminal markdown renderer ships that preserves adjacent-line breaks by default (then the blank-line fix is unnecessary)
- The table rendering in Grok Build changes to support wider tables reliably (then the ≤4-column advice is too conservative)

If any of these happen, update this reference.

## Sources

- [termaid](https://github.com/fasouto/termaid) — Mermaid → Unicode terminal renderer (18 diagram types)
- [glow](https://github.com/charmbracelet/glow) — markdown CLI renderer (Charm)
- [Claude Code markdown renderer feature request](https://github.com/anthropics/claude-code/issues/13600) (Dec 2025)
- [Cursor CLI Mermaid ASCII support](https://cursor.com/changelog/cli-feb-18-2026) (Feb 2026)
- [Grok CLI Mermaid Unicode support](https://www.linkedin.com/posts/imharismehmood_terminal-mermaid-diagrams-now-render-in-unicode-activity-7483390907166420993-BJ-w) (Jul 2026)
- [Warp markdown viewer](https://docs.warp.dev/terminal/more-features/markdown-viewer/) (Jul 2026)
- [VS Code 1.121 Mermaid preview](https://code.visualstudio.com/updates/v1_121) (May 2026)
- [Rendering Markdown in the Terminal](https://dimiro1.dev/rendering-markdown-in-the-terminal/) (Nov 2025)
- [beautiful-mermaid npm](https://www.npmjs.com/package/beautiful-mermaid) (Feb 2026)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
