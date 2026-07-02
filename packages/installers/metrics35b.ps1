# Samples llama-server RAM/CPU, system free RAM, and GPU VRAM every 1.2s for ~35s.
# Identifies the process by name (MSYS bash PID != Windows PID).
$end = (Get-Date).AddSeconds(35)
while ((Get-Date) -lt $end) {
  $p = Get-Process llama-server -ErrorAction SilentlyContinue
  $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
  $vram = (nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>$null)
  $vram = ($vram | Select-Object -First 1)
  if ($p) {
    $ws = [math]::Round($p.WorkingSet64/1GB,2)
    $cpu = [math]::Round($p.TotalProcessorTime.TotalSeconds,1)
  } else { $ws="n/a"; $cpu="n/a" }
  $free = if ($os) { [math]::Round($os.FreePhysicalMemory/1MB,2) } else { "n/a" }
  "$(Get-Date -Format HH:mm:ss)  llamaWS_GB=$ws  FreeRAM_GB=$free  VRAM_MB=$vram  ProcCPU_s=$cpu"
  Start-Sleep -Milliseconds 1200
}
