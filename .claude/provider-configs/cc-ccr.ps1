# cc-ccr.ps1 — Claude Code → CCR proxy launcher
#
# Usage:
#   . .\cc-ccr.ps1                    # start CCR, wire this shell to CCR
#   . .\cc-ccr.ps1 -Log               # start with CCR logs visible
#   . .\cc-ccr.ps1 -Stop              # kill CCR process
#   . .\cc-ccr.ps1 -Config            # launch TUI to configure model routes
#
# Model route overrides (environment variables):
#   $env:CC_CCR_OPUS_ROUTE = "zai,glm-5.2"
#   $env:CC_CCR_SONNET_ROUTE = "minimax,MiniMax-M2.7"
#   $env:CC_CCR_HAIKU_ROUTE = "opencode-go,deepseek-v4-flash"
#   $env:CC_CCR_CUSTOM_ROUTE = "provider,model"
#   cc-ccr
#
# Or use the interactive TUI: . .\cc-ccr.ps1 -Config
#
# Architecture:
#   Claude Code → CCR (3456) → external models
#   CCR routes to cost-effective models (72-94% savings)
#
# CCR config: C:\Users\brsth\.claude-code-router\config.json
# TUI script: P:\.claude\provider-configs\cc-ccr-tui.ps1

param(
    [switch]$Stop,
    [switch]$Log,
    [switch]$Config,
    [switch]$Tui
)

$headroomPort = 8787
$headroomUrl  = "http://localhost:$headroomPort"
$ccrPort      = 3456
$ccrUrl       = "http://localhost:$ccrPort"
$ccrCmd       = "$env:APPDATA\npm\ccr.cmd"

# --- Load secrets from .env ---
$envPath = "P:\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
    }
} else {
    Write-Warning "[cc-ccr] No .env file at $envPath"
}

# --- Model route overrides (environment variables) ---
# Use these to override the default routing without editing files:
#   $env:CC_CCR_OPUS_ROUTE = "zai,glm-5.2"
#   $env:CC_CCR_SONNET_ROUTE = "minimax,MiniMax-M2.7"
#   $env:CC_CCR_HAIKU_ROUTE = "opencode-go,deepseek-v4-flash"
#   $env:CC_CCR_CUSTOM_ROUTE = "provider,model"
$overrideOpus = $env:CC_CCR_OPUS_ROUTE
$overrideSonnet = $env:CC_CCR_SONNET_ROUTE
$overrideHaiku = $env:CC_CCR_HAIKU_ROUTE
$overrideCustom = $env:CC_CCR_CUSTOM_ROUTE

if ($overrideOpus) { Write-Host "[CCR] Opus override: $overrideOpus" -ForegroundColor Cyan }
if ($overrideSonnet) { Write-Host "[CCR] Sonnet override: $overrideSonnet" -ForegroundColor Cyan }
if ($overrideHaiku) { Write-Host "[CCR] Haiku override: $overrideHaiku" -ForegroundColor Cyan }
if ($overrideCustom) { Write-Host "[CCR] Custom override: $overrideCustom" -ForegroundColor Cyan }

# --- TUI mode: Launch configuration UI ---
if ($Config -or $Tui) {
    & "$PSScriptRoot\cc-ccr-tui.ps1" -SkipRestart
    return
}

# --- Stop mode ---
if ($Stop) {
    # Stop Headroom
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" | Select-Object -ExpandProperty CommandLine) -match 'headroom.*proxy' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    # Stop CCR
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" | Select-Object -ExpandProperty CommandLine) -match 'claude-code-router' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    # Cleanup health job if running
    Get-Job -Name "headroom-health" -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Job -Id $_.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

    Write-Host "[cc-ccr] Stopped Headroom and CCR." -ForegroundColor Yellow

    # Restore ANTHROPIC_BASE_URL if it was pointing at Headroom
    if ($env:ANTHROPIC_BASE_URL -eq $headroomUrl) {
        Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
        Write-Host "[cc-ccr] ANTHROPIC_BASE_URL cleared." -ForegroundColor Yellow
    }
    return
}

# --- Guard: fail fast if ccr.cmd not found ---
if (-not (Test-Path $ccrCmd)) {
    Write-Warning "[cc-ccr] ccr not found at $ccrCmd — run: npm install -g @musistudio/claude-code-router"
    return
}

# --- Hint: TUI available for easy model configuration ---
Write-Host "[cc-ccr] Tip: Run 'cc-ccr -Config' to launch the TUI for interactive model route configuration" -ForegroundColor DarkGray

# --- Opus rotation: sticky per session ---
$rotationStatePath = "$env:USERPROFILE\.claude-code-router\rotation-state.json"
$ccrConfigPath     = "$env:USERPROFILE\.claude-code-router\config.json"

$lastProvider = "zai"
if (Test-Path $rotationStatePath) {
    try { $lastProvider = (Get-Content $rotationStatePath -Raw | ConvertFrom-Json).last } catch { }
}

if ($lastProvider -eq "minimax") {
    $opusRoute    = "zai,glm-5.2"
    $sonnetRoute  = "zai,glm-4.7"
    $thisProvider = "zai"
} else {
    $opusRoute    = "minimax,MiniMax-M3"
    $sonnetRoute  = "minimax,MiniMax-M2.7"
    $thisProvider = "minimax"
}

