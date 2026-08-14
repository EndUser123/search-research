---
title: "What display format does claude code like to use?  it has bullets and connecting lines"
date: "2026-03-09"
mode: "COPILOT"
uuid: "494afbda-d8f4-425a-aa93-c1c826976b34"
entry_count: 5
---

## Human

What display format does claude code like to use?  it has bullets and connecting lines

## Assistant

Claude Code, the CLI tool from Anthropic, prefers structured outputs like extensive bullet points and hierarchical lists for readability in terminal displays. This format aligns with its use of the Rich library for rich CLI rendering, which supports tree-like structures with bullets and connecting lines (such as Unicode connectors like ├── and └──) for file trees or nested data.[1][2][3]

## Output Styles
Claude Code offers configurable output styles via `/output-style`, including Default (concise code-focused), Explanatory (with insights), and Learning modes, all emphasizing clear, list-based responses over dense prose. Custom styles can enforce bullet-heavy Markdown for summaries and plans, often compressed for terminal viewing.[2][4][1]

## Tree Displays
For codebase navigation, Claude Code frequently generates or displays file trees using the `tree .` Bash command, rendered with bullets and connecting lines in Rich-formatted output. Users add these to CLAUDE.md for quick context, helping Claude map project structures visually in the CLI.[3]

## Rich Library Integration
As a Python CLI leveraging Rich, Claude Code excels at rendering nested bullets, trees, and ASCII art with vertical/horizontal connectors for hierarchies like dependency graphs or task breakdowns. This matches your description and is common in debugging or planning workflows.[5][6]

## Human

Tips for prettier code formatting after Claude responses

## Assistant

Claude Code responses can generate unformatted code, but hooks and prompts provide reliable ways to apply Prettier or similar tools automatically. These tips leverage your VSCode and multi-terminal setup for seamless integration.[1][2][3]

## Use PostToolUse Hooks
Configure hooks in `.claude/settings.json` to run formatters after every Write or Edit action. Create `.claude/hooks/auto-format.sh` to detect file type and apply Prettier, Black, or others—e.g., `prettier --write "$CLAUDE_FILE_PATH"` for JS/TS. This auto-beautifies without manual steps, ideal for your agentic workflows.[2][4][5][3][6]

## Prompt for Formatted Output
Instruct Claude explicitly: "Format this code using Prettier conventions with 2-space indent, then output only the cleaned code."  Add project rules to CLAUDE.md, like "Always use Prettier style: 2-space JS indent, 80-char lines." Iterate with "Reformat previous output per these rules" for refinements.[7][8]

## VSCode Integration
Paste Claude's code into VSCode Insiders, then Shift+Alt+F for Prettier format-on-paste if configured. Use your git worktrees across terminals: generate in one, format/review in VSCode, commit via PowerShell. For bulk, run `npx prettier --write .` post-session.[9][1]

## MCP Skills and Alternatives
Install Prettier MCP skills from mcpmarket.com for Claude to handle formatting natively. Pair with `tree` outputs for context, ensuring consistent trees before/after formatting.[ from prior][10][11]

## Human

what are some of the most popular output styles for claude code?

## Assistant

Claude Code's most popular output styles are the three built-ins: Default, Explanatory, and Learning, with users frequently creating customs for specialized tasks. These modify the system prompt for tailored formatting, tone, and structure in terminal responses.[1][2][3][4]

## Built-in Styles
- **Default**: Concise, code-focused for efficient engineering tasks; standard for most users.[2][3][4]
- **Explanatory**: Adds "Insights" sections explaining choices and patterns; popular for codebase exploration and PR reviews.[3][5][2]
- **Learning**: Interactive teaching mode with TODO(human) markers for user code sections; favored for onboarding and pair programming.[6][2][3]

## Custom Styles
Communities share customs like YAML, table, HTML, or ultra-concise for Generative UI and agentic workflows. Create via `/output-style:new [description]` and store in `~/.claude/output-styles` for reuse across projects. Switch with `/output-style [name]`, persisting per `.claude/settings.local.json`.[7][8][1][2][3]

## Human

