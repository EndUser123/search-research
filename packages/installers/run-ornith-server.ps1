# Ornith-1.0-9B (Q4_K_M) on llama.cpp + CUDA 12.8 (RTX 5070, sm_120)
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;$env:PATH"
$bin = "P:\packages\.github_repos\llama.cpp\build\bin"
$model = "P:\packages\models\ornith-1.0-9b-Q4_K_M.gguf"
$watcherScript = "P:\packages\installers\watch-system.ps1"
$watcherLog   = "P:\packages\installers\system_watch.log"
$modelStateFile = "P:\.claude\state\local-model-state.json"
$endpoint = "http://127.0.0.1:8010"
$modelId = "ornith-1.0-9b"

# --- Parse n_ctx_slot from llama-server stdout and write local-model-state.json ---
# Called by Start-CCRProcess / cc-ccr.ps1 after llama-server is known to be up.
# Reads the server log (or health endpoint) to extract runtime context size,
# then writes a multi-model-ready JSON file for ccr-custom-router.js.
function Update-LocalModelState {
  param([string]$ServerUrl = $endpoint)

  # Try /health first (fast, structured)
  try {
    $health = Invoke-RestMethod -Uri "$ServerUrl/health" -TimeoutSec 3 -ErrorAction Stop
    # llama-server /health returns { status: "ok", slots: [...] } or similar
    # The exact schema varies by build; fall through to log parsing if missing
  } catch {}

  # Parse from llama-server process output (most reliable for n_ctx_slot)
  $nCtx = $null
  $proc = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue |
    Where-Object {
      try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction Stop).CommandLine
        $cmd -match "ornith|8010"
      } catch { $false }
    } | Select-Object -First 1

  if ($proc) {
    # Read stderr/stdout log if redirected; otherwise parse from command line -c value
    try {
      $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
      if ($cmdLine -match '(?:-c|--ctx-size)\s+(\d+)') {
        $nCtx = [int]$Matches[1]
      }
    } catch {}
  }

  # Write state file (multi-model-ready schema)
  $now = (Get-Date).ToString("o")
  $state = if ($nCtx) {
    @{
      models = @(@{
        id = $modelId
        endpoint = $endpoint
        maxContextTokens = $nCtx
        started_at = $now
      })
      active_model = $modelId
      updated_at = $now
    }
  } else {
    @{
      models = @()
      active_model = $null
      updated_at = $now
      error = "n_ctx_slot not detected — llama-server may not be running"
    }
  }

  $state | ConvertTo-Json -Depth 5 | Set-Content -Path $modelStateFile -Encoding UTF8
  Write-Host "[local-model-state] Written to $modelStateFile (maxContextTokens=$nCtx)"
}

# Start system-watcher in background (hidden PowerShell window)
Remove-Item $watcherLog -ErrorAction SilentlyContinue
$watcher = Start-Process powershell.exe -ArgumentList "-NoProfile -File `"$watcherScript`"" -WindowStyle Hidden -PassThru
Write-Host "System watcher started (PID $($watcher.Id)) — log: $watcherLog"

Write-Host "Starting llama-server with Ornith-1.0-9B on $endpoint"
Write-Host "Press Ctrl+C to stop."

try {
  & "$bin\llama-server.exe" -m "$model" -ngl 99 -c 65536 -t 6 --parallel 1 -fa on -ctk q4_0 -ctv q4_0 -b 2048 -ub 1024 --reasoning-preserve --jinja --temp 0.6 --top-p 0.95 --top-k 20 --host 127.0.0.1 --port 8010
}
finally {
  # Update local model state on exit (mark as stopped)
  $stopState = @{
    models = @()
    active_model = $null
    updated_at = (Get-Date).ToString("o")
  }
  $stopState | ConvertTo-Json -Depth 5 | Set-Content -Path $modelStateFile -Encoding UTF8
  Write-Host "[local-model-state] Cleared (server stopped)"

  # Stop watcher when server exits
  if ($watcher -and !$watcher.HasExited) {
    $watcher.Kill() | Out-Null
    Write-Host "System watcher stopped."
  }
}
