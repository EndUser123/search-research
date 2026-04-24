# ─────────────────────────────────────────────────────────────────────────────
# proxy-claude-env.ps1 — Pure terminal activator for claude-code-proxy.
# Sets ANTHROPIC_BASE_URL to an already-running proxy.
# All proxy start/stop is handled by proxy-start.ps1.
# ─────────────────────────────────────────────────────────────────────────────
param(
    [ValidateSet('anthropic', 'glm', 'm27', '')]
    [string]$Mode = '',

    [int]$Port = 0
)

$ProxyDir = $PSScriptRoot
. (Join-Path $ProxyDir "proxy-lib.ps1")

$ModeMap = [ordered]@{
    anthropic = @{ Config = 'anthropic'; Port = 3001; Label = 'Anthropic' }
    glm       = @{ Config = 'glm';       Port = 3004; Label = 'GLM' }
    m27       = @{ Config = 'm27';      Port = 3005; Label = 'MiniMax M2.7' }
}

function Test-ProxyAlive {
    param([int]$Port)
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$Port/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        return $r.StatusCode -eq 200
    } catch { return $false }
}

# ── Direct mode ───────────────────────────────────────────────────────────────
# . .\proxy-claude-env.ps1 -Mode glm
# Activates the glm proxy (must already be running).

if ($Mode) {
    if (-not $ModeMap.Contains($Mode)) {
        Write-Warning "Unknown mode. Valid: $($ModeMap.Keys -join ', ')"
        return
    }
    $entry = $ModeMap[$Mode]
    $port  = if ($Port) { $Port } else { $entry.Port }

    if (-not (Test-ProxyAlive -Port $port)) {
        Write-Host "Proxy is not running on port $port." -ForegroundColor Red
        Write-Host "Start it first: .\proxy-start.ps1" -ForegroundColor Yellow
        return
    }

    $env:ANTHROPIC_BASE_URL = "http://localhost:$port"

    $summary = Get-ConfigSummary -Config $entry.Config

    Clear-Host
    Write-Host ""
    Write-Host "  Active : $($entry.Label) (port $port)" -ForegroundColor Cyan
    Write-Host "  URL    : $env:ANTHROPIC_BASE_URL" -ForegroundColor Gray
    if ($summary -and $summary.OrchUrl) {
        Write-Host "  Driver : $($summary.OrchUrl)" -ForegroundColor DarkCyan
    }
    if ($summary -and $summary.Subagents.Count -gt 0) {
        $uniqueModels = $summary.Subagents.Values | Sort-Object -Unique
        $modelList = ($uniqueModels -join ", ")
        Write-Host "  Models : $modelList" -ForegroundColor DarkCyan
    }
    Write-Host ""
    Write-Host "  Ready. Run: claude" -ForegroundColor Green
    Write-Host ""
    return
}

# ── Interactive menu ──────────────────────────────────────────────────────────
# Shows running proxies and lets you pick one to activate.
# Does NOT start or stop proxies — use proxy-start.ps1 for that.

