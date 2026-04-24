<#
.SYNOPSIS
    Start claude-code-proxy for a named config (interactive or direct).

.DESCRIPTION
    Interactive mode shows a port menu and guides you through config selection.
    Proxies start in the background — select multiple ports in one session.
    For detached proxies that survive session exit, use proxy_manager.py instead.

.PARAMETER Config
    Config name (without the config- prefix and .yaml suffix).
    When omitted, runs in interactive menu mode.

.PARAMETER Port
    Port to run the proxy on (required in direct mode).

.PARAMETER Force
    If the port is already in use, kill the existing process and reuse the port.

.PARAMETER List
    Show all available configs, then exit.

.EXAMPLE
    .\proxy-start.ps1
    # Interactive menu — pick a port, pick a config, proxy starts in background.

.EXAMPLE
    .\proxy-start.ps1 glm -Port 3004
    # Start glm directly on port 3004, killing any existing process on that port.

.EXAMPLE
    .\proxy-status.ps1
    # Check status of all 5 proxy ports.

.NOTES
    Use proxy_manager.py for production use (detached, auto-restart capable).
#>
param(
    [Parameter(Position=0)]
    [string]$Config = '',

    [Parameter(Position=1)]
    [int]$Port = 0,

    [switch]$Force,

    [switch]$List,

    [switch]$Auto
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProxyExe = Join-Path $ScriptDir "proxy\claude-code-proxy.exe"

if (-not (Test-Path $ProxyExe)) {
    Write-Error "Proxy executable not found: $ProxyExe"
    Write-Host "Build: cd proxy && go build -o claude-code-proxy.exe ./cmd/proxy"
    exit 1
}

. (Join-Path $ScriptDir "proxy-lib.ps1")

# ─── Helper: inject API key env vars based on config's anthropic.base_url ───────
function Inject-ApiKeyEnv {
    param([string]$CfgFile)

    # Read .env
    $envFile = "P:\.env"
    $dotEnv = @{}
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$') {
                $dotEnv[$matches[1]] = $matches[2].Trim('"').Trim("'")
            }
        }
    }

    # Read config to detect provider type and inject the right API key
    try {
        $yaml = Get-Content $CfgFile -Raw
        if ($yaml -match 'base_url\s*:\s*"https://z\.ai/') {
            # ZAI: set ANTHROPIC_PROVIDER_API_KEY so the proxy replaces Claude Code's key
            $key = if ($dotEnv["ZAI_API_KEY"]) { $dotEnv["ZAI_API_KEY"] } elseif ($env:ZAI_API_KEY) { $env:ZAI_API_KEY } else { "" }
            if ($key) { $env:ANTHROPIC_PROVIDER_API_KEY = $key }
        } elseif ($yaml -match 'base_url\s*:\s*"https://[^"]*minimax') {
            # MiniMax: set ANTHROPIC_PROVIDER_API_KEY so the proxy replaces Claude Code's key
            $key = if ($dotEnv["MINIMAX_API_KEY"]) { $dotEnv["MINIMAX_API_KEY"] } elseif ($env:MINIMAX_API_KEY) { $env:MINIMAX_API_KEY } else { "" }
            if ($key) { $env:ANTHROPIC_PROVIDER_API_KEY = $key }
        } elseif ($yaml -match 'base_url\s*:\s*"https://api\.anthropic\.com') {
            # Real Anthropic: pass through Claude Code's own key to the proxy process
            # (Start-Process doesn't inherit parent env, so we must pass it explicitly)
            $key = if ($dotEnv["ANTHROPIC_API_KEY"]) { $dotEnv["ANTHROPIC_API_KEY"] } elseif ($env:ANTHROPIC_API_KEY) { $env:ANTHROPIC_API_KEY } else { "" }
            if ($key) { $env:ANTHROPIC_API_KEY = $key }
        }
    } catch {}
}

