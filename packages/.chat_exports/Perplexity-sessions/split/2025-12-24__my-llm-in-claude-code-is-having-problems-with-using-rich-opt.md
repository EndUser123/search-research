---
title: "my llm in claude code is having problems with using Rich optimally.  Is there a skill I can give it that will help it?"
date: "2025-12-24"
mode: "COPILOT"
uuid: "dc7ded5f-1d43-4253-b06d-e1318d76b293"
entry_count: 2
---

## Human

my llm in claude code is having problems with using Rich optimally.  Is there a skill I can give it that will help it?

## Assistant

## Your Claude Code LLM Can Benefit from a Custom Rich Library Skill

Yes, creating a **Claude Skill** specifically for Rich library optimization is the optimal solution for your problem. This is the most effective approach given how Claude Code discovers and uses skills.

### Why a Rich Library Skill?

Claude Skills are designed precisely for this use case—teaching Claude how to handle library-specific patterns and best practices in a reusable, composable way. Skills consume only 30-50 tokens until invoked, making them highly efficient. When Claude detects you're working with terminal output or Rich-specific tasks, it will automatically load your skill's detailed instructions.[1][2]

### What Your Skill Should Include

Based on proven patterns from the community and Anthropic's documentation, structure your Rich skill around these core components:[3]

**1. Console Management Patterns**
- Explicit Console() initialization and lifecycle management
- Avoiding the common `NotRenderableError` when mixing Console with Live/Status contexts[4]
- Proper context managers for Live displays and Status spinners

**2. Common Renderables with Examples**
- Tables with proper column configuration and styling
- Panels for grouped output
- Layout and Live updates (with Windows-specific refresh_per_second tuning)
- Progress bars with meaningful column selection
- Pretty-printing with syntax highlighting

**3. Windows Environment Considerations**
- Virtual Terminal support enabling (fixes flickering artifacts)[5]
- Appropriate `refresh_per_second` defaults for Windows Terminal vs cmd.exe
- Handling of ANSI color codes in different terminal environments

**4. Anti-Patterns to Document**
- Don't nest Console objects within Live displays
- Avoid excessive refresh rates on Windows that cause CPU contention
- Don't use raw `print()` when `console.print()` is available (breaks Rich styling)

### How to Create It

Use Claude's built-in **skill-creator** tool to generate the structure, then customize:

```markdown
---
name: rich-library-expert
description: Optimize console output using Rich library with proper patterns, renderables, and Windows environment handling
---

# Rich Library Expert

**Role**: Specialized expertise in Rich library terminal rendering, console management, and cross-platform output optimization.

**When to Use**: Terminal UI implementation, data visualization, progress tracking, formatted logging, dashboard-style applications.

**Key Capabilities**:
- Console lifecycle and context management
- Table, Panel, Layout, and Live display patterns
- Progress bars and status spinners with proper configuration
- Windows Terminal environment optimization
- Error handling for common rendering conflicts

## Best Practices...

[Include your documented patterns, examples, and solutions]
```

### Integration Strategy

Place your skill in your standard Claude Code skills directory (`~/.claude/skills/` or similar), and Claude Code will automatically discover it. When you mention terminal output, tables, or Rich-specific issues, Claude will intelligently load this skill. You can also explicitly request it with: *"Use the rich-library-expert to optimize this console output."*[2]

### Alternative: Add to CLAUDE.md

If you prefer a project-level approach, document Rich patterns directly in a `CLAUDE.md` file at your project root. This keeps library guidance available without creating a separate skill, but a dedicated skill is more portable and composable across projects.[6]

The key advantage: instead of re-explaining Rich patterns each conversation, Claude Code will have persistent, structured guidance that it proactively applies when relevant. This dramatically improves the consistency and quality of Rich-based implementations.

## Human

please make a great skill doc for Rich.

## Assistant

Perfect! I've created a comprehensive, production-grade Claude Skill document for the Rich library. Here's what's included:

## **Rich Library Expert Skill - Complete Reference**

This skill document covers everything Claude Code needs to use Rich optimally:

### **Core Sections**:

1. **Console Initialization** - The golden rule of single, module-level Console objects to prevent conflicts

2. **Lifecycle & Context Managers** - Proper patterns for:
   - Status spinners with animated feedback
   - Live displays for real-time updates
   - Progress bars with column customization
   - Manual start/stop patterns for event-driven workflows

3. **All Major Renderables**:
   - Tables (with styling, padding, width control)
   - Panels (borders, titles, sizing)
   - Layouts (multi-pane dashboards, nested splits)
   - Progress bars (customizable columns)
   - Status spinners (with 50+ spinner styles)

4. **Critical Windows Optimization**:
   - Virtual Terminal support detection
   - Refresh rate tuning (4-10 Hz recommended for Windows vs 12.5 Hz default)
   - `.clear_live()` cleanup pattern to prevent orphaned cursors

5. **Anti-Patterns & Common Pitfalls**:
   - Don't mix multiple Console objects
   - Don't nest context managers
   - Don't use `print()` instead of `console.print()`
   - Batch table updates for performance

6. **Advanced Integrations**:
   - Logging handler setup with tracebacks
   - Markdown rendering
   - Pretty-printing & REPL integration
   - Async/await patterns
   - Exception handling with Rich tracebacks

7. **Troubleshooting Guide** - Quick lookup table for common issues

### **How to Use This Skill**:

1. **Save the file** to your Claude Code skills directory:
   - Windows: `%USERPROFILE%\.claude\skills\rich-skill.md`
   - macOS/Linux: `~/.claude/skills/rich-skill.md`

2. **Claude will auto-load** when you work on terminal UI, tables, or progress bars

3. **Reference it explicitly** in prompts: *"Use the rich-library-expert skill to help with this console output"*

The skill is optimized for your Windows 11 environment with specific guidance on Virtual Terminal support, refresh rate tuning, and artifact prevention—all problems Claude typically encounters when working with Rich on Windows.
