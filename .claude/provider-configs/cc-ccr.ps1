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
    [switch]$Usage,
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

# Base routes (single provider,model pairs — fallback chains are in the config's
# `fallback` key, not in the Router value. Verified: comma-separated pairs in Router
# values do NOT create fallback chains; CCR treats the value as one provider,model pair.
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
    # Local slot via LM Studio. Renamed from claude-local-gemma (the old gemma-4-12b-coder
    # fine-tune is no longer in LM Studio). Drop the stale key so config.json stays clean.
    try { $cfg.Router.PSObject.Properties.Remove("claude-local-gemma") } catch {}
    $cfg.Router | Add-Member -NotePropertyName "claude-local-ornith"        -NotePropertyValue "lmstudio,ornith-1.0-9b@q4_k_m" -Force

    # ROLE keys in lockstep with slot keys (both routing layers agree)
    $cfg.Router | Add-Member -NotePropertyName "think"       -NotePropertyValue $actualOpus   -Force
    $cfg.Router | Add-Member -NotePropertyName "default"     -NotePropertyValue $actualSonnet -Force
    $cfg.Router | Add-Member -NotePropertyName "background"  -NotePropertyValue $actualHaiku  -Force
    $cfg.Router | Add-Member -NotePropertyName "longContext" -NotePropertyValue "minimax,MiniMax-M3[1m]" -Force

    if ($overrideCustom) {
        $cfg.Router | Add-Member -NotePropertyName "claude-custom" -NotePropertyValue $overrideCustom -Force
    }

    # Custom router: makes the local slot (claude-local-ornith) actually serve
    # from LM Studio. CCR's default router keys off opus/sonnet/haiku keywords
    # and the six named role keys, so the custom name would otherwise fall back
    # to default (minimax). The script below runs first and intercepts it.
    # Source-of-truth: ccr-custom-router.js, co-located here and version-controlled.
    $customRouterPath = (Join-Path $PSScriptRoot 'ccr-custom-router.js') -replace '\\', '/'
    $cfg | Add-Member -NotePropertyName 'CUSTOM_ROUTER_PATH' -NotePropertyValue $customRouterPath -Force

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

# --- Helper: Format an epoch-ms quota reset as a countdown + local timestamp ---
# z.ai returns nextResetTime; minimax returns end_time / weekly_end_time. Both epoch-ms.
# Smart units: <1h = "Xm", <72h = "Xh Ym", >=72h = "Xd Yh". Returns "countdown · ddd HH:mm".
function Format-QuotaReset {
    param([long]$EpochMs)
    if (-not $EpochMs -or $EpochMs -le 0) { return "" }
    try {
        $reset = [DateTimeOffset]::FromUnixTimeMilliseconds($EpochMs).LocalDateTime
        $remaining = $reset - (Get-Date)
        if ($remaining -le [TimeSpan]::Zero) { return "pending" }
        $totHr = [int][Math]::Floor($remaining.TotalHours)
        $cd = if     ($totHr -ge 72) { "{0}d {1}h" -f [int][Math]::Floor($totHr/24), ($totHr % 24) }
              elseif ($totHr -ge 1)  { "{0}h {1}m" -f $totHr, $remaining.Minutes }
              else                   { "{0}m" -f [int][Math]::Floor($remaining.TotalMinutes) }
        return "{0} · {1}" -f $cd.PadRight(8), $reset.ToString("ddd HH:mm")
    } catch { return "" }
}

# --- Helper: format a reset-by seconds-from-now countdown. opencode-go reports
# resetInSec (a duration), not an absolute epoch. Convert to epoch-ms by adding
# "now" so the display matches z.ai/minimax ("Xd Yh · ddd HH:mm").
function Format-ResetInSec {
    param([long]$Sec)
    if (-not $Sec -or $Sec -le 0) { return "" }
    $epochMs = [long]((Get-Date).ToUniversalTime() - [DateTime]::new(1970,1,1,0,0,0,[DateTimeKind]::Utc)).TotalMilliseconds + ($Sec * 1000)
    return Format-QuotaReset $epochMs
}

