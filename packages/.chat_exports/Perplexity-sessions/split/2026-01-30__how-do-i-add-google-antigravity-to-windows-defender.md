---
title: "how do I add google antigravity to windows defender?"
date: "2026-01-30"
mode: "COPILOT"
uuid: "c7d61190-e12b-4107-92eb-11d3c0b53694"
entry_count: 1
---

## Human

how do I add google antigravity to windows defender?

## Assistant

You don’t need anything special for Antigravity itself; you just add its folder or exe as a standard Microsoft Defender exclusion in Windows 11.[1][2][3]

## Quick GUI method (Windows Settings)

1. Open **Windows Security**: press Win, type “Windows Security”, hit Enter.[4][5]
2. Go to **Virus & threat protection**.[4]
3. Click **Manage settings** under “Virus & threat protection settings”.[4]
4. Scroll to **Exclusions** and click **Add or remove exclusions**.[5]
5. Click **Add an exclusion** and choose one of:
   - **Folder** → select Antigravity’s install folder, typically `C:\Program Files\Google\Antigravity`.[2][1]
   - **File** → point to the main executable if you prefer per-file.  
   - **Process** → add the Antigravity process name if you know it (e.g. `Antigravity.exe`).[4]

If Defender blocked the installer, re-run it, then when SmartScreen appears click **More info → Run anyway** as long as the publisher shows **Google LLC**.[6][7][2]

## PowerShell method (good for scripting)

Run **Windows Terminal / PowerShell as Administrator** and use one or more of:

- Exclude the install folder:  
  `Add-MpPreference -ExclusionPath "C:\Program Files\Google\Antigravity" -Force`[4]
- Exclude the exe:  
  `Add-MpPreference -ExclusionPath "C:\Program Files\Google\Antigravity\Antigravity.exe" -Force`[4]
- Exclude the process name:  
  `Add-MpPreference -ExclusionProcess "Antigravity.exe" -Force`[4]

You can confirm Defender isn’t still blocking anything under **Windows Security → Virus & threat protection → Protection history** and check for entries mentioning Antigravity.[8][9]
