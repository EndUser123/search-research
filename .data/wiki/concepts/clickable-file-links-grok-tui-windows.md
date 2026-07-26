---
title: "Clickable file links in Grok Build TUI (Windows 11)"
created: 2026-07-23
source: session-2026-07-23 (operator-provided format)
tags: [tui, windows, file-links, osc8, terminal, rendering, clickable, file-uri]
agent: grok
host: grok
verification: directly-verified
cognitive_load: 1
summary: >
  To make a file path clickable in the Grok Build TUI on Windows 11,
  use the file:// URI scheme with forward slashes: file:///C:/Users/...
  Backslashes, markdown backticks, tilde shorthand, and bare Windows
  paths are NOT clickable. The link opens in the OS default editor.
---

## The format

```
file:///C:/Users/brsth/.grok/skills/www/SKILL.md
```

Rules:

1. **Prefix with `file:///`** (three slashes)
2. **Use forward slashes** — backslashes break the link
3. **Convert the path before output**: `C:\Users\...` → `file:///C:/Users/...`
4. **No markdown wrapper** — bare URI is sufficient
5. **No raw Windows paths** — `C:\...` is not clickable in Windows Terminal
6. **No `~` shorthand** — use the full absolute path

## What does NOT work

| Format | Clickable? | Why |
|---|---|---|
| `file:///C:/Users/...` | ✅ Yes | Correct format |
| `C:\Users\...` (bare) | ❌ No | Backslashes + no scheme |
| `C:/Users/...` (bare) | ❌ No | No `file:///` prefix |
| `` `C:\Users\...` `` (backtick) | ❌ No | Renders as inline code, not link |
| `~/.grok/...` | ❌ No | Tilde not resolved by terminal |

## Examples

```
file:///P:/.data/wiki/concepts/model-fleet-provider-pools.md
file:///C:/Users/brsth/.grok/skills/tp/SKILL.md
file:///C:/Users/brsth/.grok/AGENTS.md
```

## Decision context

The operator asked how to show clickable file links. The model tried
plain text paths, backtick-wrapped paths, and backslash paths — all
failed. The operator provided the correct `file:///` format with
forward slashes, which was verified to open in the default editor.
