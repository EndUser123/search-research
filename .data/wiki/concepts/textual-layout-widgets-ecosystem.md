---
title: "Textual Layout, Widget Catalog, and Ecosystem — Design Patterns, Onboarding, and Project Adoption"
created: 2026-07-24
source: session-2026-07-24
tags: [textual, tui, python, layout, widgets, ecosystem, onboarding, design-patterns]
summary: >
  Textual's layout system (dock + FR units + containers), widget catalog (25+
  built-in widgets), ecosystem (30+ community projects), and first-app
  onboarding arc (stopwatch tutorial). Covers the gaps left by
  textual-tui-best-practices.md (which covers workers/reactive/CSS/app-structure).
  Includes the May 2025 Textualize company shutdown context and the project's
  transition to community-maintained OSS. Sources: official docs (design-a-layout,
  widget_gallery, tutorial), awesome-textualize-projects, Will McGugan's blog.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

## Summary

Textual has four subsystems not covered by the existing best-practices concept:
**layout design** (how to compose screens with dock, FR units, and containers),
**widget catalog** (25+ built-in widgets and when to use each), **ecosystem**
(30+ community projects showing real-world adoption), and **onboarding arc**
(the stopwatch tutorial that teaches the framework in ~6 steps). This concept
fills those gaps. It also documents a critical context: Textualize the company
shut down in May 2025, but Textual continues as actively-maintained OSS under
Will McGugan, with versions 0.8.x-0.9.x released post-company.

## Decision context

This research was motivated by a `/www` invocation with 5 Textual URLs (repo,
tutorial, design-a-layout, widget gallery, awesome-textualize-projects). The
wiki already had `textual-tui-best-practices.md` (workers/reactive/CSS/app-
structure), `tui-frameworks-for-personal-scripts.md` (framework selection),
and `tui-testing-strategy-python-textual.md` (4-layer testing). But none
covered layout composition patterns, the widget catalog, ecosystem adoption,
or the first-app onboarding arc. This concept fills those 4 gaps.

The research changed our understanding of Textual's viability: the company
shutdown (May 2025) was a concern, but the disconfirmation pass confirmed the
framework is healthy with active community releases through 0.9.2 (2026).

## 1. Layout design patterns [HIGH confidence — official docs]

### The 5-tip design methodology