Are there examples of what can be done with output styles?  Sometimes I ask for information and I get a wall of text that his hard to read, scan, and understand.

## Assistant

Output styles in Claude Code transform dense "wall of text" responses into scannable formats like bullet points, tables, insights sections, or even HTML/YAML for better readability. Examples from docs and users show how they break down info queries into hierarchies, avoiding overwhelming paragraphs.[1][2][3][4][5]

## Explanatory Style Example
Instead of a prose dump on a codebase change, Claude adds structured "Insights" boxes explaining trade-offs and patterns. For a "explain this function" query: it outputs the code, then bulleted insights like "- Chose async for non-blocking I/O; trade-off: added complexity vs. performance gain." This makes scanning key decisions effortless without losing details.[3][4][1]

## Learning Style Example
For tutorials or analysis, it intersperses explanations with TODO(human) markers for interactive sections. Example response to "analyze this algorithm": bulleted steps, insights, then code with "// TODO(human): Implement edge case X" for you to fill and iterate. Users praise it for turning info walls into collaborative, skimmable guides.[6][4][7][1]

## Custom Style Examples
- **Direct Objective**: Forces bullet-point facts without fluff; e.g., query "pros/cons of framework" yields ranked lists with % probabilities, no sycophancy.[7][3]
- **Table/YAML/HTML**: Reformats data queries as tables or renderable HTML (Rich CLI supports); e.g., "list deps" becomes a scannable YAML tree instead of paragraphs.[8][5]
- **Architecture Mode**: Phases like "Research → Plan → Bullets" for complex info, with blind spots listed.[9]

## Quick Setup for Info Queries
Run `/output-style explanatory` or create custom via `/output-style:new "Use bullets, tables, no walls of text"`—saves to `.claude/settings.local.json` for your worktrees. Pair with your Rich library prefs for tree connectors on nested lists.[1][3]

## Human

Examples of user-shared custom output styles on Reddit
Compare Default vs Explanatory vs Learning styles
Prompt templates for making information easy to scan
Best output styles to avoid walls of text

## Assistant

Claude Code output styles excel at turning walls of text into scannable formats, with users sharing customs on Reddit to enforce bullets, tables, and phases. Examples below address your points directly, drawing from docs, Reddit shares, and guides.[1][2][3][4]

## User-Shared Customs on Reddit
Reddit threads feature shares like "Direct Objective" for fact-focused bullets without fluff. Example template from r/ClaudeAI:[2][1]
```
---
name: Direct Objective
description: Clear, professional communication without excessive deference
---
# Direct Objective Communication Style
Maintain a professional, objective tone that focuses on facts and solutions.
- Use bullets for lists.
- Tables for comparisons.
- No walls of text.
```
Another: "Architecture Mode" with phases (Research → Plan → Execute) and blind-spot bullets.[5][1]

## Style Comparison
| Aspect | Default | Explanatory | Learning |
|--------|---------|-------------|----------|
| **Tone** | Concise, direct [2] | Educational with "Insights" boxes [2] | Interactive mentor with TODO(human) [2] |
| **Best For** | Fast tasks [2] | Codebase understanding/PRs [2] | Onboarding/learning [2] |
| **Scanability** | Minimalist, code-heavy [2] | Bullets + rationale [2] | Markers + explanations [2] |
| **Text Density** | Low  | Medium (insights add structure)  | Higher but collaborative  |

## Prompt Templates for Scannability
Use these in custom styles or CLAUDE.md to force structure:
```
Always format info responses as:
## TL;DR
- Bullet 1
- Bullet 2

## Details
| Category | Key Points |
|----------|------------|
| Pros     | ...       |

## Next Steps
1. Action 1
```
Or: "Respond in tables and top-5 bullets only; max 3 sentences per section." For info queries: "Break into hierarchy: Summary → Bullets → Tables → Risks."[4][1][5]

## Best Styles to Avoid Walls
- **Explanatory**: Adds Insights without density[2]
- **Direct Objective** (custom): Bullets/tables only[1][2]
- **Table-First** (custom): Defaults to Markdown tables for data[6]
Switch via `/output-style [name]`; persists in `.claude/settings.local.json`.[4]
