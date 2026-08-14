---
title: "claude code output styles"
date: "2026-01-26"
mode: "CONCISE"
uuid: "ab94cd31-0191-4340-8ab0-fd4d89426371"
entry_count: 1
---

## Human

claude code output styles

## Assistant

Claude Code features output styles that customize Claude's response formatting, tone, and structure by modifying its system prompt. These styles help tailor interactions for coding, explanations, or learning in your Windows 11 multi-terminal workflows.[1]

## Built-in Styles
Claude Code includes three core output styles for different needs.

| Style       | Description                                                                 | Best For Your Workflow                  |
|-------------|-----------------------------------------------------------------------------|-----------------------------------------|
| Default    | Concise, efficient responses focused on software engineering tasks like code edits and verification.  | Standard coding sprints and automation.  |
| Explanatory| Adds educational "Insights" on implementation choices and codebase patterns between task responses.  | Debugging patterns in your agentic systems.  |
| Learning   | Collaborative mode with Insights plus `TODO(human)` markers for you to contribute code snippets.  | Iterative refinement in multi-LLM sessions.  |

## Switching Styles
Use slash commands directly in your terminals: `/output-style` for a menu, or `/output-style explanatory` to switch instantly. Edit `outputStyle` in `.claude/settings.local.json` for persistence across your 5-6 terminals.

## Custom Styles
Create Markdown files in `~/.claude/output-styles` or `.claude/output-styles` with frontmatter like `name`, `description`, and `keep-coding-instructions: true` to retain testing behaviors. Example for JSON-focused output (aligning with your CLI preferences):

```
---
name: JSON-Compact
description: Strict JSON for programmatic parsing
keep-coding-instructions: true
---
Respond only in valid JSON schemas. Verify code with tests first.
```

This integrates well with your PowerShell statuslines and hook systems for structured outputs like drift indicators.[2]
