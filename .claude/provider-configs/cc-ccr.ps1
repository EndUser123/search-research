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
#   Claude Code → CCR (configured PORT) → external models
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

$ccrConfigPath = "$env:USERPROFILE\.claude-code-router\config.json"
$ccrPort = 3456  # explicit fallback when config.json is absent or invalid
if (Test-Path -LiteralPath $ccrConfigPath) {
    try {
        $configuredPort = (Get-Content -LiteralPath $ccrConfigPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop).PORT
        $parsedPort = 0
        if ([int]::TryParse([string]$configuredPort, [ref]$parsedPort) -and $parsedPort -ge 1 -and $parsedPort -le 65535) {
            $ccrPort = $parsedPort
        } else {
            Write-Warning "[cc-ccr] Invalid PORT in $ccrConfigPath; using fallback port $ccrPort"
        }
    } catch {
        Write-Warning "[cc-ccr] Could not read PORT from $ccrConfigPath; using fallback port $ccrPort"
    }
} else {
    Write-Warning "[cc-ccr] CCR config not found at $ccrConfigPath; using fallback port $ccrPort"
}
$ccrUrl = "http://127.0.0.1:$ccrPort"
$ccrCmd = "$env:APPDATA\npm\ccr.cmd"

# --- Load secrets from .env into hashtable for CCR process ---
$envPath = "P:\.env"
$ccrEnvVars = @{}

$subscriptionUsageHelper = Join-Path $PSScriptRoot 'cc-ccr-subscription-usage.ps1'
if (Test-Path -LiteralPath $subscriptionUsageHelper) {
    . $subscriptionUsageHelper
}

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

# --- Load the active Grok subscription session for CCR's Grok provider ---
# Grok CLI stores the OAuth/session bearer in ~/.grok/auth.json. This is kept
# process-local and inherited by a newly started CCR; it is never copied into
# P:\.env or written to config.json. The session token may be refreshed by the
# Grok CLI, so rerun cc-ccr after a refresh or expiry.
$grokAuthPath = "$env:USERPROFILE\.grok\auth.json"
if (Test-Path -LiteralPath $grokAuthPath) {
    try {
        $grokAuth = Get-Content -LiteralPath $grokAuthPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        $grokSessionToken = @($grokAuth.psobject.Properties.Value | ForEach-Object { $_.key } | Where-Object { $_ }) | Select-Object -First 1
        if ($grokSessionToken) {
            [System.Environment]::SetEnvironmentVariable('GROK_SESSION_TOKEN', [string]$grokSessionToken, 'Process')
            $ccrEnvVars['GROK_SESSION_TOKEN'] = [string]$grokSessionToken
        } else {
            Write-Warning "[cc-ccr] Grok auth file contains no session token; grok route will be unavailable"
        }
    } catch {
        Write-Warning "[cc-ccr] Could not read Grok session from $grokAuthPath; grok route will be unavailable"
    }
} else {
    Write-Warning "[cc-ccr] Grok auth file not found at $grokAuthPath; grok route will be unavailable"
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
    # Stop only the dedicated CCR listeners. The previous implementation
    # enumerated every node.exe process (235 on this workstation) and ran a
    # separate WMI query for each one, twice. That made -Stop appear frozen
    # for minutes and could inspect unrelated Node processes. Port ownership
    # is the precise identity of the two services this launcher owns.
    foreach ($port in @($ccrPort, 3458)) {
        $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
        foreach ($listener in $listeners) {
            if ($listener.OwningProcess) {
                Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }

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

# --- Routing source of truth: config.json ---
# Providers, Router (slot + role keys), fallback chains, and CUSTOM_ROUTER_PATH all
# live in config.json. This script does NOT rewrite routing on launch - edit
# config.json directly (or via `cc-ccr -Config`). CCR hot-reloads config.json.
# Quota spreading comes from the fallback chains in config.json (verified: CCR
# retries the next chain entry on HTTP/quota error).
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
    $w = $Window.PadRight(32)
    $r = $Remaining.PadRight(22)
    $tail = if ($Reset) { "resets $Reset" } else { "" }
    $pct = if ($Remaining -match '(\d+)%\s*(left|used)') {
        $p = [int]$Matches[1]
        if ($Matches[2] -eq 'used') { 100 - $p } else { $p }
    } else { $null }
    if ($null -ne $pct) { $color = if ($pct -gt 50) { 'Green' } elseif ($pct -ge 20) { 'Yellow' } else { 'Red' } }
    Write-Host ("                  {0}" -f $w) -NoNewline
    if ($null -ne $pct) { Write-GaugeBar $pct }
    if ($color) { Write-Host $r -NoNewline -ForegroundColor $color } else { Write-Host $r -NoNewline }
    Write-Host $tail
}

function Write-UsageStatus {
    param([string]$Status, [string]$Window = 'status')
    Write-Host ("                  {0}" -f ('{0,-32}' -f $Window)) -NoNewline
    Write-Host $Status -ForegroundColor Yellow
}

function Write-UsageAliases {
    param([object[]]$Aliases)
    foreach ($alias in @($Aliases)) {
        Write-Host ("                  └─ {0}" -f $alias) -ForegroundColor DarkGray
    }
}

function Format-UsageAge {
    param([DateTimeOffset]$UpdatedAt)
    $age = [DateTimeOffset]::UtcNow - $UpdatedAt.ToUniversalTime()
    if ($age.TotalSeconds -lt 60) { return 'just now' }
    if ($age.TotalMinutes -lt 60) { return "{0}m ago" -f [int][Math]::Floor($age.TotalMinutes) }
    return "{0}h ago" -f [int][Math]::Floor($age.TotalHours)
}

# --- Helper: draw a thin separator between provider sections ---
function Write-SectionSep { Write-Host "  ───────────────────────────────────────────────────" -ForegroundColor DarkGray }
function Write-DomainHeader {
    param([Parameter(Mandatory)][string]$Title)
    Write-Host ""
    Write-Host $Title -ForegroundColor Cyan
}
function Format-EnvState {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "<missing>" }
    return "<set>"
}
function Get-RouteDomain {
    param([Parameter(Mandatory)][string]$Name)
    if ($Name -eq 'claude-local-ornith') { return 'local models' }
    if ($Name -like 'claude-*') { return 'claude models' }
    if ($Name -in @('think', 'default', 'background', 'longContext')) { return 'roles' }
    return 'provider routes'
}
function Write-Tree {
    param(
        [Parameter(Mandatory)][object[]]$Nodes,
        [string]$Prefix = ""
    )
    for ($i = 0; $i -lt $Nodes.Count; $i++) {
        $node = $Nodes[$i]
        $last = $i -eq ($Nodes.Count - 1)
        $connector = if ($last) { '└─ ' } else { '├─ ' }
        $label = [string]$node.Label
        $color = if ($node.Color) {
            [string]$node.Color
        } elseif ($label -match '(?i)inference unverified|not ready|degraded|unavailable') {
            'Yellow'
        } elseif ($label -match '(?i)status:\s*(ready|healthy|already running|started|loaded)\b') {
            'Green'
        } else {
            'DarkGray'
        }
        Write-Host "$Prefix$connector" -NoNewline -ForegroundColor DarkGray
        Write-Host $label -ForegroundColor $color
        $children = @($node.Children)
        if ($children.Count -gt 0) {
            $childPrefix = if ($last) { "$Prefix   " } else { "$Prefix│  " }
            Write-Tree -Nodes $children -Prefix $childPrefix
        }
    }
}
function Get-LocalVramSummary {
    $nvidiaSmi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if (-not $nvidiaSmi) { return 'unavailable' }
    try {
        $row = & $nvidiaSmi.Source '--query-gpu=memory.used,memory.total' '--format=csv,noheader,nounits' 2>$null | Select-Object -First 1
        $parts = @($row -split ',') | ForEach-Object { $_.Trim() }
        if ($parts.Count -ge 2 -and $parts[0] -match '^\d+$' -and $parts[1] -match '^\d+$') {
            return "$($parts[0]) MB / $($parts[1]) MB"
        }
    } catch {}
    return 'unavailable'
}

# --- Lightweight status probes used by -Usage (does not start infrastructure) ---
function Get-UsageEndpointStatus {
    param([Parameter(Mandatory)][string]$Uri, [string]$HealthyLabel = 'healthy')
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return "${HealthyLabel} (HTTP $($response.StatusCode))"
    } catch {
        return 'offline'
    }
}

