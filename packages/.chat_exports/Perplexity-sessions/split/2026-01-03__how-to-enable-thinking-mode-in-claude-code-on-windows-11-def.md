---
title: "how to enable thinking mode in claude code on windows 11.  default is alt+tab but that doesn't work on windows 11."
date: "2026-01-03"
mode: "COPILOT"
uuid: "cd503845-6a91-4d6f-b8c9-b32ac5dfc6b6"
entry_count: 1
---

## Human

how to enable thinking mode in claude code on windows 11.  default is alt+tab but that doesn't work on windows 11.

## Assistant

Thinking mode in Claude Code on Windows 11 is no longer reliably toggled with Alt+Tab; instead you should use the built‑in toggle in `/config` and/or thinking trigger words in your prompts.[1][2]

## Current toggle behavior

- In recent Claude Code builds (around 2.0.6x+), Tab/Alt+Tab toggling is partially broken or repurposed, and users report that “tab doesn’t enable or disable thinking” anymore.[3][4][1]
- The recommended path on desktop is to open the in‑session configuration (`/config`) and flip the **Thinking mode** setting between true/false rather than relying on the old Tab shortcut.[5][1]

## How to enable thinking mode now

On Windows 11 Claude Code (native client / PowerShell):

1. In an active Claude Code session, type `/config` and send it.[1]
2. In the configuration UI that appears, locate the **Thinking mode** or similar extended thinking option (wording can vary slightly by version).[4][1]
3. Set it to **true** (or “enabled”), then save/close the config view.[1]
4. The state is “sticky”: once enabled it will stay on until you toggle it off again.[6][4]

If you do **not** see a thinking toggle in `/config`, your version may be one of the builds where UI toggling was removed or bugged; in that case, Claude Code will still honor **thinking trigger words** in your prompt:

- Include words like **think**, **think harder**, or **ultrathink** in your instructions to invoke deeper internal reasoning for that message.[7][2]
- This pattern is documented in multiple guides as the intended way to select different reasoning “levels” inside Claude Code.[2][7]

## Why Alt+Tab doesn’t work on Windows 11

- Windows reserves Alt+Tab for system‑level application switching, so a desktop app generally cannot override it globally for an in‑app toggle.[8]
- Claude Code’s thinking toggle shortcut has been shifted to Tab alone or to config‑based toggles in newer versions, and some releases have regressions where the keybinding simply does not work at all.[3][4][1]

If you want, the next step can be to set up a small AutoHotkey script that maps some other key (for example Ctrl+Alt+T) to send `/config` or a pre‑made “ultrathink” prefix into the Claude Code window for a closer to one‑key workflow on Windows 11.
