BeforeAll {
  $scriptPath = Join-Path $PSScriptRoot 'cc-ccr.ps1'

  # Extract only pure/helper functions from the launcher. Dot-sourcing the full
  # launcher would start or stop live services and is intentionally prohibited.
  $tokens = $null
  $parseErrors = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $scriptPath, [ref]$tokens, [ref]$parseErrors
  )
  if ($parseErrors.Count -gt 0) { throw 'cc-ccr.ps1 did not parse' }

  foreach ($name in @(
      'Wait-LocalModelReady',
      'Resolve-RoutingMode',
      'Format-RoutingModeDisplay',
      'Get-AdmissionProxyListener',
      'Get-AdmissionProxyOwner',
      'Test-AdmissionProxyHealth',
      'Ensure-AdmissionProxy',
      'Get-RouteDomain',
      'Format-Route',
      'Format-RoutePrimaryLabel'
  )) {
    $targetName = $name
    $functionAst = $ast.Find({
      param($node)
      $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq $targetName
    }, $true) | Select-Object -First 1
    if (-not $functionAst) { throw "$name was not found" }
    . ([scriptblock]::Create($functionAst.Extent.Text))
  }
}

Describe 'cc-ccr local model readiness' {
  It 'waits through DEAD -> LOADING -> LOADED' {
    $states = [System.Collections.Generic.Queue[object]]::new()
    @('DEAD', 'LOADING', 'LOADED') | ForEach-Object { $states.Enqueue([pscustomobject]@{ state = $_ }) }
    $sleeps = [System.Collections.Generic.List[int]]::new()
    $result = Wait-LocalModelReady -TimeoutSec 10 -StartupGraceSec 5 `
      -ProbeScript { $states.Dequeue() } `
      -SleepScript { param($Milliseconds) $sleeps.Add($Milliseconds) } `
      -NowScript { [datetime]::Parse('2026-07-16T12:00:00') }

    $result.state | Should -Be 'LOADED'
    $sleeps.Count | Should -Be 2
  }

  It 'does not stop early on persistent DEAD during the startup grace/timeout window' {
    $script:probeCount = 0
    $script:clock = [datetime]::Parse('2026-07-16T12:00:00')
    $result = Wait-LocalModelReady -TimeoutSec 3 -StartupGraceSec 2 `
      -ProbeScript { $script:probeCount++; [pscustomobject]@{ state = 'DEAD' } } `
      -SleepScript { param($Milliseconds) $script:clock = $script:clock.AddMilliseconds($Milliseconds) } `
      -NowScript { $script:clock }

    $result.state | Should -Be 'DEAD'
    $script:probeCount | Should -BeGreaterThan 1
  }

  It 'keeps startup faults transient during grace and HUNG terminal' {
    foreach ($state in @('STUCK', 'BROKEN')) {
      $script:probeCount = 0
      $script:clock = [datetime]::Parse('2026-07-16T12:00:00')
      $result = Wait-LocalModelReady -TimeoutSec 10 -StartupGraceSec 5 `
        -ProbeScript { $script:probeCount++; [pscustomobject]@{ state = $state } } `
        -SleepScript { param($Milliseconds) $script:clock = $script:clock.AddMilliseconds($Milliseconds) } `
        -NowScript { $script:clock }

      $result.state | Should -Be $state
      $script:probeCount | Should -BeGreaterThan 1
    }

    $script:probeCount = 0
    $result = Wait-LocalModelReady -TimeoutSec 10 -StartupGraceSec 5 `
      -ProbeScript { $script:probeCount++; [pscustomobject]@{ state = 'HUNG' } } `
      -SleepScript { param($Milliseconds) throw 'terminal state should not sleep' } `
      -NowScript { [datetime]::Parse('2026-07-16T12:00:00') }
    $result.state | Should -Be 'HUNG'
    $script:probeCount | Should -Be 1
  }

  It 'keeps the existing LOADING -> LOADED path successful' {
    $states = [System.Collections.Generic.Queue[object]]::new()
    @('LOADING', 'LOADED') | ForEach-Object { $states.Enqueue([pscustomobject]@{ state = $_ }) }
    $result = Wait-LocalModelReady -TimeoutSec 10 `
      -ProbeScript { $states.Dequeue() } `
      -SleepScript { param($Milliseconds) } `
      -NowScript { [datetime]::Parse('2026-07-16T12:00:00') }

    $result.state | Should -Be 'LOADED'
  }
}

Describe 'cc-ccr routing mode display' {
  It 'preserves an explicit conservative mode' {
    $mode = Resolve-RoutingMode -RoutingMode 'conservative'
    $mode.Value | Should -Be 'conservative'
    $mode.IsDefault | Should -BeFalse
    (Format-RoutingModeDisplay -RoutingModeInfo $mode) | Should -Be 'routingMode=conservative'
  }

  It 'resolves missing, null, and empty modes to aggressive defaults' {
    foreach ($value in @($null, '', '   ')) {
      $mode = Resolve-RoutingMode -RoutingMode $value
      $mode.Value | Should -Be 'aggressive'
      $mode.IsDefault | Should -BeTrue
      (Format-RoutingModeDisplay -RoutingModeInfo $mode) | Should -Be 'routingMode=aggressive (default)'
    }
  }
}

Describe 'cc-ccr route display classification' {
  It 'groups Claude aliases, roles, local, and provider routes by domain' {
    Get-RouteDomain -Name 'claude-sonnet-5' | Should -Be 'claude models'
    Get-RouteDomain -Name 'longContext' | Should -Be 'roles'
    Get-RouteDomain -Name 'claude-local-ornith' | Should -Be 'local models'
    Get-RouteDomain -Name 'grok' | Should -Be 'provider routes'
  }

  It 'retains a visible primary node for empty or nonstandard route values' {
    Format-RoutePrimaryLabel -Primary $null | Should -Be 'primary: unavailable'
    Format-RoutePrimaryLabel -Primary 'provider,model' | Should -Be 'primary: provider/model'
    Format-RoutePrimaryLabel -Primary 'provider/model' | Should -Be 'primary: provider/model'
  }
}

Describe 'cc-ccr admission proxy ownership' {
  BeforeAll {
    $script:expectedProcess = [pscustomobject]@{ ProcessId = 2222; CommandLine = 'node P:\.claude\provider-configs\ccr-admission-proxy.js' }
    $script:healthy = { $true }
  }

  It 'reuses a healthy existing expected proxy and reports its listener PID' {
    $script:spawned = $false
    $script:lookupPids = [System.Collections.Generic.List[int]]::new()
    $result = Ensure-AdmissionProxy -Port 3458 -ProxyScript 'proxy.js' `
      -ListenerLookup { [pscustomobject]@{ OwningProcess = 2222 } } `
      -ProcessLookup { param($Id) $script:lookupPids.Add($Id); $script:expectedProcess } `
      -HealthCheck $script:healthy `
      -SpawnScript { $script:spawned = $true } `
      -SleepScript { param($Milliseconds) }

    $result.Available | Should -BeTrue
    $result.Status | Should -Be 'Already running'
    $result.ListenerPid | Should -Be 2222
    $script:lookupPids | Should -HaveCount 1
    $script:lookupPids[0] | Should -Be 2222
    $script:spawned | Should -BeFalse
  }

  It 'does not kill or claim availability for a wrong-owner port collision' {
    $script:spawned = $false
    $result = Ensure-AdmissionProxy -Port 3458 -ProxyScript 'proxy.js' `
      -ListenerLookup { [pscustomobject]@{ OwningProcess = 3333 } } `
      -ProcessLookup { param($Id) [pscustomobject]@{ ProcessId = 3333; CommandLine = 'unrelated.exe' } } `
      -HealthCheck $script:healthy `
      -SpawnScript { $script:spawned = $true } `
      -SleepScript { param($Milliseconds) }

    $result.Available | Should -BeFalse
    $result.Status | Should -Be 'Ownership conflict'
    $result.FallbackUrl | Should -Be 'http://127.0.0.1:3456'
    $script:spawned | Should -BeFalse
  }

  It 'starts only without a listener and verifies health plus listener identity' {
    $script:lookupCount = 0
    $script:spawned = $false
    $result = Ensure-AdmissionProxy -Port 3458 -ProxyScript 'proxy.js' `
      -ListenerLookup {
        $script:lookupCount++
        if ($script:lookupCount -eq 1) { return $null }
        [pscustomobject]@{ OwningProcess = 4444 }
      } `
      -ProcessLookup { param($Id) [pscustomobject]@{ ProcessId = 4444; CommandLine = 'node proxy.js' } } `
      -HealthCheck $script:healthy `
      -SpawnScript { $script:spawned = $true; [pscustomobject]@{ Id = 9999 } } `
      -SleepScript { param($Milliseconds) }

    $result.Available | Should -BeTrue
    $result.Status | Should -Be 'Started'
    $result.ListenerPid | Should -Be 4444
    $result.WrapperPid | Should -Be 9999
    $script:spawned | Should -BeTrue
  }
}
