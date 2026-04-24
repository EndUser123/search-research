# ccasr-start.ps1 -- Unified launcher for claude-code-agent-sdk-router.
#
# Usage:
#   .\ccasr-start.ps1              # interactive menu (status + route picker)
#   .\ccasr-start.ps1 direct       # start with named route
#   .\ccasr-start.ps1 list         # show available route sets
#
# Route sets (from ~/.ccasr/config.json):
#   direct         -- Anthropic direct (all tiers)
#   minimax-sonnet -- Sonnet tier -> MiniMax-M2.7
#   glm-sonnet     -- Sonnet tier -> GLM-4.7
#   cheap          -- All tiers -> Gemini-2.5-Flash
#
# Port map (all routes share port 3456):
#   3456 -- current route
#   3457 -- minimax-sonnet (reserved)
#   3458 -- glm-sonnet (reserved)
#   3459 -- available slot
#   3460 -- available slot

param(
    [Parameter(Position=0)]
    [string]$Route = '',

    [switch]$List,
    [switch]$Force
)

$RouterDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = "$HOME/.ccasr/config.json"
$StateFile = Join-Path $RouterDir "ccasr-state.json"

# Fixed port assignments for all managed routes
$Routers = @{
    3456 = 'direct'
    3457 = 'minimax-sonnet'
    3458 = 'glm-sonnet'
}

# -- Load P:/.env into process env
$envFile = "P:/.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match '^[^#].*=' } | ForEach-Object {
        $parts = $_ -split '=', 2
        $key = $parts[0].Trim()
        $val = $parts[1].Trim() -replace '^\"|\"$' -replace '\0', ''
        if ($key) { [System.Environment]::SetEnvironmentVariable($key, $val, 'Process') }
    }
}

# -- Validate config exists
if (-not (Test-Path $ConfigFile)) {
    Write-Error "Config not found: $ConfigFile`nCopy $RouterDir\config.example.json to $ConfigFile"
    exit 1
}

# -- Load route sets from config
try {
    $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
} catch {
    Write-Error "Failed to parse config: $_"
    exit 1
}

$routes = if ($config.Routes) { $config.Routes.PSObject.Properties.Name } else { @() }
if ($routes.Count -eq 0) {
    Write-Error "No route sets found in $ConfigFile"
    exit 1
}

# -- State helpers
function Get-RunningRouter {
    if (-not (Test-Path $StateFile)) { return $null }
    try {
        $d = Get-Content $StateFile -Raw | ConvertFrom-Json
        return [PSCustomObject]@{
            Port  = [int]$d.port
            Route = $d.route
            PID   = [int]$d.pid
        }
    } catch { return $null }
}

function Save-RouterState($port, $route, $routerPid) {
    @{ port = $port; route = $route; pid = $routerPid } | ConvertTo-Json | Set-Content $StateFile -Encoding UTF8
}

function Remove-RouterState {
    if (Test-Path $StateFile) { Remove-Item $StateFile -Force }
}

