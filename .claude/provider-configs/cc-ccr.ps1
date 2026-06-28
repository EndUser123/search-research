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
    [switch]$Tui,
    [switch]$Test,
    [switch]$Restart
)

$headroomPort = 8787
$headroomUrl  = "http://localhost:$headroomPort"
$ccrPort      = 3456
$ccrUrl       = "http://localhost:$ccrPort"
$ccrCmd       = "$env:APPDATA\npm\ccr.cmd"

# --- Load secrets from .env into hashtable for CCR process ---
$envPath = "P:\.env"
$ccrEnvVars = @{}

if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object {
        $key = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        if ($value.Length -ge 2 -and (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        # Load into current process
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")

        # Store for passing to CCR
        $ccrEnvVars[$key] = $value
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

# --- -Restart without -Test: no-op with a hint (restart only gates -Test's clean-state restart) ---
if ($Restart -and -not $Test) {
    Write-Host "[cc-ccr] -Restart only applies with -Test (it forces a clean CCR restart before the probe)." -ForegroundColor Yellow
    Write-Host "[cc-ccr] To restart CCR without testing, use: cc-ccr -Stop; cc-ccr" -ForegroundColor DarkGray
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

# --- Static balanced routing (rotation REMOVED) ---
# Each role pinned to its BEST model every session. Quota spreads by workload type
# (heavy reasoning -> Z.ai; high-volume default/background -> MiniMax) and by the
# fallback chains in config.json (verified: CCR retries next chain entry on HTTP/quota
# error). Best-model-every-session AND quota spreading, no rotation downgrade.
# THE SCRIPT OWNS THE ROUTER SECTION. Do NOT hand-edit config.json Router keys -
# they are overwritten here every launch. Change routes here or via CC_CCR_*_ROUTE.
$ccrConfigPath = "$env:USERPROFILE\.claude-code-router\config.json"

# Phase toggles (independent, default OFF). Set before launch.
$phaseLocalApply  = ($env:CC_PHASE_LOCAL_APPLY  -eq "1")
$phaseCompactHook = ($env:CC_PHASE_COMPACT_HOOK -eq "1")

# Base routes (env override wins). Edits -> DeepSeek V4 Flash (79% SWE, best cheap editor).
$actualOpus   = if ($overrideOpus)   { $overrideOpus }   else { "zai,glm-5.2" }
$actualSonnet = if ($overrideSonnet) { $overrideSonnet } else { "minimax,MiniMax-M3[1m]" }
$actualHaiku  = if ($overrideHaiku)  { $overrideHaiku }  else { "opencode-go,deepseek-v4-flash" }

try {
    $cfg = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json

    # SLOT keys (Claude Code calls these by name; must be mapped or it errors)
    $cfg.Router | Add-Member -NotePropertyName "claude-opus-4-8"           -NotePropertyValue $actualOpus   -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-sonnet-4-6"         -NotePropertyValue $actualSonnet -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5"          -NotePropertyValue $actualHaiku  -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5-20251001" -NotePropertyValue $actualHaiku  -Force
    $cfg.Router | Add-Member -NotePropertyName "claude-local-gemma"        -NotePropertyValue "lmstudio,gemma-4-12b-coder-fable5-composer2.5-v1" -Force

    # ROLE keys in lockstep with slot keys (both routing layers agree)
    $cfg.Router | Add-Member -NotePropertyName "think"       -NotePropertyValue $actualOpus   -Force
    $cfg.Router | Add-Member -NotePropertyName "default"     -NotePropertyValue $actualSonnet -Force
    $cfg.Router | Add-Member -NotePropertyName "background"  -NotePropertyValue $actualHaiku  -Force
    $cfg.Router | Add-Member -NotePropertyName "longContext" -NotePropertyValue "minimax,MiniMax-M3[1m]" -Force

    if ($overrideCustom) {
        $cfg.Router | Add-Member -NotePropertyName "claude-custom" -NotePropertyValue $overrideCustom -Force
    }

    $tmpPath = $ccrConfigPath + ".tmp"
    ($cfg | ConvertTo-Json -Depth 10) | Set-Content $tmpPath -Encoding UTF8
    Move-Item $tmpPath $ccrConfigPath -Force

    Start-Sleep -Milliseconds 500
    try {
        Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
    } catch {
        Write-Warning "[CCR] Config updated but health check failed. CCR may need manual restart."
    }
} catch {
    Write-Warning "[CCR] Routing update failed — using existing config: $_"
}

# --- Helper: Stop CCR (kills the claude-code-router node process) ---
function Stop-CCRProcess {
    # Kill by PORT OWNERSHIP, not command-line substring. A substring match on
    # 'claude-code-router' could hit an unrelated node process (IDE backend,
    # watcher, dev server) that happens to have that path in its args. The port
    # is the precise identity of *the* CCR process.
    $listener = Get-NetTCPConnection -LocalPort $ccrPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener -and $listener.OwningProcess) {
        # Snapshot CCR's fallback events BEFORE killing - pino log closes on
        # process exit. The helper has a self-test that exits 2 on parser
        # regression; we let it propagate (don't suppress) so a broken helper
        # doesn't silently produce empty audits.
        $helper = Join-Path $PSScriptRoot 'ccr-fallback-log.ps1'
        if (Test-Path $helper) {
            & $helper 2>&1 | Out-Null
        }
        Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# --- Helper: Start CCR fresh with .env loaded into the spawned process ---
# config.json uses $VAR interpolation (APIKEY="$CCR_LOCAL_KEY", provider keys).
# Start-Process does NOT carry this session's Process-level env mutations across
# the spawn, so the child must re-source .env itself or $VAR resolves to empty.
function Start-CCRProcess {
    $ccrWindow = if ($Log) { "Normal" } else { "Hidden" }
    $startScript = @"
        foreach (`$line in (Get-Content `$envPath)) {
            if (`$line -match '^([^=]+)=(.*)`$') {
                `$k = `$Matches[1].Trim(); `$v = `$Matches[2].Trim()
                if (`$v.Length -ge 2 -and ((`$v.StartsWith('"') -and `$v.EndsWith('"')) -or (`$v.StartsWith(`"'`") -and `$v.EndsWith(`"'`")))) { `$v = `$v.Substring(1, `$v.Length - 2) }
                [System.Environment]::SetEnvironmentVariable(`$k, `$v, 'Process')
            }
        }
        & '$ccrCmd' start
"@
    Start-Process pwsh -ArgumentList "-NoProfile","-NoLogo","-NonInteractive", "-Command", $startScript -WindowStyle $ccrWindow
    Start-Sleep -Milliseconds 2000
    try {
        $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[CCR] Started at $ccrUrl  (HTTP $($r.StatusCode))" -ForegroundColor Green
        return $true
    } catch {
        Write-Warning "[CCR] Failed to start — check that ccr is installed"
        return $false
    }
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
    $ccrRunning = Start-CCRProcess
    if (-not $ccrRunning) { return }
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

# Auth: CCR accepts the local key via either x-api-key or Authorization: Bearer header.
# Claude Code's proxy-auth path reads ANTHROPIC_AUTH_TOKEN FIRST and falls back to the
# interactive /login menu when it's absent (which then 401s on the first request).
# ANTHROPIC_API_KEY is what -Test uses (x-api-key header) and what some plugin env
# reads expect. Set BOTH to the CCR key. The "Both set" warning Claude Code prints is
# cosmetic; a 401 from missing AUTH_TOKEN is fatal.
$ccrLocalKey = $ccrEnvVars["CCR_LOCAL_KEY"]
if (-not $ccrLocalKey) {
    Write-Warning "[cc-ccr] CCR_LOCAL_KEY not found in .env - gateway auth will fail (401)."
    $ccrLocalKey = "ccr-proxy-key"
}
$env:ANTHROPIC_API_KEY    = $ccrLocalKey
$env:ANTHROPIC_AUTH_TOKEN = $ccrLocalKey
# CLAUDE_CODE_DISABLE_1M_CONTEXT intentionally NOT set - routing relies on [1m] models;
# context handling is delegated to CCR (longContextThreshold) + the [1m] model ids.

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
# --- Phase status banner ---
Write-Host ""
Write-Host "Phases:"
if ($phaseLocalApply)  { Write-Host "  local-apply:  requested (verify model loaded in LM Studio)" -ForegroundColor Yellow }
else                   { Write-Host "  local-apply:  off" -ForegroundColor DarkGray }
if ($phaseCompactHook) { Write-Host "  compact-hook: requested (verify hook file present)" -ForegroundColor Yellow }
else                   { Write-Host "  compact-hook: off" -ForegroundColor DarkGray }

# --- Foundation self-test: prove ONE real request succeeds through CCR ---
# This is the check the reviewers were right to demand. Runs only with -Test.
if ($Test) {
    # Restart is OPT-IN (-Test -Restart). Automatic restart would kill CCR
    # mid-flight for any other shell routing through it. Default -Test just
    # probes the running instance; -Restart forces a clean stop+start first.
    if ($Restart) {
        Write-Host ""
        Write-Host "[Test] Restarting CCR for a clean test state..." -ForegroundColor Cyan
        Stop-CCRProcess
        Start-Sleep -Seconds 1
        $ccrRunning = Start-CCRProcess
        if (-not $ccrRunning) {
            Write-Host "  ABORT - CCR did not come back up." -ForegroundColor Red
            return
        }
    }
    Write-Host "Running end-to-end test through CCR..." -ForegroundColor Cyan
    $body = @{
        model = "claude-sonnet-4-6"
        max_tokens = 16
        messages = @(@{ role = "user"; content = "Reply with exactly: OK" })
    } | ConvertTo-Json -Depth 5
    try {
        # Mirror Claude Code's actual auth path: it uses Authorization: Bearer derived
        # from ANTHROPIC_AUTH_TOKEN. Earlier versions of -Test used x-api-key only,
        # which could PASS the test while real `claude` 401'd because Claude Code never
        # sent x-api-key. Test Bearer FIRST (Claude Code's path); fall back to x-api-key
        # so the test covers both accepted header styles.
        $bearerHeaders = @{ "Authorization" = "Bearer $env:ANTHROPIC_AUTH_TOKEN"; "anthropic-version" = "2023-06-01"; "Content-Type" = "application/json" }
        $resp = Invoke-RestMethod -Uri "$ccrUrl/v1/messages" -Method Post `
            -Headers $bearerHeaders `
            -Body $body -TimeoutSec 30 -ErrorAction Stop
        $text = ($resp.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text
        Write-Host "  PASS - CCR routed a real request via Bearer (Claude Code's auth path). Model replied: '$text'" -ForegroundColor Green
        Write-Host "  (sonnet route = $actualSonnet)" -ForegroundColor DarkGray
    } catch {
        # Fallback: try x-api-key (CCR also accepts this; some plugin code paths use it).
        try {
            $xApiHeaders = @{ "x-api-key" = $env:ANTHROPIC_API_KEY; "anthropic-version" = "2023-06-01"; "Content-Type" = "application/json" }
            $resp = Invoke-RestMethod -Uri "$ccrUrl/v1/messages" -Method Post `
                -Headers $xApiHeaders `
                -Body $body -TimeoutSec 30 -ErrorAction Stop
            $text = ($resp.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text
            Write-Host "  PASS - CCR routed via x-api-key fallback. Model replied: '$text'" -ForegroundColor Green
            Write-Host "  (sonnet route = $actualSonnet)" -ForegroundColor DarkGray
            return
        } catch {
            Write-Host "  FAIL - Both Bearer and x-api-key rejected." -ForegroundColor Red
            Write-Host "  Last error: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  Check: (1) ANTHROPIC_AUTH_TOKEN matches CCR APIKEY, (2) provider keys in .env, (3) ccr logs" -ForegroundColor Yellow
            Write-Host "" -ForegroundColor Yellow
            Write-Host "  If this failed, run these next checks to pinpoint whether the issue is the script or CCR:" -ForegroundColor Yellow
            Write-Host "  Current script key: $env:ANTHROPIC_AUTH_TOKEN" -ForegroundColor Yellow
            $resolvedCcrLocalKey = [System.Environment]::GetEnvironmentVariable('CCR_LOCAL_KEY', 'Process')
            Write-Host "  Process CCR_LOCAL_KEY: $resolvedCcrLocalKey" -ForegroundColor Yellow
            Write-Host "  Running direct CCR probes..." -ForegroundColor Yellow
            $curlBody = '{"model":"claude-sonnet-4-6","max_tokens":16,"messages":[{"role":"user","content":"Reply OK"}]}'
            $headerValues = @($env:ANTHROPIC_AUTH_TOKEN, $env:ANTHROPIC_API_KEY, $resolvedCcrLocalKey)
            foreach ($headerValue in $headerValues | Select-Object -Unique) {
                Write-Host "  Probe Bearer header value: $headerValue" -ForegroundColor Yellow
                $curlArgs = @(
                    '-s','-o','-','-w','`nHTTP %{http_code}`n',
                    '-X','POST',"$ccrUrl/v1/messages",
                    '-H',"Authorization: Bearer $headerValue",
                    '-H','anthropic-version: 2023-06-01',
                    '-H','content-type: application/json',
                    '-d',$curlBody
                )
                $curlOutput = & curl.exe @curlArgs 2>$null
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  curl exited with code $LASTEXITCODE" -ForegroundColor Yellow
                }
                if ($curlOutput) {
                    $curlOutput | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
                }
            }
            Write-Host "  These probes compare both env values plus the resolved process CCR_LOCAL_KEY. If all three return HTTP 401, the gateway is rejecting the token itself." -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "Ready. Run: claude" -ForegroundColor White
Write-Host "Tip: 'cc-ccr -Test' sends one real request to verify the whole chain works." -ForegroundColor DarkGray