function Get-UsageLocalModelStatus {
    $statePath = 'P:\.claude\state\local-model-state.json'
    try {
        if (Test-Path -LiteralPath $statePath) {
            $state = Get-Content -LiteralPath $statePath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
            if ($state.state -and $state.state -notin @('DEAD', '')) {
                return "$($state.state) - $($state.detail)"
            }
        }
    } catch {}
    return Get-UsageEndpointStatus -Uri 'http://127.0.0.1:8010/health' -HealthyLabel 'healthy'
}

# Kept outside the normal-startup branch so -Usage can render the same route
# tree even though it intentionally skips service startup and wiring.
function Format-Route {
    param([string]$s)
    if (-not $s) { return '(none)' }
    $parts = $s -split ','
    $pairs = for ($i = 0; $i -lt $parts.Length; $i += 2) {
        if ($i + 1 -lt $parts.Length) { "$($parts[$i])/$($parts[$i + 1])" } else { $parts[$i] }
    }
    $pairs -join ' → '
}

function Get-UsageListenerPid {
    param([Parameter(Mandatory)][int]$Port)
    try {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener -and $listener.OwningProcess) { return [string]$listener.OwningProcess }
    } catch {}
    return 'N/A'
}

function Get-UsageLocalTree {
    $statePath = 'P:\.claude\state\local-model-state.json'
    $state = $null
    try {
        if (Test-Path -LiteralPath $statePath) {
            $state = Get-Content -LiteralPath $statePath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        }
    } catch {}

    $model = if ($state -and $state.model) {
        [string]$state.model
    } elseif ($state -and $state.active_model) {
        [string]$state.active_model
    } else {
        'unavailable'
    }
    $status = if ($state -and $state.state -in @('READY', 'LOADED')) {
        if ($state.state -eq 'READY') { 'ready' } else { 'loaded (inference unverified)' }
    } elseif ($state -and $state.state) {
        "not ready ($($state.state))"
    } else {
        (Get-UsageLocalModelStatus)
    }
    $ctx = 'unavailable'
    try {
        if ($state.active_model) {
            $active = @($state.models) | Where-Object { $_.id -eq $state.active_model } | Select-Object -First 1
            if ($active -and $active.maxContextTokens) { $ctx = [string]$active.maxContextTokens }
        }
    } catch {}
    $pids = if ($state -and $state.pids) {
        (@($state.pids) -join ', ')
    } else {
        $llama = @(Get-Process llama-server -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
        if ($llama.Count -gt 0) { $llama -join ', ' } else { 'N/A' }
    }
    @(
        [pscustomobject]@{ Label = 'local'; Color = 'White'; Children = @(
            [pscustomobject]@{ Label = "status: $status"; Children = @() }
            [pscustomobject]@{ Label = "model: $model"; Children = @() }
            [pscustomobject]@{ Label = 'endpoint: http://127.0.0.1:8010'; Children = @() }
            [pscustomobject]@{ Label = "ctx: $ctx"; Children = @() }
            [pscustomobject]@{ Label = "vram: $(Get-LocalVramSummary)"; Children = @() }
            [pscustomobject]@{ Label = "pid: $pids"; Children = @() }
        ) }
    )
}

function Get-UsageInfrastructureTree {
    $ccrStatus = Get-UsageEndpointStatus -Uri "$ccrUrl/health"
    $proxyStatus = Get-UsageEndpointStatus -Uri 'http://127.0.0.1:3458/health'
    $localStatus = Get-UsageLocalModelStatus
    $ccrPid = Get-UsageListenerPid -Port $ccrPort
    $proxyPid = Get-UsageListenerPid -Port 3458
    $ready = $ccrStatus -like 'healthy*' -and $proxyStatus -like 'healthy*' -and $localStatus -notlike 'offline*'
    $status = if ($ready) { 'ready' } else { 'degraded' }
    $local = Get-UsageLocalTree
    @(
        [pscustomobject]@{ Label = 'Infrastructure'; Color = 'Cyan'; Children = @(
            [pscustomobject]@{ Label = "status: $status"; Children = @() }
            [pscustomobject]@{ Label = 'proxy chain'; Color = 'White'; Children = @(
                [pscustomobject]@{ Label = 'CCR'; Color = 'White'; Children = @(
                    [pscustomobject]@{ Label = "status: $($ccrStatus -replace ' \(HTTP \d+\)$', '')"; Children = @() }
                    [pscustomobject]@{ Label = "endpoint: $ccrUrl"; Children = @() }
                    [pscustomobject]@{ Label = "pid: $ccrPid"; Children = @() }
                ) }
                [pscustomobject]@{ Label = 'admission-proxy'; Color = 'White'; Children = @(
                    [pscustomobject]@{ Label = "status: $($proxyStatus -replace ' \(HTTP \d+\)$', '')"; Children = @() }
                    [pscustomobject]@{ Label = 'endpoint: http://127.0.0.1:3458'; Children = @() }
                    [pscustomobject]@{ Label = "pid: $proxyPid"; Children = @() }
                ) }
            ) }
            $local[0]
        ) }
    )
}

function Get-UsageRouteTree {
    try {
        $cfg = Get-Content $ccrConfigPath -Raw -ErrorAction Stop | ConvertFrom-Json
        $fallback = $cfg.fallback
        $nodes = @($cfg.Router.PSObject.Properties | Where-Object Name -ne 'longContextThreshold' | ForEach-Object {
            $name = $_.Name
            $chain = switch ($name) {
                'claude-opus-4-8' { if ($fallback) { $fallback.think } }
                'claude-sonnet-5' { if ($fallback) { $fallback.default } }
                'claude-haiku-4-5' { if ($fallback) { $fallback.background } }
                'claude-haiku-4-5-20251001' { if ($fallback) { $fallback.background } }
                'think' { if ($fallback) { $fallback.think } }
                'default' { if ($fallback) { $fallback.default } }
                'background' { if ($fallback) { $fallback.background } }
                'longContext' { if ($fallback) { $fallback.longContext } }
            }
            $label = switch ($name) {
                'claude-opus-4-8' { 'opus' }
                'claude-sonnet-5' { 'sonnet' }
                'claude-sonnet-4-6' { 'sonnet-5(legacy)' }
                'claude-haiku-4-5' { 'haiku' }
                'claude-haiku-4-5-20251001' { 'haiku(2025)' }
                'claude-local-ornith' { 'custom' }
                default { $name }
            }
            $children = @([pscustomobject]@{ Label = "primary: $(Format-Route ([string]$_.Value))"; Children = @() })
            if ($chain -and @($chain).Count -gt 0) {
                foreach ($entry in @($chain)) { $children += [pscustomobject]@{ Label = "fallback: $(Format-Route ([string]$entry))"; Children = @() } }
            } elseif ($label -ne 'custom') {
                $children += [pscustomobject]@{ Label = 'fallback: none configured'; Children = @() }
            }
            [pscustomobject]@{ Label = $label; Color = 'White'; Domain = (Get-RouteDomain -Name $name); Children = $children }
        })
        $groups = foreach ($domain in @('claude models', 'roles', 'provider routes', 'local models')) {
            [pscustomobject]@{ Label = $domain; Color = 'White'; Children = @($nodes | Where-Object Domain -eq $domain | Sort-Object Label) }
        }
        @(
            [pscustomobject]@{ Label = 'Routing'; Color = 'Cyan'; Children = @(
                [pscustomobject]@{ Label = "mode: $(if ($cfg.routingMode) { $cfg.routingMode } else { 'aggressive (default)' })"; Children = @() }
                [pscustomobject]@{ Label = 'routes'; Color = 'White'; Children = $groups }
            ) }
        )
    } catch {
        @([pscustomobject]@{ Label = 'Routing'; Color = 'Cyan'; Children = @([pscustomobject]@{ Label = "status: unavailable ($ccrConfigPath)"; Children = @() }) })
    }
}

# --- Start CCR if not already running ---
$ccrFreshlyStarted = $false
$ccrRunning = $false
try {
    $r = Invoke-WebRequest -Uri "$ccrUrl/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    $ccrRunning = $true
    $ccrStartupSummary = "Already running"
} catch {
    $ccrStartupSummary = "starting"
    $ccrRunning = Start-CCRProcess
    if (-not $ccrRunning) { return }
    $ccrFreshlyStarted = $true
    $ccrStartupSummary = "started"
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
# When offline/busy/over-context, CCR falls back to opencode-go (deepseek-v4-flash)
# for local-first coding failures — NOT M3. Ordinary non-local M3/GLM routing is unchanged.
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
        # Do not invoke the probe with the call operator.  When cc-ccr is
        # launched from a host without an attached console, that creates a
        # transient conhost window for every readiness poll.  Use a hidden,
        # redirected child process instead; the probe is machine-facing and
        # must never create operator UI.
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = (Get-Command pwsh.exe -ErrorAction Stop).Source
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        foreach ($arg in @("-NoProfile", "-NoLogo", "-NonInteractive", "-File", $launcherScript, "-Probe")) {
            [void]$psi.ArgumentList.Add($arg)
        }
        if ($IncludeInference) { [void]$psi.ArgumentList.Add("-IncludeInference") }

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $psi
        if (-not $process.Start()) { return $null }
        $out = $process.StandardOutput.ReadToEnd()
        [void]$process.StandardError.ReadToEnd()
        $process.WaitForExit()
        if ($out) { return ($out | ConvertFrom-Json) }
    } catch {}
    return $null
}

