---
title: "google antigravity on windows 11 won't run properly."
date: "2026-01-30"
mode: "CONCISE"
uuid: "cdbb63b7-beb7-41ca-a0c1-34e8e99b40d0"
entry_count: 2
---

## Human

google antigravity on windows 11 won't run properly.

## Assistant

**Google Antigravity often faces startup, loading, or authentication issues on Windows 11 due to permissions, antivirus interference, or environment variables.**[1][2]

**Quick Fixes**
- Fully quit Antigravity (check system tray), wait 30 seconds, and relaunch.[1]
- Run as administrator: Right-click the executable or shortcut and select "Run as administrator."[2][1]
- Set the HOME environment variable in PowerShell (as Admin): `[Environment]::SetEnvironmentVariable("HOME", "C:\Users\$env:USERNAME", "User")`, then restart Antigravity.[3][1]

**Account and Permissions**
- Use a personal @gmail.com account; Workspace accounts may need admin approval for AI services.[1]
- On standard (non-admin) accounts, switch to an admin account or add exclusions in Windows Security > Virus & threat protection.[2][1]
- Temporarily disable real-time protection in Windows Security, add Antigravity folder to exclusions, then relaunch.[1]

**Advanced Troubleshooting**
- Clear app data: Delete `%APPDATA%\Antigravity` and `%LOCALAPPDATA%\Antigravity` folders, then reinstall from the official site.[4][2]
- Check Output panel (View > Output > Antigravity Agent) for specific errors like network timeouts or tool hangs, then restart agent service via Ctrl+Shift+P.[2][1]
- Install to default path (e.g., C:\Program Files\Google Antigravity) and ensure Chrome/Edge is default browser for auth.[5][1]

If stuck on "One moment, the agent is loading," cancel the operation, type "continue," or start a new chat.  For persistent issues, check status.antigravity.google or forums like discuss.ai.google.dev.[2][1]

## Human

Fix Antigravity stuck on One moment agent loading

## Assistant

**Google Antigravity getting stuck on "One moment, the agent is currently loading" on Windows 11 is a frequent issue caused by lingering processes, corrupted cache, or conflicts like recent updates or extensions.**[1][2][3]

**Immediate Steps**
- Reboot your Windows machine to clear stuck processes.[3]
- Open Task Manager (Ctrl+Shift+Esc), end all "Antigravity" processes, then relaunch the app.[2][3]

**Clear Cache and Config (Most Reliable Fix)**
- Close Antigravity fully (check system tray).
- In File Explorer, delete these folders (replace "YourUsername" with your actual username):
  - `C:\Users\YourUsername\.antigravity`
  - `C:\Users\YourUsername\.gemini`
  - `C:\Users\YourUsername\AppData\Roaming\Antigravity`
  - `%APPDATA%\Antigravity\Cache`
  - `%APPDATA%\Antigravity\GPUCache`[4][2][3]
- Reinstall Antigravity from the official site if needed, then log in again.[3]

**In-App Troubleshooting**
- Press Ctrl+Shift+P, run "Reload Window" or "Disable All Extensions," then restart.[5][4]
- Log out from settings, relaunch, and log back in.[6]
- Check for updates or outages at status.antigravity.google.[2]

These steps resolve it for most users after updates like 1.13.3; avoid importing VS Code settings with conflicting AI extensions like GitHub Copilot.[7][2]
