param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "restart", "status", "stop-all", "help", "")]
    [string]$Command = "",

    [Parameter(Position = 1)]
    [string]$Terminal = "1"
)

# Claude Code Proxy Manager
# Wraps proxy_manager.py with colored output and a help screen.
#
# Usage:
#   proxy start [N]     Start proxy for terminal N (default: 1, port 3001)
#   proxy stop [N]      Stop proxy for terminal N
#   proxy restart [N]   Stop then start proxy for terminal N
#   proxy status        Show status of all running proxies
#   proxy stop-all      Stop all proxies
#   proxy help          Show this help

$ProxyDir = "P:\packages\.mcp\claude-code-proxy"
$ProxyScript = Join-Path $ProxyDir "proxy_manager.py"

function Show-Help {
    Write-Host ""
    Write-Host "Proxy Manager" -ForegroundColor Cyan
    Write-Host "  Manages claude-code-proxy instances (Go reverse proxy)." -ForegroundColor Gray
    Write-Host "  Config: $ProxyDir\config-terminal<N>.yaml" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  proxy start [N]     Start proxy for terminal N (default: 1, port 3001)" -ForegroundColor White
    Write-Host "  proxy stop [N]      Stop proxy for terminal N" -ForegroundColor White
    Write-Host "  proxy restart [N]   Stop then start proxy for terminal N" -ForegroundColor White
    Write-Host "  proxy status        Show status of all running proxies" -ForegroundColor White
    Write-Host "  proxy stop-all      Stop all proxies" -ForegroundColor White
    Write-Host "  proxy help          Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Port mapping:" -ForegroundColor Yellow
    Write-Host "  Terminal 1 -> port 3001" -ForegroundColor White
    Write-Host ""
}

if ($Command -eq "" -or $Command -eq "help") {
    Show-Help
    exit 0
}

if (-not (Test-Path $ProxyScript)) {
    Write-Host "ERROR: proxy_manager.py not found at $ProxyScript" -ForegroundColor Red
    exit 1
}

$label = if ($Command -in "status", "stop-all") { $Command } else { "$Command $Terminal" }
Write-Host "proxy $label" -ForegroundColor Cyan

switch ($Command) {
    "status"   { python $ProxyScript status }
    "stop-all" { python $ProxyScript stop-all }
    default    { python $ProxyScript $Command $Terminal }
}