while ($true) {
    $running = Get-RunningProxies

    # Probe live health for each known port
    $livePorts = @{}
    foreach ($key in $ModeMap.Keys) {
        $p = $ModeMap[$key].Port
        $livePorts[$p] = Test-ProxyAlive -Port $p
    }

    $currentUrl = $env:ANTHROPIC_BASE_URL
    $currentLabel = ""
    $currentKey = ""
    if ($currentUrl -and $currentUrl -match ':(\d+)$') {
        $curPort = [int]$Matches[1]
        $stateEntry = $running | Where-Object { $_.Port -eq $curPort } | Select-Object -First 1
        if ($stateEntry) {
            $cfg = $stateEntry.Config
            $currentLabel = if ($cfg -and $Global:ConfigLabels[$cfg]) { $Global:ConfigLabels[$cfg] } else { $cfg }
            $currentKey = $cfg
        } else {
            foreach ($key in $ModeMap.Keys) {
                if ($ModeMap[$key].Port -eq $curPort) {
                    $currentLabel = $ModeMap[$key].Label
                    $currentKey = $key
                    break
                }
            }
        }
    }

    Clear-Host
    Write-Host ""
    Write-Host "  Claude Proxy — Activate" -ForegroundColor Cyan
    Write-Host "  " + ("-" * 48) -ForegroundColor DarkGray

    if ($currentUrl) {
        Write-Host "  Active : $currentUrl" -NoNewline -ForegroundColor Green
        if ($currentLabel) { Write-Host "  ($currentLabel)" -ForegroundColor Green }
        Write-Host ""
    }

    # Build a port→stateEntry lookup map (robust regardless of state file key format)
    $portStateMap = @{}
    if ((Test-Path $StateFile) -and $running.Count -gt 0) {
        foreach ($entry in $running) {
            $portStateMap[$entry.Port] = $entry
        }
    }

    $i = 1
    $indexMap = @{}
    $runningProxies = @()
    foreach ($key in $ModeMap.Keys) {
        $entry = $ModeMap[$key]
        $port  = $entry.Port
        $isUp  = $livePorts[$port]

        # Get actual config from state map, fall back to ModeMap key
        $actualConfig = $null
        if ($isUp -and $portStateMap.ContainsKey($port)) {
            $actualConfig = $portStateMap[$port].Config
        }
        $configKey = if ($actualConfig) { $actualConfig } else { $entry.Config }
        $label = if ($actualConfig -and $Global:ConfigLabels[$actualConfig]) { $Global:ConfigLabels[$actualConfig] } else { $entry.Label }
        $isCurrent = ($currentKey -eq $configKey)

        if ($isUp) {
            $runningProxies += [PSCustomObject]@{
                Key = $configKey
                Label = $label
                Port = $port
                IsCurrent = $isCurrent
            }
        }
    }

    if ($runningProxies.Count -gt 0) {
        Write-Host "  Running proxies:" -ForegroundColor White
        foreach ($p in $runningProxies) {
            $indexMap[$i] = $p
            $marker = if ($p.IsCurrent) { " (current)" } else { "" }
            Write-Host ("  [{0}] {1}  port {2}{3}" -f $i, $p.Label.PadRight(16), $p.Port, $marker) -ForegroundColor Green
            $i++
        }
        Write-Host ""
    }

    Write-Host "  [q] quit" -ForegroundColor DarkGray
    Write-Host ""

    if ($runningProxies.Count -eq 0) {
        Write-Host "  No proxies running." -ForegroundColor DarkGray
        Write-Host "  Start one first: .\proxy-start.ps1" -ForegroundColor Yellow
        Write-Host ""
        $choice = Read-Host "  [q] quit"
    } else {
        $choice = Read-Host "  Pick [1-$($runningProxies.Count)], q"
    }

    # Quit
    if ($choice -eq 'q' -or $choice -eq 'Q') { return }

    # Pick a running proxy to activate
    if ($choice -match '^\d+$' -and $indexMap.ContainsKey([int]$choice)) {
        $sel = $indexMap[[int]$choice]
        $env:ANTHROPIC_BASE_URL = "http://localhost:$($sel.Port)"

        $summary = Get-ConfigSummary -Config $sel.Key

        Clear-Host
        Write-Host ""
        Write-Host "  Active : $($sel.Label) (port $($sel.Port))" -ForegroundColor Cyan
        Write-Host "  URL    : $env:ANTHROPIC_BASE_URL" -ForegroundColor Gray
        if ($summary -and $summary.OrchUrl) {
            Write-Host "  Driver : $($summary.OrchUrl)" -ForegroundColor DarkCyan
        }
        if ($summary -and $summary.Subagents.Count -gt 0) {
            $uniqueModels = $summary.Subagents.Values | Sort-Object -Unique
            $modelList = ($uniqueModels -join ", ")
            Write-Host "  Models : $modelList" -ForegroundColor DarkCyan
        }
        Write-Host ""
        Write-Host "  Ready. Run: claude" -ForegroundColor Green
        Write-Host ""
        return
    } else {
        Write-Host "  Invalid choice." -ForegroundColor Red
        Start-Sleep -Milliseconds 1000
    }
}
