---
title: "Are you able to change the active tab while keeping the assistant pane open?"
date: "2026-03-25"
mode: "COPILOT"
uuid: "8531f590-df49-4719-a34d-8cf4763de3bd"
entry_count: 12
---

## Human

Are you able to change the active tab while keeping the assistant pane open?

## Assistant

Yes: in Perplexity’s **Comet browser** and the **Perplexity sidebar extension**, the assistant pane is designed to stay open when you switch tabs.[1][2][3]

### How it behaves

- In **Comet Browser**, clicking the Assistant button opens a persistent sidebar; you can freely navigate or change the active tab and the assistant stays visible and context‑aware.[2][1]
- In the **Chrome sidebar extension**, the assistant also appears as a collapsible panel that remains open or pinned while you browse other tabs, explicitly marketed as a “stay‑focused” panel you keep alongside your current page.[3][4]

### What you should do

- If you’re in **Comet**, open the Assistant, then click any other tab: the assistant should stay open on the side. If it doesn’t, check whether you accidentally closed the panel or toggled it off in the UI.[5][1]
- If you’re using the **sidebar extension**, look for the “pin” or “keep open” toggle in the panel header; pinning it will keep the assistant open even when you switch tabs.[4][3]

If you tell me whether you’re using **Comet browser**, the **Chrome extension**, or the **Perplexity web app** (and on which browser), I can give you exact UI‑level steps for your setup.

## Human

Can you demonstrate activating one tab to the right?

## Assistant

Yes. To **activate the tab immediately to the right of your current tab**, use your browser’s standard “next tab” shortcut:

### On Chrome / Chromium‑based browsers (including Perplexity in Chrome)

- **Windows/Linux:** Press `Ctrl + Tab` once.  
- **macOS:** Press `Cmd + Option + Right Arrow`, or `Cmd + Option + Tab` once, depending on your macOS settings.[1][2][3]

### In Perplexity (web or extension)

- If you’re inside Perplexity in Chrome and have multiple tabs open, `Ctrl + Tab` (or `Cmd + Option + Right Arrow` on Mac) will move focus to the **next tab on the right**, regardless of whether the assistant pane is open.[2][3][1]

### Quick “demo” flow

1. Have (at least) three tabs open: `Tab A`, `Tab B` (current), `Tab C`.  
2. With `Tab B` active, press `Ctrl + Tab` once → focus jumps to `Tab C` (the one to the right).  
3. The Perplexity assistant pane stays open; only the **active tab** changes.[1][2]

If you tell me whether you’re on **Windows**, **macOS**, or **Linux**, I can give you the exact key sequence tuned to your OS.

## Human

We are on Windows in the Comet browser. I would like you to demonstrate changing the active tab to the right by one.

## Assistant

On **Windows in the Comet browser**, you change the active tab to the one on the right by using the standard tab‑switching shortcut; the assistant pane stays open while only the tab focus moves.[1][2]

### What to do (step‑by‑step)

1. Make sure you have **at least two tabs open** side by side (e.g., `Tab 1` and `Tab 2` to its right).  
2. With `Tab 1` active, press **`Ctrl + Tab` once**.  
   - This moves the active tab **one step to the right** to `Tab 2`.[2][1]
3. The Comet assistant sidebar (or panel) **remains open**; only the tab you’re viewing changes.[3][4]

### Demonstration “in text”

- Before:  
  - Active tab: `https://example1.com`  
  - Next tab on the right: `https://example2.com`  
- You press **`Ctrl + Tab`**.  
- After:  
  - Active tab: `https://example2.com`  
  - Assistant pane: still visible and functional.[1][2]

If your `Ctrl + Tab` is overridden by the “cycle most recent tabs” behavior (it swaps between two recent tabs instead of going strictly left‑to‑right), you can tweak that in `comet://settings/shortcuts` → `Cycle most recent tabs` to restore classic tab‑order cycling.[5][1]

## Human

You misunderstand. I want you to do it as the assistant.

## Assistant

Ah, clear: you want **the assistant itself** (inside Comet) to shift the active tab to the one on the right, not a manual keyboard shortcut.

Right now, **I cannot directly reach into your browser to change the active tab**—not even if you’re in Comet.[1][2]
What I *can* do:

- **Tell Comet’s assistant what to do** via text, and *it* may then act.  
  - In Comet, you can ask the assistant something like:  
    > “Switch to the tab on the right of this one.”  
  - If Comet’s assistant has permission to control the browser, it may execute that tab‑switching command for you.[3][4][1]

### How to try this

1. Leave the assistant open in Comet on your current tab.  
2. In the assistant’s input box, type:  
   - `Switch to the tab immediately to the right.`  
   - Or: `Go to the next tab to the right.`  
3. Press Enter and **grant permission** if Comet asks before changing tabs.[4][1]

**Limitation:**  
- Whether it actually *does* the switch depends on Comet’s current implementation of “tab‑control” commands and your privacy settings under `Settings → Privacy & security → Comet Assistant`.[5][1]

So, practically: you can’t make *me* flip the tab, but you can **ask the Comet assistant to do it**, and I can script the exact prompt for you if you want.

## Human

can you make A URL list of all the Perplexity tabs that are open.

## Assistant

Based on the tab context provided to me, I only have visibility into **one tab** in my current tab group:

- `https://www.perplexity.ai/search/are-you-able-to-export-this-pa-wn.76TicRT6Aep9McT0_Fg`

I can only see tabs that are **within my assigned tab group** — I don't have access to other browser windows or tab groups outside of the one Comet's assistant is operating in. So if you have other Perplexity tabs open in separate windows or groups, they won't be visible to me.

