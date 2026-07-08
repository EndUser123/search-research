# Ornith-1.0-9B (Q4_K_M) on llama.cpp + CUDA 12.8 (RTX 5070, sm_120)
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;$env:PATH"
$bin = "P:\packages\.github_repos\llama.cpp\build\bin"
$model = "P:\packages\models\ornith-1.0-9b-Q4_K_M.gguf"
$watcherScript = "P:\packages\installers\watch-system.ps1"
$watcherLog   = "P:\packages\installers\system_watch.log"
$modelStateFile = "P:\.claude\state\local-model-state.json"
$llamaLog      = "P:\packages\installers\ornith-server.log"
$endpoint = "http://127.0.0.1:8010"
$modelId = "ornith-1.0-9b"

# --- Update local-model-state.json from llama-server's actual runtime output ---
# llama-server prints startup log lines including the EFFECTIVE `n_ctx_slot`
# (after n_parallel division). That value is the routing truth, not the
# `-c` flag (which sets total n_ctx). We capture the log and parse it.
#
# Sources of n_ctx (in priority order):
#   1. llama-server stdout (captured to $llamaLog) - printed as "n_ctx_slot = 65536"
#   2. llama-server /health structured endpoint (if available)
#   3. process command line `-c N` or `--ctx-size N` (proxy only)
function Update-LocalModelState {
  param([string]$ServerUrl = $endpoint)

  $nCtxSlot = $null
  $source = "none"

  # Source 1: parse from captured llama-server log (most authoritative)
  if ((Test-Path $llamaLog) -and ((Get-Item $llamaLog).Length -gt 0)) {
    try {
      # llama-server typically prints:
      #   "slot 0: prompt eval time =     x ms /    N tokens (   0.0 tokens per request)"
      # and the context size is reported as "n_ctx" or "n_ctx_slot".
      # Match the literal substring exactly.
      $logContent = Get-Content $llamaLog -Raw -ErrorAction Stop
      # Look for "n_ctx = N", "n_ctx_slot = N", or "context size = N"
      $patterns = @(
        'n_ctx_slot\s*=\s*(\d+)',
        'n_ctx\s*=\s*(\d+)\s',
        'context size\s*=\s*(\d+)',
        'set\s+threads,\s*n_ctx\s*=\s*(\d+)'
      )
      foreach ($pat in $patterns) {
        if ($logContent -match $pat) {
          $nCtxSlot = [int]$Matches[1]
          $source = "llama-server log: $pat"
          break
        }
      }
    } catch {}
  }

  # Source 2: process command line as fallback (proxy only, may mislead if --parallel > 1)
  if (-not $nCtxSlot) {
    try {
      $proc = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($proc) {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)" -ErrorAction Stop).CommandLine
        if ($cmdLine -match '(?:-c|--ctx-size)\s+(\d+)') {
          $nCtxSlot = [int]$Matches[1]
          $source = "process command line (proxy)"
        }
      }
    } catch {}
  }

  # Write state file (multi-model-ready schema)
  $now = (Get-Date).ToString("o")
  if ($nCtxSlot) {
    $state = @{
      models = @(@{
        id = $modelId
        endpoint = $endpoint
        maxContextTokens = $nCtxSlot
        source = $source
        started_at = $now
      })
      active_model = $modelId
      updated_at = $now
    }
  } else {
    $state = @{
      models = @()
      active_model = $null
      updated_at = $now
      error = "n_ctx not detected - checked llama-server log and process command line"
    }
  }

  $state | ConvertTo-Json -Depth 5 | Set-Content -Path $modelStateFile -Encoding UTF8
  Write-Host "[local-model-state] maxContextTokens=$nCtxSlot (source: $source)"
  Write-Host "[local-model-state] Written to $modelStateFile"
}

# --- Idempotency guard: never launch a duplicate llama-server on :8010 ---
# If a healthy server is already bound (manual launch, prior cc-ccr session, or
# a cc-ccr probe false-negative that re-invoked this script), report it and
# exit 0 WITHOUT spawning a second process or poisoning local-model-state.json.
# A blind second launch fails to bind :8010, crashes, and its finally{} block
# would mark the (still-running) original as stopped.
# Use TcpClient (not IWR) for consistency with cc-ccr.ps1 — IWR can fail inside
# dot-sourced profile sessions, causing this guard to falsely fall through.
try {
  $tcpCheck = [System.Net.Sockets.TcpClient]::new()
  $tcpCheck.SendTimeout = 1500
  $tcpCheck.ReceiveTimeout = 1500
  $tcpCheck.Connect('127.0.0.1', 8010)
  if ($tcpCheck.Connected) {
    $tcpCheck.Close(); $tcpCheck.Dispose()
    Write-Host "[run-ornith] llama-server already healthy at $endpoint - not launching a duplicate." -ForegroundColor Green
    Update-LocalModelState
    exit 0
  }
  $tcpCheck.Dispose()
} catch {
  if ($tcpCheck) { $tcpCheck.Dispose() }
  # Port not listening yet - fall through to normal launch.
}

