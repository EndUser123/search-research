# cc-ccr.ps1 - Claude Code → CCR proxy launcher
#
# Usage:
#   . .\cc-ccr.ps1                    # start CCR, wire this shell to CCR
#   . .\cc-ccr.ps1 -Log               # start with CCR logs visible
#   . .\cc-ccr.ps1 -Stop              # kill CCR process
#   . .\cc-ccr.ps1 -Config            # launch TUI to configure model routes
#
# Routing source of truth: C:\Users\brsth\.claude-code-router\config.json
# (Providers, Router, fallback, CUSTOM_ROUTER_PATH). This script does NOT
# overwrite routing - edit config.json directly, or use the TUI: cc-ccr -Config.
# The only routing logic outside config.json is ccr-custom-router.js, which
# intercepts claude-local-ornith (CCR's built-in router can't match that name).
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
    # Stop CCR
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" | Select-Object -ExpandProperty CommandLine) -match 'claude-code-router' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    # Report local model state (independent of CCR — not killed by -Stop)
    $llAlive = Get-Process llama-server -ErrorAction SilentlyContinue
    if ($llAlive) {
        Write-Host "[cc-ccr] Stopped CCR. llama-server still running (PID $($llAlive.Id -join ','))." -ForegroundColor Yellow
    } else {
        Write-Host "[cc-ccr] Stopped CCR. llama-server was not running." -ForegroundColor Yellow
    }

    # Clear env vars this script sets (dot-sourced — mutations persist in caller's shell)
    foreach ($var in @('ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN',
                       'ANTHROPIC_CUSTOM_MODEL_OPTION','ANTHROPIC_CUSTOM_MODEL_OPTION_NAME',
                       'ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION')) {
        Remove-Item "env:$var" -ErrorAction SilentlyContinue
    }
    Write-Host "[cc-ccr] Cleared ANTHROPIC_* env vars (dot-sourced shell restored to pre-CCR state)." -ForegroundColor DarkGray
    return
}

# --- Guard: fail fast if ccr.cmd not found ---
if (-not (Test-Path $ccrCmd)) {
    Write-Warning "[cc-ccr] ccr not found at $ccrCmd - run: npm install -g @musistudio/claude-code-router"
    return
}

# --- Hint: TUI available for easy model configuration ---
Write-Host "[cc-ccr] Tip: Run 'cc-ccr -Config' to launch the TUI for interactive model route configuration" -ForegroundColor DarkGray

# --- Routing source of truth: config.json ---
# Providers, Router (slot + role keys), fallback chains, and CUSTOM_ROUTER_PATH all
# live in config.json. This script does NOT rewrite routing on launch - edit
# config.json directly (or via `cc-ccr -Config`). CCR hot-reloads config.json.
# Quota spreading comes from the fallback chains in config.json (verified: CCR
# retries the next chain entry on HTTP/quota error).
$ccrConfigPath = "$env:USERPROFILE\.claude-code-router\config.json"

# Phase toggles (independent, default OFF). Set before launch.
$phaseLocalApply  = ($env:CC_PHASE_LOCAL_APPLY  -eq "1")
$phaseCompactHook = ($env:CC_PHASE_COMPACT_HOOK -eq "1")

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
        Write-Warning "[CCR] Failed to start - check that ccr is installed"
        return $false
    }
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
        $cd = if     ($totHr -ge 72) { "{0,2}d {1,2}h" -f [int][Math]::Floor($totHr/24), ($totHr % 24) }
              elseif ($totHr -ge 1)  { "{0,2}h {1,2}m" -f $totHr, $remaining.Minutes }
              else                   { " 0h {0,2}m" -f [int][Math]::Floor($remaining.TotalMinutes) }
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

