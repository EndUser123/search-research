# Logs system metrics every 5s while llama-server runs.
# Usage (run BEFORE or alongside llama-server in a separate terminal):
#   pwsh P:\packages\installers\watch-system.ps1
# Ctrl+C to stop. Check log later via:
#   cat P:\packages\installers\system_watch.log
param(
  [int]$IntervalSeconds = 5,
  [string]$OutFile = "P:\packages\installers\system_watch.log"
)

"Time | llamaWS_GB | FreeRAM_GB | VRAM_MB" | Out-File $OutFile
Write-Host "Logging to $OutFile every ${IntervalSeconds}s — Ctrl+C to stop"

while ($true) {
  $now = Get-Date -Format "HH:mm:ss"

  $p = Get-Process llama-server -ErrorAction SilentlyContinue
  $ws = if ($p) { "{0:N1}" -f ($p.WorkingSet64 / 1GB) } else { "n/a" }

  $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
  $free = if ($os) { "{0:N1}" -f ($os.FreePhysicalMemory / 1MB) } else { "n/a" }

  $vram = (nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()

  "$now  $ws  $free  $vram" | Out-File $OutFile -Append
  Start-Sleep -Seconds $IntervalSeconds
}