# --- Helper: draw a micro gauge bar like [████████░░] from 0-100 ---
function Write-GaugeBar {
    param([int]$Percent)
    $filled = [Math]::Floor([Math]::Min(100, [Math]::Max(0, $Percent)) / 10)
    $empty  = 10 - $filled
    $barColor = if     ($Percent -gt 50) { 'Green' }
                elseif ($Percent -ge 20) { 'Yellow' }
                else                     { 'Red' }
    Write-Host "[" -NoNewline
    if ($filled -gt 0) { Write-Host ("█" * $filled) -NoNewline -ForegroundColor $barColor }
    if ($empty -gt 0)  { Write-Host ("░" * $empty) -NoNewline -ForegroundColor DarkGray }
    Write-Host "] " -NoNewline
}

# --- Helper: write one aligned usage row with color-coded gauge + remaining ---
function Write-UsageRow {
    param([string]$Window, [string]$Remaining, [string]$Reset)
    $w = $Window.PadRight(15)
    $r = $Remaining.PadRight(22)
    $tail = if ($Reset) { "resets $Reset" } else { "" }
    $pct = if ($Remaining -match '(\d+)%\s*(left|used)') {
        $p = [int]$Matches[1]
        if ($Matches[2] -eq 'used') { 100 - $p } else { $p }
    } else { $null }
    if ($null -ne $pct) { $color = if ($pct -gt 50) { 'Green' } elseif ($pct -ge 20) { 'Yellow' } else { 'Red' } }
    Write-Host "                  " -NoNewline
    Write-Host $w -NoNewline
    if ($null -ne $pct) { Write-GaugeBar $pct }
    if ($color) { Write-Host $r -NoNewline -ForegroundColor $color } else { Write-Host $r -NoNewline }
    Write-Host $tail
}

# --- Helper: draw a thin separator between provider sections ---
function Write-SectionSep { Write-Host "  ───────────────────────────────────────────────────" -ForegroundColor DarkGray }

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

# 4th model slot — local Ornith via LM Studio (qwen35-arch, tool_use capable)
$env:ANTHROPIC_CUSTOM_MODEL_OPTION             = "claude-local-ornith"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME        = "Ornith 1.0 9B (Local)"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "LM Studio · ornith-1.0-9b@q4_k_m"

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
# --- Helper: format a CCR route string (provider1,model1,provider2,model2 → provider1/model1 → provider2/model2) ---
function Format-Route { param([string]$s)
    $parts = $s -split ','
    $pairs = for ($i = 0; $i -lt $parts.Length; $i += 2) {
        if ($i + 1 -lt $parts.Length) { "$($parts[$i])/$($parts[$i+1])" }
        else { $parts[$i] }
    }
    $pairs -join " → "
}
Write-Host "Route configuration:"
try {
    $ccrCfg = Get-Content $ccrConfigPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $opusDisplay   = $ccrCfg.Router."claude-opus-4-8"
    $sonnetDisplay = $ccrCfg.Router."claude-sonnet-4-6"
    $haikuDisplay  = $ccrCfg.Router."claude-haiku-4-5"
    $customDisplay = $ccrCfg.Router."claude-local-ornith"
    Write-Host "  opus:   $(Format-Route $opusDisplay)"
    Write-Host "  sonnet: $(Format-Route $sonnetDisplay)"
    Write-Host "  haiku:  $(Format-Route $haikuDisplay)"
    if ($customDisplay) { Write-Host "  custom: $(Format-Route $customDisplay)" }
    # ── Fallback chains ── CCR's actual failover path: comma-separated provider,model
    # strings in config.fallback.<role>. The top-level Router value is single-pair only;
    # fallbacks fire only from this dedicated key.
    $fb = $ccrCfg.fallback
    if ($fb) {
        $roleMap = @{
            'opus'   = 'think'
            'sonnet' = 'default'
            'haiku'  = 'background'
        }
        foreach ($roleKey in 'opus','sonnet','haiku') {
            $chainRole = $roleMap[$roleKey]
            $chain = $fb.$chainRole
            if ($chain -and $chain.Count -gt 0) {
                $formatted = ($chain | ForEach-Object { Format-Route $_ }) -join ' → '
                Write-Host "           fallback: $formatted" -ForegroundColor DarkGray
            } else {
                Write-Host "           fallback: (none configured)" -ForegroundColor DarkGray
            }
        }
    }
} catch {
    Write-Host "  opus:   $(Format-Route $actualOpus)"
    Write-Host "  sonnet: $(Format-Route $actualSonnet)"
    Write-Host "  haiku:  $(Format-Route $actualHaiku)"
}
Write-Host ""
# --- Phase status banner ---
Write-Host ""
Write-Host "Phases:"
if ($phaseLocalApply)  { Write-Host "  local-apply:  requested (verify model loaded in LM Studio)" -ForegroundColor Yellow }
else                   { Write-Host "  local-apply:  off" -ForegroundColor DarkGray }
if ($phaseCompactHook) { Write-Host "  compact-hook: requested (verify hook file present)" -ForegroundColor Yellow }
else                   { Write-Host "  compact-hook: off" -ForegroundColor DarkGray }

