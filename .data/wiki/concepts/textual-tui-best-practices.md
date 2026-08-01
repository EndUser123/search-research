---
title: "Textual TUI Best Practices — App Architecture, Workers, Reactive, CSS"
created: 2026-07-24
source: session-2026-07-24
tags: [textual, tui, python, best-practices, workers, reactive, css, architecture]
summary: >
  Best practices for building Textual TUI apps in Python 8.x: worker patterns
  (thread vs async, call_from_thread), reactive attributes (var vs reactive,
  validate/watch/compute), CSS (external .tcss, nesting, variables), app
  structure (compose vs on_mount, @on decorator, state storage). Sources:
  official Textual docs, Will McGugan's blog, GitHub discussions, changelog
  analysis confirming API stability from 0.x through 8.x.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

## Summary

Textual (v8.x) has four core subsystems that each have established best
practices: **Workers** (concurrency), **Reactive attributes** (state with
UI superpowers), **CSS** (styling separation), and **App structure**
(lifecycle, events, state). This concept distills the authoritative
patterns from the official docs, Will McGugan's own code, and the GitHub
community — and confirms via changelog analysis that all patterns below
are stable across the 0.x → 8.x version jumps.

## Decision context

This research was motivated by building the Keep-Smaller-Copy TUI
(`D:\.code\Keep-Smaller-Copy`) on Textual 8.0.2. We needed to know:
which patterns in the existing code were correct, which were violations,
and what the canonical approach is for each subsystem. The wiki already
had [[tui-testing-strategy-python-textual]] (testing) and
[[tui-frameworks-for-personal-scripts]] (framework selection) but no
architecture/best-practices concept.

## 1. Workers (concurrency) [HIGH confidence — official docs + creator's own code]

### Thread vs async workers

| Pattern | When | Key rule |
|---------|------|----------|
| `@work` (async) | I/O-bound (httpx, async subprocess) | Can call UI methods directly |
| `@work(thread=True)` | Blocking I/O (os.walk, subprocess.run, shutil) | **MUST use `call_from_thread()` for ALL UI access** |
| `@work(exclusive=True)` | Cancels previous worker on same method | Prevents out-of-order results |
| `exit_on_error=False` | Don't want worker exceptions to crash the app | Catches and logs instead of exiting |

### The thread-worker golden rule

