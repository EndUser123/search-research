---
title: "File link format for Windows Terminal (file:/// URI)"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [windows, terminal, file-links, file-uri, hyperlink, osc8, tui]
agent: grok
host: grok
cognitive_load: 1
verification: directly-verified
sources:
  - Session transcript turns 192-208 (empirical testing of 6 link formats)
  - ~/.grok/skills/www/SKILL.md (line 266, Edit tool parameter rendering)
relations:
  - target: wiki/concepts/clickable-file-links-grok-tui-windows.md
    type: extends
---

# File link format for Windows Terminal (file:/// URI)

## The format

To create a Ctrl+Click-openable file link in output, convert Windows paths to `file:///` URIs:

1. Replace all backslashes with forward slashes
2. Prefix with `file:///` (three slashes)

Example:
```
C:\Users\brsth\.grok\skills\www\SKILL.md
  → file:///C:/Users/brsth/.grok/skills/www/SKILL.md
```

## Rules

1. **Prefix with `file:///`** (three slashes)
2. **Use forward slashes** — backslashes break the link
3. **Convert the path before output** — the URI is the link target, not the display text
4. **No markdown wrapper** — bare URI is sufficient
5. **No raw Windows paths** — `C:\...` is not clickable in Windows Terminal
6. **No `~` shorthand** — use the full absolute path

## What does NOT work

| Format | Clickable? | Why |
|---|---|---|
| `file:///C:/Users/...` | Yes | Correct URI scheme |
| `C:\Users\...` (bare) | No | Backslashes + no scheme |
| `C:/Users/...` (bare forward slashes) | No | No `file:///` prefix |
| `` `C:\Users\...` `` (backtick) | No | Renders as inline code |
| `~/.grok/...` | No | Tilde not resolved by terminal |
| `[text](file:///C:/...)` markdown | Yes (via URI) | Terminal detects the URI inside markdown, not the display text |

## What this means for another LLM

> To create a Ctrl+Click-openable file link in this terminal, output the path as a `file:///` URI: forward slashes, `file:///` prefix, drive letter after the third slash.
>
> Format: `file:///<drive>/<path>`
>
> Example: `file:///C:/Users/brsth/.grok/skills/www/SKILL.md`
>
> Do NOT output raw Windows paths (`C:\...`) — Windows Terminal does not auto-detect those as links. Do NOT rely on markdown link syntax with display text — the terminal makes the URI clickable, not the bracket text.

## Why this matters

This is a hard-won, non-obvious terminal behavior. Future sessions producing file references would otherwise rediscover it by trial. The `file:///` URI is the portable standard — works regardless of home-directory configuration and in any modern terminal (WT, WezTerm, iTerm2, Kitty).

## Receipts

- Session transcript turn 193 — operator confirmed `file:///` format works
- Session transcript turn 202 — backslash format confirmed not clickable
- Session transcript turn 204 — bare forward-slash path confirmed not clickable
- Session transcript turn 206 — operator asked for the rules to give to another LLM
