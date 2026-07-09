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
Write-Host "[llama-start] launcher started (minimized window) — first load takes ~5s" -ForegroundColor Green
Write-Host "[llama-start] check state with:  cc-ccr -usage   (local row should read 'up')" -ForegroundColor DarkGray
