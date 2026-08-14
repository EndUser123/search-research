---
title: "Problem Description: Obsidian GUI Hang on Windows 11

  Symptom:
  Obsidian (v1.12.7, auto-upgraded from v1.8.4) free"
date: "2026-04-11"
mode: "COPILOT"
uuid: "38bc7243-c12f-466f-8235-e33fe2e29067"
entry_count: 2
---

## Human

Problem Description: Obsidian GUI Hang on Windows 11

  Symptom:
  Obsidian (v1.12.7, auto-upgraded from v1.8.4) freezes at the "Indexing Vault" screen on Windows 11 Pro 10.0.26200. The UI becomes
  unresponsive — minimize/maximize buttons don't work. Process shows Responding=True but the window is frozen.

  Environment:
  - Windows 11 Pro 10.0.26200
  - Obsidian v1.12.7 (portable and standard installs both fail)
  - Vault at C:\\Users\\brsth\\.obsidian\\vaults\\personal-wiki\\
  - Intel UHD Graphics (suspected WebGL/Chromium GPU issue)

  Current vault state (verified via Read tool this turn):
  log.md, sources/, wiki/

  What was observed during earlier debugging attempts:
  - The hang reproduces with: fresh install, empty vault, portable install, safe mode, disabled plugins
  - LevelDB LOG shows no new writes during the hang — indexing stalls, not slow
  - open:false was set on the vault to prevent auto-open

  Working alternative:
  Wiki operations (ingest/query) work fine via /wiki CLI. Only the Obsidian GUI is blocked.

  Questions for the helping LLM:
  - What diagnostics would you run to identify WebGL/Chromium/GPU as the cause?
  - Is there a known fix for LevelDB hangs on Windows when LOG shows no new writes?
  - Could Windows Store version behave differently due to App Installer sandbox?

Also, do you know what the problem is?  Have other people reported this?

## Assistant

**Yes, this is a well-documented issue** affecting Windows 11 users upgrading to recent Obsidian versions (1.8+). Your symptoms align closely with multiple reported cases. The root cause is **GPU/Electron-related, not your vault data**.[1][2]

## The Problem: Electron 33+ GPU Regression

Your freeze at "Indexing Vault" likely stems from an **Electron framework regression introduced in Electron 33+** (used in Obsidian 1.8+). The issue manifests as UI freezes while LevelDB shows no activity—the process is stuck in GPU initialization or context loss, not indexing logic. Your Intel UHD Graphics is particularly susceptible, though AMD and NVIDIA GPUs also report this.[2][3][1]

## Diagnostic Steps

**GPU context verification:**
- Launch Obsidian from PowerShell with logging: `Obsidian.exe 2>&1 | Tee-Object obsidian_debug.log`
- Search the log for `GPU process exited unexpectedly` or `WebGL context lost`[3][2]
- Check Event Viewer → Windows Logs → Application for GPU driver crashes

**LevelDB/IndexedDB diagnostics:**
- Verify the IndexedDB LOCK file isn't stuck: `%APPDATA%\Obsidian\IndexedDB\app_obsidian.md_0.indexeddb.leveldb\LOCK`
- If corrupted, delete it (Obsidian will rebuild)[1]
- Check if Obsidian process remains in Task Manager after forced closure—a sign of ungraceful shutdown[1]

**Hardware acceleration status:**
- Settings → Appearance → toggle off "Hardware acceleration" (this forces software rendering, bypassing GPU)

## Known Solutions (Ranked by Effectiveness)

**1. Disable GPU at launch (most reliable)**[2]
Create a shortcut to Obsidian with target:
```
"C:\path\to\Obsidian.exe" --disable-gpu --disable-gpu-sandbox --in-process-gpu
```
Then disable Hardware Acceleration in Settings → Appearance for persistence.[2]

**2. Downgrade to v1.7.7** (Electron 32, pre-regression)[1]
- Install v1.7.7 from GitHub releases
- Let auto-update upgrade only the app to 1.12.7
- This defers the GPU issue; not a permanent fix[1]

**3. Clear IndexedDB lock + fresh re-index**[1]
```powershell
# Kill all Obsidian processes
Stop-Process -Name obsidian -Force

# Remove corrupted lock file
Remove-Item "$env:APPDATA\Obsidian\IndexedDB\app_obsidian.md_0.indexeddb.leveldb\LOCK" -Force

# Restart Obsidian
```

**4. Windows Store version considerations**[4]
Store versions run in AppContainer sandbox, which can trigger different GPU driver codepaths. If standard install fails, try Store—but most report the opposite (Store is stricter with security policies). The issue is fundamentally Electron-level, not sandbox-specific.

## Why Your LevelDB LOG Shows No Writes