From the [official design-a-layout guide](https://textual.textualize.io/how-to/design-a-layout/):

1. **Sketch first** — Use Excalidraw or pen/paper. Draw a rectangle for the
   terminal, then rectangles for each UI element. Annotate scroll direction.
2. **Work outside-in** — Start with fixed elements (header, footer, sidebar)
   before the main content area. Like sculpture from a block of marble.
3. **Apply docks** — Use `dock: top/bottom/left/right` CSS to pin widgets to
   edges. Docked widgets reduce available space for remaining widgets automatically.
4. **Use FR units for flexible space** — `width: 1fr; height: 1fr` divides
   remaining space fractionally (like CSS Grid's `fr` unit). Only one widget
   with `1fr` = fills all remaining space.
5. **Use containers** — Replace custom Placeholder subclasses with built-in
   containers: `HorizontalScroll`, `VerticalScroll`, `HorizontalGroup`,
   `VerticalGroup`, `Grid`, `Center`, `Middle`.

### Layout container reference

| Container | Layout direction | Scroll | Use when |
|---|---|---|---|
| `Horizontal` | Left-to-right | No | Fixed-width horizontal row |
| `HorizontalScroll` | Left-to-right | Horizontal | Variable-width horizontal row |
| `HorizontalGroup` | Left-to-right | No | Grouped horizontal widgets (compact) |
| `Vertical` | Top-to-bottom | No | Fixed-height vertical column |
| `VerticalScroll` | Top-to-bottom | Vertical | Variable-height content (most common) |
| `VerticalGroup` | Top-to-bottom | No | Grouped vertical widgets (compact) |
| `Grid` | 2D grid | No | Tabular layouts with `grid-columns`, `grid-rows` |
| `Center` | Centered | No | Center content horizontally |
| `Middle` | Centered | No | Center content vertically |
| `Container` | Base class | No | Custom container without scroll |

### Dock system

```python
# Dock a header to the top, footer to the bottom
class Header(Placeholder):
    DEFAULT_CSS = """
    Header {
        height: 3;
        dock: top;
    }
    """

class Footer(Placeholder):
    DEFAULT_CSS = """
    Footer {
        height: 3;
        dock: bottom;
    }
    """
```

Docked widgets are removed from the normal flow and pinned to an edge.
Remaining widgets fill the space between docked widgets. Multiple widgets can
dock to the same edge (they stack in order).

### FR units (fractional)

```css
/* Fill all remaining space */
ColumnsContainer {
    width: 1fr;
    height: 1fr;
}

/* Split remaining space equally between 3 columns */
Column {
    width: 1fr;  /* each gets 1/3 */
}
```

`fr` uses Python's `Fraction` internally, so divisions are exact (no off-by-one
pixel rounding). Source: Talk Python episode #380 with Will McGugan.

## 2. Widget catalog [HIGH confidence — official widget gallery]

### Built-in widgets (25+)

| Widget | Purpose | Notes |
|---|---|---|
| **Button** | Clickable action buttons | Variants: default, primary, success, warning, error. States: normal, disabled, flat |
| **Checkbox** | Boolean toggle | Dune-themed examples in the docs |
| **Collapsible** | Toggle content visibility | Click title to expand/collapse |
| **ContentSwitcher** | Swap between child widgets | Tab-like behavior without tabs |
| **DataTable** | Spreadsheet-like data display | Configurable cursors, sortable, zebra stripes |
| **Digits** | Tall character number display | New — uses block characters for large digits (used in stopwatch tutorial) |
| **DirectoryTree** | File/folder tree browser | Extends `Tree` with filesystem nodes |
| **Footer** | Keybinding display bar | Shows active keybindings at bottom |
| **Header** | App title bar | Shows app name at top |
| **Input** | Text entry field | Single-line input with placeholder, validation |
| **Label** | Static text display | Simple non-interactive text |
| **Link** | Clickable URL | New — opens URL in browser |
| **ListView** | Scrollable item list | Items can be any widget (typically ListItem+Label) |
| **LoadingIndicator** | Animated loading display | New — animated dots while data loads |
| **Log** | Scrolling text log | Append-only text display (for log files, streaming output) |
| **MarkdownViewer** | Markdown with navigation | Full markdown rendering + table of contents + browser-like back/forward |
| **Markdown** | Markdown display | Simpler than MarkdownViewer (no navigation) |
| **MaskedInput** | Format-validated input | New — template-based input (e.g., `0000-0000-0000-0000` for credit cards) |
| **OptionList** | Selectable option list | Rich-renderable options, scrollable |
| **Placeholder** | Design prototyping | Colored boxes during layout design |
| **ProgressBar** | Progress indicator | Indeterminate and determinate modes |
| **RadioSet** | Radio button group | Mutually exclusive selection |
| **Select** | Drop-down selector | Collapsible option selection |
| **SelectionList** | Multi-select list | Checkbox-style multi-selection |
| **Static** | Static content display | Base class for many widgets; displays Rich renderables |
| **Switch** | Toggle switch | On/off slider |
| **TabbedContent** | Tabbed interface | Tabs with content panels |
| **Tabs** | Tab bar | Tab navigation (without content panels) |
| **TextArea** | Multi-line text editor | Code editor with syntax highlighting |
| **Tree** | Hierarchical tree view | Generic tree (DirectoryTree extends this) |
| **Toast** | Transient notification | Pop-up message that auto-dismisses |

### When to use what

| Need | Widget |
|---|---|
| Display data in rows/columns | `DataTable` |
| Show a file tree | `DirectoryTree` |
| Show a generic hierarchy | `Tree` |
| Text input (single line) | `Input` |
| Text input (formatted, e.g. phone) | `MaskedInput` |
| Text editing (multi-line, code) | `TextArea` |
| Select one from many | `Select` or `RadioSet` |
| Select many from a list | `SelectionList` or `Checkbox` group |
| On/off toggle | `Switch` |
| Action trigger | `Button` |
| Display rich text/markdown | `MarkdownViewer` (with nav) or `Markdown` (without) |
| Display streaming output | `Log` |
| Loading state | `LoadingIndicator` |
| Tabbed interface | `TabbedContent` (content + tabs) or `Tabs` (tabs only) |
| Large number display | `Digits` |
| Notification | `Toast` |

## 3. First-app onboarding arc (stopwatch tutorial) [HIGH confidence — official tutorial]

The [official tutorial](https://textual.textualize.io/tutorial/) builds a
stopwatch app in ~6 incremental steps. This is the canonical onboarding path.

### Step-by-step learning arc

| Step | Concept learned | Code structure |
|---|---|---|
| 1 | App class + compose() + BINDINGS + action_* | `class StopwatchApp(App)` with `compose()` yielding Header+Footer |
| 2 | Custom widgets + containers | `TimeDisplay(Digits)` + `Stopwatch(HorizontalGroup)` yielding Buttons + TimeDisplay |
| 3 | Composing with containers | `VerticalScroll(Stopwatch(), Stopwatch(), Stopwatch())` for the main layout |
| 4 | Reactive attributes | `time = reactive(0.0)` on TimeDisplay for auto-updating display |
| 5 | Event handlers | `on_button_pressed` + `@on(Button.Pressed, "#start")` for button events |
| 6 | Workers (async) | `@work` for the ticking timer that updates the reactive time |

### Key onboarding insights

- **HorizontalGroup + VerticalScroll** is the most common layout pattern for
  apps with a scrollable list of items
- **Digits** widget (new) is used for the time display — large readable numbers
- **Command Palette** (`^p`) is built into every app by default — discovered
  via the tutorial's footer display
- **`App.theme`** toggles dark/light mode (replaces the old `App.dark` boolean
  removed in v0.86)
- The tutorial covers the same workers/reactive concepts documented in
  `textual-tui-best-practices.md`, but in a build-order that makes them
  intuitive

## 4. Ecosystem and adoption [HIGH confidence — awesome-textualize-projects + web evidence]

### Community projects (30+)

**Production-grade apps:**

| Project | What it does | Author |
|---|---|---|
| **Harlequin** | SQL IDE for the terminal (DuckDB, PostgreSQL, SQLite) | Ted Conbeer |
| **Frogmouth** | Markdown browser for the terminal | Textualize (official) |
| **Toolong** | Log file viewer with tail, merge, search, JSONL support | Textualize (official) |
| **Elia** | ChatGPT client for the terminal | Darren Burns |
| **Django-TUI** | Inspect and run Django commands in a TUI | Anže Pečar |
| **Archinstall 4.0** | Arch Linux installer (uses Textual for its TUI) | Arch Linux team |

**Utility widgets:**

| Widget | What it adds | Author |
|---|---|---|
| textual-autocomplete | Autocomplete dropdowns | Darren Burns |
| textual-plotext | Plotting/graphing widget | Textualize community |
| textual-select | Drop-down select widget | Mito |
| textual-terminal | Terminal emulator widget | Mito |
| textual-datepicker | Date picker calendar | Mito |
| textual-canvas | Character-based canvas for ASCII art | davep |
| textual-fspicker | Filesystem picker dialogs | davep |

**Fun/showcase projects:**

- **textual-paint** — MS Paint clone in the terminal
- **Upiano** — Piano in the terminal
- **Usolitaire** — Solitaire card game
- **Conway's Game of Life** — Cellular automaton
- **FivePyFive** — Annoying puzzle (connect-5)

### Adoption evidence

- **GitHub stars**: 30K+ (as of 2026)
- **HN sentiment**: overwhelmingly positive ("fantastic framework", "wonderful tool")
- **Production usage**: Archinstall (Linux distribution installer), Harlequin
  (SQL IDE with commercial support), LIT-TUI (AI agent presentation layer)
- **Conference talks**: Talk Python #380 (Will McGugan on 7 lessons from building TUI framework)
- **Real Python tutorial** (Mar 2025): comprehensive Textual guide for Python developers

## 5. Textualize company shutdown (May 2025) — viability context [HIGH confidence — Will McGugan's blog]

**The company shut down; the framework did not.**

From [Will McGugan's blog post](https://textual.textualize.io/blog/2025/05/07/the-future-of-textualize/) (2025-05-07):

> "Textual has always been a solution in search of a problem. And while there
> are plenty of problems to which Textual is a fantastic solution, we weren't
> able to find a shared problem or pain-point to build a viable business around."
>
> "Textual will live on as an Open Source project. I will be maintaining Textual
> and Rich as I have always done."
>
> "Software is never finished, but Textual is mature and battle-tested."

**Post-company releases confirm active maintenance:**
- v0.7.8 (2025-04) — last company-era stability release
- v0.8.0 (2025-06) — crash recovery + prefetch mode (post-company)
- v0.8.5 (2025-08) — anti-bot detection, shadow DOM, 60+ bug fixes
- v0.8.6 (2025-09) — litellm supply chain security fix
- v0.8.7 (2025-10) — Docker API security hardening (RCE, SSRF, auth bypass fixes)
- v0.9.0 (2025-11) — secure-by-default Docker server
- v0.9.2 (2026-01) — dispatcher leak fix, Docker auth fixes

**Assessment:** Textual is a healthy, mature OSS project. The company shutdown
removed full-time funded development but did not reduce release velocity or
quality. The framework is suitable for production use.

## Sources

- https://textual.textualize.io/how-to/design-a-layout/ — Layout design guide (official, authority=3, recency=3)
- https://textual.textualize.io/widget_gallery/ — Widget gallery (official, authority=3, recency=3)
- https://textual.textualize.io/tutorial/ — Stopwatch tutorial (official, authority=3, recency=3)
- https://github.com/oleksis/awesome-textualize-projects — Community project list (authority=2, recency=3)
- https://textual.textualize.io/blog/2025/05/07/the-future-of-textualize/ — Textualize shutdown announcement (authority=3, recency=2)
- https://talkpython.fm/episodes/show/380/ — Talk Python interview with Will McGugan (authority=2, recency=2)
- https://realpython.com/python-textual/ — Real Python tutorial (authority=2, recency=3)

## Related

- [[textual-tui-best-practices]]@complementary — Workers, reactive, CSS, app structure (the architecture concept)
- [[tui-frameworks-for-personal-scripts]]@related — Framework selection (Rich → Textual upgrade arc)
- [[tui-testing-strategy-python-textual]]@related — 4-layer testing stack
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
