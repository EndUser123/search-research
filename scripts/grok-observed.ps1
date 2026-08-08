# grok-observed.ps1 — Wrapper that captures streaming-json for skill-load observation.
#
# Usage:
#   P:\scripts\grok-observed.ps1 "your prompt here"
#   P:\scripts\grok-observed.ps1 "your prompt" -NoObserve  # skip observation
#
# Creates a wrapper-owned run identity, launches Grok in streaming-json mode,
# captures stdout, parses observations, and persists them.
# Does NOT replace the normal grok launcher.
# Does NOT modify config.toml or routing behavior.

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$Prompt,

    [switch]$NoObserve,

    [string]$GrokBinary = "C:\Users\brsth\.grok\bin\grok.exe",

    [string]$ObservationRoot = "P:\artifacts\routing-observations",

    [string]$PilotCode = "P:\tmp\pilot\routing-streaming-pilot"
)

# Prevent native command stderr from causing terminating errors
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false

# --- Create wrapper-owned run identity ---
$runId = [System.Guid]::NewGuid().ToString("N").Substring(0, 16)
$createdAt = (Get-Date).ToUniversalTime().ToString("o")
$runDir = Join-Path $ObservationRoot "runs\$runId"

if (-not $NoObserve) {
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
}

# --- Hash the prompt (do not store prompt text by default) ---
$promptBytes = [System.Text.Encoding]::UTF8.GetBytes($Prompt)
$sha256 = [System.Security.Cryptography.SHA256]::Create()
$promptHash = [System.BitConverter]::ToString($sha256.ComputeHash($promptBytes)).Replace("-", "").ToLower()

# --- Binary hash ---
$binaryHash = (Get-FileHash $GrokBinary -Algorithm SHA256).Hash
$binaryVersion = (& $GrokBinary --version 2>$null | Select-Object -First 1)

# --- Set process-scoped OTEL variables ---
$otelActive = $false
if (-not $NoObserve) {
    $env:GROK_EXTERNAL_OTEL = "1"
    $env:OTEL_LOGS_EXPORTER = "otlp"
    $env:OTEL_METRICS_EXPORTER = "otlp"
    $env:OTEL_LOG_TOOL_DETAILS = "1"
    $env:OTEL_EXPORTER_OTLP_PROTOCOL = "http/protobuf"
    $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://127.0.0.1:4318"
    $env:OTEL_EXPORTER_OTLP_LOGS_ENDPOINT = "http://127.0.0.1:4318/v1/logs"
    $env:OTEL_EXPORTER_OTLP_METRICS_ENDPOINT = "http://127.0.0.1:4318/v1/metrics"
    $env:OTEL_LOGS_EXPORT_INTERVAL = "1000"
    $env:OTEL_METRIC_EXPORT_INTERVAL = "5000"
    $otelActive = $true
}

# --- Launch Grok in streaming-json mode ---
$streamingPath = Join-Path $runDir "streaming.jsonl"
$otelPath = Join-Path $runDir "otel.jsonl"
$startedAt = (Get-Date).ToUniversalTime().ToString("o")

# Capture OTLP if receiver is running (fail-open if not)
$otelCaptured = $false
if ($otelActive) {
    # Try to capture OTLP to a local file (receiver must be running)
    $otelCaptured = $true  # best-effort; receiver handles capture
}

$stderrPath = Join-Path $runDir "stderr.txt"
$childPid = 0

try {
    # Use the & call operator for reliable $LASTEXITCODE and stdout capture.
    # Redirect stderr to file (avoids 2>&1 merge that corrupts streaming JSON).
    $output = & $GrokBinary --single $Prompt --output-format streaming-json 2>$stderrPath
    $exitCode = $LASTEXITCODE
    $stderrContent = if (Test-Path $stderrPath) { Get-Content $stderrPath -Raw -Encoding UTF8 } else { "" }
    # Child PID: query for the most recent grok.exe process as best-effort
    $grokProc = Get-Process -Name "grok" -ErrorAction SilentlyContinue | Select-Object -First 1
    $childPid = if ($grokProc) { $grokProc.Id } else { 0 }
} catch {
    $exitCode = 1
    $output = ""
    $stderrContent = $_.Exception.Message
}

$completedAt = (Get-Date).ToUniversalTime().ToString("o")

# --- Save streaming output ---
if (-not $NoObserve) {
    $output | Set-Content -Path $streamingPath -Encoding UTF8

    # Save stderr separately (does not corrupt streaming.jsonl)
    if ($stderrContent) {
        $stderrContent | Set-Content -Path $stderrPath -Encoding UTF8
    }

    # --- Write run manifest ---
    $manifest = @{
        observation_run_id = $runId
        created_at = $createdAt
        wrapper_version = "2.0"
        grok_binary_path = $GrokBinary
        grok_binary_sha256 = $binaryHash
        grok_binary_version = $binaryVersion
        grok_process_id = $childPid
        command_hash = $promptHash
        prompt_sha256 = $promptHash
        streaming_output_path = $streamingPath
        stderr_output_path = $stderrPath
        exit_code = $exitCode
        started_at = $startedAt
        completed_at = $completedAt
        observation_active = $true
    }
    $manifest | ConvertTo-Json | Set-Content -Path (Join-Path $runDir "run-manifest.json") -Encoding UTF8

    # --- Parse observations ---
    $observerScript = Join-Path $PilotCode "observe_run.py"
    if (Test-Path $observerScript) {
        & python $observerScript $runDir 2>$null
    }

    Write-Host "Observation run: $runId" -ForegroundColor Cyan
    Write-Host "Streaming output: $streamingPath" -ForegroundColor Gray
    Write-Host "Exit code: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
}

# --- Preserve and return Grok's exit code ---
exit $exitCode
