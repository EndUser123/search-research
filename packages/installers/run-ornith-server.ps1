# Ornith-1.0-9B (Q4_K_M) on llama.cpp + CUDA 12.8 (RTX 5070, sm_120)
param([switch]$Probe, [switch]$IncludeInference)
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;$env:PATH"
$bin = "P:\packages\.github_repos\llama.cpp\build\bin"
$model = "P:\packages\models\ornith-1.0-9b-Q4_K_M.gguf"
$watcherScript = "P:\packages\installers\watch-system.ps1"
$watcherLog   = "P:\packages\installers\system_watch.log"
$monitorScript = "P:\packages\installers\ornith-monitor.py"
$modelStateFile = "P:\.claude\state\local-model-state.json"
$llamaLog      = "P:\packages\installers\ornith-server.log"
$endpoint = "http://127.0.0.1:8010"
$modelId = "ornith-1.0-9b"
# Crash dossiers — one JSON per llama-server exit, written so the next crash is
# actually investigable. See P:\packages\installers\LLAMA-CRASH-RCA.md.
$crashDir = "P:\.claude\state\local-model-crashes"
$routeLog = "P:\.claude\state\ccr-route-log.jsonl"
$runbookPath = "P:\packages\installers\LLAMA-CRASH-RCA.md"

# --- Readiness probe: 5-rung ladder (cheap -> expensive, short-circuit) -------
# Single source of truth for "is the local model usable." Returns:
#   DEAD     no llama-server process
#   STUCK    process alive, port not bound (zombie)
#   BROKEN   port open, /health or /v1/models failing
#   LOADING  /health ok, GGUF not loaded yet (/v1/models empty)
#   LOADED   GGUF loaded, inference NOT probed (liveness only)
#   READY    loaded + inference produces tokens (full readiness)
#   HUNG     loaded, inference fails / 0 tokens (deadlock, GPU OOM, corruption)
#
# -IncludeInference adds rung 5. WITHOUT it, a loaded model returns LOADED —
# safe for the watchdog to poll without colliding with real requests under
# --parallel 1 (a 15s inference probe mid-generation would false-positive HUNG
# and kill a healthy busy server).
function Get-LocalModelState {
  param(
    [string]$Endpoint = $endpoint,
    [int]$Port = 8010,
    [int]$TcpMs = 1500,
    [switch]$IncludeInference
  )

  # Rung 1: PROCESS
  $procs = @(Get-Process -Name "llama-server" -ErrorAction SilentlyContinue)
  if ($procs.Count -eq 0) {
    return @{ state = "DEAD"; pids = @(); model = $null; detail = "no llama-server process" }
  }

  # Rung 2: PORT (TCP connect — closed port fails in <1ms)
  $tcp = $null
  $portOpen = $false
  try {
    $tcp = [System.Net.Sockets.TcpClient]::new()
    $tcp.SendTimeout = $TcpMs; $tcp.ReceiveTimeout = $TcpMs
    $tcp.Connect('127.0.0.1', $Port)
    $portOpen = $tcp.Connected
  } catch {}
  finally { if ($tcp) { try { $tcp.Close() } catch {}; try { $tcp.Dispose() } catch {} } }
  if (-not $portOpen) {
    return @{ state = "STUCK"; pids = $procs.Id; model = $null; detail = "process alive, port $Port not bound (zombie)" }
  }

  # Rung 3: HEALTH (/health 2xx)
  try {
    Invoke-RestMethod -Uri "$Endpoint/health" -TimeoutSec 3 -ErrorAction Stop | Out-Null
  } catch {
    return @{ state = "BROKEN"; pids = $procs.Id; model = $null; detail = "port open, /health failed" }
  }

  # Rung 4: MODEL (GGUF loaded — /v1/models non-empty). This is the signal /health
  # can't give: llama-server answers /health while the GGUF is still mmap'ing.
  $loaded = $null
  try {
    $m = Invoke-RestMethod -Uri "$Endpoint/v1/models" -TimeoutSec 3 -ErrorAction Stop
    if ($m.data) { $loaded = @($m.data)[0].id }
  } catch {
    return @{ state = "BROKEN"; pids = $procs.Id; model = $null; detail = "/health ok, /v1/models failed" }
  }
  if (-not $loaded) {
    return @{ state = "LOADING"; pids = $procs.Id; model = $null; detail = "GGUF not loaded yet (/v1/models empty)" }
  }

  # Rung 5: INFERENCE (opt-in). Gate on completion_tokens > 0, not content —
  # reasoning-preserve models emit tokens into reasoning_content first.
  if (-not $IncludeInference) {
    return @{ state = "LOADED"; pids = $procs.Id; model = $loaded; detail = "loaded (inference not probed)" }
  }
  try {
    $body = @{ model = $loaded; messages = @(@{ role = "user"; content = "hi" }); max_tokens = 8; temperature = 0; stream = $false } | ConvertTo-Json -Compress -Depth 5
    $inf = Invoke-RestMethod -Uri "$Endpoint/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15 -ErrorAction Stop
    if ($inf.usage.completion_tokens -gt 0) {
      return @{ state = "READY"; pids = $procs.Id; model = $loaded; detail = "ready" }
    }
    return @{ state = "HUNG"; pids = $procs.Id; model = $loaded; detail = "loaded, 0 completion_tokens" }
  } catch {
    return @{ state = "HUNG"; pids = $procs.Id; model = $loaded; detail = "loaded, inference failed: $($_.Exception.Message)" }
  }
}

