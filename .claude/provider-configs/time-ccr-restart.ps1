# time-ccr-restart.ps1 — time the CCR stop and start phases with live output
#
# Usage (dot-source so ANTHROPIC_* wiring remains in this PowerShell):
#   . P:\.claude\provider-configs\time-ccr-restart.ps1
#   . P:\.claude\provider-configs\time-ccr-restart.ps1 -Timing
#
# The START measurement includes the normal cc-ccr launcher work, including
# health checks and quota/status lookups. Unlike Measure-Command, this script
# leaves the launcher's output visible while it runs.

[CmdletBinding()]
param(
    [switch]$Timing
)

$dotSourced = $MyInvocation.InvocationName -eq '.'
if (-not $dotSourced) {
    Write-Warning 'Run this script with dot-sourcing (". P:\.claude\provider-configs\time-ccr-restart.ps1") so ANTHROPIC_* wiring persists in the caller.'
}

$ccrScript = Join-Path $PSScriptRoot 'cc-ccr.ps1'
if (-not (Test-Path -LiteralPath $ccrScript)) {
    throw "CCR launcher not found: $ccrScript"
}

function Invoke-TimedStep {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Action
    )

    $timer = [Diagnostics.Stopwatch]::StartNew()
    if ($Timing) {
        Write-Host "[$Name] started  $(Get-Date -Format o)" -ForegroundColor Cyan
    }

    try {
        & $Action
    }
    finally {
        $timer.Stop()
        if ($Timing) {
            Write-Host "[$Name] finished $(Get-Date -Format o) | elapsed $($timer.Elapsed)" -ForegroundColor Green
        }
    }
}

if ($Timing) {
    Write-Host "CCR restart timing: $ccrScript" -ForegroundColor White
    Write-Host ""
}

Invoke-TimedStep -Name 'STOP' -Action {
    . $ccrScript -Stop
}

Write-Host ""

Invoke-TimedStep -Name 'START' -Action {
    . $ccrScript
}
