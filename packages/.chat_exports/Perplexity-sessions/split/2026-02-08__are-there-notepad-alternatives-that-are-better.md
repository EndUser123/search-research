---
title: "are there notepad++ alternatives that are better?"
date: "2026-02-08"
mode: "CONCISE"
uuid: "87ae02e5-6452-4623-b06d-f74f6f91affb"
entry_count: 4
---

## Human

are there notepad++ alternatives that are better?

## Assistant

Yes, several modern text editors outperform Notepad++ in speed, extensibility, and features like AI integration or multi-cursor editing, especially for advanced developers handling multi-agent workflows and large codebases.[1][5]

## Top Alternatives
Visual Studio Code (VS Code) leads as the most popular free option with vast extensions, Git integration, and debugging—ideal for your Python/TypeScript projects and VSCode workflow.[5][7][1]
Sublime Text excels in raw speed and syntax highlighting, often praised over Notepad++ for spell-checking and Vim mode in large files.[3][6]
CudaText offers lightweight performance for huge logs (up to 10GB) with minimaps and customizable hotkeys, suiting your hardware-optimized setups.[9]

## Comparison Table

| Editor          | Key Strengths for You                  | Platform Fit (Windows/VSCode Heavy) | Free?     |
|-----------------|----------------------------------------|-------------------------------------|-----------|
| VS Code        | Extensions, terminal, AI plugins      | Native integration                  | Yes [1][5] |
| Sublime Text   | Speed, multi-select, Vim mode         | Cross-platform, lightweight         | Freemium [3][6] |
| CudaText       | Large files, hex viewer, minimap      | Efficient for big projects          | Yes [9] |
| UltraEdit      | Macros, column editing                | Power user tools                    | Paid [1] |

## Recommendation
For your multi-terminal Claude Code environment in Windows 11, start with VS Code—its ecosystem aligns perfectly without Notepad++'s plugin limitations.  Test Sublime for pure editing speed in 120+ hour sprints.[7][1][3]

## Human

How can I force uninstall every trace of visual studio code, visual studio code insiders, and antigravity?

## Assistant

**To completely uninstall Visual Studio Code, VS Code Insiders, and the Antigravity extension (a VS Code-compatible AI IDE or extension) on Windows 11, follow these steps to erase every trace including apps, settings, extensions, and caches.** This ensures a clean slate for your multi-terminal development setup.[1][2][3][4]

## Preparation
Close all VS Code/Antigravity processes via Task Manager (Ctrl+Shift+Esc), ending Code.exe, Code Helper, or Antigravity-related tasks.[5]
Restart your PC afterward to unlock files.[1][5]
Open PowerShell as admin for commands (Win+X, then Terminal (Admin)).[1]