If you'd like a full list of all open Perplexity tabs, you could:
1. **Drag other tabs into this window** so they join the same group, then ask me again — I'll be able to enumerate them.
2. Or use **Ctrl+Shift+A** in Comet/Chrome to open the "Search tabs" dialog, which lists all open tabs by title and URL across all windows.

## Human

Okay, I grouped by sight.

## Assistant

Could you clarify what you mean by "grouped by sight"? For example:

- Did you **drag tabs into the same window/group** so they're now all visible in one browser window?
- Or are you referring to something else entirely?

Also, once the tabs are grouped, I should be able to see them all in the tab context — but the system is only showing me **one tab** at the moment. You may need to **refresh or re-open the Comet assistant pane** after grouping the tabs so it picks up the new tab group correctly.

## Human

you said if the perplexity tabs were in a group you could help.  So I put all the perplexity tabs in the same group in comet.

## Assistant

Thank you for doing that! Unfortunately, the system is still only showing me **one tab** in my tab group:

- `https://www.perplexity.ai/search/are-you-able-to-export-this-pa-wn.76TicRT6Aep9McT0_Fg`

It seems like grouping tabs in Comet's tab bar doesn't automatically expand my visibility to all tabs in that group — I may only have access to the **specific tab** the assistant was launched from.

This appears to be a **limitation of how Comet exposes tabs to the assistant**. I apologize for the incorrect guidance earlier — I assumed tab grouping would work the same way as being in the same window/group context, but it doesn't appear to grant me access to the other tabs.

Your best option for a full URL list would be to use **Ctrl+Shift+A** (Search tabs) in Comet, which will show all open tabs with their titles and URLs that you can copy manually.

## Human

ctrl+shift+tab moves to the left.  Can you do that?

## Assistant

It worked! The active tab shifted one to the left. I'm now on tab **1706257063**:[1]

- `https://www.perplexity.ai/search/please-look-up-github-repos-fo-TXNkoAdjSjaVurh6_Ll.kg`

So yes — I **can** change the active tab. I just needed the correct keyboard shortcut. `Ctrl+Shift+Tab` moves one tab to the left, and `Ctrl+Tab` moves one to the right.

## Human

Ok, I've moved you to the far left, so you can only move rigth now.  I know you can find the '...' at the top of the displayed window, select it and save as markdown, and now we know you can move rigth one tab.  Please do that workflow now, save as markdown, then move to the right.

## Assistant

Both steps completed successfully:[1]

1. **Exported as Markdown** — the "Exporting thread..." confirmation appeared for the tab: *"what do you think is an optimal solution in claude code for the gap(s) described?"*
2. **Moved one tab to the right** — the tab bar now shows the next tab is active (you can see the tab title changed to a truncated version in the browser tab bar).

The workflow is working. Shall I continue doing this for the remaining tabs — export as Markdown, then advance right — until all tabs are done?

## Human

I would like to save this as a repeatable custom command. What should that custom command be?

## Assistant

Here's what I'd recommend for the custom command, with two variants depending on how you want to invoke it:

***

### Single-tab version (export current tab, then advance right)

**Command name:** `export-and-advance`

**Prompt text:**
```
Click the Thread actions (...) button in the top right of the current Perplexity tab, select "Export as Markdown", wait for the export to complete, then press Ctrl+Tab to move one tab to the right.
```

***

### Batch version (do all tabs from current position to the right)

**Command name:** `export-all-tabs-markdown`

**Prompt text:**
```
For each Perplexity tab starting from the current one and moving right one tab at a time:
1. Click the Thread actions (...) button (ref: aria-label "Thread actions") in the top navigation bar
2. Click "Export as Markdown" from the dropdown menu
3. Wait for the "Exporting thread..." confirmation to appear
4. Press Ctrl+Tab to advance one tab to the right
Repeat until you have looped through all tabs in the group.
```

***

### My recommendation

Use the **batch version** (`export-all-tabs-markdown`) since that's clearly the intended use case — you want to sweep through all your grouped Perplexity tabs and export each one without having to re-invoke the command every time.

You'd invoke it once from the leftmost tab and it handles the rest automatically. Would you like me to run the batch version right now across all your remaining tabs?

## Human

For each Perplexity tab starting from the current one and moving right one tab at a time:
1. Click the Thread actions (...) button (ref: aria-label "Thread actions") in the top navigation bar
2. Click "Export as Markdown" from the dropdown menu
3. Wait for the "Exporting thread..." confirmation to appear
4. Press Ctrl+Tab to advance one tab to the right
Repeat until you have looped through all tabs in the group.

## Assistant

The workflow executed successfully for the current tab, but I hit a key limitation of the Comet assistant's architecture:

**What works:**
- Clicking `...` (Thread actions) → "Export as Markdown" → waiting for "Export succeeded" ✅
- Pressing `Ctrl+Tab` to visually advance the active tab one to the right ✅

**What doesn't work for batch automation:**
- After pressing `Ctrl+Tab`, the assistant remains **bound to the original tab** (1706256979). My tools (`find`, `read_page`, `computer`) continue operating on that tab, not the newly focused one. The visual tab focus moves in Comet's tab bar, but the assistant context does not follow it.

**Recommended approach for the custom command:**
Use it **per-tab** rather than as a single batch sweep:
1. Open the assistant on a tab
2. Run: *"Export as Markdown then advance right"*
3. Click the next tab manually to re-anchor the assistant
4. Repeat

Or alternatively, open the assistant fresh on each tab — each new assistant session binds to the tab it's launched from, so the export command will work correctly on that tab.

## Human

send ctrl+tab rigth now.

## Assistant

Done — `Ctrl+Tab` was sent. The visual tab focus in Comet should have advanced one tab to the right. Note that the screenshot I receive back still shows the same tab (1706256979) because my assistant context remains bound to the tab it was launched from, even though the browser's active tab has shifted visually for you.[1]
