# Signal Reader Module for Claude Code Statusline
# Reads signal files from ~/.claude/signals/ and returns processed state

$SIGNALS_DIR = $env:USERPROFILE + "\.claude\signals"
$SIGNAL_TTL = 300  # 5 minutes

function Get-Signals {
    <#
    .SYNOPSIS
    Read and process signal files from the signals directory.

    .DESCRIPTION
    Reads JSON signal files from ~/.claude/signals/, filters by type,
    cleans up old signals, and returns processed signal state.

    .OUTPUTS
    Hashtable with signal states (e.g., @{ planning_mode = "show" })
    #>
    param([string]$SignalType = "")

    $signalsDir = $SIGNALS_DIR
    if (!(Test-Path $signalsDir)) {
        return @{}
    }

    $now = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $state = @{}
    $signalsProcessed = 0

    try {
        $signalFiles = Get-ChildItem -Path $signalsDir -Filter "*.json" -ErrorAction SilentlyContinue
        $filesToDelete = @()

        foreach ($file in $signalFiles) {
            try {
                $content = Get-Content $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
                if ([string]::IsNullOrWhiteSpace($content)) {
                    $filesToDelete += $file.FullName
                    continue
                }

                $signal = $content | ConvertFrom-Json -ErrorAction SilentlyContinue
                if (-not $signal) {
                    $filesToDelete += $file.FullName
                    continue
                }

                # Check TTL
                $timestamp = if ($signal.timestamp) { [int]$signal.timestamp } else { 0 }
                if (($now - $timestamp) -gt $SIGNAL_TTL) {
                    $filesToDelete += $file.FullName
                    continue
                }

                # Filter by type if specified
                $type = if ($signal.type) { $signal.type } else { "" }
                if ($SignalType -and $type -ne $SignalType) {
                    continue
                }

                # Update state with latest signal for this type
                $action = if ($signal.action) { $signal.action } else { "" }
                if ($action) {
                    # "show" takes precedence over "clear" for same type
                    if ($action -eq "show") {
                        $state[$type] = "show"
                    } elseif ($action -eq "clear" -and -not $state.ContainsKey($type)) {
                        $state[$type] = "clear"
                    }
                    $signalsProcessed++
                }
            }
            catch {
                # Skip invalid signal files
                $filesToDelete += $file.FullName
            }
        }

        # Clean up old/invalid signals
        foreach ($filePath in $filesToDelete) {
            try {
                Remove-Item $filePath -Force -ErrorAction SilentlyContinue
            }
            catch {
                # Ignore deletion errors
            }
        }
    }
    catch {
        # Return empty state on error
        return @{}
    }

    return $state
}

function Get-PlanningModeState {
    <#
    .SYNOPSIS
    Get planning mode signal state.

    .OUTPUTS
    "show" if planning mode active, "clear" if cleared, $null if no signal
    #>
    $state = Get-Signals -SignalType "planning_mode"
    if ($state.ContainsKey("planning_mode")) {
        return $state["planning_mode"]
    }
    return $null
}

Export-ModuleMember -Function Get-Signals, Get-PlanningModeState