try {
    $cfg = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json

    # Apply default routes (with rotation)
    $actualOpus = if ($overrideOpus) { $overrideOpus } else { $opusRoute }
    $actualSonnet = if ($overrideSonnet) { $overrideSonnet } else { $sonnetRoute }
    $actualHaiku = if ($overrideHaiku) { $overrideHaiku } else { "opencode-go,deepseek-v4-flash" }

    $cfg.Router | Add-Member -NotePropertyName "claude-opus-4-8"          -NotePropertyValue $actualOpus                  -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-sonnet-4-6"        -NotePropertyValue $actualSonnet                -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5"         -NotePropertyValue $actualHaiku                -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5-20251001" -NotePropertyValue $actualHaiku                -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-local-gemma"        -NotePropertyValue "lmstudio,gemma-4-12b-coder-fable5-composer2.5-v1" -Force

    # Apply custom override if specified
    if ($overrideCustom) {
        $cfg.Router | Add-Member -NotePropertyName "claude-custom"       -NotePropertyValue $overrideCustom              -Force
    }

    $tmpPath = $ccrConfigPath + ".tmp"
    ($cfg | ConvertTo-Json -Depth 10) | Set-Content $tmpPath -Encoding UTF8
    Move-Item $tmpPath $ccrConfigPath -Force
    [PSCustomObject]@{ last = $thisProvider } | ConvertTo-Json | Set-Content $rotationStatePath -Encoding UTF8

    # Wait for CCR to pick up config changes
    Start-Sleep -Milliseconds 500
    try {
        Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
    } catch {
        Write-Warning "[CCR] Config updated but health check failed. CCR may need manual restart."
    }
} catch {
    Write-Warning "[CCR] Rotation failed — using existing config: $_"
}

# --- Helper: Start Headroom ---
function Start-Headroom {
    # DISABLED: Headroom removed - routing directly to CCR
    return $false
}

# --- Start CCR if not already running (Headroom needs upstream) ---
$ccrRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $ccrRunning = $true
    Write-Host "[CCR] Already running at $ccrUrl" -ForegroundColor DarkGray
} catch {
    Write-Host "[CCR] Starting..." -ForegroundColor Cyan
    $ccrWindow = if ($Log) { "Normal" } else { "Hidden" }
    Start-Process pwsh -ArgumentList "-Command", "& '$ccrCmd' start" -WindowStyle $ccrWindow
    Start-Sleep -Milliseconds 2000
    try {
        $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[CCR] Started at $ccrUrl  (HTTP $($r.StatusCode))" -ForegroundColor Green
        $ccrRunning = $true
    } catch {
        Write-Warning "[CCR] Failed to start — check that ccr is installed"
        return
    }
}

if (-not $ccrRunning) {
    return
}

# --- Headroom REMOVED ---
# Headroom compression removed — routing directly to CCR
$headroomRunning = $false

# --- Wire this shell's Claude Code ---
# Claude → CCR → external (Headroom removed)
$env:ANTHROPIC_BASE_URL = $ccrUrl
$proxyLabel = "CCR"

$env:ANTHROPIC_API_KEY              = "ccr-proxy-key"
$env:CLAUDE_CODE_DISABLE_1M_CONTEXT = "1"

Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

# Clear model-alias vars that would bypass the chain
foreach ($var in @(
    'ANTHROPIC_DEFAULT_HAIKU_MODEL',
    'ANTHROPIC_DEFAULT_SONNET_MODEL',
    'ANTHROPIC_DEFAULT_OPUS_MODEL',
    'ANTHROPIC_DEFAULT_OPUS_MODEL_NAME',
    'ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION',
    'ANTHROPIC_CUSTOM_MODEL_OPTION',
    'ANTHROPIC_CUSTOM_MODEL_OPTION_NAME',
    'ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION'
)) {
    Remove-Item "env:$var" -ErrorAction SilentlyContinue
}

# 4th model slot — local Gemma via LM Studio
$env:ANTHROPIC_CUSTOM_MODEL_OPTION             = "claude-local-gemma"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME        = "Gemma 4 12B Coder (Local)"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "LM Studio · gemma-4-12b-coder-fable5-composer2.5-v1"

# --- Health monitoring removed ---
# PowerShell job scoping prevents cross-scope variable updates.
# Use manual health checks if Headroom degradation suspected.

# --- Stats section removed (Headroom disabled) ---
$stats = @{}

# --- Get PIDs for display ---
$headroomPid = "N/A"

$ccrPid = try {
    $ccrPortCheck = Get-NetTCPConnection -LocalPort $ccrPort -State Listen -ErrorAction SilentlyContinue
    if ($ccrPortCheck) { $ccrPortCheck.OwningProcess } else { "N/A" }
} catch { "N/A" }

# --- Render output ---
Write-Host ""

Write-Host "✓ Infrastructure Ready" -ForegroundColor Green

Write-Host ""
Write-Host "  CCR: $ccrUrl (PID $ccrPid)"
Write-Host ""
Write-Host "Route configuration:"
try {
    $ccrCfg = Get-Content $ccrConfigPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $opusDisplay   = $ccrCfg.Router."claude-opus-4-8"
    $sonnetDisplay = $ccrCfg.Router."claude-sonnet-4-6"
    $haikuDisplay  = $ccrCfg.Router."claude-haiku-4-5"
    Write-Host "  opus:   $opusDisplay"
    Write-Host "  sonnet: $sonnetDisplay"
    Write-Host "  haiku:  $haikuDisplay"
} catch {
    Write-Host "  opus:   $actualOpus"
    Write-Host "  sonnet: $actualSonnet"
    Write-Host "  haiku:  $actualHaiku"
}
Write-Host ""
Write-Host "Ready. Run: claude" -ForegroundColor White