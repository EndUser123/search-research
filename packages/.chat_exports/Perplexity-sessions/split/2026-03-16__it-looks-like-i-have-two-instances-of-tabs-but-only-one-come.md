---
title: "it looks like I have two instances of tabs, but only one comet browser window."
date: "2026-03-16"
mode: "COPILOT"
uuid: "9f4eb0dd-8705-4bc7-afa5-dd537753584b"
entry_count: 1
---

## Human

it looks like I have two instances of tabs, but only one comet browser window.

## Assistant

You’re probably seeing two Perplexity/Comet “instances” in the taskbar or Alt‑Tab, even though there’s just one Comet window with multiple tabs.

### What’s likely going on

- Comet is built like a native app with multiple internal **tabs**, but Windows groups running apps by process “identity” (AppUserModelID, executable path, etc.), not by how many browser windows you see.[1]
- If Comet spawns a helper process or changes identity between updates or runs, Windows can think it’s a second app and show a second icon/instance, even if there’s only one visible window.[1]
- Comet itself supports multitasking across multiple tabs in a single window (cross‑tab intelligence, multi‑tab agents), so it’s normal that the app behaves as “multi‑tab” while still appearing as one logical browser; the duplication is at the Windows shell level, not in Comet’s UI.[2][3]

### Things you can try (low‑friction)

- Check whether both icons jump to the same window when clicked; if yes, it’s almost certainly just Windows treating one app as two identities.[1]
- Fully quit Comet (ensure no background process in Task Manager), then relaunch; this often clears transient duplicate icons caused by shell glitches.[1]
- Make sure you’re on the latest Comet build; new multitask/cross‑tab features have been rolling out and UI/taskbar behavior has changed over time.[3][2]

If you describe where you see the “two instances” (taskbar, Alt‑Tab, Comet sidebar, something else), I can map it much more precisely to either a Windows shell quirk or a Comet feature and suggest a concrete fix.