# Load all configs (port is picked at runtime, not from config file)
$configs = @()
foreach ($file in Get-ChildItem "$ScriptDir\config-*.yaml") {
    $name = $file.BaseName -replace '^config-', ''
    $configs += [PSCustomObject]@{ Name = $name; File = $file.FullName }
}
$configs = $configs | Sort-Object Name

if ($List) {
    Write-Host ""
    Write-Host "Available configs:" -ForegroundColor Cyan
    foreach ($c in $configs) {
        $label = if ($Global:ConfigLabels[$c.Name]) { $Global:ConfigLabels[$c.Name] } else { "" }
        if ($label) {
            Write-Host "  $($c.Name)  ($label)" -ForegroundColor Cyan
        } else {
            Write-Host "  $($c.Name)" -ForegroundColor Cyan
        }
    }
    Write-Host ""
    return
}

# Track interactive vs direct invocation
$Interactive = $false

if (-not $Config) {
    $Interactive = $true
}

# ─── Helper: scan port status ─────────────────────────────────────────────────
function Get-PortStatus {
    param([int[]]$PortRange = @(3001, 3002, 3003, 3004, 3005))

    $netstat = netstat -ano | Select-String "LISTENING"
    $running = Get-RunningProxies

    $portMap = @{}
    foreach ($port in $PortRange) {
        $inUse = $netstat | Select-String ":$port\b"
        $procId = $null
        if ($null -ne $inUse) {
            foreach ($line in $inUse) {
                $parts = $line -split '\s+'
                $pidCandidate = $parts[-1]
                if ($pidCandidate -match '^\d+$') {
                    $procId = [int]$pidCandidate
                    break
                }
            }
        }
        $entry = $running | Where-Object { $_.Port -eq $port } | Select-Object -First 1
        $portMap[$port] = @{
            Port   = $port
            InUse  = ($null -ne $inUse)
            PID    = $procId
            Config = if ($entry) { $entry.Config } else { $null }
        }
    }
    $sorted = $portMap.Values | Sort-Object Port
    return @{
        Free = @($sorted | Where-Object { -not $_.InUse })
        Used = @($sorted | Where-Object { $_.InUse })
    }
}

# ─── Helper: start proxy in background ───────────────────────────────────────
function Start-Proxy {
    param([string]$Cfg, [int]$Port, [string]$CfgFile, [bool]$AutoKill)

    # Capture startup output from a brief run
    Inject-ApiKeyEnv -CfgFile $CfgFile
    $tempFile = [System.IO.Path]::GetTempFileName()
    $proc = Start-Process -FilePath $ProxyExe -ArgumentList "--config", $CfgFile -NoNewWindow -PassThru -RedirectStandardOutput $tempFile
    Start-Sleep -Milliseconds 3000
    if (-not $proc.HasExited) { Stop-Process $proc.Id -Force -ErrorAction SilentlyContinue }
    $proc.WaitForExit() | Out-Null

    $output = Get-Content $tempFile -Raw -ErrorAction SilentlyContinue
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue

    # Show providers
    $providerLines = $output -split "`n" | Where-Object { $_ -match 'provider registered:' }
    if ($providerLines) {
        Write-Host "Providers:" -ForegroundColor Green
        foreach ($line in $providerLines) {
            if ($line -match '🔗\s+(.+?)\s+provider registered:\s+(.+)') {
                Write-Host "  $($matches[1].Trim())  →  $($matches[2].Trim())"
            }
        }
        Write-Host ""
    }

    # Show model mappings
    $mappingLines = $output -split "`n" | Where-Object { $_ -match '    \w' -and $_ -notmatch '[-─]{5,}' }
    if ($mappingLines) {
        Write-Host "Model Mappings:" -ForegroundColor Green
        foreach ($line in $mappingLines) {
            if ($line -match '    (.+?)\s{2,}(.+?)[\s→]*$') {
                Write-Host "  $($matches[1].Trim())  →  $($matches[2].Trim())"
            }
        }
        Write-Host ""
    }

    # Port conflict check
    $netstatLines = netstat -ano | Where-Object { $_ -match ":$Port\b.*LISTENING" }
    $proxyPid = $null
    foreach ($line in $netstatLines) {
        $parts = $line -split '\s+'
        $pidCandidate = $parts[-1]
        if ($pidCandidate -match '^\d+$') {
            $proxyPid = $pidCandidate
            break
        }
    }

    if ($proxyPid) {
        if ($Force -or $AutoKill) {
            Write-Host "Port $Port in use (PID $proxyPid) — killing..." -ForegroundColor Yellow
            Stop-Process -Id $proxyPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        } else {
            Write-Host "Port $Port is already in use (PID $proxyPid)." -ForegroundColor Yellow
            Write-Host "Run with -Force to kill it and reuse the port." -ForegroundColor Yellow
            return $false
        }
    }

    # Start proxy in background
    Inject-ApiKeyEnv -CfgFile $CfgFile
    $startInfo = Start-Process -FilePath $ProxyExe -ArgumentList "--config", $CfgFile -WindowStyle Hidden -PassThru
    Update-ProxyState -Port $Port -Config $Cfg -NewPID $startInfo.Id
    Write-Host "Proxy running: http://localhost:$Port/" -ForegroundColor Green
    Write-Host "             http://localhost:$Port/health" -ForegroundColor DarkGreen
    Write-Host ""
    return $true
}

