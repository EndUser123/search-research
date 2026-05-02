# Bifrost Route Benchmark
# Usage: & "P:\.claude\provider-configs\cc-bf-bench.ps1"
# Or add to profile: function cc-bf-bench { & "P:\.claude\provider-configs\cc-bf-bench.ps1" @Args }

param(
    [string]$Prompt = "Explain why a timestamp with timezone is more accurate than one without. Be specific and give an example where the difference matters."
)

$ANTHROPIC_BASE_URL = "http://localhost:8081/anthropic"
$ANTHROPIC_API_KEY = "sk-bf-99f7318e-ad10-4ae0-8669-d9e874661853"

$routes = @(
    @{ Name = "M27";                    Model = "MiniMax-M2.7" },
    @{ Name = "GLM-5.1";                Model = "glm-5.1" },
    @{ Name = "DSv4-flash";             Model = "Nvidia-Deepseek-v4-flash" },
    @{ Name = "or-ling-2.6-1t";         Model = "OpenRouter-ling-2.6-1t" },
    @{ Name = "or-hy3-preview";          Model = "OpenRouter-hy3-preview" },
    @{ Name = "or-devstral";             Model = "OpenRouter-devstral" },
    @{ Name = "step-3.5-flash";          Model = "Nvidia-step-3.5-flash" },
    @{ Name = "gemini-3.1-flash-lite";   Model = "Gemini-3.1-flash-lite" },
    @{ Name = "gemini-3.1-flash";        Model = "Gemini-3.1-flash" },
    @{ Name = "gemini-3.1-pro";          Model = "Gemini-3.1-pro" },
    @{ Name = "gh-gpt-5-mini";           Model = "GitHub-gpt-5-mini" },
    @{ Name = "or-gemma-4-31b";          Model = "OpenRouter-gemma-4-31b" },
    @{ Name = "or-qwen3-coder";          Model = "OpenRouter-qwen3-coder" }
)

Write-Host ""
Write-Host "Bifrost Route Benchmark" -ForegroundColor Yellow
$pLen = $Prompt.Length
if ($pLen -gt 80) { $preview = $Prompt.Substring(0, 80) + "..." } else { $preview = $Prompt }
Write-Host "   Prompt ($pLen chars): $preview" -ForegroundColor DarkGray
Write-Host ""

Write-Host "Starting parallel benchmark of" $routes.Count "routes..." -ForegroundColor Cyan

$jobs = @()
foreach ($route in $routes) {
    $job = Start-Job -Name "bench-$($route.Name)" -ScriptBlock {
        param($model, $prompt, $baseUrl, $apiKey)

        $body = @{
            model = $model
            max_tokens = 512
            messages = @(
                @{ role = "user"; content = $prompt }
            )
        } | ConvertTo-Json -Compress

        $headers = @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
            "anthropic-version" = "2023-06-01"
        }

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $resp = Invoke-WebRequest -Uri "$baseUrl/v1/messages" -Method POST -Headers $headers -Body $body -TimeoutSec 90
            $sw.Stop()
            $elapsed = $sw.ElapsedMilliseconds
            $status = $resp.StatusCode
            $content = $resp.Content | ConvertFrom-Json | Select-Object -ExpandProperty content -First 1
            $outputLen = if ($content) { $content[0].text.Length } else { 0 }
            return @{ Name = $model; Success = $true; Elapsed = $elapsed; Status = $status; OutputLen = $outputLen; Error = $null }
        } catch {
            $sw.Stop()
            return @{ Name = $model; Success = $false; Elapsed = $sw.ElapsedMilliseconds; Status = 0; OutputLen = 0; Error = $_.Exception.Message }
        }
    } -ArgumentList $route.Model, $Prompt, $ANTHROPIC_BASE_URL, $ANTHROPIC_API_KEY

    $jobs += @{ Job = $job; Name = $route.Name; Model = $route.Model }
}

$startTime = Get-Date
$prevRunning = -1

while (($jobs | Where-Object { $_.Job.State -eq 'Running' }).Count -gt 0) {
    Start-Sleep -Milliseconds 500
    $running = ($jobs | Where-Object { $_.Job.State -eq 'Running' }).Count
    if ($running -ne $prevRunning) {
        $done = $jobs.Count - $running
        Write-Host "  $done/$($jobs.Count) done, $running running..." -ForegroundColor DarkGray
        $prevRunning = $running
    }
}

Write-Host "Collecting results..." -ForegroundColor DarkGray

$results = @()
foreach ($j in $jobs) {
    $data = Receive-Job -Job $j.Job -Keep
    $results += $data
    Remove-Job -j.Job -Force
}

$totalTime = ((Get-Date) - $startTime).TotalSeconds

$sorted = $results | Sort-Object { $_.Elapsed }

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "RESULTS (sorted by speed, fastest first)" -ForegroundColor Yellow
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host ""

$rank = 1
foreach ($r in $sorted) {
    if ($r.Success) {
        $timeStr = "$($r.Elapsed)ms"
        $lenStr = "$($r.OutputLen) chars"
        $color = "Green"
    } else {
        $timeStr = "$($r.Elapsed)ms"
        $lenStr = "-"
        $color = "Red"
        if ($r.Error) { $timeStr = "$timeStr  $($r.Error)" }
    }
    $namePadded = $r.Name.PadRight(32)
    Write-Host ("#{0,2}  {1}  {2}" -f $rank, $namePadded, $timeStr) -ForegroundColor $color
    $rank++
}

Write-Host ""
Write-Host "Total benchmark time:" ([Math]::Round($totalTime, 1)) "seconds" -ForegroundColor DarkGray
Write-Host ""

$successful = $results | Where-Object { $_.Success }
if ($successful.Count -gt 0) {
    $avgVal = ($successful | Measure-Object -Property Elapsed -Average).Average
    $minVal = ($successful | Measure-Object -Property Elapsed -Minimum).Minimum
    $maxVal = ($successful | Measure-Object -Property Elapsed -Maximum).Maximum
    $avgStr = [Math]::Round($avgVal, 0).ToString() + "ms"
    $minStr = $minVal.ToString() + "ms"
    $maxStr = $maxVal.ToString() + "ms"
    Write-Host "Summary:" $successful.Count "/" $results.Count "routes responded successfully" -ForegroundColor Cyan
    Write-Host "  Average: $avgStr  |  Fastest: $minStr  |  Slowest: $maxStr" -ForegroundColor Cyan
}

Write-Host ""