## Uninstall Main Apps
1. Go to Settings > Apps > Installed apps, search "Visual Studio Code" and "Visual Studio Code Insiders," click the three dots, and select Uninstall for both.[2]
2. If Antigravity appears separately (as Google's AI IDE fork), uninstall it the same way; it's often a standalone VS Code fork.[4][6]
3. For .zip installs, manually delete extracted folders (e.g., C:\Users\[YourUser]\AppData\Local\Programs\Microsoft VS Code). []

## Delete User Data and Extensions
Run these in PowerShell to nuke configs:  
```
Remove-Item "$env:APPDATA\Code" -Recurse -Force
Remove-Item "$env:APPDATA\Code - Insiders" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.vscode" -Recurse -Force
```
- This wipes settings, keybindings, snippets, and extensions (including Antigravity if extension-based). [][][]  
- Check/delete %LOCALAPPDATA%\Programs\Microsoft VS Code if remnants exist. []

## Clean Registry (Optional, Advanced)
1. Run regedit (Win+R > regedit).  
2. Backup registry (File > Export).  
3. Search (Ctrl+F) for "Visual Studio Code," "Code," or "Antigravity," delete VS Code-specific keys (e.g., under HKEY_CURRENT_USER\Software\Microsoft\VSCode). Be cautious—skip if unsure. []

## Verify and Reboot
Search Windows for "code" or "antigravity" files/folders and delete any leftovers (e.g., in %LOCALAPPDATA%). []  
Reboot, then reinstall cleanly if needed—your Claude Code workflow will start fresh. []

## Human

can you create a powershell script that does everything you said?

## Assistant

Yes, here's a comprehensive PowerShell script that automates the full uninstall of VS Code, VS Code Insiders, and Antigravity (covering app, data, extensions, and remnants) on Windows 11—tailored for your PowerShell-heavy workflow.[1][2]

## Usage
Save as `Uninstall-VSCodeAll.ps1`, right-click > Run with PowerShell (admin required for registry/app parts). It prompts for confirmation, logs actions, and handles errors safely.[2]

## The Script
```powershell
# Complete VS Code / Insiders / Antigravity Uninstall Script for Windows 11
# Run as Administrator. Backs up registry first.

param(
    [switch]$NoPrompt
)

# Colors for logging
$LogInfo = "Cyan"
$LogWarn = "Yellow"
$LogError = "Red"
$LogSuccess = "Green"

function Write-Log($Message, $Color) {
    Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] $Message" -ForegroundColor $Color
}

# Check admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Log "ERROR: Run as Administrator!" $LogError
    exit 1
}

if (-not $NoPrompt) {
    $confirm = Read-Host "This will uninstall VS Code, Insiders, Antigravity & delete ALL data (settings/extensions). Continue? (y/N)"
    if ($confirm -ne 'y') { exit 0 }
}

Write-Log "Starting uninstall..." $LogInfo

# 1. Kill processes
$processes = @("Code", "Code - Insiders", "Antigravity", "electron")
foreach ($proc in $processes) {
    Get-Process $proc -ErrorAction SilentlyContinue | Stop-Process -Force
}
Write-Log "Processes killed." $LogSuccess

# 2. Uninstall via Apps & Features (WINGET/APPX)
$apps = @("Visual Studio Code", "Visual Studio Code Insiders", "Antigravity")
foreach ($app in $apps) {
    Get-AppxPackage *code* -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue
    winget uninstall --id Microsoft.VisualStudioCode --exact --silent --force 2>$null
    winget uninstall --id Microsoft.VisualStudioCodeInsiders --exact --silent --force 2>$null
    winget uninstall --id Antigravity* --exact --silent --force 2>$null
}
Write-Log "Apps uninstalled." $LogSuccess

# 3. Delete install dirs
$installPaths = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code",
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code Insiders",
    "$env:PROGRAMFILES\Microsoft VS Code",
    "$env:PROGRAMFILES(x86)\Microsoft VS Code",
    "$env:LOCALAPPDATA\Antigravity"
)
foreach ($path in $installPaths) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Deleted: $path" $LogSuccess
    }
}

# 4. Delete user data & extensions
$dataPaths = @(
    "$env:APPDATA\Code",
    "$env:APPDATA\Code - Insiders",
    "$env:LOCALAPPDATA\Code",
    "$env:USERPROFILE\.vscode",
    "$env:APPDATA\Antigravity",
    "$env:LOCALAPPDATA\Antigravity"
)
foreach ($path in $dataPaths) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Deleted data: $path" $LogSuccess
    }
}

# 5. Registry cleanup (backup first)
$regBackup = "$env:TEMP\VSCodeRegBackup-$(Get-Date -Format 'yyyyMMdd-HHmmss').reg"
reg export "HKEY_CURRENT_USER\Software\Microsoft\VisualStudio\Code" $regBackup /y 2>$null
reg export "HKEY_CURRENT_USER\Software\Microsoft\vscode" $regBackup.vscode.reg /y 2>$null
Write-Log "Registry backed up to: $regBackup" $LogInfo

$regPaths = @(
    "HKCU:\Software\Microsoft\VisualStudio\Code",
    "HKCU:\Software\Microsoft\vscode",
    "HKCU:\Software\Microsoft\VisualStudio\Code - Insiders",
    "HKLM:\Software\Microsoft\VisualStudio\Code"
)
foreach ($reg in $regPaths) {
    if (Test-Path $reg) {
        Remove-Item $reg -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Cleaned registry: $reg" $LogSuccess
    }
}

Write-Log "Uninstall complete! Reboot recommended. Log paths checked above." $LogSuccess
```

## Verification
Rerun the script—it logs what's deleted. For stubborn files, add paths to `$installPaths` or `$dataPaths`. This preserves your Claude/VSCode extensions elsewhere.[3]

## Human

we need to delete the extensions also.

## Assistant

The previous script already deletes all VS Code extensions (including Antigravity) by recursively removing `$env:USERPROFILE\.vscode\extensions`, `$env:APPDATA\Code\User`, and equivalent Insiders/Antigravity paths—these store everything.[1][2]

## Enhanced Paths
If global/multi-user extensions linger (rare on Windows), add these to the script's `$dataPaths` array before running:

```
"$env:LOCALAPPDATA\.vscode\extensions",
"$env:PROGRAMDATA\Code",
"$env:APPDATA\Code\CachedExtensions",
"$env:LOCALAPPDATA\Antigravity\extensions"
```

Rerun as admin; it logs deletions. For verification, add this check at script end:
```powershell
Get-ChildItem "$env:USERPROFILE\.vscode" -ErrorAction SilentlyContinue
```
No output means clean.[3][4]
