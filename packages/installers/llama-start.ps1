# llama-start.ps1 — clean start of the local model stack.
# Stops any existing stack (launcher + watcher + llama-server) THEN launches a
# fresh launcher in its own minimized window. The launcher owns the restart
# loop, watcher dedup, idempotency guard, and sets its own window title
# ("llama.cpp: ...") so you can see it in the taskbar.
#
# Use:  llama-start                 (clean start)
#       llama-stop; llama-start     (explicit — but start already calls stop)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $here "llama-stop.ps1")

$launcher = "P:\packages\installers\run-ornith-server.ps1"
if (-not (Test-Path $launcher)) { Write-Warning "[llama-start] launcher not found: $launcher"; return }

# -WindowStyle Minimized: own console window (taskbar-visible), survives the
# calling terminal closing. The launcher sets its title to "llama.cpp: ...".
Start-Process pwsh.exe -ArgumentList "-NoProfile","-File","`"$launcher`"" -WindowStyle Minimized
Write-Host "[llama-start] launcher started (minimized window) — waiting for model to load..." -ForegroundColor Green

# Block until llama-server is up + serving (port bound + /health 200), so a
# chained `llama-start; <next command>` doesn't race the ~5s GGUF load.
# Uses the launcher's own readiness definition via -Probe (rungs 1-4, no
# inference — cheap, no slot contention under --parallel 1).
$deadline = (Get-Date).AddSeconds(60)
$last = $null
while ((Get-Date) -lt $deadline) {
  try {
    $probe = & pwsh.exe -NoProfile -File $launcher -Probe 2>$null | ConvertFrom-Json
    $last = $probe
    if ($probe.state -eq "LOADED" -or $probe.state -eq "READY") { break }
  } catch {}
  Start-Sleep -Seconds 2
}

if ($last -and ($last.state -eq "LOADED" -or $last.state -eq "READY")) {
  Write-Host "[llama-start] ready: state=$($last.state) model=$($last.model)" -ForegroundColor Green
} else {
  $st = if ($last) { $last.state } else { "no response" }
  Write-Warning "[llama-start] not ready after 60s (last state: $st) — check the launcher window"
}
