$scriptPath = Join-Path $PSScriptRoot 'run-ornith-server.ps1'
$source = Get-Content -Raw $scriptPath

# Extract only the pure formatter from the supervisor. Dot-sourcing the full
# launcher would start llama-server, so tests load the function definition from
# its AST instead.
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
  $scriptPath, [ref]$tokens, [ref]$parseErrors
)
if ($parseErrors.Count -gt 0) { throw "run-ornith-server.ps1 did not parse" }
$formatterAst = $ast.Find({
  param($node)
  $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Format-HeartbeatLine'
}, $true) | Select-Object -First 1
if (-not $formatterAst) { throw 'Format-HeartbeatLine was not found' }
. ([scriptblock]::Create($formatterAst.Extent.Text))

Describe 'run-ornith heartbeat output' {
  It 'reports prompt progress instead of zero-token busy status' {
    $model = @{ state = 'LOADED' }
    $slot = @{ state = 'BUSY'; detail = 'prompt 12000/40000 (30%)'; task = 123 }
    $line = Format-HeartbeatLine -ModelState $model -SlotStatus $slot -Gpu 99 -Temperature 67 -VramMb 10218

    $line | Should Be '[run-ornith] LOADED • GPU 99% 67C • VRAM 10218MB • busy task 123 • prompt 12000/40000 (30%)'
  }

  It 'reports generation progress and remaining tokens' {
    $model = @{ state = 'LOADED' }
    $slot = @{ state = 'BUSY'; detail = 'gen 2124, remain 61876'; task = 456 }
    $line = Format-HeartbeatLine -ModelState $model -SlotStatus $slot -Gpu 81 -Temperature 54 -VramMb 10915

    $line | Should Be '[run-ornith] LOADED • GPU 81% 54C • VRAM 10915MB • busy task 456 • gen 2124, remain 61876'
  }

  It 'keeps idle output compact and does not repeat idle twice' {
    $model = @{ state = 'LOADED' }
    $slot = @{ state = 'IDLE'; detail = 'idle'; task = 789 }
    $line = Format-HeartbeatLine -ModelState $model -SlotStatus $slot -Gpu 2 -Temperature 46 -VramMb 10203

    $line | Should Be '[run-ornith] LOADED • GPU 2% 46C • VRAM 10203MB • idle task 789'
    $line | Should Not Match 'idle.*idle'
  }

  It 'uses read-only slot telemetry and change-aware heartbeat logic' {
    $source | Should Match 'Get-LocalSlotStatus'
    $source | Should Match '/slots'
    $source | Should Match 'lastHeartbeatKey'
    $source | Should Not Match 'slot busy 0tok'
  }
}
