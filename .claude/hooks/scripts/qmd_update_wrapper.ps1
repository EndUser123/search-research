# qmd_update_wrapper.ps1 - Pure PowerShell QMD wiki update with retry
# Replaces inline PowerShell in wiki SKILL.md that fails via bash -> pwsh cross-shell
# Note: `qmd update` accepts only an optional collection name — no --lang flag.
# Passing --lang was rejected every run (exit 2) and the retry loop retried the
# permanently-broken command; stderr was swallowed so it read as "occasional".
param(
    [string]$Collection = "wiki",
    [int]$MaxRetries = 2
)

$retry = 0
$success = $false
$lastResult = ""

while ($retry -le $MaxRetries) {
    $lastResult = qmd update $Collection 2>&1
    if ($LASTEXITCODE -eq 0) {
        $success = $true
        break
    }
    $retry++
    if ($retry -le $MaxRetries) {
        Start-Sleep -Seconds 1
    }
}

if (-not $success) {
    Write-Error "QMD update failed after $MaxRetries retries. Underlying qmd error:`n$lastResult"
    exit 1
}
