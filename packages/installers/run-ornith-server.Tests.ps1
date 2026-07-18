$scriptPath = Join-Path $PSScriptRoot 'run-ornith-server.ps1'
Describe 'run-ornith dashboard ownership' {
  It 'delegates operator display to the Python dashboard' {
    $source = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'run-ornith-server.ps1')
    $source | Should -Match 'Start-OrnithDashboard'
    $source | Should -Match 'ornith-monitor\.py'
  }

  It 'does not retain a second PowerShell heartbeat renderer' {
    $source = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'run-ornith-server.ps1')
    $source | Should -Not -Match 'Get-LocalSlotStatus'
    $source | Should -Not -Match 'Format-HeartbeatLine'
    $source | Should -Not -Match 'Write-HeartbeatBlock'
  }

  It 'keeps the read-only probe side-effect free' {
    $source = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'run-ornith-server.ps1')
    $source | Should -Match 'if \(\$Probe\)'
    $source | Should -Match 'Get-LocalModelState -IncludeInference:\$IncludeInference'
  }
}
