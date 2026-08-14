---
title: "in antigravity and vscode, the codex extension button in the left bar has gone.  How do I get it back?"
date: "2026-02-01"
mode: "COPILOT"
uuid: "fd497e3c-606d-4294-b7c5-180a276344df"
entry_count: 5
---

## Human

in antigravity and vscode, the codex extension button in the left bar has gone.  How do I get it back?

## Assistant

Most likely the Codex view just got hidden or moved; you can re‑enable it without reinstalling anything.[1][2][3]

### Quick ways to bring it back

Try these in Antigravity (same as VS Code):

1. Right‑click on any icon in the left activity bar and look for an entry like “Codex” or “OpenAI Codex”; if it’s unchecked, click it to re‑enable.[2][1]
2. Use the Command Palette: run `View: Reset View Locations` to restore all extension views (including Codex) to their defaults.[1]
3. Run `View: Open View...`, type “Codex”, and open its view from there; once open, its icon should reappear in the sidebar.[4]
4. If you previously dragged Codex to the right sidebar, its icon may now be over there; open the right sidebar and drag the Codex icon back to the left activity bar if desired.[3]

If none of that works, try disabling/re‑enabling the Codex extension (or reinstalling its VSIX in Antigravity) and then re‑run `View: Reset View Locations`.[5][1]

## Human

how can I put codex in the middle pane?

## Assistant

**Codex views can't be dragged directly into the main editor (middle pane) as full tabs, since they're sidebar/panel webviews.**  However, you can open them in the panel (bottom) or secondary sidebar first, then resize/split to maximize space.[1][2][3]

### Steps to maximize Codex in middle area
- Click and drag the Codex icon (or its header tab in sidebar) toward the center editor drop zone; it won't dock there but will highlight panel/secondary sidebar options—drop it in the panel for bottom-middle access.[3][1]
- Right-click the Codex view header > "Move Panel to Side Bar" or drag to secondary sidebar (split the screen), giving it ~half the middle real estate.[2]
- Use `Ctrl+B` to hide primary sidebar, focus editor/Codex in panel, or run Command Palette (`Ctrl+Shift+P`) > "View: Toggle Secondary Side Bar Visibility" for split layout.[4][3]

### Alternative: Open as editor-like tab
Run Command Palette > "Codex: Open Output" or check extension settings for "webview as editor" if available (rare for Codex); otherwise, pin the panel view.  Restart Antigravity if drag fails.[5][6]

## Human

How to customize Antigravity layout permanently

## Assistant

Antigravity, being a VS Code fork, lets you customize layouts permanently via settings.json and layout persistence. Changes apply globally or per-workspace and survive restarts.[1][2][3]

## Save Current Layout
Layouts auto-save when you adjust them (drag views, resize panels), but force it with Command Palette (`Ctrl+Shift+P`) > "Developer: Reload Window" after tweaks.[2]

## Edit settings.json
Open Command Palette > "Preferences: Open User Settings (JSON)" for global changes, or "Preferences: Open Workspace Settings (JSON)" for project-specific.[3][1]

Key layout settings:
```
{
  "workbench.layoutControl.enabled": true,
  "workbench.activityBar.location": "default",
  "workbench.panel.defaultLocation": "bottom",
  "workbench.sideBar.location": "left"
}
```
Add/rearrange views like Codex via `"workbench.sideBar.visible": true` or move panels.[2][3]

## Advanced Customization
- Click top-right "Customize Layout" icon to reorder activity bar/panels visually (saves automatically).[4]
- For Codex/workspace-specific: Create `.vscode/settings.json` in project root with layout prefs.[5]
- Reset if needed: Command Palette > "View: Reset View Locations".[2]

## Human

How to set up multi-agent workflows after layout customization

## Assistant

After layout tweaks in Antigravity, set up multi-agent workflows using your Claude Code orchestration patterns like /cwo, subagents, and Git worktrees for parallel execution without conflicts.[1]

## Leverage Your Existing Setup
Use 5-6 terminals (as you do) with Git worktrees: each agent gets `git worktree add ../agent-task feature-task` for isolated branches, merge via PRs post-review.[1]
Add slash commands like /cwo for orchestration: decompose → spawn subagents → TDD → validate, with shared files for coordination (no GitHub Issues).
Enable skill auto-activation via skill-rules.json for agent factories and policy feedback loops.

## Post-Layout Workflow Integration
```
{
  "terminal.integrated.tabs.enabled": true,
  "workbench.panel.opensMaximized": "never",
  "multiCommand.commands": [
    {
      "command": "multiCommand.orchestrateAgents",
      "sequence": ["workbench.action.terminal.new", "workbench.action.splitEditor", "claude.spawnSubagent"]
    }
  ]
}
```
Add to settings.json; bind to hotkey for spawning agents in split panels.[2]

## Recommended Steps
- **Spawn Agents**: Prompt Claude: "/cwo --parallel --worktrees" to auto-create worktrees/subagents.
- **Coordinate**: Shared claude.md for plans/reviews; subagents critique via hooks.
- **Validate**: Pre-commit hooks for doc sync/tests; monitor via PowerShell jobs.[3][4]
Test in your P:/__csf setup—scales your 26k+ repo workflows seamlessly.

## Human

any youtube videos showing how to customize the layout of vscode or antigravity?

## Assistant

Yes, several YouTube videos demonstrate VS Code layout customization (directly applicable to Antigravity as its fork), covering dragging views, activity bar tweaks, and the Customize Layout button.[1][2]

## VS Code Layout Deep Dive
Watch "Customizing VS Code's layout — An in-depth look at views, managing editors, and more!" (50 min, timestamps for sidebar/activity bar/panel at 31:29+).[1]
- Covers dragging views (like Codex) between sidebars/panels.  
- Hiding/rearranging activity bar icons (43:16).

## Quick Customize Button
"VS Code tips — The Customize Layout Control" (2 min): Shows top-right menu for toggling/hiding elements instantly.[2]

## Drag Views Demo
"Moving the explorer view to the panel or secondary side bar" (short): Drag any view header/icon to reposition—exact for Codex.[3]

## Antigravity-Specific
"Google Antigravity IDE: Complete Setup & Tutorial Guide" (includes layout during setup) and "Google Anti-Gravity IDE - AI Based Code Editor" (sidebar toggles at ~4:20).[4][5]
