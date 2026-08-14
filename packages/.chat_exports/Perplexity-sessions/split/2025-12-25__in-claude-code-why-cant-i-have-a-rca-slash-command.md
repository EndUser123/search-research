---
title: "in claude code, why can't I have a /rca slash command?"
date: "2025-12-25"
mode: "COPILOT"
uuid: "8122b92a-cb6f-44bc-8635-c0af00bc6384"
entry_count: 1
---

## Human

in claude code, why can't I have a /rca slash command?

## Assistant

In Claude Code, you can certainly have a custom `/rca` (Root Cause Analysis) slash command, but there are specific configuration requirements and a known bug that might be preventing it from appearing in your terminal session.

### Configuration Requirements
Custom slash commands are not active by default unless you create the correct file structure in one of two locations. Claude Code scans these directories at startup to register commands.[1][2]

*   **Global Scope:** Place your command in `~/.claude/commands/rca.md` to use it across all projects.[3][4]
*   **Project Scope:** Place it in your project's root under `.claude/commands/rca.md` to keep it project-specific.[2][5]

### Technical Prerequisites
For the `/rca` command to be recognized and usable by the AI agent itself (via the `SlashCommand` tool), the Markdown file must meet two criteria:[6][7]
1.  **Frontmatter Description:** You must include a `description` field in the file's YAML frontmatter. Without this, Claude cannot see the command as a tool it can invoke.[7][6]
2.  **File Extension:** The file must end in `.md`.[8][1]

### Common Issues and Bugs
If you have created the file but still cannot see `/rca` in the autocomplete list, you may be encountering one of the following documented issues:

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Silent Failure** | No `description` in frontmatter [6]. | Add `description: Perform root cause analysis` to the top of the file. |
| **Linux/WSL Bug** | Permissions or installation issues in `.claude/commands` [9]. | Reinstall Claude Code or clear the `~/.claude/projects` directory [9]. |
| **Character Budget** | Total command descriptions exceed 15,000 characters [7]. | Shorten descriptions of other custom commands to ensure `/rca` is loaded [7]. |

### Example Implementation
To fix the issue, ensure your `.claude/commands/rca.md` looks like this:

```markdown
---
description: Perform a detailed Root Cause Analysis on a bug or system failure.
---
Analyze the following logs or issue description to find the root cause:
$ARGUMENTS
```
