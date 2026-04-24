# ccasr-launch.ps1 -- One-shot: kill old router, start fresh, activate, launch Claude Code.
param(
    [string]$Route = "direct"
)

$RouterDir = "P:\packages\.mcp\claude-code-agent-sdk-router"
$ConfigFile = "$HOME/.ccasr/config.json"
$Port = 3456

# Kill anything on the port
$existing = netstat -ano | Select-String ":$Port\b.*LISTENING"
if ($existing) {
    foreach ($l in $existing) {
        $parts = $l -split '\s+'
        $procId = $parts[-1]
        if ($procId -match '^\d+$') {
            Write-Host "Killing PID $procId on port $Port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Milliseconds 500
}

# Start router (background, no new window)
Write-Host "Starting ccasr-router ($Route) on port $Port..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "node" `
    -ArgumentList "dist/cli.js", "start", "--route", $Route, "--config", $ConfigFile `
    -WorkingDirectory $RouterDir `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput "$RouterDir\ccasr-$Route.log"

Start-Sleep -Milliseconds 2000

if ($proc.HasExited) {
    Write-Host "Router exited with code $($proc.ExitCode)." -ForegroundColor Red
    Write-Host "Check: $RouterDir\ccasr-$Route.log" -ForegroundColor DarkGray
    exit 1
}

# Verify it started
$verify = netstat -ano | Select-String ":$Port\b.*LISTENING"
if (-not $verify) {
    Write-Host "Router failed to bind to port $Port." -ForegroundColor Red
    exit 1
}

# Activate
$env:ANTHROPIC_BASE_URL = "http://localhost:$Port"

Write-Host ""
Write-Host "  Router running: http://localhost:$Port/" -ForegroundColor Green
Write-Host "  Route:         $Route" -ForegroundColor Gray
Write-Host "  ANTHROPIC_BASE_URL = $env:ANTHROPIC_BASE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Launching Claude Code..." -ForegroundColor Green

# Launch Claude Code in a new window
start Process -FilePath "claude" -ArgumentList "--noprofile" -WorkingDirectory "P:\"

Write-Host "Done." -ForegroundColor DarkGray
