# find_zombie_terminal.ps1 - Find which terminal window holds the zombie socket

$holderPid = 58312
Write-Host "[Lookup] PID $holderPid holds port 8787" -ForegroundColor Cyan

$holderProc = Get-Process -Id $holderPid -ErrorAction SilentlyContinue

if ($holderProc) {
    Write-Host "`nProcess details:" -ForegroundColor Yellow
    Write-Host "  PID: $($holderProc.Id)"
    Write-Host "  Name: $($holderProc.ProcessName)"
    Write-Host "  Path: $($holderProc.Path)"
    Write-Host "  StartTime: $($holderProc.StartTime)"

    if ($holderProc.ProcessName -eq "pwsh") {
        Write-Host "`n⚠️  This is a PowerShell terminal holding the zombie socket." -ForegroundColor Red

        # List all PowerShell terminals
        $allProcesses = Get-Process -Name pwsh -ErrorAction SilentlyContinue
        Write-Host "`nOpen PowerShell terminals:"
        foreach ($proc in $allProcesses) {
            $age = (Get-Date) - $proc.StartTime
            Write-Host "  PID $($proc.Id) - started $($age.TotalMinutes.ToString("0.0")) minutes ago - Window: $($proc.MainWindowTitle)"
        }

        Write-Host "`nClose the terminal matching PID $holderPid, then re-run the test."
    } else {
        Write-Host "`nThis is a $($holderProc.ProcessName) process."
        Write-Host "You can safely kill it:"
        Write-Host "  Stop-Process -Id $holderPid -Force"
    }
} else {
    Write-Host "Process not found - orphaned handle. Restart required."
}