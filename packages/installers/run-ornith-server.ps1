# Ornith-1.0-9B (Q4_K_M) on llama.cpp + CUDA 12.8 (RTX 5070, sm_120)
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;$env:PATH"
$bin = "P:\packages\.github_repos\llama.cpp\build\bin"
$model = "P:\packages\models\ornith-1.0-9b-Q4_K_M.gguf"
$watcherScript = "P:\packages\installers\watch-system.ps1"
$watcherLog   = "P:\packages\installers\system_watch.log"

# Start system-watcher in background (hidden PowerShell window)
Remove-Item $watcherLog -ErrorAction SilentlyContinue
$watcher = Start-Process powershell.exe -ArgumentList "-NoProfile -File `"$watcherScript`"" -WindowStyle Hidden -PassThru
Write-Host "System watcher started (PID $($watcher.Id)) — log: $watcherLog"

Write-Host "Starting llama-server with Ornith-1.0-9B on http://127.0.0.1:8010"
Write-Host "Press Ctrl+C to stop."

try {
  & "$bin\llama-server.exe" -m "$model" -ngl 99 -c 32768 -t 6 --parallel 1 -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 1024 --reasoning-preserve --jinja --temp 0.6 --top-p 0.95 --top-k 20 --host 127.0.0.1 --port 8010
}
finally {
  # Stop watcher when server exits
  if ($watcher -and !$watcher.HasExited) {
    $watcher.Kill() | Out-Null
    Write-Host "System watcher stopped."
  }
}
