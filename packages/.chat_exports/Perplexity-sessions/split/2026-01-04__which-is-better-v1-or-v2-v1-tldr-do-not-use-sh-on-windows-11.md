---
title: "Which is better v1 or v2?
v1:
TL;DR: Do not use .sh on Windows 11 unless you are strictly running Claude Code inside WSL"
date: "2026-01-04"
mode: "COPILOT"
uuid: "e6cbe69e-1343-4351-8835-7bfced3ee9d4"
entry_count: 1
---

## Human

Which is better v1 or v2?
v1:
TL;DR: Do not use .sh on Windows 11 unless you are strictly running Claude Code inside WSL (Windows Subsystem for Linux) or Git Bash. It will not work natively in PowerShell or Command Prompt.
For Windows 11, Python is your best choice.
Here is the breakdown of your options:
Python (Recommended): Best balance. You likely already have it installed. It handles JSON parsing (needed for the drift detector) and file timestamps (needed for stale docs) much easier than PowerShell. It is also cross-platform if you switch OS later.
PowerShell (.ps1): Native to Windows, but parsing JSON and making API calls for the "Drift Detector" logic is verbose and painful compared to Python.
TypeScript/Node: Too slow. The startup time for the Node runtime every 300ms might cause the statusline to flicker or lag.
The Windows 11 Implementation Plan
Since we are prioritizing Python, here is how the "Unified" script looks for your Windows environment. This single script handles the Tamagotchi, Git Status, Stale Docs, and Drift Detection.
1. Create C:\Users\YourName\.claude\statusline.py
This script replaces the bash script. It checks all your prioritized items safely on Windows.
Python
import os
import sys
import time
import subprocess
import json
from pathlib import Path

# --- CONFIGURATION ---
# Adjust these paths to match your project structure
PROJECT_ROOT = os.getcwd() 
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
DRIFT_FILE = os.path.join(os.environ.get("TEMP"), "cc_drift_state.json")
TEST_FILE = os.path.join(os.environ.get("TEMP"), "cc_test_status")

def get_git_status():
    try:
        # Run git command to get branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        if branch in ["main", "master"]:
            return f"🚨 PROD ({branch})"
        return f"🌿 {branch}"
    except:
        return "" # Not a git repo

def check_stale_docs():
    """Returns warning if src is significantly newer than docs"""
    try:
        # Get latest modification time in src and docs
        latest_src = 0
        latest_doc = 0
        
        for root, _, files in os.walk(SRC_DIR):
            for f in files:
                latest_src = max(latest_src, os.path.getmtime(os.path.join(root, f)))
                
        for root, _, files in os.walk(DOCS_DIR):
            for f in files:
                latest_doc = max(latest_doc, os.path.getmtime(os.path.join(root, f)))
        
        # If src is > 30 mins (1800s) newer than docs
        if latest_src > (latest_doc + 1800):
            return "⚠️ DOCS STALE"
    except:
        pass
    return ""

def get_drift_and_pet():
    """Reads the Drift Detector State and returns the Pet + Warning"""
    pet = "(◕‿◕)" # Default Happy
    alert = ""
    
    if os.path.exists(DRIFT_FILE):
        try:
            with open(DRIFT_FILE, 'r') as f:
                data = json.load(f)
                
            if not data.get("on_task", True):
                pet = "(ಠ_ಠ)" # Angry
                alert = "🛑 DRIFTING"
                
        except:
            pass
            
    # Check test status (written by shadow hook)
    if os.path.exists(TEST_FILE):
        try:
            with open(TEST_FILE, 'r') as f:
                status = f.read().strip()
            if status == "FAIL":
                pet = "(✖╭╮✖)" # Sad/Dead
                alert = "❌ TESTS FAILED"
        except:
            pass
            
    return pet, alert

def main():
    git_status = get_git_status()
    docs_status = check_stale_docs()
    pet, drift_alert = get_drift_and_pet()
    
    # Build the final string
    # Filter out empty strings
    parts = [p for p in [pet, drift_alert, git_status, docs_status] if p]
    
    # Print for Claude Code to display
    print(" | ".join(parts))

if __name__ == "__main__":
    main()

