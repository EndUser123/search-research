---
title: "do others encounter these issues with Claude Code on Windows 11 with multiple CC sessions in different terminals?"
date: "2026-01-14"
mode: "COPILOT"
uuid: "085aaefc-775c-49a9-b1e4-550bffac2e34"
entry_count: 3
---

## Human

do others encounter these issues with Claude Code on Windows 11 with multiple CC sessions in different terminals?

## Assistant

Yes, many users encounter issues with Claude Code when running multiple sessions in different terminals on Windows 11, particularly around freezing, hanging, config corruption, and session interference.[1][2][3]

## Common Problems
Sessions often freeze with stuck animations like "Synthesizing..." while tokens remain flat, or one session pauses/interrupts another, indicated by color changes in the thinking indicator. Config files like ~/.claude.json corrupt from simultaneous access, and console windows pop up unexpectedly. Context or information leaks between sessions have also been reported, breaking isolation.[2][3][4][5][6]

## Workarounds
Users recommend git worktrees for separate directories per session to avoid conflicts in shared repos. Running sessions in different directories or projects works reliably for some, with 4-5 concurrent terminals possible without issues. Windows Terminal is preferred over PowerShell or CMD for better handling of UI elements.[3][7][8][1]

## Relation to VCS
Your multi-agent setup with 60 concurrent git operations exacerbates these, as git's index.lock serializes commits, but Claude Code session limits compound the problem in shared directories. Git worktrees align well with your needs for parallel agents without lock contention.[9][1][3]

## Human

Windows Terminal is preferred over PowerShell, I thought they were the same thing?

## Assistant

Windows Terminal and PowerShell are distinct tools often confused due to their overlap in Windows workflows. Windows Terminal serves as a modern host application that can run PowerShell (or CMD, WSL) inside its tabs and panes, while PowerShell is specifically the advanced shell and scripting engine.[3][6]

## Key Differences
Windows Terminal excels with GPU acceleration for smooth rendering, multiple tabs/panes for concurrent sessions, and extensive customization like themes and profiles—ideal for running multiple Claude Code instances without UI glitches. PowerShell focuses on automation cmdlets, .NET integration, and scripting but lacks native tabs or modern rendering, leading to poorer handling of concurrent terminals in tools like Claude Code.[6][7][3]

## Why Terminal for Claude Code
Users prefer Terminal over standalone PowerShell windows because it isolates sessions better (e.g., via separate tabs per project), handles Unicode/UI elements from Claude Code more reliably, and avoids hanging or misalignment issues reported in pure PowerShell on Windows 11. In your multi-agent setup, Terminal's pane support aligns with parallel workflows without the desync problems of basic PowerShell prompts.[1][12][13][3]

## Human

How do I use Windows Terminal without PowerShell?

## Assistant

Windows Terminal defaults to PowerShell on Windows 11 but supports switching to Command Prompt (CMD), WSL, or other shells for a non-PowerShell experience. This setup improves handling of multiple Claude Code sessions by providing better tab isolation and rendering without PowerShell's scripting overhead.[1][2]

## Change Default Profile
Open Windows Terminal, click the dropdown arrow next to the + tab button, and select "Settings" (or Ctrl+,). In Settings > Startup > Default profile, choose "Command prompt" from the dropdown instead of "Windows PowerShell" or "PowerShell," then save. New tabs will now open in CMD by default.[2][1]

## Add New Profiles
In Settings > Profiles, click "Add a new profile" to create entries for CMD, Git Bash, or WSL distributions. Assign hotkeys or set as startup tasks for quick access to non-PowerShell environments. For Claude Code, launch sessions via CMD tabs to avoid PowerShell-specific UI quirks.[3][2]

## Launch Specific Shells
Open a new tab with Ctrl+Shift+1 (for first profile) or right-click the tab bar > New tab > select CMD/another shell. Use `wt new-tab cmd` from an existing tab or Run dialog for quick CMD launches. This keeps your multi-terminal Claude Code workflow lightweight and focused on command execution.[1]
