---
name: rich-library-expert
description: Terminal UI mastery using Rich library for console output, renderables, and cross-platform support.
version: 1.0.0
status: stable
category: development
tags: ['terminal', 'ui', 'rich', 'console', 'formatting', 'python']
triggers:
  - '/rich-skill'
aliases:
  - '/rich-skill'

suggest:
  - /docs
  - /build
  - /nse
---


# Rich Library Expert

**Role**: Specialized expertise in Rich library terminal rendering, advanced console patterns, context lifecycle management, and cross-platform optimization for Windows, macOS, and Linux environments.

## Purpose

Terminal UI mastery using Rich library for console output, renderables, and cross-platform support.

## Project Context

### Constitution/Constraints
- Single Console object pattern (no multiple instances)
- Context manager lifecycle for Live/Status/Progress
- Windows Terminal optimization (Virtual Terminal, refresh rates)
- Solo-developer appropriate (no enterprise monitoring)

### Technical Context
- Official Documentation: https://rich.readthedocs.io/
- GitHub Repository: https://github.com/Textualize/rich
- Key renderables: Table, Panel, Layout, Live, Progress, Status
- CKS knowledge base: `/cks "Rich library"` for reference docs

### Architecture Alignment
- Integrates with `/docs` for documentation patterns
- Works alongside `/build` for console output in builds
- Suggests `/nse` for intelligent recommendations

## Your Workflow

1. **Initialize Console**: Create single module-level Console object
2. **Context Manager**: Use `with` statements for Live/Status/Progress
3. **Manual Lifecycle**: Use `.start()/.stop()` when context manager not viable
4. **Windows Cleanup**: Call `.clear_live()` after `.stop()` on Windows
5. **Batch Updates**: Minimize redraws for performance

### Core Pattern: Console Lifecycle
- **Static output**: `console.print()`
- **Status spinner**: `with console.status()`
- **Live display**: `with Live() as live:`
- **Progress bar**: `with Progress() as progress:`
- **Manual control**: `progress.start()` → updates → `progress.stop()` → `progress.console.clear_live()`

## Validation Rules

### Critical Anti-Patterns
- Do NOT mix multiple Console objects (causes conflicts)
- Do NOT use `print()` instead of `console.print()`
- Do NOT nest Live/Status context managers (causes errors)
- Do NOT create Live objects without context manager

### Windows-Specific Rules
- Always call `progress.console.clear_live()` after `.stop()` to prevent cursor artifacts
- Lower `refresh_per_second` (try 4 Hz) if flickering occurs

### Prohibited Actions
- Do NOT use nested context managers
- Do NOT skip Windows cleanup on terminal apps

**When to Use**:
- Terminal UI implementation and interactive applications
- Real-time progress tracking and status indicators
- Data visualization and formatted output (tables, panels, layouts)
- Debugging aids and pretty-printing
- Structured logging with Rich handlers
- Dashboard-style applications with live updates

**Key Capabilities**:
- Advanced Console lifecycle and context management
- All Rich renderables (Table, Panel, Layout, Live, Progress, Status)
- Proper error handling for common rendering conflicts
- Windows Terminal environment optimization (Virtual Terminal, refresh rates)
- Performance tuning and resource optimization
- Multi-threaded Live updates with proper synchronization

---

## Quick Reference: Console Initialization

Always initialize a **single, module-level Console object** rather than creating multiple instances:

```python
# ✅ CORRECT: Single console object
from rich.console import Console

console = Console()

# Then import from anywhere:
# from my_app.console import console
```

This ensures consistent output formatting and prevents conflicts with context managers like `Live()` and `Status()`.

---

## Core Pattern: Console Lifecycle & Context Managers

### Basic Pattern
```python
from rich.console import Console

console = Console()

# For output that doesn't need updates:
console.print("[bold blue]Static output[/bold blue]")

# For output that updates over time, use context managers:
with console.status("[bold yellow]Processing...") as status:
    # Perform operations
    status.update("[bold green]Step 1 complete[/]")
    time.sleep(1)
    status.update("[bold green]Step 2 complete[/]")
```

### Key Context Managers

**Status (spinner with text)**:
```python
with console.status("[bold cyan]Connecting...") as status:
    result = connect_to_server()
    status.update("[bold green]Connected!")
```

**Live Display (full control)**:
```python
from rich.live import Live
from rich.table import Table

table = Table(title="Live Data")
table.add_column("Column A")
table.add_column("Column B")

with Live(table, refresh_per_second=4) as live:
    for i in range(100):
        table.add_row(f"Row {i}", f"Value {i}")
        live.update(table)
```

**Progress Bar**:
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Processing...", total=100)
    for i in range(100):
        do_work()
        progress.update(task, advance=1)
