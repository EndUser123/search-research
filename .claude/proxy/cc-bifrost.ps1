param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]] $Args
)

# Bifrost AI Gateway Proxy Configuration Script
# Routes Claude Code through Bifrost's M27 and GLM-5.1 routes
# Usage: cc-bf [claude args...]

$env:ANTHROPIC_BASE_URL = "http://localhost:8081/anthropic"
$env:ANTHROPIC_API_KEY = "sk-bf-99f7318e-ad10-4ae0-8669-d9e874661853"

# Route selection via model name
# M27    → MiniMax/MiniMax-M2.7 via Bifrost
# GLM-5.1 → Z.AI/glm-5.1 via Bifrost
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "M27"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "M27"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "M27"

Write-Host "🔧 Bifrost Configuration:" -ForegroundColor Yellow
Write-Host "   - Provider:             Bifrost AI Gateway" -ForegroundColor White
Write-Host "   - Endpoint:            http://localhost:8081/anthropic" -ForegroundColor White
Write-Host "   - Sonnet/Opus/Haiku:    M27" -ForegroundColor White
Write-Host ""
Write-Host "Available routes in Bifrost:" -ForegroundColor Yellow
Write-Host "   M27     → MiniMax/MiniMax-M2.7" -ForegroundColor White
Write-Host "   GLM-5.1 → Z.AI/glm-5.1" -ForegroundColor White
Write-Host ""
Write-Host "Usage: cc-bf              # start Claude Code with M27" -ForegroundColor Cyan
Write-Host "       cc-bf --model GLM-5.1  # use GLM-5.1 route instead" -ForegroundColor Cyan
Write-Host ""

# Check for --model override
foreach ($arg in $Args) {
    if ($arg -eq "--model" -or $arg -eq "-m") {
        # Next arg is the model name
        continue
    }
    if ($arg -match "^(M27|GLM-5.1|glm-5.1)$") {
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $arg
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = $arg
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $arg
        Write-Host "   Route overridden to: $arg" -ForegroundColor Green
    }
}

# Start Claude with any remaining args, else just Claude
if ($Args.Count -gt 0 -and $Args[0] -ne "--model" -and $Args[0] -ne "-m") {
    claude @Args
} else {
    claude
}