# --- Start CCR if not already running ---
$ccrFreshlyStarted = $false
$ccrRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $ccrRunning = $true
    Write-Host "[CCR] Already running at $ccrUrl" -ForegroundColor DarkGray
} catch {
    Write-Host "[CCR] Starting..." -ForegroundColor Cyan
    $ccrRunning = Start-CCRProcess
    if (-not $ccrRunning) { return }
    $ccrFreshlyStarted = $true
}

if (-not $ccrRunning) {
    return
}

# ══════════════════════════════════════════════════════════════════════════════
# Local Model — llama.cpp / ornith-1.0-9b (port 8010)
# ══════════════════════════════════════════════════════════════════════════════
#
# CCR routes coding tasks to the local model when:
#   - llama-server is healthy on port 8010
#   - Token count fits within effective context window
#   - routingMode = aggressive OR task = trivial-coding
#
# When offline, CCR falls back to MiniMax M3 for coding tasks.
#
# Process lifecycle:
#   cc-ccr.ps1 → pwsh.exe (Minimized) → run-ornith-server.ps1 → llama-server.exe
#   NOTE: Start-Process creates a separate process but Windows Terminal job
#   objects may still tear down the tree on WT tab close. The watchdog loop in
#   run-ornith-server.ps1 auto-restarts on crash; for true job-object breakaway
#   use CREATE_BREAKAWAY_FROM_JOB via Add-Type (future hardening).
#
# ────────────────────────────────────────────────────────────────────────────

$localModelId       = "ornith-1.0-9b"
$localModelEndpoint = "http://127.0.0.1:8010"
$localModelStatePath = "P:\.claude\state\local-model-state.json"

# ── Readiness probe (single source of truth: run-ornith-server.ps1 -Probe) ────
# The launcher owns the model's health definition (5-rung ladder). We query it
# rather than re-implementing probes, so the gate and the launcher always agree
# on what "ready" means. Kills the false "GGUF not loaded" warnings that came
# from gating on TCP port-open (llama-server binds the port before the GGUF
# finishes loading). State ∈ DEAD|STUCK|BROKEN|LOADING|LOADED|READY|HUNG.
$launcherScript = "P:\packages\installers\run-ornith-server.ps1"

function Invoke-LocalModelProbe {
    param([switch]$IncludeInference)
    try {
        $pa = @("-NoProfile", "-NoLogo", "-NonInteractive", "-File", $launcherScript, "-Probe")
        if ($IncludeInference) { $pa += "-IncludeInference" }
        $out = & pwsh.exe @pa 2>$null
        if ($out) { return ($out | ConvertFrom-Json) }
    } catch {}
    return $null
}

function Wait-LocalModelReady {
    # Poll rungs 1-4 (cheap, no inference) until LOADED, then ONE -IncludeInference
    # probe to confirm READY. Stops early on a failure state (DEAD/STUCK/BROKEN/HUNG).
    param([int]$TimeoutSec = 60)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $s = $null
    while ((Get-Date) -lt $deadline) {
        $s = Invoke-LocalModelProbe
        if (-not $s) { Start-Sleep -Seconds 2; continue }
        if ($s.state -eq "LOADED" -or $s.state -eq "READY") {
            return (Invoke-LocalModelProbe -IncludeInference)
        }
        if ($s.state -in @("DEAD", "STUCK", "BROKEN", "HUNG")) { return $s }
        Start-Sleep -Seconds 2
    }
    return $s
}

$lm = Invoke-LocalModelProbe -IncludeInference
$localModelHealth = $false

