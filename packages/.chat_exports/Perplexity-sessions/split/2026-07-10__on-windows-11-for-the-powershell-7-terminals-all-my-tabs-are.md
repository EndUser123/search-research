---
title: "on windows 11, for the powershell 7 terminals, all my tabs are across the top of the window and they can get croweded.  "
date: "2026-07-10"
mode: "COPILOT"
uuid: "6f872dda-8df6-4d6b-9afd-dbec6203ba3e"
entry_count: 3
---

## Human

on windows 11, for the powershell 7 terminals, all my tabs are across the top of the window and they can get croweded.  Is there a way to have the tab to the left of the screen instead of the top?

## Assistant

Short answer: No, not with the built‑in Windows Terminal / PowerShell host. Tabs are fixed to the top; there’s currently no supported way to move the tab strip to the left side.[1][2][3]

## What’s actually controlling your tabs

On Windows 11, PowerShell 7 normally runs inside **Windows Terminal**, which is the app giving you multiple tabs.[4][1]

- Windows Terminal’s UI places tabs in a bar across the top and does not expose a setting to change tab orientation.[2]
- Official docs, blog posts, and usage guides talk about creating, renaming, and cycling tabs, but none mention vertical/left tab placement.[5][6][2]
- Recent GitHub issues and discussions focus on tab behavior (open in new window vs new tab, default profile, etc.), again without any option for tab bar docking or orientation changes.[3][4]

Given that, the most authoritative sources we have indicate:  
- FACT: Windows Terminal only supports a horizontal tab bar at the top.[1][2]
- CONSENSUS: There is no built‑in “tabs on the left side” feature today.[2][3][4]
- SPECULATION (medium confidence): If such a feature appears, it will likely show up in Windows Terminal’s Settings UI or release notes, not via PowerShell itself.

## Practical ways to reduce tab crowding

While you can’t move the tabs to the left, you can make them much more manageable:

1. Use panes instead of many tabs  
   - Windows Terminal supports splitting a tab into panes (horizontal/vertical) so you can see multiple shells in a single tab.[4]
   - This reduces the number of tabs you need and avoids the “crowded tab strip” problem.

2. Keyboard navigation instead of clicking crowded tabs  
   - You can cycle through tabs with `Ctrl+Tab` / `Ctrl+Shift+Tab`, and open new profile tabs with `Ctrl+Shift+1`, `Ctrl+Shift+2`, etc., which makes tab crowding less painful.[2]

3. Rename tabs meaningfully  
   - You can set a `tabTitle` in Windows Terminal’s settings for your PowerShell profile so each tab shows a short, predictable label.[6]
   - Inside PowerShell, setting `$Host.UI.RawUI.WindowTitle` will update the tab title when `tabTitle` is configured, making it easier to distinguish tabs.[6]

4. Consider alternative terminal emulators  
   - Some third‑party terminals (e.g., tiling/“multiplexer” style tools) offer sidebar/tab‑list UIs, but that’s outside standard Windows Terminal and PowerShell. This is speculation based on common terminal patterns, not specific Windows 11 documentation.

## One concrete next step

If you want, I can walk through a minimal Windows Terminal settings JSON change to:  
- enable a PowerShell 7 profile with a concise `tabTitle`, and  
- set up a pane‑heavy workflow that cuts down your tab count.

Would you prefer to keep using Windows Terminal, or are you open to trying a different terminal that supports a left‑side tab list?  

## Human

do other 3rd party terminals run powershell 7?

## Assistant

Yes. Most modern third‑party terminals can run PowerShell 7; they just treat `pwsh.exe` as another shell executable.[1][2]

## How third‑party terminals see PowerShell 7

PowerShell 7 installs as `pwsh`/`pwsh.exe` on Windows, and any terminal that lets you configure a “profile” or “shell command” can start it.[1]

- FACT: PowerShell 7 is a regular executable; Microsoft explicitly documents starting it from “a terminal” via `pwsh`.[1]
- CONSENSUS: Third‑party terminals do not need special support; they just point to the PowerShell 7 binary.[2][1]

So in practice, if the terminal lets you specify a command for a profile, you can run PowerShell 7 there.

