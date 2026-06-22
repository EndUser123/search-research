# cc-ccr.ps1 — Claude Code → Headroom → CCR proxy launcher
#
# Usage:
#   . .\cc-ccr.ps1          # start Headroom + CCR chain, wire this shell to Headroom
#   . .\cc-ccr.ps1 -Stop    # kill Headroom and CCR processes
#
# Architecture:
#   Claude Code → Headroom (8787) → CCR (3456) → external models
#   Headroom compresses (30-95% savings), CCR routes (cost reduction)
#
# CCR config:       C:\Users\brsth\.claude-code-router\config.json
# Headroom stats:   curl http://localhost:8787/stats

param(
    [switch]$Stop
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

# --- Stop mode ---
if ($Stop) {
    # Stop Headroom
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -match 'headroom proxy' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    # Stop CCR
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -match 'claude-code-router' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

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
    $cfg.Router | Add-Member -NotePropertyName "claude-opus-4-8"          -NotePropertyValue $opusRoute                   -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-sonnet-4-6"        -NotePropertyValue $sonnetRoute                 -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5"         -NotePropertyValue "opencode-go,deepseek-v4-flash" -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5-20251001" -NotePropertyValue "opencode-go,deepseek-v4-flash" -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-local-gemma"        -NotePropertyValue "lmstudio,gemma-4-12b-coder-fable5-composer2.5-v1" -Force
    $tmpPath = $ccrConfigPath + ".tmp"
    ($cfg | ConvertTo-Json -Depth 10) | Set-Content $tmpPath -Encoding UTF8
    Move-Item $tmpPath $ccrConfigPath -Force
    [PSCustomObject]@{ last = $thisProvider } | ConvertTo-Json | Set-Content $rotationStatePath -Encoding UTF8
} catch {
    Write-Warning "[CCR] Rotation failed — using existing config: $_"
}

# --- Start CCR if not already running (Headroom needs upstream) ---
$ccrRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $ccrRunning = $true
    Write-Host "[CCR] Already running at $ccrUrl" -ForegroundColor DarkGray
} catch {
    Write-Host "[CCR] Starting..." -ForegroundColor Cyan
    Start-Process pwsh -ArgumentList "-Command", "& '$ccrCmd' start" -WindowStyle Normal
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

# --- Start Headroom if not already running ---
$headroomRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$headroomUrl/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $headroomRunning = $true
    Write-Host "[Headroom] Already running at $headroomUrl" -ForegroundColor DarkGray
} catch {
    Write-Host "[Headroom] Starting proxy (compress → CCR)..." -ForegroundColor Cyan
    # Start Headroom with CCR as upstream
    Start-Process python -ArgumentList "-m", "headroom", "proxy", "--port", $headroomPort, "--anthropic-api-url", $ccrUrl -WindowStyle Normal
    Start-Sleep -Milliseconds 2000
    try {
        $r = Invoke-WebRequest -Uri "$headroomUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[Headroom] Started at $headroomUrl  (HTTP $($r.StatusCode))" -ForegroundColor Green
        $headroomRunning = $true
    } catch {
        Write-Warning "[Headroom] Failed to start — run: PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install headroom-ai"
        # Don't fail hard — fall through to CCR-only mode
        $headroomRunning = $false
    }
}

# --- Wire this shell's Claude Code ---
#
# If Headroom is running: Claude → Headroom → CCR → external
# If Headroom failed:   Claude → CCR → external (compression disabled)
if ($headroomRunning) {
    $env:ANTHROPIC_BASE_URL = $headroomUrl
    $proxyLabel = "Headroom → CCR"
} else {
    $env:ANTHROPIC_BASE_URL = $ccrUrl
    $proxyLabel = "CCR (Headroom unavailable)"
}

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

Write-Host ""
Write-Host "  ANTHROPIC_BASE_URL  = $env:ANTHROPIC_BASE_URL" -ForegroundColor Cyan
Write-Host "  Proxy chain         = $proxyLabel" -ForegroundColor Magenta
Write-Host "  ANTHROPIC_API_KEY   = ccr-proxy-key (dummy)" -ForegroundColor Cyan
Write-Host "  Router opus         = $opusRoute" -ForegroundColor Magenta
Write-Host "  Router sonnet       = $sonnetRoute  [was: $lastProvider -> now: $thisProvider]" -ForegroundColor Magenta
Write-Host "  Router haiku        = opencode-go,deepseek-v4-flash" -ForegroundColor Cyan
Write-Host "  Router local (4th)  = lmstudio,gemma-4-12b-coder-fable5-composer2.5-v1" -ForegroundColor DarkCyan
Write-Host ""
if ($headroomRunning) {
    Write-Host "Stats: curl $headroomUrl/stats" -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "Ready. Run: claude" -ForegroundColor White