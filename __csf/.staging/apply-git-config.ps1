#!/usr/bin/env pwsh
# Windows Git Configuration Optimization Script
# Applies Windows-specific git optimizations for Claude Code development
#
# Usage: .\apply-git-config.ps1
# Requirements: PowerShell 5.1+ and Git for Windows installed
#
# This script is idempotent - safe to run multiple times

Write-Host "Applying Windows Git Configuration Optimizations..." -ForegroundColor Cyan
Write-Host ""

# Function to apply a git config setting and show the change
function Apply-GitConfig {
    param(
        [string]$Scope,
        [string]$Key,
        [string]$Value,
        [string]$Description
    )

    $currentValue = & git config --get $Scope $key 2>$null

    if ($currentValue -eq $Value) {
        Write-Host "✓ $key" -ForegroundColor Green -NoNewline
        Write-Host " = '$Value' (already set)" -ForegroundColor Gray
        Write-Host "  $Description" -ForegroundColor DarkGray
    } else {
        if ($currentValue) {
            Write-Host "→ $key" -ForegroundColor Yellow -NoNewline
            Write-Host " = '$Value' (was: '$currentValue')" -ForegroundColor Gray
        } else {
            Write-Host "+ $key" -ForegroundColor Cyan -NoNewline
            Write-Host " = '$Value' (new)" -ForegroundColor Gray
        }
        Write-Host "  $Description" -ForegroundColor DarkGray

        & git config $Scope $key $Value
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Applied successfully" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: Failed to apply" -ForegroundColor Red
            return $false
        }
    }
    Write-Host ""
    return $true
}

$allSuccess = $true

# Core settings
# -------------------------

# Line ending handling: Convert CRLF to LF on commit, keep LF on checkout
# Prevents CRLF pollution in repository while working on Windows
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "core.autocrlf" -Value "input" -Description "LF only, no CRLF pollution in repo")

# Disable filemode tracking: Ignore Windows chmod noise
# Windows doesn't support Unix file permissions, so this prevents false diffs
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "core.filemode" -Value "false" -Description "Ignore Windows chmod noise")

# Preload index: Faster git status operations
# Loads index tree structure into memory for quicker status checks
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "core.preloadindex" -Value "true" -Description "Faster git status")

# Enable long paths: Support Windows 260+ character path limits
# Required for node_modules and other deep directory structures
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "core.longpaths" -Value "true" -Description "Enable long paths (>260 chars)")

# Default branch: Use 'main' as the default branch name
# Claude Code expects 'main' as the primary branch
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "init.defaultBranch" -Value "main" -Description "Default to 'main' branch")

# Pull behavior: Use merge instead of rebase
# Safer for most workflows, preserves merge history
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "pull.rebase" -Value "false" -Description "Use merge pulls (safer)")

# Diff algorithm: Use histogram for faster diffs
# Better performance on large files and repositories
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "diff.algorithm" -Value "histogram" -Description "Faster diff algorithm")

# Status behavior: Disable submodule summary
# Reduces noise in git status output
$allSuccess = $allSuccess -and (Apply-GitConfig -Scope "--global" -Key "status.submoduleSummary" -Value "false" -Description "Less noise in status")

Write-Host "─────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

if ($allSuccess) {
    Write-Host "✓ All git configurations applied successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Current Git Configuration:" -ForegroundColor Cyan
    Write-Host ""
    & git config --global --list | Select-String "^(core\.(autocrlf|filemode|preloadindex|longpaths)|init\.defaultBranch|pull\.rebase|diff\.algorithm|status\.submoduleSummary)" | ForEach-Object {
        $parts = $_.Line.Split('=')
        $key = $parts[0]
        $value = $parts[1]
        Write-Host "  $key = $value" -ForegroundColor White
    }
} else {
    Write-Host "✗ Some configurations failed. Please check the output above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
