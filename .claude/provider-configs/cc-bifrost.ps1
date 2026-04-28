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
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "GLM-5.1"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "M27"

# Parse --model override (handles: cc-bf --model M27, cc-bf --model=GLM-5.1, cc-bf M27)
$modelOverride = $null
$i = 0
while ($i -lt $Args.Count) {
    $arg = $Args[$i]
    if ($arg -eq "--model" -or $arg -eq "-m") {
        # Next positional arg is the model value
        $i++
        if ($i -lt $Args.Count) { $modelOverride = $Args[$i] }
    } elseif ($arg -match "^--model=(.+)$") {
        $modelOverride = $matches[1]
    } elseif ($arg -match "^(M27|GLM-5.1|glm-5.1|MiniMax-M2.7|DeepSeek|Nvidia-Deepseek-v4-flash|nvidia-deepseek-v4-flash)$") {
        $modelOverride = $arg
    }
    $i++
}

# Apply per-tier model assignments based on override
if ($modelOverride) {
    $modelOverride = $modelOverride -replace "^glm-5.1$", "GLM-5.1" -replace "^MiniMax-M2.7$", "M27"
    if ($modelOverride -eq "GLM-5.1") {
        # Matching cc-glm: Sonnet=glm-5.1, Opus=glm-5.1, Haiku=glm-4.5-air
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "glm-5.1"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "glm-5.1"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "glm-4.5-air"
    } elseif ($modelOverride -eq "M27") {
        # Matching cc-mm: Sonnet=MiniMax-M2.7, Opus=MiniMax-M2.7, Haiku=MiniMax-M2.7
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "MiniMax-M2.7"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "MiniMax-M2.7"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "MiniMax-M2.7"
    } elseif ($modelOverride -match "^(DeepSeek|Nvidia-Deepseek-v4-flash|nvidia-deepseek-v4-flash)$") {
        # DeepSeek V4 Flash via Nvidia route in Bifrost
        # All three tiers use the same model (Flash with thinking modes via effort level)
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "Nvidia-Deepseek-v4-flash"
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "Nvidia-Deepseek-v4-flash"
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "Nvidia-Deepseek-v4-flash"
    }
}

# Dynamic display — reflects actual current env var values
Write-Host "🔧 Bifrost Configuration:" -ForegroundColor Yellow
Write-Host "   - Provider:             Bifrost AI Gateway" -ForegroundColor White
Write-Host "   - Endpoint:            http://localhost:8081/anthropic" -ForegroundColor White
Write-Host ("   - Sonnet:              " + $env:ANTHROPIC_DEFAULT_SONNET_MODEL) -ForegroundColor White
Write-Host ("   - Opus:                " + $env:ANTHROPIC_DEFAULT_OPUS_MODEL) -ForegroundColor White
Write-Host ("   - Haiku:               " + $env:ANTHROPIC_DEFAULT_HAIKU_MODEL) -ForegroundColor White
Write-Host ""
Write-Host "Available routes in Bifrost:" -ForegroundColor Yellow
Write-Host "   M27     → MiniMax/MiniMax-M2.7" -ForegroundColor White
Write-Host "   GLM-5.1 → Z.AI/glm-5.1" -ForegroundColor White
Write-Host "   DeepSeek → Nvidia-Deepseek-v4-flash" -ForegroundColor White
Write-Host ""
Write-Host "Usage: cc-bf               # default: Sonnet=M27, Opus=GLM-5.1, Haiku=M27" -ForegroundColor Cyan
Write-Host "       cc-bf --model M27     # MiniMax route (Sonnet/Opus/Haiku = MiniMax-M2.7)" -ForegroundColor Cyan
Write-Host "       cc-bf --model GLM-5.1 # GLM route (Sonnet/Opus = glm-5.1, Haiku = glm-4.5-air)" -ForegroundColor Cyan
Write-Host "       cc-bf --model DeepSeek # DeepSeek route (all tiers = Nvidia-Deepseek-v4-flash)" -ForegroundColor Cyan