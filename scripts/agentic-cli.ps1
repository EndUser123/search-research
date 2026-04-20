# agentic-cli.ps1 - Generic CLI wrapper for capturing output to file
# Usage: pwsh -File P:/scripts/agentic-cli.ps1 -cli "codex" -command "exec [args]" -outputPath "P:/tmp/output.txt"

param(
    [Parameter(Mandatory=$true)]
    [string]$cli,

    [Parameter(Mandatory=$true)]
    [string]$command,

    [Parameter(Mandatory=$true)]
    [string]$outputPath,

    [string]$model
)

$ErrorActionPreference = "Continue"

# Build the full CLI command
if ($model -and $model -ne "") {
    $fullCommand = "$cli $command -m $model"
} else {
    $fullCommand = "$cli $command"
}

# Execute and capture output
$result = Invoke-Expression $fullCommand 2>&1
$exitCode = $LASTEXITCODE

# Write output to file
$result | Out-File -FilePath $outputPath -Encoding UTF8

# Exit with the CLI's exit code
exit $exitCode