2. Update config.json (Settings)
You need to tell Claude Code to run python.
Location: C:\Users\YourName\.claude\config.json (or %APPDATA%\Claude\config.json)
JSON
{
  "statusline": "python C:\\Users\\YourName\\.claude\\statusline.py",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python C:\\Users\\YourName\\.claude\\hooks\\drift_detector.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python C:\\Users\\YourName\\.claude\\hooks\\shadow_test.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}

Summary of Changes for Windows
Paths: I switched /tmp/ to os.environ.get("TEMP"). On Windows, this usually resolves to C:\Users\Name\AppData\Local\Temp.
Commands: I explicitly added python before the script names in the config. Windows doesn't always know how to execute a .py file directly if the shebang (#!/usr/bin/env python3) isn't respected by the shell.
File Operations: Used os.path.join to ensure backslashes \ are handled correctly on Windows.

---

v2:
TL;DR: Do not use .sh on Windows unless you are exclusively running Claude Code inside WSL (Windows Subsystem for Linux). Since you are likely running it via PowerShell or Command Prompt, PowerShell (.ps1) is the best choice for the statusline, and Python (.py) is best for the hooks.
Here is why, and how to adapt the roadmap for Windows 11.
Why not TypeScript?
You asked about TypeScript. Avoid it for the statusline. The statusline executes ~3 times per second. ts-node or compiling TS takes too long to start up (latency). It will make your terminal flicker and feel sluggish.
Statusline: Use PowerShell (Native, instant startup).
Hooks: Use Python (Great for JSON/API calls, cross-platform).
The Windows 11 Implementation Plan
We will adapt the architecture to use Windows-native tools.
1. The Statusline: Switch to PowerShell (statusline.ps1)
PowerShell is powerful enough to handle file checks and JSON parsing quickly.
Create File: ~/.claude/statusline.ps1 (Note: ~ on Windows usually resolves to C:\Users\YourName\)
PowerShell
# Set encoding to handle Emojis properly
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- 1. CONFIGURATION ---
$tempDir = [System.IO.Path]::GetTempPath()
$driftFile = Join-Path $tempDir "cc_drift_state.json"
$testFile = Join-Path $tempDir "cc_test_status"
$srcDir = Resolve-Path "src" -ErrorAction SilentlyContinue
$docDir = Resolve-Path "docs" -ErrorAction SilentlyContinue

# --- 2. GIT STATUS ---
try {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branch -eq "main" -or $branch -eq "master") {
        $gitDisplay = "🚨 PROD"
    } elseif ($null -ne $branch) {
        $gitDisplay = "🌿 $branch"
    } else {
        $gitDisplay = "No Git"
    }
} catch {
    $gitDisplay = "Git Err"
}

# --- 3. STALE DOCS CHECK (Compare LastWriteTime) ---
$docMsg = ""
if ($srcDir -and $docDir) {
    # Get latest timestamp from src and docs
    $latestSrc = Get-ChildItem -Path $srcDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $latestDoc = Get-ChildItem -Path $docDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($latestSrc -and $latestDoc) {
        # If Source is > 30 mins newer than Docs
        if (($latestSrc.LastWriteTime - $latestDoc.LastWriteTime).TotalMinutes -gt 30) {
            $docMsg = "⚠️ DOCS STALE"
        }
    }
}

# --- 4. READ BACKGROUND STATES (Drift & Tests) ---
$driftEmoji = ""
if (Test-Path $driftFile) {
    try {
        $json = Get-Content $driftFile -Raw | ConvertFrom-Json
        if ($json.on_task -eq $false) {
            $driftEmoji = "🛑 DRIFT"
        }
    } catch {}
}

$testIcon = ""
if (Test-Path $testFile) {
    $status = Get-Content $testFile -Raw
    switch ($status.Trim()) {
        "PASS" { $testIcon = "🧪✅" }
        "FAIL" { $testIcon = "🧪❌" }
        "RUNNING" { $testIcon = "🧪⏳" }
    }
}

# --- 5. THE TAMAGOTCHI ---
$pet = "(◕‿◕)" # Default Happy
if ($driftEmoji) { $pet = "(ಠ_ಠ)" } # Angry at drift
if ($testIcon -match "❌") { $pet = "(✖╭╮✖)" } # Sad at broken tests

