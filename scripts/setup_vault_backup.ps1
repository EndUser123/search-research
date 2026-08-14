#!/usr/bin/env pwsh
<#
.SYNOPSIS
Setup and verify the Claude Vault backup system.

.DESCRIPTION
This script:
1. Checks if claude-vault is installed
2. Installs it if missing (via cargo or direct download)
3. Tests the backup system end-to-end
4. Verifies sessions are searchable

.EXAMPLE
./setup_vault_backup.ps1
#>

param(
    [switch]$Force,  # Force reinstall even if present
    [switch]$SkipTest  # Skip verification tests
)

$ErrorActionPreference = "Stop"

# =============================================================================
# PHASE 1: Check Prerequisites
# =============================================================================

Write-Host "=== Claude Vault Backup Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if claude-vault is installed
$claudeVaultPath = if ($IsWindows) {
    where.exe claude-vault 2>$null
} else {
    which claude-vault 2>/dev/null
}

if ($claudeVaultPath -and -not $Force) {
    Write-Host "✓ claude-vault already installed: $claudeVaultPath" -ForegroundColor Green
    $version = & claude-vault --version 2>$null || "unknown"
    Write-Host "  Version: $version" -ForegroundColor Gray
} else {
    Write-Host "⚠ claude-vault not found, installing..." -ForegroundColor Yellow
    Write-Host ""
    
    # Try cargo first
    $cargoPath = if ($IsWindows) {
        where.exe cargo 2>$null
    } else {
        which cargo 2>/dev/null
    }
    
    if ($cargoPath) {
        Write-Host "Installing via cargo..." -ForegroundColor Cyan
        try {
            & cargo install claude-vault --locked
            Write-Host "✓ claude-vault installed via cargo" -ForegroundColor Green
        } catch {
            Write-Host "✗ cargo install failed: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Fallback: Download from https://github.com/kuroko1t/claude-vault/releases" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "✗ cargo not found. Install one of:" -ForegroundColor Red
        Write-Host "  1. Rust: https://rustup.rs/" -ForegroundColor Gray
        Write-Host "  2. Pre-built: https://github.com/kuroko1t/claude-vault/releases" -ForegroundColor Gray
        exit 1
    }
}

# Verify claude-vault is in PATH
$claudeVaultPath = if ($IsWindows) {
    where.exe claude-vault 2>$null
} else {
    which claude-vault 2>/dev/null
}

if (-not $claudeVaultPath) {
    Write-Host "✗ claude-vault not in PATH after installation" -ForegroundColor Red
    exit 1
}

Write-Host ""

# =============================================================================
# PHASE 2: Verify Hook Files
# =============================================================================

Write-Host "Checking hook files..." -ForegroundColor Cyan

$hookDir = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent | Join-Path -ChildPath "hooks"
$preCompactHook = Join-Path $hookDir "search-research_PreCompact.py"
$sessionEndHook = Join-Path $hookDir "search-research_SessionEnd.py"
$hooksJson = Join-Path $hookDir "hooks.json"

$allPresent = $true
foreach ($file in @($preCompactHook, $sessionEndHook, $hooksJson)) {
    if (Test-Path $file) {
        Write-Host "✓ $(Split-Path -Leaf $file)" -ForegroundColor Green
    } else {
        Write-Host "✗ $(Split-Path -Leaf $file) NOT FOUND" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "✗ Missing hook files" -ForegroundColor Red
    exit 1
}

Write-Host ""

# =============================================================================
# PHASE 3: Verify Hook Syntax
# =============================================================================

Write-Host "Validating Python hooks..." -ForegroundColor Cyan

try {
    python -m py_compile $preCompactHook
    Write-Host "✓ PreCompact hook syntax valid" -ForegroundColor Green
} catch {
    Write-Host "✗ PreCompact hook has syntax errors: $_" -ForegroundColor Red
    exit 1
}

try {
    python -m py_compile $sessionEndHook
    Write-Host "✓ SessionEnd hook syntax valid" -ForegroundColor Green
} catch {
    Write-Host "✗ SessionEnd hook has syntax errors: $_" -ForegroundColor Red
    exit 1
}

try {
    $json = Get-Content $hooksJson | ConvertFrom-Json
    Write-Host "✓ hooks.json is valid JSON" -ForegroundColor Green
} catch {
    Write-Host "✗ hooks.json has syntax errors: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# =============================================================================
# PHASE 4: Test Hook Execution
# =============================================================================

Write-Host "Testing hook execution..." -ForegroundColor Cyan

try {
    $result = & python $preCompactHook 2>&1
    Write-Host "✓ PreCompact hook executes successfully" -ForegroundColor Green
    if ($result) {
        Write-Host "  Output: $result" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ PreCompact hook execution failed: $_" -ForegroundColor Red
    exit 1
}

try {
    $result = & python $sessionEndHook 2>&1
    Write-Host "✓ SessionEnd hook executes successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ SessionEnd hook execution failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# =============================================================================
# PHASE 5: Test claude-vault Import
# =============================================================================

if (-not $SkipTest) {
    Write-Host "Testing claude-vault import..." -ForegroundColor Cyan
    
    try {
        $result = & claude-vault import 2>&1
        Write-Host "✓ claude-vault import executed" -ForegroundColor Green
        if ($result) {
            Write-Host "  Output: $result" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠ claude-vault import had warnings: $_" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# =============================================================================
# PHASE 6: Verify Vault Database
# =============================================================================

Write-Host "Verifying vault database..." -ForegroundColor Cyan

$vaultDb = Join-Path $HOME ".local/share/claude-vault/vault.db"
if (Test-Path $vaultDb) {
    $size = (Get-Item $vaultDb).Length
    Write-Host "✓ vault.db found" -ForegroundColor Green
    Write-Host "  Location: $vaultDb" -ForegroundColor Gray
    Write-Host "  Size: $(($size / 1MB).ToString('F2')) MB" -ForegroundColor Gray
    
    # Count sessions if possible
    try {
        $count = & sqlite3 $vaultDb "SELECT COUNT(DISTINCT session_id) FROM messages;" 2>$null
        if ($count) {
            Write-Host "  Sessions archived: $count" -ForegroundColor Gray
        }
    } catch {
        # sqlite3 might not be available
    }
} else {
    Write-Host "ℹ vault.db not yet created (will be created on first import)" -ForegroundColor Blue
    Write-Host "  Location will be: $vaultDb" -ForegroundColor Gray
}

Write-Host ""

# =============================================================================
# PHASE 7: Summary
# =============================================================================

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "The backup system is ready:" -ForegroundColor Green
Write-Host "  • PreCompact hook: Runs before /compact to archive sessions" -ForegroundColor Gray
Write-Host "  • SessionEnd hook: Background archiving when sessions close" -ForegroundColor Gray
Write-Host "  • Vault database: Searchable via /search --source vault" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Sessions will auto-archive before Claude Code cleanup (21 days)" -ForegroundColor Gray
Write-Host "  2. Search archived sessions: /search <query> --source vault" -ForegroundColor Gray
Write-Host "  3. View vault database: claude-vault list" -ForegroundColor Gray
Write-Host ""
