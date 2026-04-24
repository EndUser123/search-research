# /v Workflow Verification Test
Write-Host "=== /v Workflow Hook Verification Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if custom bypass is disabled
Write-Host "1. Verifying custom bypass is disabled..." -ForegroundColor Yellow
$routerContent = Get-Content "P:\.claude\hooks\UserPromptSubmit_router.py" -Raw
if ($routerContent -match '#\s*"skill_enforcement"') {
    Write-Host "   [OK] Custom bypass disabled" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Custom bypass still active" -ForegroundColor Red
}

# Check if test flag is removed
Write-Host ""
Write-Host "2. Verifying test flag removed..." -ForegroundColor Yellow
$settingsContent = Get-Content "P:\.claude\settings.json" -Raw
if ($settingsContent -match 'SKILL_ENFORCEMENT_ENABLED') {
    Write-Host "   [FAIL] Flag still present - restart needed" -ForegroundColor Red
} else {
    Write-Host "   [OK] Flag removed" -ForegroundColor Green
}

# Check /v state file
Write-Host ""
Write-Host "3. Current /v state..." -ForegroundColor Yellow
if (Test-Path "P:\.claude\.v_state.json") {
    $stateContent = Get-Content "P:\.claude\.v_state.json" | ConvertFrom-Json
    Write-Host "   Stage: $($stateContent.current_stage)" -ForegroundColor Cyan
    Write-Host "   Target: $($stateContent.target_file)" -ForegroundColor Cyan
} else {
    Write-Host "   No state file (created on first /v run)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Restart Claude Code to load new settings" -ForegroundColor White
Write-Host "2. Run: /v P:\__csf\src\cks\query_expansion.py" -ForegroundColor Yellow
Write-Host "3. Verify Skill tool invokes (not additionalContext)" -ForegroundColor White
Write-Host "4. Confirm hooks fire and .v_state.json updates" -ForegroundColor White
