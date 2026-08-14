---
title: "In Antigravity, which is a vscode clone, how do I get rid of the middle part?"
date: "2025-12-14"
mode: "COPILOT"
uuid: "c5cf3431-61e6-4880-a848-15269efbf67f"
entry_count: 4
---

## Human

In Antigravity, which is a vscode clone, how do I get rid of the middle part?

## Assistant

That middle section is the Agent Manager view; to “get rid of it” you need to switch back to the regular editor layout rather than closing it permanently.[1][2]

## Switch back to editor

- Use the keyboard shortcut to toggle:  
  - Windows/Linux: `Ctrl + E`  
  - macOS: `Cmd + E`  
  This switches between the Agent Manager (what you are seeing on the right/middle) and the normal editor layout.[1]

- You can also click the “Open Editor” button in the main area, or the corresponding icon in the top-right header bar, which does the same toggle between Agent Manager and editor.[3][1]

## Prevent it from popping up

- Avoid clicking “Open Agent Manager” in the central start screen or top bar; that is what replaces your editor space with the Agent Manager pane.[4][3]
- If you opened a project from the Agent Manager, once you are back in the editor layout it behaves like VS Code and the middle area will stay as the code editor until you explicitly re-open the Agent Manager.[5][2]

## Human

I don't understand.  How about in vscode?

## Assistant

That “middle” area is just the empty editor group; to get rid of it you either close its tabs or collapse/switch editor groups.

## Close or collapse the middle editor

- Click the “x” on any tab in the middle editor group, or use `Ctrl+W` / `Cmd+W` until no files are open there; VS Code will close that group when it has no tabs.[1]
- To immediately collapse that group, right‑click in its tab bar (or the split divider between groups) and choose “Close Editor Group” or “Move Editor Group Left/Right” so you end up with only one group.[1]

## Avoid opening a center group

- When you use split commands like “Split Right” or drag a tab toward the center, VS Code creates another editor group; to keep only side chat + code, always keep your actual files in a single editor group and close extra groups as above.[1]

## Human

All the files are closed.  I opened rigth panel and left panel, I can't get rid of the middle panel.

## Assistant

What you are seeing is the normal editor region between the primary sidebar (left) and the secondary sidebar / chat (right); VS Code does not let you remove that region entirely, only shrink it or hide one of the sidebars.[1][2]

## What you can do

- Toggle off one of the sidebars so the “middle” editor expands to fill the space:  
  - View → Appearance → Side Bar (or `Ctrl+B` / `Cmd+B`) to hide the primary sidebar.  
  - View → Appearance → Secondary Side Bar to hide the right sidebar.[4][1]

- If the editor looks like a narrow centered strip, turn off Centered Layout with:  
  - View → Appearance → Centered Layout, or run “View: Toggle Centered Layout” from the Command Palette.[3][1]

- You can resize the editor area by dragging the vertical sashes between the editor and each sidebar, but the editor region itself cannot be closed while VS Code is running; it is always present between the two sidebars.[2][6]

## Human

how do I open panels as if it were a file in the middle?

## Assistant

You “open” panels in the middle by opening their *views* as editor tabs instead of in the side bar or bottom panel; some built‑in views now support this explicitly.[1][2]

## Open chat / tools in the editor

- For GitHub Copilot Chat (and similarly for other chat extensions), use the command palette: run **“Chat: New Chat Editor”** or click the `...` menu in the Chat view and choose **“New Chat Editor”**; this opens chat as a regular editor tab in the center area.[3][4]
- To move an existing chat from the right side into the editor, open the Chat view, click the `...` menu, and choose **“Open Chat in Editor”**; it appears like a file tab you can drag, split, etc.[4][5]

## Open terminal / panel content in the editor

- Integrated terminals can be dragged from the bottom **Panel** into the editor tab strip; grab the terminal tab’s title and drop it into the editor area, and it becomes a full editor‑style tab in the middle.[6][1]
- You can move it back later with the **“Move Terminal To Panel”** command from the terminal’s context menu or Command Palette.[6]

If you tell which specific panel or extension you want in the middle (terminal, debug, problems, Antigravity agent manager, etc.), more precise steps can be listed.
