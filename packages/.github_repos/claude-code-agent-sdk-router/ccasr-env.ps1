# ccasr-env.ps1 -- Activate a running ccasr-router (supports multi-port).
#
# Usage:
#   . .\ccasr-env.ps1              # interactive menu
#   . .\ccasr-env.ps1 -Port 3456  # direct, port 3456
#   . .\ccasr-env.ps1 -Port 3457  # minimax-sonnet, port 3457
#   . .\ccasr-env.ps1 -Port 3458  # glm-sonnet, port 3458
param(
    [int]$Port = 0
)

$RouterDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-RouterAlive {
    param([int]$Port)
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$Port/health" -Method GET -TimeoutSec 3 -ErrorAction Stop
        return $r.StatusCode -eq 200
    } catch { return $false }
}

# Map of known ports to route names
$RouterMap = @{
    3456 = 'direct'
    3457 = 'minimax-sonnet'
    3458 = 'glm-sonnet'
}

# -- Direct mode
if ($Port -gt 0) {
    if (-not (Test-RouterAlive -Port $Port)) {
        Write-Host "No router running on port $Port." -ForegroundColor Red
        $route = $RouterMap[$Port]
        if ($route) {
            Write-Host "Start it: node dist/cli.js start --route $route --port $Port" -ForegroundColor Yellow
        }
        return
    }

    $env:ANTHROPIC_BASE_URL = "http://localhost:$Port"

    Clear-Host
    Write-Host ""
    Write-Host "  ccasr-router active" -ForegroundColor Cyan
    Write-Host "  Port : $Port" -ForegroundColor Gray
    $route = $RouterMap[$Port]
    if ($route) { Write-Host "  Route: $route" -ForegroundColor Gray }
    Write-Host "  URL  : $env:ANTHROPIC_BASE_URL" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Ready. Run: claude" -ForegroundColor Green
    Write-Host ""
    return
}

# -- Interactive menu
while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "  ccasr-router -- Activate" -ForegroundColor Cyan
    Write-Host "  " + ("-" * 44) -ForegroundColor DarkGray

    $currentUrl = $env:ANTHROPIC_BASE_URL
    if ($currentUrl) {
        Write-Host "  Active : $currentUrl" -ForegroundColor Green
    } else {
        Write-Host "  Active : (none)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "  Running routers:" -ForegroundColor White

    $i = 1
    $portMap = @{}
    foreach ($port in ($RouterMap.Keys | Sort-Object)) {
        $route = $RouterMap[$port]
        $alive = Test-RouterAlive -Port $port
        $isActive = $currentUrl -eq "http://localhost:$port"

        if ($alive) {
            $flag = if ($isActive) { "  ← active" } else { "" }
            Write-Host ("    [{0}] port {1}  ({2}){3}" -f $i, $port, $route, $flag) -ForegroundColor Green
        } else {
            Write-Host ("    [{0}] port {1}  ({2})  -- down" -f $i, $port, $route) -ForegroundColor DarkGray
        }
        $portMap[$i] = $port
        $i++
    }

    Write-Host ""
    Write-Host "  [q] quit" -ForegroundColor DarkGray
    Write-Host ""

    $anyUp = ($RouterMap.Keys | Where-Object { Test-RouterAlive -Port $_ } | Measure-Object).Count -gt 0
    if (-not $anyUp) {
        Write-Host "  No router is running." -ForegroundColor Yellow
        Write-Host "  Run .\ccasr-all.ps1 to start all routers." -ForegroundColor Yellow
        $choice = Read-Host "  [q]"
        if ($choice -eq 'q') { return }
        continue
    }

    $choice = Read-Host "  Pick [1-$($RouterMap.Count)], q"

    if ($choice -eq 'q' -or $choice -eq 'Q') { return }

    if ($portMap.ContainsKey([int]$choice)) {
        $port = $portMap[[int]$choice]
        if (-not (Test-RouterAlive -Port $port)) {
            Write-Host "  That router is not running." -ForegroundColor Red
            Start-Sleep -Milliseconds 1500
            continue
        }

        $env:ANTHROPIC_BASE_URL = "http://localhost:$port"

        Clear-Host
        Write-Host ""
        Write-Host "  ccasr-router active" -ForegroundColor Cyan
        Write-Host "  Port : $port" -ForegroundColor Gray
        Write-Host "  Route: $($RouterMap[$port])" -ForegroundColor Gray
        Write-Host "  URL  : $env:ANTHROPIC_BASE_URL" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Ready. Run: claude" -ForegroundColor Green
        Write-Host ""
        return
    }

    Write-Host "  Invalid choice." -ForegroundColor Red
    Start-Sleep -Milliseconds 1000
}