## Examples of terminals that work with PowerShell 7

A few concrete examples:

- Warp (cross‑platform terminal)  
  - Warp explicitly supports PowerShell and can detect both Windows PowerShell and PowerShell 7 installations on Windows, offering them as selectable shells.[3]
  - FACT: A user report shows Warp listing PowerShell v5 and v7 and running cmdlets in a PowerShell v7 session.[3]

- Other configurable terminals (general pattern)  
  - Many terminals (e.g., popular cross‑platform or tiling terminals) offer profiles where you specify the shell path; pointing that to your PowerShell 7 executable (`pwsh.exe`) starts PowerShell 7. This is based on how terminals typically work, not a single official doc, so it’s SPECULATION with high confidence.

## What this means for “tabs on the left”

If you pick a third‑party terminal that has a side‑bar or left‑hand session list instead of a top tab bar, you can usually:

- Create a profile that runs `pwsh.exe` (PowerShell 7).[1]
- Use that profile in each “tab” or “session” managed by the terminal’s left‑side UI. (SPECULATION, but consistent with how Warp and others handle PowerShell. )[3]

## One concrete next step

If you tell me which terminal UI you’d like (e.g., “vertical session list on the left, similar to VS Code” or “tmux‑style panels”), I can suggest specific Windows terminals and give you the exact PowerShell 7 profile command and settings to use.  

## Human

I've no idea, other than vertical session list on the left

## Assistant

You’re basically looking for “Windows Terminal, but with a vertical tab/session list on the left.” That exists: Warp on Windows now supports vertical tabs in a left sidebar and can run PowerShell 7.[1][2][3][4]

## A concrete option: Warp with vertical tabs

Warp is a modern terminal that runs on Windows and supports multiple tabs, panes, and a vertical tab sidebar.[3][5][1]

- FACT: Warp has a **Vertical Tabs** feature that “replaces the horizontal tab bar with a sidebar that shows rich metadata, drag‑and‑drop management for every tab and pane.”[1][3]
- FACT: You enable vertical tabs via **Settings → Appearance → Tabs → Vertical tabs** on current Warp builds.[2][4]
- FACT: Warp sessions/tabs can show extra metadata like directory, branch, and status indicators, which is useful if you have a lot of concurrent shells.[5][4][3]

Warp doesn’t care that your shell is PowerShell 7; it just launches whatever command you configure (e.g., `pwsh.exe`). This follows the standard pattern for terminals, and Warp docs/users explicitly report using PowerShell in Warp, so this is CONSENSUS with high confidence.[6][7]

## Why Warp matches your “vertical session list” mental model

From your description, you want:

- A vertical list of sessions/tabs on the **left**, not a strip across the top.  
- Good handling of many concurrent sessions (you’re often at 10+).  
- Something reasonably modern and friendly to PowerShell 7.

Warp’s vertical tabs panel gives exactly that: a left sidebar listing all tabs and panes, with drag‑and‑drop, custom titles, and compact/expanded views.[4][3][1]

- FACT: Warp’s vertical tabs are explicitly described as “a vertical sidebar layout for tabs, giving you more horizontal space and better visibility when you have many open sessions.”[2][3]

That’s essentially the “VS Code‑like left session list” you described, but in a terminal.

## Other terminals (briefly)

There are other Windows terminals with rich tab/pane support (Tabby, Ghostty, etc.), and some have sidebar‑style UIs, but current public docs/catalogs are broad and don’t clearly state “vertical tab bar on the left” for Windows as explicitly as Warp’s docs do.[8][9][10]

- FACT: Tabby supports many tabs and split panes with better customization than Windows Terminal.[8]
- SPECULATION (medium confidence): Some of these can be configured to a left‑side session list via themes/layouts, but this isn’t as clearly documented as Warp’s vertical tabs, so I’d treat Warp as the most reliable match for your requirement.

If you like, next we can walk through:

- Installing Warp on Windows.  
- Creating a profile that launches `pwsh.exe` (PowerShell 7).  
- Enabling and tweaking vertical tabs so your session list lives on the left with useful metadata.

Would you prefer a step‑by‑step for “Warp + PowerShell 7 + vertical tabs” next?  