```

---

## Critical Pattern: Manual Progress/Live Outside Context Manager

Use `.start()` and `.stop()` when you need control outside context managers (e.g., multi-step workflows, event-driven updates):

```python
from rich.progress import Progress

progress = Progress()
progress.start()  # Start explicitly

task = progress.add_task("[blue]Processing", total=100)

# ... perform operations ...
progress.update(task, advance=25)

# ... more work ...
progress.update(task, advance=25)

progress.refresh()  # Manual refresh if needed
progress.stop()     # Clean shutdown
progress.console.clear_live()  # Cleanup on Windows/Notebooks
```

**Windows-Specific Note**: Call `progress.console.clear_live()` after `.stop()` to prevent orphaned cursor artifacts in Windows Terminal.

---

## CKS: Extended Reference Documentation

**Detailed reference documentation is stored in CKS** (Constitutional Knowledge System). Use `/cks` to query:

| Topic | CKS Query |
|-------|-----------|
| Tables, Panels, Layouts, Live, Progress, Status spinners | `/cks "create Rich library tables panels layouts"` |
| DO/DON'T patterns and anti-patterns | `/cks "common Rich library patterns anti-patterns"` |
| Styling, colors, markup syntax | `/cks "style Rich library output colors"` |
| Markdown, logging, tracebacks, pretty printing | `/cks "Rich library advanced features Markdown logging debugging"` |
| Windows Terminal optimization | `/cks "optimize Rich library Windows Terminal"` |
| Performance tips, asyncio, argparse integration | `/cks "Rich library performance tips integration patterns"` |
| Troubleshooting common issues | `/cks "troubleshoot common Rich library issues"` |

---

## Essential Quick Patterns

### Markup Syntax
```python
console.print("[bold red]Error:[/] File not found")
console.print("[cyan underline]https://example.com[/]")
console.print("[on yellow black]Highlighted[/]")
```

**Markup**: `[style_name]text[/]`
- Colors: `red`, `blue`, `green`, `yellow`, `magenta`, `cyan`, `white`, `black`, `bright_red`, etc.
- Effects: `bold`, `dim`, `italic`, `underline`, `strike`, `blink`
- Backgrounds: `on_red`, `on_blue`, etc.

### Critical Anti-Patterns
- ❌ DON'T: Mix multiple Console objects (causes conflicts)
- ❌ DON'T: Use `print()` instead of `console.print()` (bypasses formatting)
- ❌ DON'T: Nest Live/Status context managers (causes errors)
- ❌ DON'T: Create Live objects without context manager (won't display)

### Windows Cursor Cleanup
Always call after `.stop()`:
```python
progress.console.clear_live()  # Prevents orphaned cursor artifacts
```

---

## Teachable Moments for Claude

When assisting with Rich library tasks, Claude should:

1. **Always initialize a single Console object** and import it where needed
2. **Default to context managers** (`with` statements) for Live/Status/Progress
3. **Use `.start()/.stop()` only when context manager isn't viable** (multi-step workflows)
4. **Always call `.clear_live()` after Progress/Live on Windows** to prevent artifacts
5. **Batch table updates** to minimize redraws
6. **Use Rich markup (`[bold red]...[/]`)** instead of ANSI codes
7. **Explain `refresh_per_second` tuning** when performance is a concern
8. **Provide complete, runnable examples** that show proper lifecycle management
9. **Avoid nested context managers** (e.g., Status inside Status)
10. **Validate that output works across Windows, macOS, and Linux** when cross-platform is relevant

**When detailed reference is needed**, query CKS:
- For renderable-specific syntax: `/cks "create Rich library tables panels layouts"`
- For platform-specific issues: `/cks "optimize Rich library Windows Terminal"`

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "NotRenderableError" | Don't pass non-renderable objects; wrap in Panel or Text |
| Live display won't update | Use context manager or call `.start()` before updates |
| Spinner/Progress flickering on Windows | Lower `refresh_per_second` (try 4 Hz) and add `.clear_live()` |
| Colors not showing | Enable `force_terminal=True` or check `$TERM` env var |
| Text wrapping incorrectly | Set explicit table `width` or Panel size |
| Nested context manager conflict | Never nest Live/Status; use one or switch between them |
| Orphaned cursor after exit | Call `console.clear_live()` after `.stop()` |

---

## Resources

- **Official Documentation**: https://rich.readthedocs.io/
- **GitHub Repository**: https://github.com/Textualize/rich
- **Rich Box Styles**: https://rich.readthedocs.io/en/stable/tables.html#box-styling
- **Markup Reference**: https://rich.readthedocs.io/en/latest/markup.html
- **CKS Knowledge Base**: `/cks "Rich library"` for ingested reference documentation