function Start-OrnithDashboard {
  if (-not (Test-Path -LiteralPath $monitorScript)) { return $null }
  $existing = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'ornith-monitor\.py' } |
    Sort-Object ProcessId)
  if ($existing.Count -gt 0) {
    # Concurrent cc-ccr starts can race between discovery and Start-Process.
    # Keep the oldest monitor and remove only exact monitor-script duplicates.
    foreach ($duplicate in @($existing | Select-Object -Skip 1)) {
      Stop-Process -Id $duplicate.ProcessId -Force -ErrorAction SilentlyContinue
    }
    return Get-Process -Id $existing[0].ProcessId -ErrorAction SilentlyContinue
  }

  $python = Get-Command python.exe -ErrorAction SilentlyContinue
  if (-not $python) { return $null }
  $pythonPath = $python.Source
  # The uv tool shim remains as a parent process while the real interpreter
  # runs the dashboard. Prefer the installed direct runtime when the shim is
  # what PATH resolves, so process ownership and taskbar identity stay one-to-
  # one with the dashboard.
  if ($pythonPath -match '\\uv\\' -and (Test-Path -LiteralPath 'C:\Python314\python.exe')) {
    $pythonPath = 'C:\Python314\python.exe'
  }
  try {
    return Start-Process -FilePath $pythonPath `
      -ArgumentList @($monitorScript, '--endpoint', $endpoint, '--state-file', $modelStateFile, '--poll-seconds', '2') `
      # The dashboard is the operator-facing window. Keep the supervisor
      # minimized, but show this window so a fresh start immediately displays
      # the STARTING/BROKEN snapshot before llama-server is loaded.
      -WindowStyle Normal -PassThru
  } catch { return $null }
}

# -Probe mode: emit state as JSON and exit. Read-only, no side effects. Lets
# cc-ccr query the launcher's health definition without re-implementing probes.
if ($Probe) {
  Get-LocalModelState -IncludeInference:$IncludeInference | ConvertTo-Json -Depth 3
  exit 0
}

# The Python dashboard is independent of the llama-server child and should be
# available even when this invocation finds an already-running server.
$dashboard = Start-OrnithDashboard
if ($dashboard) {
  Write-Host "Operator dashboard active (PID $($dashboard.Id)) - ornith-monitor.py"
}

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

