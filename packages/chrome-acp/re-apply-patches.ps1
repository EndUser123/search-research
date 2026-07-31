# Re-apply Chrome ACP proxy patches after npm update.
# Run: powershell -ExecutionPolicy Bypass -File P:\packages\chrome-acp\re-apply-patches.ps1
#
# Patches:
#   1. command.js — hard-code WORKSPACE_ROOT = "P:\" (fixes vanishing writes +
#      empty read_file when proxy is launched from wrong directory)
#   2. server.js — POST /restart-proxy endpoint (for sidepanel restart button)
#   3. sidepanel JS — all IIFE-injected features:
#      - Restart Proxy button (power icon) in status bar
#      - Working directory lock (P:\)
#      - File search, resize handle, thinking/tool-call toggles
#      - Tool-result collapse (P-collapse-tools): caps .acp-tc blocks at
#        max-height:300px with overflow-y:auto; maximize toggle button in
#        floating controls expands all tool results. State persists in
#        localStorage("acp_et").

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

# --- Patch 3: sidepanel JS (copy patched version) ---
# Adds all IIFE-injected features: Restart Proxy button, working dir lock,
# file search, resize handle, thinking/tool-call toggles, and tool-result
# collapse (P-collapse-tools). See wiki for full patch inventory.
$srcSide = Join-Path $patchDir "dist\sidepanel-t6n74ra3.patched.js"
$dstSide = Join-Path $patchDir "dist\sidepanel-t6n74ra3.js"
if (Test-Path $srcSide) {
    Copy-Item $srcSide $dstSide -Force
    Write-Host "OK: sidepanel patched (Restart Proxy button)" -ForegroundColor Green
} else {
    Write-Host "SKIP: sidepanel-t6n74ra3.patched.js not found" -ForegroundColor Yellow
}

# --- Patch 4: start-proxy.bat already has the right command; no re-apply needed ---

Write-Host "`nDone. Restart the proxy to apply." -ForegroundColor Cyan