# ─── Helper: show stop sub-menu ───────────────────────────────────────────────
function Show-StopMenu {
    $status = Get-PortStatus
    $usedPorts = $status.Used

    Write-Host ""
    Write-Host "Stop a running proxy:" -ForegroundColor Cyan
    Write-Host ""

    if ($usedPorts.Count -eq 0) {
        Write-Host "  No proxies running." -ForegroundColor DarkGray
        Write-Host ""
        return $null
    }

    $optionNum = 1
    $optionMap = @{}
    foreach ($entry in $usedPorts) {
        $label = if ($entry.Config -and $Global:ConfigLabels[$entry.Config]) { $Global:ConfigLabels[$entry.Config] } else { if ($entry.Config) { $entry.Config } else { "?" } }
        $configStr = if ($entry.Config) { " ($label)" } else { "" }
        Write-Host ("  [{0}] port {1}{2}  PID {3}" -f $optionNum, $entry.Port, $configStr, $entry.PID) -ForegroundColor Yellow
        $optionMap[$optionNum] = $entry
        $optionNum++
    }

    Write-Host ""
    Write-Host "  [q] cancel" -ForegroundColor DarkGray
    $choice = Read-Host "Pick [1-$($optionNum - 1)], q"

    if ($choice -eq 'q' -or $choice -eq 'Q') {
        return $null
    }

    if ($choice -match '^\d+$' -and $optionMap.ContainsKey([int]$choice)) {
        return $optionMap[[int]$choice]
    }

    Write-Host "Invalid selection." -ForegroundColor Red
    return $null
}

function Stop-ProxyByEntry {
    param([PSCustomObject]$Entry)
    if (-not $Entry -or -not $Entry.PID) { return }

    $port = $Entry.Port
    $pid = $Entry.PID

    Write-Host "Stopping proxy on port $port (PID $pid)..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500

    # Verify it's dead
    $stillRunning = netstat -ano | Select-String "LISTENING" | Select-String ":$port\b"
    if ($stillRunning) {
        Write-Host "  Failed to stop — port still in use." -ForegroundColor Red
    } else {
        Write-Host "  Stopped." -ForegroundColor Green
        Remove-FromProxyState -Port $port
    }
}

