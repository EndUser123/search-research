# Re-apply Chrome ACP proxy patches after npm update.
# Run: powershell -ExecutionPolicy Bypass -File P:\packages\chrome-acp\re-apply-patches.ps1
#
# Patches:
#   1. command.js — hard-code WORKSPACE_ROOT = "P:\" (fixes vanishing writes +
#      empty read_file when proxy is launched from wrong directory)
#   2. server.js — POST /restart-proxy endpoint (for sidepanel restart button)
#   3. sidepanel JS — prepend tracked IIFE (patches/sidepanel-iife.js) onto the
#      base bundle. The IIFE contains ALL custom UI features:
#      - Header control buttons (reload, restart proxy, toggle tools/thinking,
#        expand tool results) next to the theme toggle
#      - Working directory lock (P:\)
#      - File search, resize handle, tool-result collapse (P-collapse-tools)
#      The IIFE is git-tracked (~10KB, readable). The base bundle is NOT tracked
#      (13.6MB third-party minified artifact). This script strips any existing
#      IIFE from the live file, then prepends the tracked version — idempotent.

$ErrorActionPreference = "Stop"
$patchDir = $PSScriptRoot
$cliDir = "C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\cli"

# --- Patch 1: command.js (copy patched version) ---
# Hard-codes workspace root to P:\ instead of process.cwd().
# The agent process MUST run from P:\ so native write/read_file tools work.
$src = Join-Path $patchDir "command.patched.js"
$dst = Join-Path $cliDir "command.js"
if (Test-Path $src) {
    Copy-Item $src $dst -Force
    Write-Host "OK: command.js patched (--cwd flag)" -ForegroundColor Green
} else {
    Write-Host "SKIP: command.patched.js not found in $patchDir" -ForegroundColor Yellow
}

# --- Patch 2: server.js (copy patched version) ---
# Adds POST /restart-proxy endpoint for the sidepanel "Restart Proxy" button.
# Also includes all prior server.js patches (P1-P18 from the wiki).
$srcServer = Join-Path $patchDir "server.patched.js"
$dstServer = Join-Path $cliDir "..\server.js"
if (Test-Path $srcServer) {
    Copy-Item $srcServer $dstServer -Force
    Write-Host "OK: server.js patched (/restart-proxy endpoint)" -ForegroundColor Green
} else {
    Write-Host "SKIP: server.patched.js not found" -ForegroundColor Yellow
}

# --- Patch 3: sidepanel JS (prepend tracked IIFE via Python) ---
# Uses a Python helper for byte-level safety — PowerShell's ReadAllText corrupts
# non-UTF-8 byte sequences in the 13MB minified bundle. The helper strips any
# existing IIFE (idempotent) and prepends the tracked version.
$iifeSrc = Join-Path $patchDir "patches\sidepanel-iife.js"
$sideDst = Join-Path $patchDir "dist\sidepanel-t6n74ra3.js"
if (Test-Path $iifeSrc) {
    $prependScript = Join-Path $patchDir "patches\prepend_iife.py"
    & python $prependScript $sideDst $iifeSrc
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: sidepanel patched (IIFE prepended from tracked file)" -ForegroundColor Green
    } else {
        Write-Host "ERROR: sidepanel IIFE prepend failed (exit $LASTEXITCODE)" -ForegroundColor Red
    }
} else {
    Write-Host "SKIP: patches/sidepanel-iife.js not found in $patchDir" -ForegroundColor Yellow
}

# --- Patch 4: start-proxy.bat already has the right command; no re-apply needed ---

Write-Host "`nDone. Restart the proxy to apply." -ForegroundColor Cyan
