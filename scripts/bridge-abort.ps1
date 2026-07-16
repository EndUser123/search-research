<#
.SYNOPSIS
    Abort the bridge active injection for a specific lane.

.DESCRIPTION
    Deletes the lane-scoped UIMutex lock file that terminal_adapter holds
    while injecting.  The daemon detects the missing lock, aborts, and
    resets the lane phase to IDLE.

.PARAMETER LaneId
    The lane ID to abort (default: "default").

.PARAMETER All
    Abort ALL active bridge injections.

.EXAMPLE
    .ridge-abort.ps1 -LaneId chatgpt-claude

.EXAMPLE
    .ridge-abort.ps1 -All
#>
param(
    [string]$LaneId = "default",
    [switch]$All,
    [switch]$Force
)
$lockDir = "P:/.ai-lanes/controller/locks"
if ($All) {
    $locks = Get-ChildItem -Path $lockDir -Filter "ui-input-*.lock"
    if (-not $locks) { Write-Host "No active bridge locks found." -ForegroundColor Yellow; exit 0 }
    foreach ($lock in $locks) {
        try {
            $data = Get-Content -Raw -Encoding UTF8 $lock.FullName | ConvertFrom-Json
            $lane = $data.lane_id
            Remove-Item -Path $lock.FullName -Force
            Write-Host "✓ Aborted bridge injection for lane '$lane'" -ForegroundColor Green
        } catch {
            Remove-Item -Path $lock.FullName -Force -ErrorAction SilentlyContinue
            Write-Host "? Removed stale lock: $($lock.Name)" -ForegroundColor Yellow
        }
    }
    exit 0
}
$lockPath = Join-Path $lockDir "ui-input-$LaneId.lock"
if (-not (Test-Path $lockPath)) { Write-Host "No active bridge lock for lane '$LaneId'." -ForegroundColor Yellow; exit 0 }
try {
    $data = Get-Content -Raw -Encoding UTF8 $lockPath | ConvertFrom-Json
    $pid = $data.pid
    $lane = $data.lane_id
    if (-not $Force) {
        Write-Host "Bridge lock found for lane '$lane' (PID $pid)." -ForegroundColor Cyan
        $confirm = Read-Host "Abort this bridge injection? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") { Write-Host "Abort cancelled." -ForegroundColor Yellow; exit 1 }
    }
    Remove-Item -Path $lockPath -Force
    Write-Host "✓ Aborted bridge injection for lane '$lane' (PID $pid)" -ForegroundColor Green
    # Reset lane phase to IDLE
    $phasePath = "P:/.ai-lanes/$LaneId/phase.json"
    if (Test-Path $phasePath) {
        try { $phase = Get-Content -Raw -Encoding UTF8 $phasePath | ConvertFrom-Json
            $phase.phase = "IDLE"
            $phase.heartbeat_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ" -AsUTC)
            $phase | ConvertTo-Json | Set-Content -Path $phasePath -Encoding UTF8
            Write-Host "✓ Reset lane phase to IDLE" -ForegroundColor Green } catch { Write-Host "Warning: could not reset phase: $_" -ForegroundColor Yellow }
    }
} catch { Remove-Item -Path $lockPath -Force -ErrorAction SilentlyContinue; Write-Host "? Removed corrupt lock file for lane '$LaneId'" -ForegroundColor Yellow }