# ─── Helper: show port menu ─────────────────────────────────────────────────
function Show-Menu {
    $status = Get-PortStatus
    $freePorts = $status.Free
    $inUsePorts = $status.Used

    # Read state file so we know about proxies that haven't fully bound yet
    $running = Get-RunningProxies
    $runningByPort = @{}
    foreach ($r in $running) { $runningByPort[$r.Port] = $r }

    Write-Host ""
    Write-Host "claude-code-proxy" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select a port to run the proxy on. Ports in use will be killed first." -ForegroundColor White
    Write-Host "Or [s] to stop a running proxy." -ForegroundColor White
    Write-Host ""

    # Merge free and in-use ports into a single list sorted by port number
    $allPorts = @()
    foreach ($p in $freePorts) {
        # Check if a proxy is supposed to be on this port (may not have bound yet)
        $stateEntry = if ($runningByPort.ContainsKey($p.Port)) { $runningByPort[$p.Port] } else { $null }
        $allPorts += @{ Port = $p.Port; Config = if ($stateEntry) { $stateEntry.Config } else { $null }; PID = if ($stateEntry) { $stateEntry.PID } else { $null }; InUse = if ($stateEntry) { $true } else { $false } }
    }
    foreach ($p in $inUsePorts) { $allPorts += @{ Port = $p.Port; Config = $p.Config; PID = $p.PID; InUse = $true } }
    $allPorts = $allPorts | Sort-Object Port

    $optionNum = 1
    $optionMap = @{}

    foreach ($entry in $allPorts) {
        if ($entry.InUse) {
            $label = if ($entry.Config -and $Global:ConfigLabels[$entry.Config]) { $Global:ConfigLabels[$entry.Config] } else { if ($entry.Config) { $entry.Config } else { "?" } }
            $configStr = if ($label) { " ($label)" } else { "" }
            Write-Host ("  [{0}] port {1}{2}  PID {3}  (will be killed)" -f `
                $optionNum, $entry.Port, $configStr, $entry.PID) -ForegroundColor Yellow
        } else {
            Write-Host "  [$optionNum] port $($entry.Port)  free" -ForegroundColor Green
        }
        $optionMap[$optionNum] = $entry.Port
        $optionNum++
    }

    Write-Host ""
    Write-Host "  [s] stop a running proxy" -ForegroundColor DarkGray
    Write-Host "  [q] quit" -ForegroundColor DarkGray
    Write-Host ""
    $defaultPort = $allPorts[0].Port
    Write-Host "Press Enter to use the first free port ($defaultPort)" -ForegroundColor DarkGray
    $choice = Read-Host "Pick [1-$($optionNum - 1)], s, q, or Enter"

    return @{
        Choice    = $choice
        OptionMap = $optionMap
        FreePorts = $freePorts
        UsedPorts = $inUsePorts
        Running   = $running
    }
}

# ─── Direct config mode (non-interactive) ────────────────────────────────────
if (-not $Interactive) {
    $ConfigFile = Join-Path $ScriptDir "config-$Config.yaml"
    if (-not (Test-Path $ConfigFile)) {
        Write-Error "Config not found: $Config"
        Write-Host "Run with -List to see available configs."
        exit 1
    }
    if (-not $Port) {
        Write-Error "Port is required in direct mode. Use: .\proxy-start.ps1 $Config -Port 3001"
        Write-Host "Run with -List to see available configs."
        exit 1
    }

    Write-Host ""
    Write-Host "Starting claude-code-proxy on port $port ($Config)..." -ForegroundColor Cyan
    Write-Host "  Config: $ConfigFile"
    Write-Host ""

    $ok = Start-Proxy -Cfg $Config -Port $port -CfgFile $ConfigFile -AutoKill $Force
    if (-not $ok) { exit 1 }
    exit 0
}

# ─── Interactive loop ────────────────────────────────────────────────────────
while ($true) {
    $result = Show-Menu
    $choice = $result.Choice
    $optionMap = $result.OptionMap
    $freePorts = $result.FreePorts
    $usedPorts = $result.UsedPorts
    $running = $result.Running

    # Build port→runningEntry and config→runningEntry maps
    $runningByPort = @{}
    $runningByConfig = @{}
    foreach ($r in $running) {
        $runningByPort[$r.Port] = $r
        $runningByConfig[$r.Config] = $r
    }

    # Quit?
    if ($choice -eq 'q' -or $choice -eq 'Q') {
        Write-Host "Goodbye." -ForegroundColor Cyan
        exit 0
    }

    # Stop sub-menu?
    if ($choice -eq 's' -or $choice -eq 'S') {
        $toStop = Show-StopMenu
        if ($toStop) {
            Stop-ProxyByEntry -Entry $toStop
        }
        continue
    }

    # Default: first free port
    if ([string]::IsNullOrWhiteSpace($choice)) {
        $port = $freePorts[0].Port
    } elseif ($choice -match '^\d+$' -and $optionMap.ContainsKey([int]$choice)) {
        $port = $optionMap[[int]$choice]
    } else {
        Write-Host "Invalid selection." -ForegroundColor Red
        continue
    }

    # Show all configs and let user pick
    Write-Host ""
    Write-Host "Port $port — pick a config:" -ForegroundColor White
    $configNum = 1
    $configMap = @{}
    foreach ($c in $configs) {
        $isRunning = $runningByConfig.ContainsKey($c.Name)
        $label = if ($Global:ConfigLabels[$c.Name]) { $Global:ConfigLabels[$c.Name] } else { "" }
        $marker = if ($isRunning) { "  ← $(if ($label) { $label } else { $c.Name }) (current)" } else { "" }
        $summary = Get-ConfigSummary -Config $c.Name
        $driver = if ($summary -and $summary.OrchUrl) { "  → $($summary.OrchUrl)" } else { "" }
        $models = if ($summary -and $summary.Subagents.Count -gt 0) {
            $uniqueModels = $summary.Subagents.Values | Sort-Object -Unique
            "  models: $($uniqueModels -join ', ')"
        } else { "" }

        if ($label) {
            Write-Host "  [$configNum] $($c.Name)  ($label)$marker" -ForegroundColor Cyan
        } else {
            Write-Host "  [$configNum] $($c.Name)$marker" -ForegroundColor Cyan
        }
        if ($driver) { Write-Host "$driver" -ForegroundColor DarkGray }
        if ($models) { Write-Host "$models" -ForegroundColor DarkGray }
        $configMap[$configNum] = $c.Name
        $configNum++
    }
    $portInUse = $usedPorts | Where-Object { $_.Port -eq $port }
    if ($portInUse) {
        Write-Host "  [n] none — stop proxy only" -ForegroundColor DarkGray
        $stopOnly = $true
    } else {
        $stopOnly = $false
    }
    $prompt = if ($stopOnly) { "Pick a config [1-$($configNum - 1)] or n" } else { "Pick a config [1-$($configNum - 1)]" }
    $configChoice = Read-Host $prompt
    if ($configChoice -eq 'n' -or $configChoice -eq 'N') {
        if ($portInUse) {
            Stop-ProxyByEntry -Entry $portInUse
        }
        continue
    }
    if ($configChoice -match '^\d+$' -and $configMap.ContainsKey([int]$configChoice)) {
        $Config = $configMap[[int]$configChoice]
    } else {
        Write-Host "Invalid config selection." -ForegroundColor Red
        continue
    }

    $ConfigFile = Join-Path $ScriptDir "config-$Config.yaml"

    Write-Host ""
    Write-Host "Starting claude-code-proxy on port $port ($Config)..." -ForegroundColor Cyan
    Write-Host ""

    $ok = Start-Proxy -Cfg $Config -Port $port -CfgFile $ConfigFile -AutoKill $true
    if (-not $ok) {
        Write-Host "Proxy failed to start." -ForegroundColor Red
    }
}
