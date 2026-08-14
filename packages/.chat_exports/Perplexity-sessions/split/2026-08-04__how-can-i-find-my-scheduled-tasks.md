---
title: "How can I find my scheduled tasks?"
date: "2026-08-04"
mode: "COPILOT"
uuid: "2a1dac7a-d722-4dac-aba6-2f30a4c4e222"
entry_count: 2
---

## Human

How can I find my scheduled tasks?

## Assistant

Given your PowerShell 7/Windows 11 workflow, the fastest and most script-friendly way is via PowerShell, though the GUI Task Scheduler also works.

## PowerShell (recommended for your setup)

Since you already work heavily in PowerShell 7 for automation, use the built-in cmdlet:

```powershell
Get-ScheduledTask
```

This lists every registered scheduled task with its name, path, and state. To narrow results:[1]

- `Get-ScheduledTask -TaskName "*backup*"` — filter by name (wildcards supported)[2]
- `Get-ScheduledTask -TaskPath "\Microsoft\Windows\"` — filter by folder path[1]
- `Get-ScheduledTask | Get-ScheduledTaskInfo` — adds last/next run time details

The older `schtasks` command also works from PowerShell or CMD: `schtasks /query /fo LIST /v` gives a verbose listing, and you can redirect results to a CSV for logging or scheduled-task audits.[3][4]

## GUI: Task Scheduler app

Search "Task Scheduler" in the Windows Start menu and open it; expand **Task Scheduler Library** in the left pane to browse all registered tasks by folder, with details like triggers and last run status shown in the middle pane. Note that the GUI has no built-in search box — you can't type a task name to filter directly in the app.[5][2]

## Where tasks are actually stored

If you need to inspect or script against the underlying files/registry rather than the API:

| Location | Path | Purpose |
|---|---|---|
| Task Scheduler 2.0 files | `C:\Windows\System32\Tasks` | Task definition XML files [6][7] |
| Legacy Task Scheduler 1.0 | `C:\Windows\Tasks` | Older .job format tasks [6][7] |
|

## Human

I mean, in this Perplexity iOS app

## Assistant

Within the Perplexity iOS app, your scheduled Tasks live in a dedicated **Tasks** section accessible from your profile menu.

## Finding your Tasks in the iOS app

Tap your profile icon (bottom of the sidebar/menu) to open the account menu, then tap **Tasks** — this opens the list of all your scheduled recurring queries. Each task card shows its cadence (once, daily, weekly, monthly, yearly), next run time, and a **Paused/Active** toggle you can tap to enable or disable it.[1][2][3]

## Managing an existing task

- Tap a task card to open its details, where you can edit the instructions, schedule, or notification method[3]
- Toggle **Paused** off/on to activate or pause a task without deleting it[3]
- Tap the **+** icon from the Tasks list to create a new scheduled task, choosing between "Scheduled" and "Price Alert" types[4]

## A caveat worth noting

Tasks require a **Pro, Max, Enterprise Pro, or Enterprise Max** subscription — the feature isn't available on the free tier. Also note that Perplexity has recently rolled this into a broader **Computer → Tasks** experience (perplexity.ai/computer/tasks) on the web, which runs on Computer's agent system with more capabilities (connectors, subagents); the iOS Tasks section may show a simpler version depending on your app version. If you don't see a Tasks option in your profile menu, check that your app is updated to the latest version, since this feature shipped in stages across web and iOS starting mid-2025.[5][6][7][8][1]
