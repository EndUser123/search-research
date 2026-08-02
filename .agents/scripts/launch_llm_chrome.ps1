<#
.SYNOPSIS
Launch Chrome with the dedicated LLM profile and create the DevToolsActivePort file.

.DESCRIPTION
Chrome's chrome://inspect toggle enables remote debugging on port 9222 but
does not create the DevToolsActivePort file that chrome-devtools-mcp's
--autoConnect needs. This script:
1. Kills any existing Chrome (clean start)
2. Launches Chrome with the dedicated LLM profile
3. Waits for Chrome to bind port 9222
4. Writes the DevToolsActivePort file
5. Verifies the MCP can connect

USAGE
    python P:/.agents/scripts/launch_llm_chrome.ps1
    # Or just run directly:
    P:/.agents/scripts/launch_llm_chrome.ps1
#>

$ErrorActionPreference = "Stop"
$ChromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$ProfileDir = "P:\.data\chrome-llm-profile"
$PortFile = Join-Path $ProfileDir "DevToolsActivePort"
$Port = 9222

# Step 1: Kill existing Chrome
$existing = Get-Process chrome -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Killing existing Chrome processes..." -ForegroundColor Yellow
    taskkill /F /IM chrome.exe /T 2>$null
    Start-Sleep -Seconds 3
}

# Step 2: Launch Chrome with dedicated profile
Write-Host "Launching Chrome with LLM profile: $ProfileDir" -ForegroundColor Cyan
Start-Process $ChromeExe -ArgumentList "--user-data-dir=$ProfileDir", "--new-window"
Start-Sleep -Seconds 4

$alive = (Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count
if ($alive -eq 0) {
    Write-Host "ERROR: Chrome failed to start" -ForegroundColor Red
    exit 1
}
Write-Host "Chrome running: $alive processes" -ForegroundColor Green

# Step 3: Wait for port 9222 to be listening (toggle must be on)
Write-Host "Checking port $Port..." -ForegroundColor Cyan
$maxWait = 15
$waited = 0
while ($waited -lt $maxWait) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "Port $Port is listening" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 1
    $waited++
}

if (-not $conn) {
    Write-Host "WARNING: Port $Port not listening after ${maxWait}s." -ForegroundColor Yellow
    Write-Host "Enable the toggle at chrome://inspect in the LLM profile, then re-run this script." -ForegroundColor Yellow
    exit 1
}

# Step 4: Write DevToolsActivePort file
# The wsPath needs to match Chrome's actual browser endpoint.
# Query the HTTP endpoint for the real WebSocket path.
try {
    $version = Invoke-RestMethod "http://127.0.0.1:$Port/json/version" -TimeoutSec 3
    $wsUrl = $version.webSocketDebuggerUrl
    if ($wsUrl -match "/devtools/browser/([a-f0-9-]+)") {
        $wsPath = "/devtools/browser/$($Matches[1])"
    } else {
        $wsPath = "/devtools/browser"
    }
} catch {
    # HTTP endpoint returns 404 with pipe protocol — use default path
    $wsPath = "/devtools/browser"
}

Write-Host "Writing DevToolsActivePort: $Port + $wsPath" -ForegroundColor Cyan
Set-Content -Path $PortFile -Value "$Port`n$wsPath" -NoNewline -Encoding ASCII
Write-Host "DevToolsActivePort created at $PortFile" -ForegroundColor Green

# Step 5: Verify
Write-Host ""
Write-Host "Chrome LLM profile is ready." -ForegroundColor Green
Write-Host "  Profile: $ProfileDir"
Write-Host "  Port: $Port"
Write-Host "  DevToolsActivePort: $PortFile"
Write-Host ""
Write-Host "Reload plugins (r) for the MCP server to connect." -ForegroundColor Cyan
