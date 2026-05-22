param(
    [switch]$GetTestCommands,
    [ValidateSet('4', '5')]
    [string]$Model = '5'
)

# GLM/Z.ai LLM Proxy Configuration Script
# Usage: .\cc-glm.ps1 [-Model 4|5]

if ($GetTestCommands) {
    [PSCustomObject]@{
        Description = 'Test Claude Code Integration (Proxy)'
        Executable = 'curl.exe'
        Arguments = @(
            '-s',
            '-X', 'POST',
            'http://localhost:5000/v1/chat/completions',
            '-H', 'Content-Type: application/json',
            '-H', 'Authorization: Bearer your_zai_api_key_here',
            '-d', '{"model": "claude-sonnet-4-20250514", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
        )
    }
    return
}

# Set GLM/Z.ai API endpoints
$env:ANTHROPIC_BASE_URL = 'https://api.z.ai/api/anthropic'
$env:ANTHROPIC_AUTH_TOKEN = '2cad921721204afc94eb39f25dc1ac0a.7rcNIxBWcuWkaJck'
$env:ZAI_API_KEY = 'your_zai_api_key_here'

# Model selection: GLM-4 or GLM-5 family
if ($Model -eq '5') {
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL = 'glm-4.7'
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL = 'glm-5.1'
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = 'glm-4.5-air'
    $selectedFamily = 'GLM-5.1'
} else {
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL = 'glm-4.7'
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL = 'glm-5'
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = 'glm-4.5-air'
    $selectedFamily = 'GLM-4'
}

Write-Host ([char]0xD83D + [char]0xDD27 + ' Configuration:') -ForegroundColor Yellow
Write-Host '   - Provider:             GLM/Z.ai' -ForegroundColor White
Write-Host ('   - Opus:                 ' + $env:ANTHROPIC_DEFAULT_OPUS_MODEL) -ForegroundColor White
Write-Host ('   - Sonnet:               ' + $env:ANTHROPIC_DEFAULT_SONNET_MODEL) -ForegroundColor White
Write-Host ('   - Haiku:                ' + $env:ANTHROPIC_DEFAULT_HAIKU_MODEL) -ForegroundColor White
Write-Host ''
