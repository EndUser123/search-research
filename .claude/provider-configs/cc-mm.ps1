param(
    [switch]$GetTestCommands
)

# MiniMax LLM Proxy Configuration Script
# Usage: .\cc-mm.ps1

if ($GetTestCommands) {
    [PSCustomObject]@{
        Description = 'Test MiniMax Claude Code Integration'
        Executable  = 'curl.exe'
        Arguments   = @(
            '-s',
            '-X', 'POST',
            'https://api.minimax.io/anthropic/v1/messages',
            '-H', 'Content-Type: application/json',
            '-H', 'Authorization: Bearer $env:ANTHROPIC_AUTH_TOKEN',
            '-d', '{"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
        )
    }
    return
}

# Set MiniMax API endpoints
$env:ANTHROPIC_BASE_URL   = 'https://api.minimax.io/anthropic'
$env:ANTHROPIC_AUTH_TOKEN = 'sk-cp-KaSmY8e9E1Pw9XbCWOiVexNvnLGwmKJ8fBGf57gEvA3fb95gq73n7AGVyIL3zBrjvFzxRQFyocfa8QdgborzQoupFzI0UX5cjw7MCkIY3DCy5-kAFVza5z8'

# MiniMax model mapping
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = 'MiniMax-M2.7'
$env:ANTHROPIC_DEFAULT_OPUS_MODEL   = 'MiniMax-M2.7'
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL  = 'MiniMax-M2.7'

Write-Host ([char]0xD83D + [char]0xDD27 + ' Configuration:') -ForegroundColor Yellow
Write-Host '   - Provider:             MiniMax' -ForegroundColor White
Write-Host ('   - Opus:                 ' + $env:ANTHROPIC_DEFAULT_OPUS_MODEL) -ForegroundColor White
Write-Host ('   - Sonnet:               ' + $env:ANTHROPIC_DEFAULT_SONNET_MODEL) -ForegroundColor White
Write-Host ('   - Haiku:                ' + $env:ANTHROPIC_DEFAULT_HAIKU_MODEL) -ForegroundColor White
Write-Host ''