> From thread workers, you should **avoid calling methods on your UI
> directly** or setting reactive variables. Use `call_from_thread()`.
> — [Official Textual Workers guide](https://textual.textualize.io/guide/workers/)

```python
@work(thread=True, exclusive=True)
def scan_files(self, path: str) -> None:
    worker = get_current_worker()
    for root, dirs, files in os.walk(path):
        if worker.is_cancelled:
            return
        # ... process ...
        self.call_from_thread(self._status, f"Found {count} files")
```

### Worker lifecycle events

```python
def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
    # States: PENDING → RUNNING → CANCELLED / ERROR / SUCCESS
    if event.worker.state == Worker.State.SUCCESS:
        # Worker completed normally
        pass
```

**Source:** https://textual.textualize.io/guide/workers/ (official, authority=3, recency=3)

## 2. Reactive attributes [HIGH confidence — official docs]

### `reactive` vs `var` — the critical distinction

| Attribute type | Triggers refresh? | Triggers layout? | Use when |
|----------------|-------------------|------------------|----------|
| `reactive()` | ✅ (calls `render()`) | ❌ (unless `layout=True`) | Attribute drives displayed content |
| `var()` | ❌ | ❌ | Internal state that shouldn't trigger renders |

**Common mistake:** using `reactive()` for state that doesn't affect `render()`.
This causes unnecessary refreshes.

### The reactive superpowers (4 lifecycle hooks)

```
assign value → compute_*() → validate_*() → watch_*() → refresh (if reactive)
```

1. **`compute_*`** — derived attributes, cached, recalculated when any
   other reactive changes. Avoid slow operations here.
2. **`validate_*`** — validate/clamp incoming values. Return the (possibly
   modified) value.
3. **`watch_*`** — side effects on change. Receives old+new values (if
   2 params) or just new (if 1 param).
4. **Refresh** — automatic for `reactive()`, skipped for `var()`.

### Constructor pitfall: `set_reactive()`

```python
# BAD — watcher fires before widget is mounted, crashes on query_one()
def __init__(self, name="World"):
    super().__init__()
    self.name = name  # triggers watch_name before mount

# GOOD — set without triggering watchers
def __init__(self, name="World"):
    super().__init__()
    self.set_reactive(MyWidget.name, name)
```

### Mutable collections

Textual detects reassignment (`self.items = [...]`) but **not mutation**
(`self.items.append(x)`). After mutating, call:

```python
self.names.append(name)
self.mutate_reactive(MyApp.names)
```

**Source:** https://textual.textualize.io/guide/reactivity/ (official, authority=3, recency=3, last updated May 2025)

## 3. CSS [HIGH confidence — official docs]

### Three CSS classvars (increasing specificity)

| Classvar | Scope | When to use |
|----------|-------|-------------|
| `DEFAULT_CSS` | Widget-level defaults | Reusable widgets — provides sensible defaults |
| `CSS` | App-level inline | Small apps, quick prototypes |
| `CSS_PATH = "app.tcss"` | External `.tcss` file | **Recommended for any non-trivial app** |

### Why external CSS?

1. **Separation of concerns** — styling lives outside logic
2. **Live editing** — `textual run app.py --dev` hot-reloads CSS changes
   without restarting the app
3. **Multiple files** — `CSS_PATH = ["base.tcss", "widgets.tcss"]`
4. **VS Code extension** — official TCSS syntax highlighter available

### CSS best practices

- **Variables** (`$name`) for design tokens — `$accent`, `$panel`, `$text-muted`
- **Nesting** (since v0.47.0) — group related rules, reduce repetition
- **`add_class`/`remove_class`** for dynamic visual state (NOT inline style manipulation)
- **Specificity**: IDs (`#name`) > classes (`.name`) > types (`Button`)
- **Avoid `!important`** — "if everything is important, nothing is"
- **`initial`** value resets to default

```css
/* Nesting example */
#main {
    padding: 1;

    .path-row {
        height: 3;

        Input { width: 1fr; }
        Button { min-width: 11; }
    }
}
```

**Source:** https://textual.textualize.io/guide/CSS/ (official, authority=3, recency=3, last updated Jul 2025)

## 4. App structure [HIGH confidence — creator's blog + official docs + GitHub]

### Lifecycle hooks (order matters)

| Hook | When | What goes here |
|------|------|----------------|
| `compose()` | Building the widget tree | Yield widgets — layout only, no logic |
| `on_mount()` | After widgets are mounted | Load data, check environment, set up intervals |
| `on_unmount()` | Cleanup | Stop timers, close resources |

### Event handling: `@on` decorator vs naming convention

```python
# RECOMMENDED — explicit, clear, no magic names
@on(Button.Pressed, "#scan")
def _start_scan(self) -> None:
    ...

# ALSO VALID — naming convention (auto-dispatched)
def on_button_pressed(self, event: Button.Pressed) -> None:
    ...
```

The `@on` decorator is preferred because:
- Can filter by selector (`"#scan"`, `".primary"`)
- Works on arbitrary events, not just DOM-prefixed names
- Clearer about which widget triggers which handler

### Where to store app state

**From davep (Textualize core dev) in [GitHub discussion #4107](https://github.com/Textualize/textual/discussions/4107):**

> Your app is simply a Python class, so you can "declare" that attribute
> as you generally would with any other Python class: create/assign/type
> the attribute in `__init__`.

```python
class MyApp(App):
    def __init__(self):
        super().__init__()
        self._candidates: list = []      # plain attribute
        self._stop_event = threading.Event()
        self.busy = reactive(False)       # reactive for UI-bound state
```

**Rule of thumb:** `reactive()` for state that drives `render()`. Plain
attributes for internal state. `var()` for state that needs reactive
superpowers (watch/validate) but shouldn't trigger renders.

### `App[ReturnType]` generic

```python
class FolderBrowser(ModalScreen[str]):
    # dismiss("path") returns "path" to caller
    ...

class MyApp(App[dict]):
    def on_button_pressed(self, event):
        self.exit({"result": "data"})  # app.run() returns this
```

### `AUTO_FOCUS` classvar

```python
class MyApp(App):
    AUTO_FOCUS = "Input"  # focus first Input on startup
```

## 5. Version stability (disconfirmation analysis) [HIGH confidence — changelog]

Textual's version history: 0.18 (2023) → 0.89 (2024) → **1.0** (Dec 2024) →
**8.0** (Feb 2026). All patterns above are **stable across this range**.

Breaking changes that DON'T affect these patterns:
- v1.0: default quit key → `ctrl+q` (was `q`)
- v2.0: arbitrary text selection added (new feature, not breaking for existing code)
- v6.0: `Static.renderable` → `Static.content` (only affects code reading that property)
- v0.86: `App.dark` removed → use `App.theme` instead

**Key API additions relevant to TUI best practices:**
- v0.47.0: CSS nesting added
- v0.49.0: `data_bind`, `set_reactive`, `action_toggle` added
- v0.73.0: `mutate_reactive` added
- v1.0.0: `ctrl+q` default quit, `ctrl+c`/`ctrl+v` copy/paste
- v6.2.0: `Pilot.click` returns True if mouse-down hits target

## 6. Violations in the current Keep-Smaller-Copy app

| Violation | Fix |
|-----------|-----|
| Inline `CSS` string (80+ lines) | Move to `CSS_PATH = "app.tcss"` for live editing |
| `busy = reactive(False)` never triggers render | Change to `var(False)` or remove |
| Workers missing `exit_on_error=False` | Add to prevent app crash on scan errors |
| `action_quit` was sync but `App.action_quit` is async in 8.x | Already fixed — `async def action_quit` |
| Comparison logic trapped in `@work` method | Extract to pure function (see refactor plan) |

## Sources

- https://textual.textualize.io/guide/workers/ — Workers guide (official, authority=3, recency=3)
- https://textual.textualize.io/guide/reactivity/ — Reactivity guide (official, authority=3, recency=3, updated May 2025)
- https://textual.textualize.io/guide/CSS/ — CSS guide (official, authority=3, recency=3, updated Jul 2025)
- https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/ — Will McGugan's TUI anatomy (authority=3, evidence=3)
- https://github.com/Textualize/textual/discussions/4107 — State storage Q&A (davep, authority=3)
- https://github.com/Textualize/textual/blob/main/CHANGELOG.md — Full changelog (0.18 → 8.2.8)
- https://realpython.com/python-textual/ — Real Python tutorial (authority=2, Mar 2025)

## Related

- [[tui-testing-strategy-python-textual]]@related — 4-layer testing stack
- [[tui-frameworks-for-personal-scripts]]@related — Framework selection (Rich → Textual)
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