# --- FINAL OUTPUT ---
# This line is what actually prints to your Claude Code footer
Write-Output "$pet $gitDisplay | $testIcon $driftEmoji $docMsg"

2. The Hooks: Stick with Python (.py)
Python works perfectly on Windows. You just need to ensure your paths in the Python script handle backslashes correctly (using pathlib solves this automatically).
The Drift Detector: You can use the exact Python script provided in the previous history. It uses standard libraries. Just ensure you update the file write path to use the system temp directory so PowerShell can find it.
Update the Python script's write section:
Python
import tempfile
import os

# Instead of hardcoding /tmp/, use:
temp_dir = tempfile.gettempdir()
file_path = os.path.join(temp_dir, 'cc_drift_state.json')

with open(file_path, 'w') as f:
    json.dump(state, f)

3. The Wiring: settings.json for Windows
You need to tell Claude how to run these files using the Windows command syntax.
File: ~/.claude/settings.json
JSON
{
  "statusline": "pwsh -NoProfile -ExecutionPolicy Bypass -File \"~/.claude/statusline.ps1\"",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python \"~/.claude/hooks/drift_detector.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}

Key Windows Gotchas to Watch Out For
Execution Policy: If statusline.ps1 refuses to run, you may need to run Set-ExecutionPolicy RemoteSigned -Scope CurrentUser in your terminal once. The -ExecutionPolicy Bypass flag in the JSON above helps avoid this, but it's good to know.
Path Expansion: Claude Code usually expands ~ correctly on Windows, but if you see errors saying "path not found," replace ~ with your full path (e.g., C:\\Users\\Bob\\.claude\\...). Note the double backslashes \\ in JSON.
Encoding: If the emojis (⚠️, 🛑) show up as weird question marks ? or squares [] in your terminal, it's a PowerShell encoding issue. The line [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 at the top of the script fixes this.
What should you do next?
I recommend starting with Phase 1 (Statusline only) using the PowerShell script above.
Save the statusline.ps1 code.
Update your settings.json.
Restart Claude Code.
Check if you see the "Git Branch" and the "Pet" in your footer.
Once that works, then add the Python hooks.

## Assistant

**V2 is better for your Windows 11 PowerShell workflow.** It uses native PowerShell for the high-frequency statusline, minimizing startup and execution overhead critical for the ~300ms update cycle. Python handles hooks effectively, aligning with your preference for it in prior setups.[1][2]

## Key Comparison

| Aspect          | V1 (Python Statusline)                  | V2 (PowerShell Statusline + Python Hooks) | Winner |
|-----------------|-----------------------------------------|-------------------------------------------|--------|
| Statusline Speed | Interprets Python every 300ms; minor startup lag possible | Native PowerShell; instant execution, no interpreter overhead | V2 [1][3] |
| Windows Native  | Requires "python" prefix; works but less seamless | "pwsh -NoProfile"; direct integration, handles emojis/paths natively | V2 [4] |
| JSON/File Handling | Excellent (json/os libs)               | Good (ConvertFrom-Json/Get-ChildItem); sufficient for small files | Tie [5] |
| Maintenance     | Single language; your Python expertise | Split but simple; matches your multi-tool habits | V2  |
| Git/Docs Checks | Walks directories (slower on large repos) | Get-ChildItem -Recurse (optimized for Windows FS) | V2 [3] |

## Implementation Advantages
V2 addresses Windows gotchas like execution policy and ~ expansion upfront, reducing debugging time in your multi-terminal setup. PowerShell's UTF8 encoding fix ensures emojis display cleanly in terminals. Start with V2's Phase 1 (statusline.ps1 + settings.json) for quick wins on git/pet display.[6][1]

## Potential Drawbacks
V1 unifies everything in Python, easier if avoiding PowerShell quirks, but risks flicker on status updates due to invocation. Both integrate drift/tests via temp files, but V2's test states (PASS/FAIL/RUNNING) add granularity. Your history favors Python overall, yet V2 fits native PowerShell runs better.[7][2][3]