# -- Env var validation
function Test-RequiredEnvVars {
    param([string]$RouteName)
    $routeConfig = $config.Routes.$RouteName
    if (-not $routeConfig) { return $true }

    $providerEnvMap = @{
        'anthropic'  = 'ANTHROPIC_API_KEY'
        'openrouter' = 'OPENROUTER_API_KEY'
        'gemini'     = 'GEMINI_FREE_API_KEY'
        'groq'       = 'GROQ_API_KEY'
        'mistral'    = 'MISTRAL_API_KEY'
        'ollama'     = $null
        'minimax'    = 'MINIMAX_API_KEY'
        'glm'        = 'ZHIPU_API_KEY'
    }

    $providers = $routeConfig.PSObject.Properties.Value | ForEach-Object { ($_ -split ',')[0].Trim() } | Sort-Object -Unique
    $missing = @()
    foreach ($p in $providers) {
        $envVar = $providerEnvMap[$p]
        if (-not $envVar) { continue }
        $providerEntry = $config.Providers.$p
        # Support both string ("api_key") and object ({ api_key, api_base_url }) formats
        $providerKey = if ($providerEntry -is [string]) { $providerEntry } elseif ($providerEntry -is [hashtable] -or $providerEntry.PSObject.TypeNames -contains 'System.Collections.Hashtable') { $providerEntry['api_key'] } else { $null }
        if ([string]::IsNullOrEmpty($providerKey)) { continue }
        if (-not [System.Environment]::GetEnvironmentVariable($envVar)) {
            $missing += $envVar
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Host "Missing required environment variables for route '$RouteName':" -ForegroundColor Red
        foreach ($m in $missing) {
            Write-Host "  - $m" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "Set them before starting the router, e.g.:" -ForegroundColor DarkGray
        Write-Host "  `$env:$($missing[0]) = 'your-key'" -ForegroundColor DarkGray
        return $false
    }
    return $true
}

# -- Port helpers
function Test-PortInUse {
    param([int]$Port)
    $r = netstat -ano | Select-String ":$Port\b.*LISTENING"
    return $null -ne $r
}

function Get-RouterPID {
    param([int]$Port)
    $lines = netstat -ano | Select-String ":$Port\b.*LISTENING"
    foreach ($l in $lines) {
        $parts = $l -split '\s+'
        $procId = $parts[-1]
        if ($procId -match '^\d+$') { return [int]$procId }
    }
    return $null
}

# -- List mode
if ($List) {
    Write-Host ""
    Write-Host "Available route sets:" -ForegroundColor Cyan
    foreach ($r in $routes) {
        Write-Host "  $r" -ForegroundColor Green
    }
    Write-Host ""
    exit 0
}

# -- Direct route start
if ($Route) {
    if ($Route -notin $routes) {
        Write-Error "Unknown route '$Route'. Run with -List to see available."
        exit 1
    }

    $port = 3456  # all routes share 3456
    $existing = Get-RouterPID -Port $port

    if ($existing) {
        if ($Force) {
            Write-Host "Killing existing router on port $port (PID $existing)..." -ForegroundColor Yellow
            Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        } else {
            Write-Error "Port $port is already in use (PID $existing). Run with -Force to kill it."
            exit 1
        }
    }

    if (-not (Test-RequiredEnvVars -RouteName $Route)) {
        exit 1
    }

    Write-Host "Starting ccasr-router on port $port (route: $Route)..." -ForegroundColor Cyan

    $proc = Start-Process -FilePath "node" `
        -ArgumentList "dist/cli.js", "start", "--route", $Route, "--config", $ConfigFile `
        -WorkingDirectory $RouterDir `
        -NoNewWindow -PassThru `
        -RedirectStandardOutput (Join-Path $RouterDir "ccasr-$Route.log")

    Start-Sleep -Milliseconds 2000

    if ($proc.HasExited) {
        Write-Error "Router exited immediately with code $($proc.ExitCode)."
        exit 1
    }

    $verify = Test-PortInUse -Port $port
    if (-not $verify) {
        Write-Error "Router failed to bind to port $port."
        exit 1
    }

    Save-RouterState -port $port -route $Route -routerPid $proc.Id
    Write-Host ""
    Write-Host "Router running: http://localhost:$port/" -ForegroundColor Green
    Write-Host "Health:        http://localhost:$port/health" -ForegroundColor DarkGreen
    Write-Host "Route:         $Route" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Activate:      `$env:ANTHROPIC_BASE_URL = 'http://localhost:$port'" -ForegroundColor Cyan
    Write-Host "Or run:        . $RouterDir\ccasr-env.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Tip: In new Claude Code terminals, run the above to activate the router." -ForegroundColor DarkGray
    exit 0
}

# -- Interactive menu
while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "  ccasr-router -- Start" -ForegroundColor Cyan
    Write-Host "  " + ("-" * 44) -ForegroundColor DarkGray

    # Check all 5 ports
    $portStatuses = @{}
    $running = Get-RunningRouter
    foreach ($port in (3456, 3457, 3458, 3459, 3460)) {
        $inUse = Test-PortInUse -Port $port
        $procId = if ($inUse) { Get-RouterPID -Port $port } else { $null }
        $route = $Routers[$port]
        $isRunning = $running -and $running.Port -eq $port -and $inUse
        $portStatuses[$port] = @{
            InUse  = $inUse
            PID    = $procId
            Route  = $route
            Active = $isRunning
        }
    }

    Write-Host "  Port status:" -ForegroundColor White

    $routeMap = @{ 1 = 'direct'; 2 = 'minimax-sonnet'; 3 = 'glm-sonnet'; 4 = 'cheap' }
    $i = 1

    # Show only non-direct routes (direct requires ANTHROPIC_API_KEY, broken for OAuth users)
    foreach ($port in (3456, 3457, 3458)) {
        $s = $portStatuses[$port]
        $route = $Routers[$port]

        if ($s.Active) {
            Write-Host ("    [{0}] port {1}  ({2})  PID {3}  ← active" -f $i, $port, $route, $s.PID) -ForegroundColor Green
        } elseif ($s.InUse) {
            Write-Host ("    [{0}] port {1}  ({2})  PID {3}  -- in use" -f $i, $port, $route, $s.PID) -ForegroundColor Yellow
        } else {
            Write-Host ("    [{0}] port {1}  ({2})  -- down" -f $i, $port, $route) -ForegroundColor DarkGray
        }
        $i++
    }

    # Free slots
    foreach ($port in (3459, 3460)) {
        Write-Host ("    [{0}] port {1}  -- FREE" -f $i, $port) -ForegroundColor DarkGray
        $i++
    }

    Write-Host ""
    Write-Host "  [q] quit" -ForegroundColor DarkGray
    Write-Host ""

    $choice = Read-Host "Pick [1-5], q"

    if ($choice -eq 'q' -or $choice -eq 'Q') { return }

    # Map choice to route
    if ($choice -eq '1') { $Route = 'direct' }
    elseif ($choice -eq '2') { $Route = 'minimax-sonnet' }
    elseif ($choice -eq '3') { $Route = 'glm-sonnet' }
    elseif ($choice -eq '4') { $Route = 'cheap' }
    else {
        Write-Host "Invalid choice." -ForegroundColor Red
        Start-Sleep -Milliseconds 1000
        continue
    }

    Write-Host ""

    $port = 3456
    $existing = Get-RouterPID -Port $port

    if ($existing) {
        Write-Host "Killing existing router on port $port..." -ForegroundColor Yellow
        Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    if (-not (Test-RequiredEnvVars -RouteName $Route)) {
        Start-Sleep -Milliseconds 1500
        continue
    }

    Write-Host "Starting ccasr-router (route: $Route)..." -ForegroundColor Cyan

    $proc = Start-Process -FilePath "node" `
        -ArgumentList "dist/cli.js", "start", "--route", $Route, "--config", $ConfigFile `
        -WorkingDirectory $RouterDir `
        -NoNewWindow -PassThru `
        -RedirectStandardOutput (Join-Path $RouterDir "ccasr-$Route.log")

    Start-Sleep -Milliseconds 2000

    if ($proc.HasExited) {
        Write-Host "Router exited with code $($proc.ExitCode)." -ForegroundColor Red
        Write-Host "Check: $RouterDir\ccasr-$Route.log" -ForegroundColor DarkGray
    } else {
        Save-RouterState -port $port -route $Route -routerPid $proc.Id
        Write-Host ""
        Write-Host "  Running: http://localhost:$port/" -ForegroundColor Green
        Write-Host "  Health:  http://localhost:$port/health" -ForegroundColor DarkGreen
        Write-Host ""
        Write-Host "  Activate: `$env:ANTHROPIC_BASE_URL = 'http://localhost:$port'" -ForegroundColor Cyan
        Write-Host "  Tip: In new Claude Code terminals, run: . $RouterDir\ccasr-env.ps1" -ForegroundColor DarkGray
    }

    Write-Host ""
    $anyKey = Read-Host "Press Enter to continue"
}
