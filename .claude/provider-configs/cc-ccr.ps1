# cc-ccr.ps1 — Claude Code -> CCR proxy launcher
#
# Usage:
#   . .\cc-ccr.ps1          # start CCR in new window, wire this shell to it
#   . .\cc-ccr.ps1 -Stop    # kill running CCR process
#
# After sourcing: run 'claude' in this terminal.
# CCR config:  C:\Users\brsth\.claude-code-router\config.json
# Normalizer:  C:\Users\brsth\.claude-code-router\plugins\minimax-normalizer.js

param(
    [switch]$Stop
)

$ccrPort = 3456
$ccrUrl  = "http://localhost:$ccrPort"
$ccrCmd  = "$env:APPDATA\npm\ccr.cmd"

# --- Load secrets from .env ---
$envPath = "P:\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
    }
} else {
    Write-Warning "[CCR] No .env file at $envPath"
}

# --- Stop mode ---
if ($Stop) {
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -match 'claude-code-router' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[CCR] Stopped." -ForegroundColor Yellow

    # Restore ANTHROPIC_BASE_URL to Anthropic default if it was pointing at CCR
    if ($env:ANTHROPIC_BASE_URL -eq $ccrUrl) {
        Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
        Write-Host "[CCR] ANTHROPIC_BASE_URL cleared." -ForegroundColor Yellow
    }
    return
}

# --- Guard: fail fast if ccr.cmd not found ---
if (-not (Test-Path $ccrCmd)) {
    Write-Warning "[CCR] ccr not found at $ccrCmd — run: npm install -g @musistudio/claude-code-router"
    return
}

# --- Opus rotation: sticky per session ---
# Rotates the claude-opus-4-8 route between minimax,MiniMax-M2.7 and zai,glm-5.1.
# State persists in rotation-state.json; each cc-ccr invocation flips the provider.
$rotationStatePath = "$env:USERPROFILE\.claude-code-router\rotation-state.json"
$ccrConfigPath     = "$env:USERPROFILE\.claude-code-router\config.json"

$lastProvider = "zai"   # if no state file, default so first run picks minimax
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

# --- Start CCR if not already running ---
$ccrRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $ccrRunning = $true
    Write-Host "[CCR] Already running at $ccrUrl" -ForegroundColor DarkGray
} catch { }

if (-not $ccrRunning) {
    Start-Process pwsh -ArgumentList "-Command", "& '$ccrCmd' start" -WindowStyle Normal
    Start-Sleep -Milliseconds 2000
    try {
        $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[CCR] Started at $ccrUrl  (HTTP $($r.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Warning "[CCR] Failed to start — check that ccr is installed (npm install -g @musistudio/claude-code-router)"
        return
    }
}

# --- Wire this shell's Claude Code to CCR ---
#
# ANTHROPIC_BASE_URL  — CCR listens on :3456 and handles /v1/messages natively
# ANTHROPIC_API_KEY   — CCR ignores this; Claude Code requires it to be non-empty
# ANTHROPIC_AUTH_TOKEN — must be absent so it doesn't shadow the API key path
$env:ANTHROPIC_BASE_URL             = $ccrUrl
$env:ANTHROPIC_API_KEY              = "ccr-proxy-key"
$env:CLAUDE_CODE_DISABLE_1M_CONTEXT = "1"

Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue

# Clear model-alias vars that would bypass CCR's Router config
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

# 4th model slot — local Gemma via LM Studio (set after clear to override inherited values)
$env:ANTHROPIC_CUSTOM_MODEL_OPTION             = "claude-local-gemma"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME        = "Gemma 4 12B Coder (Local)"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "LM Studio · gemma-4-12b-coder-fable5-composer2.5-v1"

Write-Host ""
Write-Host "  ANTHROPIC_BASE_URL  = $env:ANTHROPIC_BASE_URL" -ForegroundColor Cyan
Write-Host "  ANTHROPIC_API_KEY   = ccr-proxy-key (dummy — CCR ignores it)" -ForegroundColor Cyan
Write-Host "  Router default      = opencode-go,deepseek-v4-flash  (fallthrough)" -ForegroundColor Cyan
Write-Host "  Router opus         = $opusRoute" -ForegroundColor Magenta
Write-Host "  Router sonnet       = $sonnetRoute  [was: $lastProvider -> now: $thisProvider]" -ForegroundColor Magenta
Write-Host "  Router haiku        = opencode-go,deepseek-v4-flash  (fixed)" -ForegroundColor Cyan
Write-Host "  Router local (4th)  = lmstudio,gemma-4-12b-coder-fable5-composer2.5-v1  (ANTHROPIC_CUSTOM_MODEL_OPTION=claude-local-gemma)" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "Ready. Run: claude" -ForegroundColor White
