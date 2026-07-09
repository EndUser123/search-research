# llama-stop.ps1 — full clean shutdown of the local model stack.
# Kills: launcher (run-ornith-server.ps1, non-Probe) + watcher + llama-server.
# Waits for port 8010 to release so an immediate llama-start doesn't race the
# old process letting go of the port.
#
# Use:  llama-stop            (standalone)
#       llama-stop; llama-start   (clean restart — start calls stop internally anyway)
$killed = @()

# Launcher (the long-running supervisor) — exclude -Probe invocations, which are
# transient health checks, not supervisors.
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'run-ornith-server\.ps1' -and $_.CommandLine -notmatch '-Probe' } |
  ForEach-Object { $killed += "launcher PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Watcher
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'watch-system\.ps1' } |
  ForEach-Object { $killed += "watcher PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# llama-server itself
Get-Process llama-server -ErrorAction SilentlyContinue |
  ForEach-Object { $killed += "llama-server PID $($_.Id)"; Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }

# Wait for port 8010 to release (so a follow-on llama-start's idempotency guard
# doesn't see a stale bound port and exit without launching).
$deadline = (Get-Date).AddSeconds(5)
while ((Get-Date) -lt $deadline) {
  $listener = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue
  if (-not $listener) { break }
  Start-Sleep -Milliseconds 200
}

if ($killed.Count -gt 0) {
  Write-Host "[llama-stop] stopped: $($killed -join ', ')" -ForegroundColor Yellow
} else {
  Write-Host "[llama-stop] nothing running (no launcher/watcher/llama-server found)" -ForegroundColor DarkGray
}