# --- Subscription usage (opt-in via -Usage). z.ai and MiniMax expose quota APIs
# authenticated by the inference key itself; opencode-go has no API, so its block
# scrapes the workspace page with the browser `auth` cookie. Mirrors -Test's
# opt-in pattern so normal launches pay zero extra latency.
if ($Usage) {
    Write-Host ""
    Write-Host "Usage (remaining quota):" -ForegroundColor Cyan
    # ── z.ai / GLM Coding Plan ──
    try {
        $zaiKey = $ccrEnvVars["ZAI_API_KEY"]
        if (-not $zaiKey) { throw "ZAI_API_KEY missing in .env" }
        $zHeaders = @{ "Authorization" = $zaiKey; "Accept-Language" = "en-US,en"; "Content-Type" = "application/json" }
        $z = Invoke-RestMethod -Uri "https://api.z.ai/api/monitor/usage/quota/limit" -Headers $zHeaders -TimeoutSec 15 -ErrorAction Stop
        $level = $z.data.level
        # Canonical field mapping (per glm-plan-usage fork: query-usage.mjs):
        #   TOKENS_LIMIT = "Token usage (5 Hour)" — the rolling 5h GLM-model token window (percentage only)
        #   TIME_LIMIT   = "MCP usage (1 Month)"  — monthly tool/MCP budget (search-prime/web-reader/zread; has currentValue/usage)
        # The previous labels swapped these ("5h"=TIME_LIMIT, "weekly"=TOKENS_LIMIT), which made the
        # nextResetTime countdowns read as nonsense (a "5h" window resetting in 20 days).
        $tokensLimit = $z.data.limits | Where-Object { $_.type -eq "TOKENS_LIMIT" } | Select-Object -First 1
        $mcpLimit    = $z.data.limits | Where-Object { $_.type -eq "TIME_LIMIT" }   | Select-Object -First 1
        $tokStr   = if ($tokensLimit) { "$(100 - [int]$tokensLimit.percentage)% left" } else { "n/a" }
        $tokReset = if ($tokensLimit -and $tokensLimit.nextResetTime) { Format-QuotaReset ([long]$tokensLimit.nextResetTime) } else { "" }
        $mcpStr   = if ($mcpLimit) { "$(100 - [int]$mcpLimit.percentage)% left ($($mcpLimit.currentValue)/$($mcpLimit.usage))" } else { "n/a" }
        $mcpReset = if ($mcpLimit -and $mcpLimit.nextResetTime) { Format-QuotaReset ([long]$mcpLimit.nextResetTime) } else { "" }
        Write-Host "  z.ai            [$level]" -ForegroundColor White
        Write-UsageRow "tokens 5h" $tokStr $tokReset
        Write-UsageRow "MCP month"  $mcpStr $mcpReset
        Write-SectionSep
    } catch {
        Write-Host "  z.ai            error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    # ── MiniMax Coding Plan ──
    try {
        $mmKey = $ccrEnvVars["MINIMAX_API_KEY"]
        if (-not $mmKey) { throw "MINIMAX_API_KEY missing in .env" }
        $mmHeaders = @{ "Authorization" = "Bearer $mmKey"; "Accept-Language" = "en-US,en"; "Content-Type" = "application/json" }
        $mm = Invoke-RestMethod -Uri "https://api.minimax.io/v1/api/openplatform/coding_plan/remains" -Headers $mmHeaders -TimeoutSec 15 -ErrorAction Stop
        $g = $mm.model_remains | Where-Object { $_.model_name -eq "general" } | Select-Object -First 1
        if ($g) {
            $iStr   = "$($g.current_interval_remaining_percent)% left"
            $iReset = if ($g.end_time)        { Format-QuotaReset ([long]$g.end_time) }        else { "" }
            $wStr   = "$($g.current_weekly_remaining_percent)% left"
            $wReset = if ($g.weekly_end_time) { Format-QuotaReset ([long]$g.weekly_end_time) } else { "" }
            Write-Host "  minimax         [general]" -ForegroundColor White
            Write-UsageRow "interval" $iStr $iReset
            Write-UsageRow "weekly"   $wStr $wReset
            Write-SectionSep
        } else {
            Write-Host "  minimax         [general]  (no 'general' entry in response)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  minimax         error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    # ── opencode-go quota (scraped) ──
    # Cookie-scraped from workspace page (no API). Only in .env.
    try {
        $ogWs     = $ccrEnvVars["OPENCODE_GO_WORKSPACE_ID"]
        $ogCookie = $ccrEnvVars["OPENCODE_GO_AUTH_COOKIE"]
        if (-not $ogWs -or -not $ogCookie) { throw "set OPENCODE_GO_WORKSPACE_ID + OPENCODE_GO_AUTH_COOKIE in .env" }
        $ogHeaders = @{
            "Cookie"     = "auth=$ogCookie"
            "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
            "Accept"     = "text/html,application/xhtml+xml,*/*;q=0.8"
        }
        $ogRes  = Invoke-WebRequest -Uri "https://opencode.ai/workspace/$ogWs/go" -Headers $ogHeaders -TimeoutSec 15 -UseBasicParsing -ErrorAction Stop
        $ogHtml = $ogRes.Content
        $ogRows = @()
        foreach ($pair in @(
            @{ Label = 'rolling'; Pat = 'rollingUsage:\$R\[\d+\]=(\{[^}]+\})' },
            @{ Label = 'weekly';  Pat = 'weeklyUsage:\$R\[\d+\]=(\{[^}]+\})' },
            @{ Label = 'monthly'; Pat = 'monthlyUsage:\$R\[\d+\]=(\{[^}]+\})' }
        )) {
            if ($ogHtml -match $pair.Pat) {
                # JS object literal → JSON: quote the bare keys, then parse.
                $lit = $Matches[1] -replace '(?<=[{,])\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', '"$1":'
                try {
                    $obj   = $lit | ConvertFrom-Json
                    $ogRows += @{ Label = $pair.Label; Pct = [int]$obj.usagePercent; Reset = Format-ResetInSec ([long]$obj.resetInSec) }
                } catch { $ogRows += @{ Label = $pair.Label; Pct = -1; Reset = "(parse failed)" } }
            }
        }
        if ($ogRows.Count -gt 0) {
            Write-Host "  opencode-go     [go]" -ForegroundColor White
            $ogRows | ForEach-Object {
                $str = if ($_.Pct -ge 0) { "{0}% left" -f (100 - $_.Pct) } else { "(parse failed)" }
                Write-UsageRow $_.Label $str $_.Reset
            }
        } else {
            Write-Host "  opencode-go     (no usage data scraped — cookie expired or page layout changed)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  opencode-go     error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    # Local LM Studio — reachability + which model is actually loaded. Catches the
    # case where the custom route points at a model LM Studio isn't serving.
    # NOTE: the local slot is routed by ccr-custom-router.js (CUSTOM_ROUTER_PATH),
    # not the default keyword router. Reachability check below confirms LM Studio is
    # actually serving the model the router points at.
    try {
        $lm = Invoke-RestMethod -Uri "http://127.0.0.1:1234/api/v0/models" -TimeoutSec 3 -ErrorAction Stop
        $loaded = $lm.data | Where-Object { $_.state -eq "loaded" } | Select-Object -First 1
        if ($loaded) {
            Write-Host "  local           LM Studio     loaded: $($loaded.id)"
        } else {
            Write-Host "  local           LM Studio     up, no model loaded" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  local           LM Studio     offline (127.0.0.1:1234)" -ForegroundColor DarkGray
    }
}

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
