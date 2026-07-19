# Stop only the AgentGateway instance owned by the shared launcher.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exeName = 'agentgateway.exe'
$stopped = @()

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $exeName -and $_.CommandLine -match [regex]::Escape($here) } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $stopped += "PID $($_.ProcessId)"
    }

if ($stopped.Count) {
    Write-Host "[agentgateway] stopped: $($stopped -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host '[agentgateway] nothing running' -ForegroundColor DarkGray
}
