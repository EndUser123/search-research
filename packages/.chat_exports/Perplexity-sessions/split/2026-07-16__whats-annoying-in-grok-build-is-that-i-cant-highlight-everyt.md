---
title: "what's annoying in grok build, is that I can't highlight everything I want and ctrl+c to copy.  Is there a way to enable"
date: "2026-07-16"
mode: "COPILOT"
uuid: "45fdc336-d335-4173-bebb-0e6dbfd9606b"
entry_count: 1
---

## Human

what's annoying in grok build, is that I can't highlight everything I want and ctrl+c to copy.  Is there a way to enable this?

## Assistant

You can’t currently switch Grok Build’s TUI into “normal terminal” selection mode, but there is a workaround for selecting and copying arbitrary ranges of text: hold Shift while dragging to select, then copy.[1]

## What’s going on

Grok Build runs in a custom text UI that doesn’t behave like a standard terminal buffer, so your usual mouse selection + Ctrl+C often doesn’t work the way it does in plain Warp, Windows Terminal, or iTerm.  The UI is optimized for structured steps, panes, and progress, not traditional text selection, which is why selection feels constrained.[2][3][4]

## Current workaround

According to a recent Grok Build issue filed by users on Warp/Windows:

- You can select arbitrary text if you hold Shift while dragging with the mouse inside Grok Build.[1]
- Once the region is highlighted, Ctrl+C (or right‑click → Copy, depending on your terminal) will copy just that selection instead of the whole line/pane.[1]

This is explicitly described as a temporary workaround, which implies the current behavior is considered a bug or limitation rather than a deliberate “no selection” design.[1]

## Is there a setting to enable “normal” selection?

Right now there’s no documented flag or config option in the Grok Build CLI or changelog that turns off the TUI and restores raw terminal selection behavior.  The official materials focus on features like `/goal`, subagents, MCP support, and project skills, but don’t mention a selection mode toggle.[5][6][3][4][2]

So, as of the latest public info:

- FACT: Shift + mouse drag lets you select text more flexibly in Grok Build on Windows/WSL and Warp.[1]
- CONSENSUS: There is no stable “disable TUI / enable native selection” option exposed in the CLI yet.[4][5][2]
- SPECULATION (medium confidence): xAI will likely address this with a config or improved selection behavior in a future release, given it’s tracked as an issue and labeled a temporary workaround.[5][1]

## Practical next steps

If you want a reliable way to copy larger blocks right now:

1. In Grok Build, hold Shift and drag with the mouse to select the text you want.[1]
2. Press Ctrl+C to copy the selection; paste into your editor/notes as usual.[1]
3. If this still misbehaves in your environment, check that your terminal emulator (Warp, Windows Terminal, iTerm, etc.) isn’t intercepting Shift+drag or remapping copy bindings.

If you’d like, I can look up whether your specific terminal (Warp on Windows, Windows Terminal, etc.) has any extra settings that make Grok Build selection less painful—what terminal are you running Grok Build in right now?  
