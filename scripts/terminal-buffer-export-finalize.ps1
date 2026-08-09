[CmdletBinding()]
param(
    [string]$RawPath = 'D:\OneDrive\Documents\Terminal History\.terminal-buffer-current.txt',
    [string]$OutputDirectory = 'D:\OneDrive\Documents\Terminal History',
    [int]$WaitSeconds = 20
)

$ErrorActionPreference = 'Stop'

$startedAt = [DateTime]::UtcNow
$deadline = $startedAt.AddSeconds($WaitSeconds)
$minimumRecentWrite = $startedAt.AddSeconds(-10)
$previousLength = -1L
$previousWriteTime = [DateTime]::MinValue
$stableSamples = 0
$source = $null

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

while ([DateTime]::UtcNow -lt $deadline) {
    if (Test-Path -LiteralPath $RawPath -PathType Leaf) {
        try {
            $candidate = Get-Item -LiteralPath $RawPath -ErrorAction Stop
            $writeTime = $candidate.LastWriteTimeUtc

            # The action runs immediately before this foreground helper. Do not
            # reuse a stale staging file left by an interrupted export.
            if ($writeTime -ge $minimumRecentWrite) {
                if ($candidate.Length -eq $previousLength -and $writeTime -eq $previousWriteTime) {
                    $stableSamples++
                } else {
                    $previousLength = $candidate.Length
                    $previousWriteTime = $writeTime
                    $stableSamples = 0
                }

                if ($stableSamples -ge 2) {
                    $source = $candidate
                    break
                }
            }
        } catch {
            # The Terminal may still have the staging file open. Retry below.
        }
    }

    Start-Sleep -Milliseconds 150
}

if ($null -eq $source) {
    throw "Timed out waiting for a fresh, stable Windows Terminal export at '$RawPath'."
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$outputPath = Join-Path $OutputDirectory "terminal-history-$stamp.txt"
$suffix = 1
while (Test-Path -LiteralPath $outputPath) {
    $outputPath = Join-Path $OutputDirectory "terminal-history-$stamp-$suffix.txt"
    $suffix++
}

$copied = $false
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        [System.IO.File]::Copy($RawPath, $outputPath, $false)
        $copied = $true
        break
    } catch {
        if ($attempt -eq 5) {
            throw
        }
        Start-Sleep -Milliseconds 200
    }
}

if (-not $copied) {
    throw "The exported buffer was not copied to '$outputPath'."
}

try {
    Remove-Item -LiteralPath $RawPath -Force -ErrorAction Stop
} catch {
    Write-Warning "Saved '$outputPath', but could not remove the staging file '$RawPath': $($_.Exception.Message)"
}

Write-Output "Saved terminal buffer: $outputPath"