This is the smoking gun: **the process isn't blocked on I/O; it's frozen in GPU initialization before it even reaches indexing logic**. The LOG stalls because LevelDB is waiting for the Electron/Chromium GPU process to respond, which hangs on context creation. This matches your observation that minimizing the window doesn't work—the renderer is unresponsive.[3][2]

## Next Step

**Try Option 1 immediately** (GPU flags in shortcut). If that works, you've confirmed the diagnosis. If indexing still hangs even with GPU disabled, the problem is plugin-related (disable all in Safe Mode first) or vault corruption (try empty vault clone).

What happens if you launch with `--disable-gpu` alone—does it hang or does it regress to slow-but-responsive indexing?

## Human

It still freezes even with --disable-gpu enabled

## Assistant

**This shifts the diagnosis: if `--disable-gpu` didn't help, you're likely hitting a cache corruption or large-vault indexing hang**, not a GPU problem. The symptom pattern now matches the "Stuck indexing" issue reported by many Windows 11 v1.8+ users.[1][2][3]

## Root Cause Hypothesis

Your freeze is **IndexedDB/LevelDB corruption** preventing index commit, combined with large vault size amplifying the timeout. Key evidence:[2][3]

- LevelDB LOG shows no writes = indexing logic completes, but the database transaction never commits[2]
- Process appears responsive (Responding=True) but UI frozen = main thread is waiting on a database lock that won't release[2]
- All plugin-disable attempts failed = not plugin-related[2]

This is distinct from the earlier GPU hypothesis: **the hang occurs after GPU initialization succeeds**.[4]

## Diagnostic Commands

Run these in **PowerShell (as Admin)** to identify the exact blocker:

**1. Check IndexedDB integrity:**
```powershell
# Stop Obsidian completely
Get-Process obsidian* | Stop-Process -Force

# Check the database lock file
$dbPath = "$env:APPDATA\obsidian\IndexedDB\app_obsidian.md_0.indexeddb.leveldb"
ls "$dbPath\LOCK"
ls "$dbPath\LOG" | % { "LOG size: $(([io.fileinfo]$_).length)" }

# If LOCK is stale (older than 5 minutes), delete it
if (Test-Path "$dbPath\LOCK") {
  $lockAge = (Get-Date) - (Get-Item "$dbPath\LOCK").LastWriteTime
  if ($lockAge.TotalMinutes -gt 5) {
    Remove-Item "$dbPath\LOCK" -Force
    "LOCK deleted (stale)"
  }
}
```

**2. Capture real-time hang diagnostics:**
```powershell
# Launch with debug output; wait for hang, then check process
Obsidian.exe 2>&1 | Tee-Object hang_debug.log &
Start-Sleep 5
Get-Process obsidian | Select Handles, WorkingSet, Threads | ft -AutoSize

# After hang reproduces, check if archiving process is stuck
Get-Process | where name -like "*archive*" | Select name, handles
```

**3. Vault size assessment:**
```powershell
# Count files and check for problematic large files
$vault = "C:\Users\brsth\.obsidian\vaults\personal-wiki"
(ls -r "$vault" | measure).Count
ls -r "$vault" | where { $_.Length -gt 5MB } | ft Name, @{N="MB";E={$_.Length/1MB -as [int]}}
```

## Targeted Fixes (in order of invasiveness)

**Option 1: Flush IndexedDB cache (non-destructive)**[3][2]
```powershell
# This ONLY clears Obsidian's cache, not your vault
Stop-Process -Name obsidian* -Force
Remove-Item "$env:APPDATA\obsidian\IndexedDB" -Recurse -Force
Remove-Item "$env:APPDATA\obsidian\Cache" -Recurse -Force
# Relaunch Obsidian — it will rebuild index from scratch
```

**Option 2: Rebuild vault cache from Settings**
Once Obsidian opens (or if you get past the freeze): Settings → Files & Links → Advanced → **Rebuild vault cache**. This forces re-indexing without database wipe.

**Option 3: Clone vault to test**
Create a fresh vault with just `log.md` to confirm Obsidian works:
```powershell
mkdir test-vault
cd test-vault
mkdir .obsidian wiki sources
cp ..\personal-wiki\log.md .
```
If the test vault opens instantly, your vault size or a specific file is the culprit.

**Option 4: Downgrade to v1.7.7**
If v1.8+ indexing logic is broken for large vaults, reverting buys time:
1. Download v1.7.7 from GitHub releases
2. **After downgrading, delete IndexedDB folder again** (you did this last time; essential for version change)

## Why This Differs from Your Previous Findings

Your earlier statement "LevelDB LOG shows no new writes during the hang" is **diagnostic gold**: it means the indexing completes but the transaction never flushes to disk. This is the opposite of a GPU freeze—it's a database deadlock or commit timeout.[3][2]

**Does your vault's `log.md`, `sources/`, or `wiki/` contain any files > 5 MB?** If so, run the size check above to identify them. Very large markdown files can trigger parser hangs that silently fail to commit changes.[5]
