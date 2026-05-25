# qmd_update_wrapper.ps1 - Pure PowerShell QMD wiki update with retry
# Replaces inline PowerShell in wiki SKILL.md that fails via bash -> pwsh cross-shell
param(
    [string]$Collection = "wiki",
    [string]$Lang = "en",
    [int]$MaxRetries = 2
)

$retry = 0
$success = $false

while ($retry -le $MaxRetries) {
    $result = qmd update wiki --lang $Lang 2>&1
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
    Write-Error "QMD update failed after $MaxRetries retries -- wiki index may be stale"
    exit 1
}