function Wait-LocalModelReady {
    # Poll rungs 1-4 (cheap, no inference) until LOADED/READY. DEAD, null, and
    # LOADING are transient while a newly spawned supervisor/model is starting;
    # only definitive watchdog states terminate the wait early.
    param(
        [int]$TimeoutSec = 60,
        [int]$StartupGraceSec = 15,
        [int]$PollMilliseconds = 2000,
        [scriptblock]$ProbeScript,
        [scriptblock]$SleepScript,
        [scriptblock]$NowScript
    )
    if (-not $ProbeScript) { $ProbeScript = { Invoke-LocalModelProbe } }
    if (-not $SleepScript) { $SleepScript = { param($Milliseconds) Start-Sleep -Milliseconds $Milliseconds } }
    if (-not $NowScript) { $NowScript = { Get-Date } }

    $startedAt = & $NowScript
    $deadline = $startedAt.AddSeconds($TimeoutSec)
    $startupGraceDeadline = $startedAt.AddSeconds($StartupGraceSec)
    $s = $null
    while ((& $NowScript) -lt $deadline) {
        $s = & $ProbeScript
        if (-not $s) {
            & $SleepScript $PollMilliseconds
            continue
        }
        if ($s.state -eq "LOADED" -or $s.state -eq "READY") {
            # LOADED (GGUF in memory, port bound) is sufficient for routing readiness.
            # Do NOT re-probe with -IncludeInference here: under --parallel 1 the
            # inference call queues behind real traffic, times out, returns HUNG,
            # and prints "local model not ready" while the launcher finishes 4s
            # later (the "terrible" stale-usage race). Same collision the watchdog
            # deliberately avoids. Drop the double-probe; LOADED == ready.
            return $s
        }
        # During startup, llama-server can have a process and partial HTTP
        # listener while /health or /v1/models is not ready yet. Treat STUCK
        # and BROKEN as transient inside the grace window; otherwise a normal
        # model load is reported as an unhealthy server and the caller prints
        # a stale degraded tree. HUNG remains terminal because it is an
        # inference failure, not a load transition.
        if ($s.state -in @("STUCK", "BROKEN")) {
            if ((& $NowScript) -lt $startupGraceDeadline) {
                & $SleepScript $PollMilliseconds
                continue
            }
            return $s
        }
        if ($s.state -eq "HUNG") { return $s }
        if ($s.state -eq "DEAD" -and (& $NowScript) -lt $startupGraceDeadline) {
            # A supervisor can report DEAD before llama-server binds its port.
            & $SleepScript $PollMilliseconds
            continue
        }
        # DEAD after the grace period, null results, and LOADING remain
        # non-terminal: keep the bounded poll alive until the hard timeout.
        & $SleepScript $PollMilliseconds
    }
    return $s
}

function Resolve-RoutingMode {
    param([AllowNull()][object]$RoutingMode)
    $value = if ($null -eq $RoutingMode) { "" } else { ([string]$RoutingMode).Trim() }
    if ([string]::IsNullOrWhiteSpace($value)) {
        return [pscustomobject]@{ Value = "aggressive"; IsDefault = $true }
    }
    return [pscustomobject]@{ Value = $value; IsDefault = $false }
}

function Format-RoutingModeDisplay {
    param([Parameter(Mandatory)]$RoutingModeInfo)
    if ($RoutingModeInfo.IsDefault) {
        return "routingMode=$($RoutingModeInfo.Value) (default)"
    }
    return "routingMode=$($RoutingModeInfo.Value)"
}