if (-not $lm -or $lm.state -eq "DEAD") {
    Write-Host "[CCR] local model offline (no llama-server) - starting..." -ForegroundColor Cyan
    if (Test-Path $launcherScript) {
        # P/Invoke CreateProcess with CREATE_BREAKAWAY_FROM_JOB so the launcher
        # (and its llama-server grandchild + watchdog) survive the parent exiting.
        if (-not ([System.Management.Automation.PSTypeName]'CCR_BREAKAWAY').Type) {
            Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CCR_BREAKAWAY {
    const uint CREATE_BREAKAWAY_FROM_JOB = 0x01000000;
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO { public int cb; public IntPtr lpReserved; public IntPtr lpDesktop; public IntPtr lpTitle; public int dwX; public int dwY; public int dwXSize; public int dwYSize; public int dwXCountChars; public int dwYCountChars; public int dwFillAttribute; public int dwFlags; public short wShowWindow; public short cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput; public IntPtr hStdOutput; public IntPtr hStdError; }
    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION { public IntPtr hProcess; public IntPtr hThread; public uint dwProcessId; public uint dwThreadId; }
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);
    public static bool Launch(string exe, string args) {
        var si = new STARTUPINFO { cb = Marshal.SizeOf(typeof(STARTUPINFO)) };
        var pi = new PROCESS_INFORMATION();
        return CreateProcess(exe, args, IntPtr.Zero, IntPtr.Zero, false, CREATE_BREAKAWAY_FROM_JOB, IntPtr.Zero, null, ref si, out pi);
    }
}
"@
        }
        $pwshPath = (Get-Command pwsh.exe -ErrorAction SilentlyContinue).Source
        if (-not $pwshPath) { $pwshPath = "pwsh.exe" }
        $launchArgs = "-NoProfile -NoLogo -NonInteractive -File `"$launcherScript`""
        $launched = [CCR_BREAKAWAY]::Launch($pwshPath, $launchArgs)
        if (-not $launched) {
            Write-Host "  CREATE_BREAKAWAY_FROM_JOB failed - falling back to Start-Process" -ForegroundColor Yellow
            Start-Process -FilePath "pwsh.exe" `
                -ArgumentList @("-NoProfile", "-NoLogo", "-NonInteractive", "-File", $launcherScript) `
                -WindowStyle Minimized
        }
        $lm = Wait-LocalModelReady -TimeoutSec 60
    } else {
        Write-Host "[CCR] run-ornith-server.ps1 not found at $launcherScript" -ForegroundColor Yellow
    }
} elseif ($lm.state -eq "LOADING") {
    Write-Host "[CCR] local model loading - waiting..." -ForegroundColor Cyan
    $lm = Wait-LocalModelReady -TimeoutSec 60
} elseif ($lm.state -in @("STUCK", "BROKEN", "HUNG")) {
    Write-Host "[CCR] local model $($lm.state) ($($lm.detail)) - watchdog recovers; or relaunch the launcher" -ForegroundColor Yellow
} elseif ($lm.state -eq "READY" -or $lm.state -eq "LOADED") {
    $localModelHealth = $true
}

# Report
if ($lm -and ($lm.state -eq "READY" -or $lm.state -eq "LOADED")) {
    $ctx = ""
    if (Test-Path $localModelStatePath) {
        try {
            $lms = Get-Content $localModelStatePath -Raw | ConvertFrom-Json
            if ($lms.active_model) {
                $active = $lms.models | Where-Object { $_.id -eq $lms.active_model } | Select-Object -First 1
                if ($active -and $active.maxContextTokens) { $ctx = " | ctx: $($active.maxContextTokens)" }
            }
        } catch {}
    }
    $tag = if ($lm.state -eq "READY") { "ready" } else { "loaded (inference unverified)" }
    Write-Host "[CCR] local: $($lm.model) | endpoint: $localModelEndpoint$ctx | $tag" -ForegroundColor Green
} else {
    Write-Host "[CCR] local model not ready (aggressive mode fallback to M3 for coding)" -ForegroundColor DarkGray
}
$script:localModelState = $lm

# --- Log routing mode ---
$routingMode = "unknown"
try {
    $routingConfig = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json
    $routingMode = $routingConfig.routingMode
    Write-Host "[CCR] routingMode=$routingMode" -ForegroundColor Cyan
} catch {}

# --- Wire this shell's Claude Code ---
# Claude → CCR → external models
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

# 4th model slot - local Ornith via llama.cpp (run-ornith-server.ps1, port 8010)
$env:ANTHROPIC_CUSTOM_MODEL_OPTION             = "claude-local-ornith"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME        = "Ornith 1.0 9B (Local)"
$env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "llama.cpp · ornith-1.0-9b@q4_k_m"

# --- Post-start smoke probe (FRESH START ONLY) ---
# ccr-custom-router.js is require()-cached at CCR startup and is NOT hot-reloaded
# with config.json (config.json IS hot-reloaded). If the custom router was edited
# and CCR restarted, a stale module can route claude-local-ornith to a dead provider
# - surfacing only when a user selects that model. Probe the local slot once after a
# fresh start so staleness is caught now. Local slot only: it is the one routable
# entity that depends on the require()-cached file AND has no fallback chain. Free
# (hits local llama.cpp, no provider quota) and ~1s. External routes (opus/sonnet/
# haiku) have fallback chains and are audited via `cc-ccr -Test`.
if ($ccrFreshlyStarted) {
    try {
        $probeHeaders = @{ "Authorization" = "Bearer $env:ANTHROPIC_AUTH_TOKEN"; "anthropic-version" = "2023-06-01"; "Content-Type" = "application/json" }
        $probeBody = @{ model = "claude-local-ornith"; max_tokens = 8; messages = @(@{ role = "user"; content = "hi" }) } | ConvertTo-Json -Depth 5 -Compress
        $probe = Invoke-RestMethod -Uri "$ccrUrl/v1/messages" -Method Post -Headers $probeHeaders -Body $probeBody -TimeoutSec 20 -ErrorAction Stop
        if ($probe.error) { throw ($probe.error | ConvertTo-Json -Compress -Depth 5) }
        Write-Host "[CCR] Post-start probe OK: claude-local-ornith routed (custom router live, not stale)." -ForegroundColor Green
    } catch {
        $probeMsg = $_.ErrorDetails.Message
        if (-not $probeMsg) { $probeMsg = $_.Exception.Message }
        Write-Warning "[CCR] Post-start probe FAILED for claude-local-ornith: $probeMsg"
        Write-Warning "[CCR]   Likely: stale ccr-custom-router.js (did you edit it? the require() cache only clears on restart) or llama.cpp (port 8010) is down."
    }
}

# --- Get PID for display ---

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
function Format-Route {
    param([string]$s)
    if (-not $s) { return "(none)" }
    $parts = $s -split ','
    $pairs = for ($i = 0; $i -lt $parts.Length; $i += 2) {
        if ($i + 1 -lt $parts.Length) { "$($parts[$i])/$($parts[$i+1])" }
        else { $parts[$i] }
    }
    $pairs -join " → "
}

try {
    $ccrCfg = Get-Content $ccrConfigPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $fb = $ccrCfg.fallback

    # Build a list of all router keys (slots + roles)
    $routerProps = $ccrCfg.Router.PSObject.Properties
    $routes = @()

    foreach ($prop in $routerProps) {
        $name  = $prop.Name
        $value = $prop.Value

        # Derive a label and which fallback chain (if any) to show
        $label = $name
        $chain = $null

        switch ($name) {
            "claude-opus-4-8"           { $label = "opus";        $chain = if ($fb) { $fb.think }       else { $null } }
            "claude-sonnet-5"           { $label = "sonnet";      $chain = if ($fb) { $fb.default }     else { $null } }
            "claude-sonnet-4-6"         { $label = "sonnet-5(legacy)"; $chain = $null }  # backward-compat alias; routes via claude-sonnet-5
            "claude-haiku-4-5"          { $label = "haiku";       $chain = if ($fb) { $fb.background }  else { $null } }
            "claude-haiku-4-5-20251001" { $label = "haiku(2025)"; $chain = if ($fb) { $fb.background }  else { $null } }
            "claude-local-ornith"       { $label = "custom";      $chain = $null }
            "think"                     { $label = "think";       $chain = if ($fb) { $fb.think }       else { $null } }
            "default"                   { $label = "default";     $chain = if ($fb) { $fb.default }     else { $null } }
            "background"               { $label = "background";  $chain = if ($fb) { $fb.background }  else { $null } }
            "longContext"              { $label = "longContext"; $chain = if ($fb) { $fb.longContext } else { $null } }
        }

        $routes += @{
            Label  = $label
            Name   = $name
            Primary = $value
            Chain   = $chain
        }
    }

    # Sort by label then name so it's stable and readable
    $routes = $routes | Sort-Object Label, Name
    $labelWidth = ($routes | ForEach-Object { $_.Label.Length } | Measure-Object -Maximum).Maximum

    foreach ($r in $routes) {
        if (-not $r.Primary -or $r.Primary -notmatch ',') { continue }
        $paddedLabel = $r.Label.PadRight($labelWidth)
        $indent = ' ' * ($labelWidth + 2)

        Write-Host ("  {0}: {1}" -f $paddedLabel, (Format-Route $r.Primary))

        if ($r.Chain -and $r.Chain.Count -gt 0) {
            $r.Chain | ForEach-Object {
                Write-Host ("{0}└─ {1}" -f $indent, (Format-Route $_)) -ForegroundColor DarkGray
            }
        } elseif ($r.Label -notin @('custom')) {
            Write-Host ("{0}└─ (no fallback configured)" -f $indent) -ForegroundColor DarkGray
        }
    }
}
catch {
    Write-Host "  (could not read routes from config.json - check $ccrConfigPath)" -ForegroundColor Yellow
}
Write-Host ""
# --- Phase status banner ---
Write-Host ""
Write-Host "Phases:"
if ($phaseLocalApply)  { Write-Host "  local-apply:  requested (verify model loaded in llama.cpp)" -ForegroundColor Yellow }
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
        #   TOKENS_LIMIT = "Token usage (5 Hour)" - the rolling 5h GLM-model token window (percentage only)
        #   TIME_LIMIT   = "MCP usage (1 Month)"  - monthly tool/MCP budget (search-prime/web-reader/zread; has currentValue/usage)
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
            Write-Host "  opencode-go     (no usage data scraped - cookie expired or page layout changed)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  opencode-go     error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    # Local llama.cpp — reuse the readiness probe from above (single source of
    # truth). Avoids a second independent /v1/models probe that can disagree with
    # the triage line (the cause of stale "offline" in this block).
    if ($script:localModelState -and ($script:localModelState.state -eq "READY" -or $script:localModelState.state -eq "LOADED")) {
        Write-Host "  local           llama.cpp      up: $($script:localModelState.model)" -ForegroundColor Green
    } elseif ($script:localModelState -and $script:localModelState.state -ne "DEAD") {
        Write-Host "  local           llama.cpp      $($script:localModelState.state) - $($script:localModelState.detail)" -ForegroundColor Yellow
    } else {
        Write-Host "  local           llama.cpp      offline (127.0.0.1:8010)" -ForegroundColor DarkGray
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
        model = "claude-sonnet-5"
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
    } catch {
        # Fallback: try x-api-key (CCR also accepts this; some plugin code paths use it).
        try {
            $xApiHeaders = @{ "x-api-key" = $env:ANTHROPIC_API_KEY; "anthropic-version" = "2023-06-01"; "Content-Type" = "application/json" }
            $resp = Invoke-RestMethod -Uri "$ccrUrl/v1/messages" -Method Post `
                -Headers $xApiHeaders `
                -Body $body -TimeoutSec 30 -ErrorAction Stop
            $text = ($resp.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text
            Write-Host "  PASS - CCR routed via x-api-key fallback. Model replied: '$text'" -ForegroundColor Green
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
            $curlBody = '{"model":"claude-sonnet-5","max_tokens":16,"messages":[{"role":"user","content":"Reply OK"}]}'
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