# Start system-watcher in background (hidden PowerShell window)
Remove-Item $watcherLog -ErrorAction SilentlyContinue
Remove-Item $llamaLog -ErrorAction SilentlyContinue
$watcher = Start-Process pwsh.exe -ArgumentList "-NoProfile -File `"$watcherScript`"" -WindowStyle Hidden -PassThru
Write-Host "System watcher started (PID $($watcher.Id)) - log: $watcherLog"

Write-Host "Starting llama-server with Ornith-1.0-9B on $endpoint"
Write-Host "Log: $llamaLog"
Write-Host "Press Ctrl+C to stop."

# Launch llama-server in background with stdout/stderr captured to file.
# Run in foreground would lose the log; tee via Start-Process preserves both.
$llamaArgs = @("-m", "$model", "-ngl", "99", "-c", "65536", "-t", "6",
               "--parallel", "1", "-fa", "on", "-ctk", "q4_0", "-ctv", "q4_0",
               "-b", "2048", "-ub", "1024", "--reasoning-preserve", "--jinja",
               "--temp", "0.6", "--top-p", "0.95", "--top-k", "20",
               "--host", "127.0.0.1", "--port", "8010")

$crashCount = 0
$lastStartTime = $null
try {
  while ($true) {
    # Clear per-restart log so watchdog tail shows only the latest run
    Remove-Item "$llamaLog.err" -ErrorAction SilentlyContinue

    $procHandle = Start-Process -FilePath "$bin\llama-server.exe" `
                                -ArgumentList $llamaArgs `
                                -RedirectStandardOutput $llamaLog `
                                -RedirectStandardError "$llamaLog.err" `
                                -NoNewWindow -PassThru -WorkingDirectory (Split-Path $bin)
    $lastStartTime = Get-Date
    Write-Host "llama-server started (PID $($procHandle.Id))"

    # Wait for the server to be reachable, then update local-model-state
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
      Start-Sleep -Seconds 1
      try {
        $r = Invoke-WebRequest -Uri "$endpoint/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
          $ready = $true
          Write-Host "llama-server health OK after ${i}s"
          break
        }
      } catch {}
    }
    if ($ready) {
      Update-LocalModelState
    } else {
      # Startup failure - kill the orphaned process before retry to free the port
      if ($procHandle -and -not $procHandle.HasExited) {
        Stop-Process -Id $procHandle.Id -Force -ErrorAction SilentlyContinue
      }
      $crashCount++
      if ($crashCount -ge 3) {
        Write-Warning "[run-ornith] 3 consecutive startup failures - giving up"
        break
      }
      Write-Warning "[run-ornith] startup failed, retrying in 5s (attempt $($crashCount + 1)/3)"
      Start-Sleep -Seconds 5
      continue
    }

    # Block until llama-server exits (crash or manual stop)
    Wait-Process -Id $procHandle.Id -ErrorAction SilentlyContinue

    # If the server ran for more than 60s, consider it a stable session - reset crash counter
    $ranSecs = if ($lastStartTime) { ((Get-Date) - $lastStartTime).TotalSeconds } else { 0 }
    if ($ranSecs -gt 60) {
      $crashCount = 0
    } else {
      $crashCount++
    }

    if ($crashCount -ge 3) {
      Write-Warning "[run-ornith] 3 rapid crashes (${ranSecs}s avg) - giving up"
      break
    }

    Write-Warning "[run-ornith] llama-server exited after ${ranSecs}s (PID $($procHandle.Id)). Restarting in 3s... (attempt $($crashCount + 1)/3)"
    Start-Sleep -Seconds 3
  }
} finally {
  # Update local model state on exit (mark as stopped)
  $stopState = @{
    models = @()
    active_model = $null
    updated_at = (Get-Date).ToString("o")
    error = "llama-server stopped"
  }
  $stopState | ConvertTo-Json -Depth 5 | Set-Content -Path $modelStateFile -Encoding UTF8
  Write-Host "[local-model-state] Cleared (server stopped)"

  # Stop watcher when server exits
  if ($watcher -and !$watcher.HasExited) {
    $watcher.Kill() | Out-Null
    Write-Host "System watcher stopped."
  }
}