function Get-AdmissionProxyListener {
    param(
        [int]$Port = 3458,
        [scriptblock]$ListenerLookup
    )
    if ($ListenerLookup) { return (& $ListenerLookup $Port | Select-Object -First 1) }
    return (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Get-AdmissionProxyOwner {
    param(
        $Listener,
        [scriptblock]$ProcessLookup,
        [string]$ExpectedScript = "ccr-admission-proxy.js"
    )
    if (-not $Listener -or -not $Listener.OwningProcess) { return $null }
    $listenerPid = [int]$Listener.OwningProcess
    if ($ProcessLookup) {
        $process = & $ProcessLookup $listenerPid | Select-Object -First 1
    } else {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $listenerPid" -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    $commandLine = if ($process) { [string]$process.CommandLine } else { "" }
    $expectedName = [IO.Path]::GetFileName($ExpectedScript)
    return [pscustomobject]@{
        ListenerPid = $listenerPid
        CommandLine = $commandLine
        IsExpected = (-not [string]::IsNullOrWhiteSpace($commandLine) -and $commandLine -match [regex]::Escape($expectedName))
    }
}

function Test-AdmissionProxyHealth {
    param(
        [int]$Port = 3458,
        [scriptblock]$HealthCheck
    )
    if ($HealthCheck) { return [bool](& $HealthCheck $Port) }
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Start-AdmissionProxyProcess {
    param(
        [Parameter(Mandatory)][string]$ProxyScript,
        [Parameter(Mandatory)][string]$ProxyLog,
        [Parameter(Mandatory)][int]$CcrPort
    )
    # Start node directly (not via a pwsh wrapper pipe). The previous version
    # used `pwsh -Command "node ... 2>&1 | Set-Content ..."` which buffers the
    # entire pipeline and only writes the log when the process exits — so the
    # proxy log was always 0 bytes while the proxy was alive. Starting node
    # directly with -RedirectStandardError gives live stderr logging.
    $env:CCR_PORT = $CcrPort
    $errLog = "$ProxyLog.err"
    return Start-Process -FilePath "node" `
        -ArgumentList @($ProxyScript) `
        -WindowStyle Hidden -PassThru `
        -RedirectStandardError $errLog
}

function Get-SecretFingerprint {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrEmpty($Value)) { return 'missing' }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $digest = $sha.ComputeHash($bytes)
        $hex = [BitConverter]::ToString($digest).Replace('-', '').ToLowerInvariant()
        return "$($Value.Length) chars, sha256:$($hex.Substring(0, 12))"
    } finally {
        $sha.Dispose()
    }
}

function Ensure-AdmissionProxy {
    param(
        [int]$Port = 3458,
        [int]$CcrPort = 3456,
        [string]$ProxyScript,
        [string]$ProxyLog,
        [int]$MaxAttempts = 3,
        [scriptblock]$ListenerLookup,
        [scriptblock]$ProcessLookup,
        [scriptblock]$HealthCheck,
        [scriptblock]$SpawnScript,
        [scriptblock]$SleepScript
    )
    if (-not $SpawnScript) { $SpawnScript = { Start-AdmissionProxyProcess -ProxyScript $ProxyScript -ProxyLog $ProxyLog -CcrPort $CcrPort } }
    if (-not $SleepScript) { $SleepScript = { param($Milliseconds) Start-Sleep -Milliseconds $Milliseconds } }

    $listener = Get-AdmissionProxyListener -Port $Port -ListenerLookup $ListenerLookup
    if ($listener) {
        $owner = Get-AdmissionProxyOwner -Listener $listener -ProcessLookup $ProcessLookup -ExpectedScript $ProxyScript
        if ($owner -and $owner.IsExpected -and (Test-AdmissionProxyHealth -Port $Port -HealthCheck $HealthCheck)) {
            # Code-version check: if the proxy script has been modified since
            # the running proxy started, kill and restart so the new code loads.
            # Node caches the module at startup; without this, code changes to
            # ccr-admission-proxy.js are invisible until the proxy is manually
            # killed. This was the root cause of multiple failed compaction
            # tests this session — the running proxy had stale code while the
            # file on disk had the fix.
            try {
                $proxyProcess = Get-Process -Id $owner.ListenerPid -ErrorAction Stop
                $scriptLastWrite = (Get-Item $ProxyScript).LastWriteTime
                if ($scriptLastWrite -gt $proxyProcess.StartTime) {
                    Write-Host "[admission-proxy] script changed since proxy started ($($proxyProcess.StartTime) < $scriptLastWrite) — restarting" -ForegroundColor Yellow
                    Stop-Process -Id $owner.ListenerPid -Force -ErrorAction SilentlyContinue
                    # Wait for the port to actually release before spawning a
                    # new proxy. Stop-Process returns immediately but the OS
                    # may hold the TCP socket in TIME_WAIT or the node process
                    # may have child threads that haven't exited yet. Poll
                    # until the port is free or timeout (5s max).
                    $portReleaseDeadline = (Get-Date).AddSeconds(5)
                    while ((Get-Date) -lt $portReleaseDeadline) {
                        $stillListening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
                        if (-not $stillListening) { break }
                        Start-Sleep -Milliseconds 250
                    }
                    # Also wait for the process to fully exit
                    $exitDeadline = (Get-Date).AddSeconds(3)
                    while ((Get-Date) -lt $exitDeadline) {
                        if (-not (Get-Process -Id $owner.ListenerPid -ErrorAction SilentlyContinue)) { break }
                        Start-Sleep -Milliseconds 250
                    }
                    # Fall through to the spawn path below
                } else {
                    return [pscustomobject]@{
                        Available = $true; Status = "Already running"; ListenerPid = $owner.ListenerPid
                        WrapperPid = $null; FallbackUrl = "http://127.0.0.1:$CcrPort"
                    }
                }
            } catch {
                # If the process lookup fails, reuse the existing listener
                return [pscustomobject]@{
                    Available = $true; Status = "Already running"; ListenerPid = $owner.ListenerPid
                    WrapperPid = $null; FallbackUrl = "http://127.0.0.1:$CcrPort"
                }
            }
        }
        return [pscustomobject]@{
            Available = $false; Status = "Ownership conflict"; ListenerPid = $owner.ListenerPid
            WrapperPid = $null; FallbackUrl = "http://127.0.0.1:$CcrPort"
        }
    }

    $wrapper = & $SpawnScript
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        if ($attempt -gt 1) { & $SleepScript 250 }
        $listener = Get-AdmissionProxyListener -Port $Port -ListenerLookup $ListenerLookup
        if (-not $listener) { continue }
        $owner = Get-AdmissionProxyOwner -Listener $listener -ProcessLookup $ProcessLookup -ExpectedScript $ProxyScript
        if ($owner -and $owner.IsExpected -and (Test-AdmissionProxyHealth -Port $Port -HealthCheck $HealthCheck)) {
            return [pscustomobject]@{
                Available = $true; Status = "Started"; ListenerPid = $owner.ListenerPid
                WrapperPid = if ($wrapper) { $wrapper.Id } else { $null }; FallbackUrl = "http://127.0.0.1:$CcrPort"
            }
        }
    }
    return [pscustomobject]@{
        Available = $false; Status = "Unavailable"; ListenerPid = $null
        WrapperPid = if ($wrapper) { $wrapper.Id } else { $null }; FallbackUrl = "http://127.0.0.1:$CcrPort"
    }
}

# Initial one-shot probe: rungs 1-4 only (no inference). A 15s inference probe
# here races real work under --parallel 1: it queues behind the single slot,
# times out, and reports HUNG while llama.cpp is alive and making progress.
# Liveness (LOADED/READY via rungs 1-4) is sufficient for routing readiness;
# real inference validation stays reserved for the explicit -Test path.
$lm = Invoke-LocalModelProbe
$localModelHealth = $false

if (-not $lm -or $lm.state -eq "DEAD") {
    Write-Host "[CCR] local model not ready (starting or probe transient) - starting..." -ForegroundColor Cyan
    # Clean slate: kill any orphaned launchers + llama-server + watchers from
    # prior runs BEFORE spawning a fresh launcher. cc-ccr -stop deliberately
    # leaves these running (local model is independent of CCR), so without
    # this dedup each -start spawns a new launcher while the old one keeps
    # racing to restart llama-server — observed as 2+ run-ornith-server.ps1
    # processes + colliding idempotency-guard exits (2026-07-09).
    # Non-Probe filter: -Probe invocations are transient health checks, not
    # launchers — don't kill those mid-probe.
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -match 'run-ornith-server\.ps1' -and $_.CommandLine -notmatch '-Probe' } |
      ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -match 'watch-system\.ps1' } |
      ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500  # let the port release before the new launcher probes it
    if (Test-Path $launcherScript) {
        # P/Invoke CreateProcess so the launcher (and its llama-server grandchild
        # + watchdog) survive the parent exiting AND run in its OWN console window
        # — not the caller's. Without CREATE_NEW_CONSOLE the child shares the
        # parent's console, so the launcher's Write-Host spills into the terminal
        # where the user runs cc-ccr/claude (they had to ^C to escape it).
        #   CREATE_NEW_CONSOLE      -> own console, own stdout (isolation)
        #   CREATE_BREAKAWAY_FROM_JOB -> survives parent exit
        #   STARTF_USESHOWWINDOW + SW_HIDE -> window created but never shown.
        #     Single-window operator experience: the dashboard (which the
        #     supervisor's Start-OrnithDashboard opens with -WindowStyle Normal)
        #     is the only window the user sees. The supervisor's own console
        #     still exists so Write-Host output is captured (and goes to the
        #     hidden buffer), but the user does not see a second window.
        #     The dashboard's in-place TUI already surfaces the live state
        #     the previous minimized supervisor's title bar was carrying, so
        #     no information is lost by hiding the supervisor's window.
        if (-not ([System.Management.Automation.PSTypeName]'CCR_BREAKAWAY').Type) {
            Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CCR_BREAKAWAY {
    const uint CREATE_BREAKAWAY_FROM_JOB = 0x01000000;
    const uint CREATE_NEW_CONSOLE        = 0x00000010;
    const uint STARTF_USESHOWWINDOW       = 0x00000001;
    const short SW_HIDE                    = 0;
    const short SW_SHOWMINNOACTIVE        = 7;
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO { public int cb; public IntPtr lpReserved; public IntPtr lpDesktop; public IntPtr lpTitle; public int dwX; public int dwY; public int dwXSize; public int dwYSize; public int dwXCountChars; public int dwYCountChars; public int dwFillAttribute; public uint dwFlags; public short wShowWindow; public short cbReserved2; public IntPtr lpReserved2; public IntPtr hStdInput; public IntPtr hStdOutput; public IntPtr hStdError; }
    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION { public IntPtr hProcess; public IntPtr hThread; public uint dwProcessId; public uint dwThreadId; }
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);
    public static bool Launch(string exe, string args) {
        var si = new STARTUPINFO {
            cb = Marshal.SizeOf(typeof(STARTUPINFO)),
            dwFlags = STARTF_USESHOWWINDOW,
            wShowWindow = SW_HIDE
        };
        var pi = new PROCESS_INFORMATION();
        uint flags = CREATE_BREAKAWAY_FROM_JOB | CREATE_NEW_CONSOLE;
        return CreateProcess(exe, args, IntPtr.Zero, IntPtr.Zero, false, flags, IntPtr.Zero, null, ref si, out pi);
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
                -WindowStyle Hidden
        }
        $lm = Wait-LocalModelReady -TimeoutSec 60
    } else {
        Write-Host "[CCR] run-ornith-server.ps1 not found at $launcherScript" -ForegroundColor Yellow
    }
} elseif ($lm.state -eq "LOADING") {
    Write-Host "[CCR] local model loading - waiting..." -ForegroundColor Cyan
    $lm = Wait-LocalModelReady -TimeoutSec 60
} elseif ($lm.state -in @("STUCK", "BROKEN")) {
    # STUCK/BROKEN: the launcher watchdog detects these (rungs 1-4, no inference)
    # and kill+restarts, so "watchdog recovers" is accurate HERE. HUNG is excluded:
    # it only arises from an inference probe, the initial probe no longer runs one,
    # and the watchdog deliberately does NOT probe inference under --parallel 1 —
    # so HUNG is neither auto-detected nor auto-recovered. See LLAMA-CRASH-RCA.md.
    Write-Host "[CCR] local model $($lm.state) ($($lm.detail)) - watchdog recovers; or relaunch the launcher" -ForegroundColor Yellow
} elseif ($lm.state -eq "READY" -or $lm.state -eq "LOADED") {
    $localModelHealth = $true
}

# A newly spawned supervisor can cross the LOADED boundary just after the
# bounded startup wait returns (especially while the GGUF is still being
# mapped). Take one fresh, short readiness pass immediately before rendering
# the infrastructure tree so the report describes the current server rather
# than the earlier startup snapshot.
if (-not $lm -or $lm.state -notin @("READY", "LOADED")) {
    $freshLm = Wait-LocalModelReady -TimeoutSec 15 -StartupGraceSec 3 -PollMilliseconds 1000
    if ($freshLm) { $lm = $freshLm }
    if ($lm -and $lm.state -in @("READY", "LOADED")) { $localModelHealth = $true }
}

# Report
$localPidSummary = if ($lm -and $lm.pids) { (@($lm.pids) -join ', ') } else { 'N/A' }
$localVramSummary = Get-LocalVramSummary
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
    $localModelSummary = "local"
    $localModelDetails = @(
        "status: $tag",
        "model: $($lm.model)",
        "endpoint: $localModelEndpoint",
        "ctx: $(if ($ctx) { $ctx.TrimStart(' ', '|').Trim() -replace '^ctx:\s*', '' } else { 'unavailable' })",
        "gpu-vram: $localVramSummary",
        "pid: $localPidSummary"
    )
} else {
    $localPidLabel = if ($lm -and $lm.pids) { "process alive, readiness: $($lm.state.ToLower())" } else { "no llama-server process" }
    $localStatus = if ($lm -and $lm.state -eq "LOADING") {
        "loading (GGUF not ready yet)"
    } elseif ($lm -and $lm.state -eq "HUNG") {
        # HUNG means the process and model were found, but the optional
        # inference probe failed. It must not be presented as a dead process.
        "loaded; inference unresponsive"
    } elseif ($lm -and $lm.state -in @("STUCK", "BROKEN")) {
        "unhealthy ($($lm.state.ToLower()))"
    } elseif ($lm) {
        "readiness unavailable ($($lm.state.ToLower()))"
    } else {
        "readiness probe unavailable"
    }
    $localModelSummary = "local"
    $localModelDetails = @(
        "status: $localStatus (fallback: opencode-go/deepseek-v4-flash for coding)",
        "model: $(if ($lm -and $lm.model) { $lm.model } else { 'unavailable' })",
        "endpoint: $localModelEndpoint",
        "ctx: unavailable",
        "gpu-vram: $localVramSummary",
        "pid: $localPidSummary ($localPidLabel)"
    )
}
$script:localModelState = $lm

# --- Log routing mode ---
$routingModeInfo = Resolve-RoutingMode -RoutingMode $null
try {
    $routingConfig = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json
    $routingModeInfo = Resolve-RoutingMode -RoutingMode $routingConfig.routingMode
} catch {}
$routingModeSummary = Format-RoutingModeDisplay -RoutingModeInfo $routingModeInfo

# --- Start admission proxy (observability layer) ---
# The admission proxy sits between Claude Code and CCR. It counts logical
# requests, records lifecycle events in a SQLite ledger, and exposes
# Prometheus metrics on /metrics. The context ceiling was removed — all
# requests are forwarded regardless of estimated token count. CCR's routing
# determines the provider model; most primary routes support up to 1M context.
$proxyPort = 3458
$proxyScript = "P:\.claude\provider-configs\ccr-admission-proxy.js"
$proxyLog = "P:\.claude\state\ccr-admission-proxy.log"

$proxyResult = Ensure-AdmissionProxy -Port $proxyPort -CcrPort $ccrPort -ProxyScript $proxyScript -ProxyLog $proxyLog
$proxyAvailable = $proxyResult.Available
if ($proxyAvailable) {
    $proxyStatusSummary = $proxyResult.Status
    $proxyPidSummary = $proxyResult.ListenerPid
} else {
    if ($proxyResult.Status -eq "Ownership conflict") {
        Write-Warning "[admission-proxy] Port $proxyPort is owned by an unexpected process; leaving it untouched and falling back to CCR on port $ccrPort."
    } else {
        Write-Warning "[admission-proxy] Proxy failed ownership/health verification; falling back to CCR on port $ccrPort."
    }
    if (Test-Path $proxyLog) {
        $proxyFailure = Get-Content -LiteralPath $proxyLog -Tail 1 -ErrorAction SilentlyContinue
        if ($proxyFailure) { Write-Warning "[admission-proxy] $proxyFailure" }
    }
    $proxyStatusSummary = "unavailable"
    $proxyPidSummary = "N/A"
}
$script:admissionProxyPid = $proxyResult.ListenerPid

# --- Wire this shell's Claude Code ---
# Claude → admission proxy (:3458) → CCR (configured PORT) → external models
$env:ANTHROPIC_BASE_URL = if ($proxyAvailable) {
    "http://127.0.0.1:$proxyPort"
} else {
    "http://127.0.0.1:$ccrPort"
}
$proxyLabel = if ($proxyAvailable) { "admission-proxy → CCR" } else { "CCR direct (admission-proxy unavailable)" }

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
if ($ccrFreshlyStarted -and $localModelHealth) {
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

# --- Fleet status: comprehensive liveness check across all 6 components ---
# Closes the observability gap that allowed the operator dashboard to go
# missing silently under external pressure (Codex taskkill /t storms, IDE
# restarts, user closing the window). Each component returns a small
# hashtable; Write-FleetStatusSection renders them in a single block.
# The supervisor (run-ornith-server.ps1) now also runs a dashboard
# watchdog that respawns the dashboard child automatically, but the
# launcher still needs to surface the full state on every run so the
# operator can see "where's the dashboard? is llama.cpp working?" at
# a glance.

function Get-FleetCcrStatus {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'claude-code-router' })
    if ($procs.Count -eq 0) { return @{ alive = $false; pid = $null; message = "CCR not running" } }
    $primary = $procs | Select-Object -First 1
    $port = $ccrPort
    $listening = $false
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
        $listening = $null -ne $conn
    } catch {}
    $msg = if ($listening) { "PID $($primary.ProcessId), port $port listening" }
           else { "PID $($primary.ProcessId), port $port NOT listening" }
    return @{ alive = $true; pid = [int]$primary.ProcessId; message = $msg }
}

function Get-FleetProxyStatus {
    $alive = [bool](Test-AdmissionProxyHealth -Port 3458)
    $pidVal = $null
    try { $pidVal = (Get-NetTCPConnection -LocalPort 3458 -State Listen -ErrorAction Stop).OwningProcess } catch {}
    $msg = if ($alive) { "port 3458, /health OK" } else { "port 3458 not listening" }
    return @{ alive = $alive; pid = $pidVal; message = $msg }
}

function Get-FleetSupervisorStatus {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'run-ornith-server\.ps1' })
    if ($procs.Count -eq 0) { return @{ alive = $false; pid = $null; message = "supervisor not running" } }
    $primary = $procs | Select-Object -First 1
    return @{ alive = $true; pid = [int]$primary.ProcessId; message = "PID $($primary.ProcessId)" }
}

function Get-FleetLlamaStatus {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'llama-server.exe' })
    if ($procs.Count -eq 0) { return @{ alive = $false; pid = $null; message = "process not running" } }
    $primary = $procs | Select-Object -First 1
    $health = $false
    $loaded = $false
    try {
        $h = Invoke-WebRequest 'http://127.0.0.1:8010/health' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $health = $h.StatusCode -eq 200
    } catch {}
    try {
        $m = Invoke-WebRequest 'http://127.0.0.1:8010/v1/models' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $loaded = $m.StatusCode -eq 200 -and ($m.Content -match 'data')
    } catch {}
    $msg = if ($health -and $loaded) { "PID $($primary.ProcessId), healthy, model loaded" }
           elseif ($health) { "PID $($primary.ProcessId), /health OK, model not loaded" }
           elseif ($loaded) { "PID $($primary.ProcessId), model loaded, /health failed" }
           else { "PID $($primary.ProcessId), unhealthy" }
    return @{ alive = $true; pid = [int]$primary.ProcessId; message = $msg }
}

function Get-FleetDashboardStatus {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'ornith-monitor\.py' })
    if ($procs.Count -eq 0) { return @{ alive = $false; pid = $null; message = "not running" } }
    $primary = $procs | Sort-Object ProcessId | Select-Object -First 1
    return @{ alive = $true; pid = [int]$primary.ProcessId; message = "PID $($primary.ProcessId)" }
}

function Get-FleetWatcherStatus {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'watch-system\.ps1' })
    if ($procs.Count -eq 0) { return @{ alive = $false; pid = $null; message = "not running" } }
    $primary = $procs | Select-Object -First 1
    $logPath = "P:\packages\installers\system_watch.log"
    $age = $null
    if (Test-Path $logPath) {
        $age = ((Get-Date) - (Get-Item $logPath).LastWriteTime).TotalSeconds
    }
    $status = if ($null -eq $age) { "no log file" }
              elseif ($age -lt 60) { "logging ($([int]$age)s ago)" }
              else { "log stale ($([int]$age)s ago)" }
    return @{ alive = $true; pid = [int]$primary.ProcessId; message = "PID $($primary.ProcessId), $status" }
}

function Write-FleetStatusRow {
    param([string]$Label, [hashtable]$Status)
    $mark = if ($Status.alive) { '✓' } else { '✗' }
    $color = if ($Status.alive) { 'Green' } else { 'Red' }
    Write-Host ("  {0,-14} {1} {2}" -f $Label, $mark, $Status.message) -ForegroundColor $color
}

function Write-FleetStatusSection {
    Write-DomainHeader "Fleet"
    Write-FleetStatusRow "CCR:"        (Get-FleetCcrStatus)
    Write-FleetStatusRow "proxy:"      (Get-FleetProxyStatus)
    Write-FleetStatusRow "supervisor:" (Get-FleetSupervisorStatus)
    Write-FleetStatusRow "llama.cpp:"  (Get-FleetLlamaStatus)
    Write-FleetStatusRow "dashboard:"  (Get-FleetDashboardStatus)
    Write-FleetStatusRow "watcher:"    (Get-FleetWatcherStatus)
}

# --- Render output ---
# When -Usage is requested, the usage section below renders its own
# infrastructure, environment, and routing trees. Skip the normal launch
# output to avoid duplication.
if (-not $Usage) {
Write-DomainHeader "Infrastructure"
$gatewayHealthy = $ccrRunning -and $proxyAvailable
$infrastructureStatus = if ($gatewayHealthy -and $localModelHealth) {
    'status: ready'
} elseif ($gatewayHealthy) {
    'status: gateway ready; local degraded'
} else {
    'status: degraded (gateway unavailable or no context-limit enforcement)'
}
$infrastructureTree = @(
    [pscustomobject]@{ Label = $infrastructureStatus; Children = @() }
    [pscustomobject]@{
        Label = 'proxy chain'
        Children = @(
            [pscustomobject]@{
                Label = 'CCR'
                Children = @(
                    [pscustomobject]@{ Label = "status: $ccrStartupSummary"; Children = @() }
                    [pscustomobject]@{ Label = "endpoint: $ccrUrl"; Children = @() }
                    [pscustomobject]@{ Label = "pid: $ccrPid"; Children = @() }
                )
            }
            [pscustomobject]@{
                Label = 'admission-proxy'
                Children = @(
                    [pscustomobject]@{ Label = "status: $proxyStatusSummary"; Children = @() }
                    [pscustomobject]@{ Label = "endpoint: http://127.0.0.1:$proxyPort"; Children = @() }
                    [pscustomobject]@{ Label = "pid: $proxyPidSummary"; Children = @() }
                )
            }
        )
    }
    [pscustomobject]@{
        Label = $localModelSummary
        Children = @($localModelDetails | ForEach-Object {
            [pscustomobject]@{ Label = $_; Children = @() }
        })
    }
)
Write-Tree -Nodes $infrastructureTree

# --- Fleet health: comprehensive per-component status (observability for
# components the Infrastructure tree above doesn't surface, e.g. the
# dashboard, the system watcher, and the actual llama.cpp inference state). ---
Write-FleetStatusSection

Write-DomainHeader "Claude environment"
Write-Host "  ANTHROPIC_BASE_URL                 $env:ANTHROPIC_BASE_URL"
Write-Host "  ANTHROPIC_API_KEY                  $(Format-EnvState $env:ANTHROPIC_API_KEY)"
Write-Host "  ANTHROPIC_AUTH_TOKEN               $(Format-EnvState $env:ANTHROPIC_AUTH_TOKEN)"
Write-Host "  ANTHROPIC_CUSTOM_MODEL_OPTION      $env:ANTHROPIC_CUSTOM_MODEL_OPTION"
Write-Host "  ANTHROPIC_CUSTOM_MODEL_OPTION_NAME $env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME"

Write-DomainHeader "Routing"
# --- Helper: format a CCR route string (provider1,model1,provider2,model2 → provider1/model1 → provider2/model2) ---
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
function Format-RoutePrimaryLabel {
    param([AllowNull()][string]$Primary)
    if ([string]::IsNullOrWhiteSpace($Primary)) { return 'primary: unavailable' }
    return "primary: $(Format-Route $Primary)"
}

try {
    $ccrCfg = Get-Content $ccrConfigPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
    $fb = $ccrCfg.fallback

    # Build a list of all router keys (slots + roles)
    # Threshold is routing policy metadata, not a model route.
    $routerProps = $ccrCfg.Router.PSObject.Properties | Where-Object Name -ne 'longContextThreshold'
    $routes = @()

    foreach ($prop in $routerProps) {
        $name  = $prop.Name
        $value = $prop.Value

        # Derive a label and which fallback chain (if any) to show
        $label = $name
        $chain = $null
        $domain = Get-RouteDomain -Name $name

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
            Domain = $domain
            Primary = $value
            Chain   = $chain
        }
    }

    # Sort by label then name so it's stable and readable
    $routes = $routes | Sort-Object Label, Name

    $routeNodes = @($routes | ForEach-Object {
        $r = $_
        $primaryLabel = Format-RoutePrimaryLabel -Primary $r.Primary
        $children = @(
            [pscustomobject]@{ Label = $primaryLabel; Children = @() }
        )
        if ($r.Chain -and $r.Chain.Count -gt 0) {
            foreach ($fallback in $r.Chain) {
                $children += [pscustomobject]@{ Label = "fallback: $(Format-Route $fallback)"; Children = @() }
            }
        } elseif ($r.Label -notin @('custom')) {
            $children += [pscustomobject]@{ Label = 'fallback: none configured'; Children = @() }
        }
        [pscustomobject]@{ Label = $r.Label; Domain = $r.Domain; Color = 'White'; Children = $children }
    })
    $claudeNodes = @($routeNodes | Where-Object { $_.Domain -eq 'claude models' })
    $roleNodes = @($routeNodes | Where-Object { $_.Domain -eq 'roles' })
    $providerNodes = @($routeNodes | Where-Object { $_.Domain -eq 'provider routes' })
    $localNodes = @($routeNodes | Where-Object { $_.Domain -eq 'local models' })

    $routeGroups = @(
        [pscustomobject]@{
            Label = "mode: $($routingModeSummary -replace '^routingMode=', '')"
            Children = @()
        }
        [pscustomobject]@{
            Label = 'routes'
            Children = @(
                [pscustomobject]@{ Label = 'claude models'; Color = 'White'; Children = $claudeNodes }
                [pscustomobject]@{ Label = 'roles'; Color = 'White'; Children = $roleNodes }
                [pscustomobject]@{ Label = 'provider routes'; Color = 'White'; Children = $providerNodes }
                [pscustomobject]@{ Label = 'local models'; Color = 'White'; Children = $localNodes }
            )
        }
    )
    Write-Tree -Nodes $routeGroups
}
catch {
    Write-Tree -Nodes @([pscustomobject]@{
        Label = "routes unavailable - check $ccrConfigPath"
        Children = @()
    })
}
Write-DomainHeader "Runtime flags"
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
    Write-Host ""
    $usageInfrastructure = Get-UsageInfrastructureTree
    Write-Host "Infrastructure" -ForegroundColor Cyan
    Write-Tree -Nodes @($usageInfrastructure[0].Children)

    Write-Host ""
    Write-Host "Claude environment (effective)" -ForegroundColor Cyan
    $usageProxyHealthy = (Get-UsageEndpointStatus -Uri 'http://127.0.0.1:3458/health') -like 'healthy*'
    $usageBaseUrl = if ($usageProxyHealthy) {
        'http://127.0.0.1:3458'
    } else {
        $ccrUrl
    }
    $effectiveBaseUrl = "$env:ANTHROPIC_BASE_URL (process; normal CCR wiring)"
    $effectiveKeySource = if ($env:ANTHROPIC_API_KEY) {
        if ($ccrLocalKey) { 'process; P:\.env: CCR_LOCAL_KEY' } else { 'process' }
    } else { $null }
    $effectiveAuthSource = if ($env:ANTHROPIC_AUTH_TOKEN) {
        if ($ccrLocalKey) { 'process; P:\.env: CCR_LOCAL_KEY' } else { 'process' }
    } else { $null }
    $effectiveCustomModel = "$env:ANTHROPIC_CUSTOM_MODEL_OPTION (process; normal CCR wiring)"
    $effectiveCustomName = "$env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME (process; normal CCR wiring)"
    $environmentNodes = @(
        [pscustomobject]@{ Label = "ANTHROPIC_BASE_URL: $effectiveBaseUrl"; Color = 'White'; Children = @() }
        [pscustomobject]@{ Label = "ANTHROPIC_API_KEY: $(if ($effectiveKeySource) { "<set> ($effectiveKeySource)" } else { '<missing>' })"; Color = $(if ($effectiveKeySource) { 'Green' } else { 'Yellow' }); Children = @() }
        [pscustomobject]@{ Label = "ANTHROPIC_AUTH_TOKEN: $(if ($effectiveAuthSource) { "<set> ($effectiveAuthSource)" } else { '<missing>' })"; Color = $(if ($effectiveAuthSource) { 'Green' } else { 'Yellow' }); Children = @() }
        [pscustomobject]@{ Label = "ANTHROPIC_CUSTOM_MODEL_OPTION: $effectiveCustomModel"; Color = 'White'; Children = @() }
        [pscustomobject]@{ Label = "ANTHROPIC_CUSTOM_MODEL_OPTION_NAME: $effectiveCustomName"; Color = 'White'; Children = @() }
        [pscustomobject]@{ Label = "ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION: $(if ($env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION) { "$($env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION) (process)" } else { 'llama.cpp · ornith-1.0-9b@q4_k_m (launcher default)' })"; Color = 'White'; Children = @() }
        [pscustomobject]@{ Label = "CLAUDE_CODE_DISABLE_1M_CONTEXT: $(if ($env:CLAUDE_CODE_DISABLE_1M_CONTEXT) { $env:CLAUDE_CODE_DISABLE_1M_CONTEXT } else { '<not set> (intentional)' })"; Color = 'DarkGray'; Children = @() }
    )
    Write-Tree -Nodes $environmentNodes

    Write-Host ""
    $usageRoutes = Get-UsageRouteTree
    Write-Host "Routing" -ForegroundColor Cyan
    Write-Tree -Nodes @($usageRoutes[0].Children)

    Write-Host ""
    Write-Host "Runtime flags" -ForegroundColor Cyan
    Write-Tree -Nodes @(
        [pscustomobject]@{ Label = "local-apply: $(if ($phaseLocalApply) { 'requested' } else { 'off' })"; Color = $(if ($phaseLocalApply) { 'Yellow' } else { 'DarkGray' }); Children = @() }
        [pscustomobject]@{ Label = "compact-hook: $(if ($phaseCompactHook) { 'requested' } else { 'off' })"; Color = $(if ($phaseCompactHook) { 'Yellow' } else { 'DarkGray' }); Children = @() }
    )

    Write-Host ""
    Write-Host "Provider quotas" -ForegroundColor Cyan
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
    Write-SectionSep
    # ── OpenAI ChatGPT subscription quota ──
    # Uses the local Codex ChatGPT login. This intentionally does not inspect
    # API keys, API spend, or purchased credit balances.
    if (Get-Command Get-OpenAISubscriptionUsage -ErrorAction SilentlyContinue) {
        $openaiUsage = Get-OpenAISubscriptionUsage
        if ($openaiUsage.Available) {
            Write-Host "  openai          [$($openaiUsage.Plan)]" -ForegroundColor White
            foreach ($window in $openaiUsage.Windows) {
                $reset = if ($window.ResetEpochMs) { Format-QuotaReset $window.ResetEpochMs } else { "" }
                Write-UsageRow $window.Name "$($window.Remaining)% left" $reset
            }
        } else {
            Write-Host "  openai          [subscription]" -ForegroundColor White
            Write-UsageStatus "unavailable - $($openaiUsage.Error)"
        }
        Write-SectionSep
    }
    # ── xAI / Grok subscription session ──
    # The subscription exposes model access through the authenticated Grok CLI
    # proxy. xAI's public docs do not expose a quota JSON endpoint for this pool,
    # so report API availability and models without inventing a percentage.
    Write-Host "  x.ai            [SuperGrok]" -ForegroundColor White
    if ($grokSessionToken) {
        try {
            $grokHeaders = @{ Authorization = "Bearer $grokSessionToken" }
            $grokModels = Invoke-RestMethod -Uri 'https://cli-chat-proxy.grok.com/v1/models' -Headers $grokHeaders -TimeoutSec 5 -ErrorAction Stop
            $grokModelNames = @($grokModels.data | ForEach-Object { $_.id } | Where-Object { $_ })
            Write-UsageStatus ("available - " + ($grokModelNames -join ', '))
        } catch {
            Write-UsageStatus "unavailable - $($_.Exception.Message)"
        }
    } else {
        Write-UsageStatus 'unavailable - Grok session token not loaded'
    }
    Write-SectionSep
    # ── Anthropic Claude subscription quota ──
    # Reads Claude subscription OAuth credentials directly. The statusline
    # snapshot remains an optional fallback, not a prerequisite.
    if (Get-Command Get-AnthropicSubscriptionUsage -ErrorAction SilentlyContinue) {
        $anthropicUsage = Get-AnthropicSubscriptionUsage
        if ($anthropicUsage.Available) {
            Write-Host "  anthropic       [$($anthropicUsage.Plan)]" -ForegroundColor White
            foreach ($window in $anthropicUsage.Windows) {
                $reset = if ($window.ResetEpochMs) { Format-QuotaReset $window.ResetEpochMs } else { "" }
                Write-UsageRow $window.Name "$($window.Remaining)% left" $reset
            }
        } else {
            Write-Host "  anthropic       [subscription]" -ForegroundColor White
            Write-UsageStatus "unavailable - $($anthropicUsage.Error)"
        }
        Write-SectionSep
    }
    # ── Google Antigravity / Gemini subscription quota ──
    # antigravity-usage uses its Google-authenticated Cloud Code path directly;
    # the IDE and language server do not need to be running for -Usage.
    if (Get-Command Get-AntigravityUsage -ErrorAction SilentlyContinue) {
        $geminiUsage = Get-AntigravityUsage
        if ($geminiUsage.Available) {
            $freshness = if ($geminiUsage.UpdatedAt) { " · $(Format-UsageAge $geminiUsage.UpdatedAt)" } else { '' }
            if ($geminiUsage.Stale) { $freshness += ' · stale' }
            $headerColor = if ($geminiUsage.Stale) { 'Yellow' } else { 'White' }
            Write-Host "  antigravity     [$($geminiUsage.Plan)]$freshness" -ForegroundColor $headerColor
            foreach ($window in $geminiUsage.Windows) {
                $reset = if ($window.ResetEpochMs) { Format-QuotaReset $window.ResetEpochMs } else { "" }
                Write-UsageRow $window.Name "$($window.Remaining)% left" $reset
                if ($window.Aliases) {
                    Write-UsageAliases $window.Aliases
                }
            }
        } else {
            Write-Host "  antigravity     [$($geminiUsage.Plan)]" -ForegroundColor White
            Write-UsageStatus "unavailable - $($geminiUsage.Error)"
        }
        Write-SectionSep
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
            Write-Host "  Script auth token: $(Get-SecretFingerprint $env:ANTHROPIC_AUTH_TOKEN)" -ForegroundColor Yellow
            $resolvedCcrLocalKey = [System.Environment]::GetEnvironmentVariable('CCR_LOCAL_KEY', 'Process')
            Write-Host "  Process CCR_LOCAL_KEY: $(Get-SecretFingerprint $resolvedCcrLocalKey)" -ForegroundColor Yellow
            Write-Host "  Running direct CCR probes..." -ForegroundColor Yellow
            $curlBody = '{"model":"claude-sonnet-5","max_tokens":16,"messages":[{"role":"user","content":"Reply OK"}]}'
            $headerValues = @($env:ANTHROPIC_AUTH_TOKEN, $env:ANTHROPIC_API_KEY, $resolvedCcrLocalKey)
            foreach ($headerValue in $headerValues | Select-Object -Unique) {
                Write-Host "  Probe Bearer header: $(Get-SecretFingerprint $headerValue)" -ForegroundColor Yellow
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
} # end if (-not $Usage)
