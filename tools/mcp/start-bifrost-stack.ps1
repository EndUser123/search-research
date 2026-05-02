# start-bifrost-stack.ps1
# Starts @cyanheads/filesystem-mcp-server in HTTP mode on port 3010.
# Bifrost itself is started separately via `cc-bf` (which sets env vars and launches claude).
# This script only manages the filesystem MCP server.

param(
    [string]$FsRoot = "P:\",
    [int]$McpPort = 3010
)

$ErrorActionPreference = "Stop"

$RepoDir = Join-Path $env:TEMP "filesystem-mcp-server"

# --- Clone if not present ---
if (-not (Test-Path $RepoDir)) {
    Write-Host "Cloning filesystem-mcp-server..." -ForegroundColor Cyan
    git clone --depth 1 https://github.com/cyanheads/filesystem-mcp-server.git $RepoDir
}

# --- Build if dist/index.js missing ---
if (-not (Test-Path (Join-Path $RepoDir "dist\index.js"))) {
    Write-Host "Building filesystem-mcp-server..." -ForegroundColor Cyan
    Push-Location $RepoDir
    npm install
    npm run build
    Pop-Location
}

# --- Start HTTP server ---
$env:MCP_TRANSPORT_TYPE = "http"
$env:MCP_HTTP_HOST = "127.0.0.1"
$env:MCP_HTTP_PORT = "$McpPort"
$env:FS_BASE_DIRECTORY = $FsRoot

Write-Host ""
Write-Host "=== Filesystem MCP Server ===" -ForegroundColor Yellow
Write-Host "  Root: $FsRoot"
Write-Host "  URL:  http://$($env:MCP_HTTP_HOST):$McpPort" -ForegroundColor White
Write-Host ""

$serverJob = Start-Job -ScriptBlock {
    param($repoDir, $host, $port, $root)
    $env:MCP_TRANSPORT_TYPE = "http"
    $env:MCP_HTTP_HOST = $host
    $env:MCP_HTTP_PORT = "$port"
    $env:FS_BASE_DIRECTORY = $root
    Set-Location $repoDir
    node dist/index.js
} -ArgumentList $RepoDir, $env:MCP_HTTP_HOST, $env:MCP_HTTP_PORT, $env:FS_BASE_DIRECTORY

Start-Sleep -Seconds 3

if ($serverJob.State -ne 'Running') {
    Write-Host "Filesystem MCP server failed to start." -ForegroundColor Red
    Receive-Job $serverJob -Keep
    exit 1
}

Write-Host "Filesystem MCP server started (Job Id: $($serverJob.Id))" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Cyan

# --- Wait for interrupt ---
try {
    Wait-Job $serverJob -Timeout ([TimeSpan]::FromDays(365)) | Out-Null
} finally {
    Write-Host ""
    Write-Host "Stopping filesystem MCP server..." -ForegroundColor Yellow
    Stop-Job $serverJob -Force -ErrorAction SilentlyContinue
    Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped." -ForegroundColor Green
}
