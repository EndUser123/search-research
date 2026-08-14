---
title: "I often paste from claude code to you and the response back and forth.  Is there a way to automate this?"
date: "2026-02-28"
mode: "COPILOT"
uuid: "20a82bfa-8723-4c2b-b63b-1185cbbe6131"
entry_count: 1
---

## Human

I often paste from claude code to you and the response back and forth.  Is there a way to automate this?

## Assistant

Yes, but not fully end‑to‑end “no clipboard involved” yet; you can, however, get very close with the right combo of tools on Windows plus some light glue.

## 3 practical levels of automation

### 1. Low‑friction manual (no setup)

These are the “do today” ergonomics upgrades:

- Use global shortcuts:
  - Alt+Tab between Claude Code and browser, Ctrl+A / Ctrl+C / Ctrl+V.
  - Map mouse side buttons or a Stream Deck to those key chords using AutoHotkey or PowerToys.
- Keep one dedicated Perplexity **thread** per coding session so you don’t need to re-explain context each time.[1]

This doesn’t remove copying, but it makes the loop much faster.

### 2. OS‑level macros (what I’d actually do first)

On Windows 11, you can get near‑hands‑free copy‑relay with:

- **AutoHotkey script**:
  - Hotkey in Claude terminal or editor:
    - Select current block (e.g., paragraph / fenced code block via editor shortcuts).
    - Copy to clipboard.
    - Switch to Perplexity window.
    - Paste into the chat box.
    - Optionally send Enter.
  - Another hotkey that:
    - Copies the latest Perplexity answer (e.g., Ctrl+L, Ctrl+C or DOM‑focused selection).
    - Switches back to Claude Code.
    - Pastes either into:
      - Your “context” buffer (for Claude), or
      - A scratch file that Claude is already watching.

Concrete sketch in AHK (pseudo):

```ahk
; Send selected text from current app → Perplexity
^!p::  ; Ctrl+Alt+P
  Send ^c
  WinActivate, Perplexity
  Sleep 100
  Send ^v
  return

; Send last Perplexity answer → current editor
^!o::  ; Ctrl+Alt+O
  WinActivate, Perplexity
  ; here you might script a click into the last message, select all in that div, copy
  ; (XPath/Acc library or fixed coordinates if your layout is stable)
  ; then:
  WinActivate, ahk_exe Code.exe
  Send ^v
  return
```

You’ll want to tailor this to your exact Claude Code UX and Perplexity layout. Once tuned, it becomes “muscle memory”: press one combo to fire content to Perplexity, another to pull the answer back.

### 3. Browser‑side helpers (if you lean into a custom browser)

If you’re using a Chromium‑based browser (including Comet), you can:

- Install a “copy last response block” userscript/extension that:
  - Adds a button beside each Perplexity message to copy as markdown/plain text.
  - Gives you a consistent DOM target for automation (CSS selector), which makes step 2’s AHK much more robust.[2]
- In Comet specifically, you can take advantage of its tight AI integration to reduce context‑switching in the browser itself, though it won’t directly talk to Claude Code yet.[3][4][5]

This still uses the clipboard, but the number of clicks and selections drops to nearly zero.

## Is a *full* Claude ↔ Perplexity pipe possible?

- There is **no official direct API bridge** between Claude Code and Perplexity right now, so you can’t just “wire” them together in a clean programmatic way from either side.[1]
- You *could* roll a custom integration if you:
  - Drive Claude Code via its CLI / local interface.
  - Call Perplexity’s API (if/when accessible to you) from a local script.
  - Use that script as the “hub” that sends prompts to both and relays content.
- But in practice, for your workflow, an AHK + small conventions layer is usually 90% of the value for 10% of the effort.

## Suggested concrete path for you

Given your setup:

1. Pick two global hotkeys and define:
   - “Send current selection to Perplexity and focus it.”
   - “Copy last Perplexity reply and paste into the currently focused editor/terminal.”
2. Add a browser helper (extension or userscript) that:
   - Gives a stable “copy last answer” button/selector.
3. If it feels good, later:
   - Wrap these into a tiny PowerShell/CLI wrapper so you can also trigger them from your terminal workflow.

If you tell me your exact Claude Code surface (VS Code Insiders + Claude extension? standalone app? browser?) and your primary browser, I can sketch a concrete AHK script tailored to your window titles, selectors, and a minimal convention for grabbing “the right” chunk from each side.
