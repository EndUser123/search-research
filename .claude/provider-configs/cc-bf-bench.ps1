# Bifrost Route Benchmark (PS7 Optimized)
# Usage: & "P:\.claude\provider-configs\cc-bf-bench.ps1"

param(
    [string]$Prompt = "Explain why a timestamp with timezone is more accurate than one without. Be specific and give an example where the difference matters."
)

# Load secrets if available, else fallback
$envPath = "P:\.claude\provider-configs\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
$apiKey = $env:BIFROST_API_KEY ?? "sk-bf-99f7318e-ad10-4ae0-8669-d9e874661853"
$port = if ($env:BIFROST_HTTP_PORT) { $env:BIFROST_HTTP_PORT } else { "8080" }
if ($env:BIFROST_BASE_URL) {
    $baseUrl = $env:BIFROST_BASE_URL.TrimEnd('/')
    if ($baseUrl -notmatch '/anthropic$') {
        $baseUrl = "$baseUrl/anthropic"
    }
} else {
    $baseUrl = "http://localhost:$port/anthropic"
}

$routes = @(
    @{ Name = "M27";                    Model = "MiniMax-M2.7" },
    @{ Name = "GLM-5.1";                Model = "glm-5.1" },
    @{ Name = "DSv4-flash";             Model = "Nvidia-Deepseek-v4-flash" },
    @{ Name = "or-ling-2.6-1t";         Model = "OpenRouter-ling-2.6-1t" },
    @{ Name = "or-hy3-preview";         Model = "OpenRouter-hy3-preview" },
    @{ Name = "or-devstral";            Model = "OpenRouter-devstral" },
    @{ Name = "step-3.5-flash";         Model = "Nvidia-step-3.5-flash" },
    @{ Name = "gemini-3.1-flash-lite";  Model = "Gemini-3.1-flash-lite" },
    @{ Name = "gemini-3.1-flash";       Model = "Gemini-3.1-flash" },
    @{ Name = "gemini-3.1-pro";         Model = "Gemini-3.1-pro" },
    @{ Name = "gh-gpt-5-mini";          Model = "GitHub-gpt-5-mini" },
    @{ Name = "or-gemma-4-31b";         Model = "OpenRouter-gemma-4-31b" },
    @{ Name = "or-qwen3-coder";         Model = "OpenRouter-qwen3-coder" }
)

Write-Host "`nBifrost Route Benchmark" -ForegroundColor Yellow
$preview = if ($Prompt.Length -gt 80) { $Prompt.Substring(0, 80) + "..." } else { $Prompt }
Write-Host "   Prompt ($($Prompt.Length) chars): $preview`n" -ForegroundColor DarkGray
Write-Host "Starting parallel benchmark of $($routes.Count) routes (Runspace Pool)..." -ForegroundColor Cyan

$startTime = Get-Date

# PS7 Native Parallelism (Near-zero overhead)
$results = $routes | ForEach-Object -Parallel {
    $route = $_
    $body = @{
        model = $route.Model
        max_tokens = 512
        messages = @( @{ role = "user"; content = $using:Prompt } )
    } | ConvertTo-Json -Compress

    $headers = @{
        "x-api-key" = $using:apiKey
        "Content-Type" = "application/json"
        "anthropic-version" = "2023-06-01"
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-WebRequest -Uri "$($using:baseUrl)/v1/messages" -Method POST -Headers $headers -Body $body -TimeoutSec 90
        $sw.Stop()
        $content = $resp.Content | ConvertFrom-Json | Select-Object -ExpandProperty content -First 1
        $outputLen = if ($content) { $content[0].text.Length } else { 0 }

        @{ Name = $route.Name; Success = $true; Elapsed = $sw.ElapsedMilliseconds; OutputLen = $outputLen; Error = $null }
    } catch {
        $sw.Stop()
        @{ Name = $route.Name; Success = $false; Elapsed = $sw.ElapsedMilliseconds; OutputLen = 0; Error = $_.Exception.Message }
    }
} -ThrottleLimit 15

$totalTime = ((Get-Date) - $startTime).TotalSeconds
$sorted = $results | Sort-Object { $_.Elapsed }

Write-Host "`n==============================================================" -ForegroundColor Yellow
Write-Host "RESULTS (sorted by speed, fastest first)" -ForegroundColor Yellow
Write-Host "==============================================================`n" -ForegroundColor Yellow

$rank = 1
foreach ($r in $sorted) {
    if ($r.Success) {
        Write-Host ("#{0,2}  {1,-32}  {2}ms" -f $rank, $r.Name, $r.Elapsed) -ForegroundColor Green
    } else {
        Write-Host ("#{0,2}  {1,-32}  {2}ms  ({3})" -f $rank, $r.Name, $r.Elapsed, $r.Error) -ForegroundColor Red
    }
    $rank++
}

Write-Host "`nTotal benchmark time: $([Math]::Round($totalTime, 1)) seconds" -ForegroundColor DarkGray

$successful = $results | Where-Object { $_.Success }
if ($successful.Count -gt 0) {
    $avgVal = [Math]::Round(($successful | Measure-Object -Property Elapsed -Average).Average, 0)
    $minVal = ($successful | Measure-Object -Property Elapsed -Minimum).Minimum
    $maxVal = ($successful | Measure-Object -Property Elapsed -Maximum).Maximum

    Write-Host "`nSummary: $($successful.Count) / $($results.Count) routes responded successfully" -ForegroundColor Cyan
    Write-Host "  Average: ${avgVal}ms  |  Fastest: ${minVal}ms  |  Slowest: ${maxVal}ms`n" -ForegroundColor Cyan
}