# Start system-watcher in background (hidden PowerShell window).
# Kill any orphaned watchers from prior launcher runs FIRST — without this,
# each launcher restart spawns a new watcher while the old one keeps appending
# to the same file, producing a mixed-encoding corrupt log (UTF-8 header +
# UTF-16 appends from the orphan, 28% null bytes observed 2026-07-09).
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'watch-system\.ps1' -and $_.ProcessId -ne $PID } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Remove-Item $watcherLog -ErrorAction SilentlyContinue
Remove-Item $llamaLog -ErrorAction SilentlyContinue
$watcher = Start-Process pwsh.exe -ArgumentList "-NoProfile -File `"$watcherScript`"" -WindowStyle Hidden -PassThru
Write-Host "System watcher started (PID $($watcher.Id)) - log: $watcherLog"
if (-not $dashboard) {
  Write-Warning "Operator dashboard unavailable; lifecycle log remains in $llamaLog"
}

Write-Host "Starting llama-server with Ornith-1.0-9B on $endpoint"
Write-Host "Log: $llamaLog"
Write-Host "(Window stays visible+minimized so the taskbar shows live state.)"

# Set the window title once at startup — the supervisor poll below keeps it
# current. The operator-facing live display belongs to ornith-monitor.py.
$host.UI.RawUI.WindowTitle = "llama.cpp: starting…"

# Launch llama-server in background with stdout/stderr captured to file.
# Run in foreground would lose the log; tee via Start-Process preserves both.
$llamaArgs = @("-m", "$model", "-ngl", "99", "-c", "65536", "-t", "6",
               "--parallel", "1", "-fa", "on", "-ctk", "q4_0", "-ctv", "q4_0",
               "--metrics",
               "-b", "2048", "-ub", "1024", "--reasoning-preserve", "--jinja",
               "--temp", "0.6", "--top-p", "0.95", "--top-k", "20",
               "--host", "127.0.0.1", "--port", "8010")

$crashCount = 0
$lastStartTime = $null

# Write a crash dossier on every llama-server exit so the next crash is
# actually investigable. Wrapped in try/catch so a bug here can NEVER kill
# the launcher (the launcher staying up is more important than a perfect
# dossier). One JSON per exit: P:\.claude\state\local-model-crashes\<ts>.json
function Write-CrashDossier {
  param($Proc, $StartedAt, $LlamaArgs, $CrashNum)
  try {
    $ts = (Get-Date).ToString("yyyyMMdd-HHmmss")
    if (-not (Test-Path $crashDir)) { New-Item -ItemType Directory -Path $crashDir -Force | Out-Null }

    $uptime = if ($StartedAt) { [math]::Round(((Get-Date) - $StartedAt).TotalSeconds) } else { 0 }
    $exitCode = $null
    try { $exitCode = $Proc.ExitCode } catch {}

    # GPU snapshot at crash moment. May fail/hang if GPU is in a faulted state.
    $gpu = $null
    try {
      $gpu = (nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null) -split ',' | ForEach-Object { $_.Trim() }
    } catch {}

    # VRAM trajectory — last 5 watch samples (was VRAM climbing into the crash?)
    $vramTraj = @()
    try {
      if (Test-Path $watcherLog) { $vramTraj = @(Get-Content $watcherLog -Tail 5) }
    } catch {}

    # Last 3 local-bound requests (what was being processed when it died)
    $lastReq = @()
    try {
      if (Test-Path $routeLog) {
        $lastReq = @(Get-Content $routeLog -Tail 50 | Where-Object { $_ -match '"local_used":\s*true' } | Select-Object -Last 3)
      }
    } catch {}

    # Windows Event Log — GPU driver / TDR events. PRIMARY signal for a
    # GPU/driver fault (llama-server's .err often doesn't flush on hard crash).
    # EventID 4101 (source Display) = TDR recovery; 153 = driver error.
    $events = @()
    try {
      $since = (Get-Date).AddMinutes(-5)
      $events = @(Get-WinEvent -FilterHashtable @{ LogName='System'; StartTime=$since; Level=1,2,3 } -ErrorAction SilentlyContinue |
        Where-Object { $_.ProviderName -match 'nvlddmkm|Display|nvwmi|Kernel-Power|EventLog' -or $_.Id -in 4101,153,41,6008 } |
        Select-Object TimeCreated, Id, ProviderName, @{n='msg';e={ $_.Message.Substring(0, [math]::Min(300, $_.Message.Length)) } } |
        Select-Object -First 10)
    } catch {}

    # .err tail — secondary; may be empty/truncated on hard crash
    $errTail = @()
    try {
      if (Test-Path "$llamaLog.err") { $errTail = @(Get-Content "$llamaLog.err" -Tail 50) }
    } catch {}

    $dossier = [ordered]@{
      crash_ts           = $ts
      runbook            = $runbookPath
      pid                = if ($Proc) { $Proc.Id } else { $null }
      exit_code          = $exitCode
      uptime_s           = $uptime
      crash_count_session= $CrashNum
      args               = ($LlamaArgs -join ' ')
      gpu_snapshot       = if ($gpu) { [ordered]@{ vram_used_mb=$gpu[0]; vram_total_mb=$gpu[1]; gpu_util_pct=$gpu[2]; temp_c=$gpu[3]; power_w=$gpu[4] } } else { $null }
      vram_trajectory    = $vramTraj
      last_local_requests= $lastReq
      windows_events     = $events
      err_tail           = $errTail
    }
    $path = Join-Path $crashDir "$ts.json"
    $dossier | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8
    Write-Host "[run-ornith] crash dossier written: $path" -ForegroundColor Yellow
  } catch {
    try { Write-Warning "[run-ornith] dossier write failed: $($_.Exception.Message)" } catch {}
  }
}

try {
  while ($true) {
    # Archive (don't delete) the prior run's stderr so the watchdog tail shows
    # only the latest run BUT crash signatures survive for diagnosis. The old
    # Remove-Item wiped every crash log, making the 3-crash give-up (3.3h→12m→
    # startup-fail→10s) impossible to root-cause.
    if (Test-Path "$llamaLog.err") {
      $arch = "$llamaLog.err.$(Get-Date -Format yyyyMMdd-HHmmss)"
      Move-Item "$llamaLog.err" $arch -Force -ErrorAction SilentlyContinue
      # Keep only the newest 5 archives
      Get-ChildItem "$llamaLog.err.*" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -Skip 5 |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }

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
      # Capture the startup-fail dossier (the "startup-fail→10s" crash path).
      Write-CrashDossier -Proc $procHandle -StartedAt $lastStartTime -LlamaArgs $llamaArgs -CrashNum $crashCount
      $crashCount++
      if ($crashCount -ge 3) {
        Write-Warning "[run-ornith] 3 consecutive startup failures - giving up"
        Write-Warning "[run-ornith] see $runbookPath — dossiers in $crashDir"
        break
      }
      Write-Warning "[run-ornith] startup failed, retrying in 5s (attempt $($crashCount + 1)/3)"
      Start-Sleep -Seconds 5
      continue
    }

    # Block until llama-server exits OR goes unhealthy. Polls rungs 1-4 every 15s
    # (NO inference — a probe mid-generation would false-positive HUNG under
    # --parallel 1 and kill a healthy busy server). Kill+restart on STUCK/BROKEN
    # (zombie / HTTP broken). Leave LOADING/LOADED alone — those are alive.
    # Same poll also samples VRAM and updates the window title so the taskbar
    # shows live state ("llama.cpp: READY • VRAM 11451MB" / "…idle" / "…busy").
    while (-not $procHandle.HasExited) {
        Start-Sleep -Seconds 15
        if ($procHandle.HasExited) { break }
        $poll = Get-LocalModelState -Endpoint $endpoint
        # GPU sample for usage signal + taskbar title. Same data source
        # watch-system.ps1 uses; ~50ms, runs once per 15s cycle.
        $gpu = $null
        $temperature = $null
        $vram = $null
        try {
          $gpuRaw = (nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
          if ($gpuRaw) {
            $parts = $gpuRaw -split ',' | ForEach-Object { $_.Trim() }
            if ($parts.Count -ge 3) {
              [int]$gpu = $parts[0]
              [int]$temperature = $parts[1]
              [int]$vram = $parts[2]
            }
          }
        } catch {}

        try {
          $vramTitle = if ($null -ne $vram) { "${vram}MB" } else { "n/a" }
          $host.UI.RawUI.WindowTitle = "llama.cpp: $($poll.state) • $($slot.state.ToLower()) • VRAM $vramTitle"
        } catch {}

        if ($poll.state -eq "STUCK" -or $poll.state -eq "BROKEN") {
            Write-Warning "[run-ornith] watchdog: model $($poll.state) ($($poll.detail)) - killing PID $($procHandle.Id) for restart"
            Stop-Process -Id $procHandle.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            break
        }

        # Dashboard watchdog: the operator-facing ornith-monitor.py is a
        # separate child whose lifetime is not coupled to llama-server. An
        # external tree-kill (Codex taskkill /t storms, IDE restart, user
        # closing the window) can take it down without taking down
        # llama-server. Detect and respawn on the same 15s poll cycle as
        # the llama watchdog so one tree-poll covers both children.
        if ($dashboard -and $dashboard.HasExited) {
            $oldId = $dashboard.Id
            Write-Warning "[run-ornith] watchdog: dashboard PID $oldId exited - respawning"
            $dashboard = Start-OrnithDashboard
            if ($dashboard) {
                Write-Host "[run-ornith] dashboard respawned: PID $($dashboard.Id)"
            } else {
                Write-Warning "[run-ornith] dashboard respawn FAILED - check ornith-monitor.py path"
            }
        }
    }

    # llama-server has exited (crash, watchdog kill, or clean). Capture a
    # dossier BEFORE the restart counter logic so every exit is recorded.
    Write-CrashDossier -Proc $procHandle -StartedAt $lastStartTime -LlamaArgs $llamaArgs -CrashNum $crashCount

    # If the server ran for more than 60s, consider it a stable session - reset crash counter
    $ranSecs = if ($lastStartTime) { ((Get-Date) - $lastStartTime).TotalSeconds } else { 0 }
    if ($ranSecs -gt 60) {
      $crashCount = 0
    } else {
      $crashCount++
    }

    if ($crashCount -ge 3) {
      Write-Warning "[run-ornith] 3 rapid crashes (${ranSecs}s avg) - giving up"
      Write-Warning "[run-ornith] see $runbookPath — dossiers in $crashDir"
      break
    }

    Write-Warning "[run-ornith] llama-server exited after ${ranSecs}s (PID $($procHandle.Id)). Restarting in 3s... (attempt $($crashCount + 1)/3)"
    Start-Sleep -Seconds 3
  }
} finally {
  # Kill any live llama-server child before we declare "stopped". Without this,
  # the 3-crash give-up exits the launcher but leaves the most recent PID
  # running (orphan): GPU still pegged, port still bound, but no watchdog and
  # local-model-state.json says stopped — cc-ccr thinks local is down.
  if ($procHandle -and -not $procHandle.HasExited) {
    Write-Host "[run-ornith] killing live child PID $($procHandle.Id) on exit"
    Stop-Process -Id $procHandle.Id -Force -ErrorAction SilentlyContinue
    # Brief wait for the port to release (otherwise a manual relaunch races)
    $deadline = (Get-Date).AddSeconds(3)
    while ((Get-Date) -lt $deadline) {
      try {
        $t = [System.Net.Sockets.TcpClient]::new(); $t.Connect('127.0.0.1', 8010)
        if ($t.Connected) { $t.Close(); Start-Sleep -Milliseconds 200; continue }
        break
      } catch { break }
    }
  }
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
