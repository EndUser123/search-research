# plugin-audit-and-fix.ps1
# Comprehensive audit and auto-fix for Claude Code plugin manifests
# Run from PowerShell; handles plugin.json, hooks.json, and marketplace validation
#
# USAGE:
#   .\plugin-audit-and-fix.ps1                         Default audit
#   .\plugin-audit-and-fix.ps1 -AutoFix                Auto-fix manifest issues
#   .\plugin-audit-and-fix.ps1 -ScanForHardcodedPaths Scan source files for hardcoded paths
#   .\plugin-audit-and-fix.ps1 -AutoFix -ScanForHardcodedPaths  Full audit + fix
#   .\plugin-audit-and-fix.ps1 -DeleteHooks            Delete hooks.json instead of fixing
#
# PATH RESOLUTION (auto-detected):
#   $CLAUDE_PLUGIN_ROOT  — preferred, set by Claude Code at runtime
#   Script location      — fallback, derived from this script's path
#   Parameter           — override with -MarketplaceRoot "path"

param(
    [string]$MarketplaceRoot = "",
    [switch]$AutoFix = $false,
    [switch]$DeleteHooks = $false,
    [switch]$ScanForHardcodedPaths = $false
)

# Auto-detect plugin root: prefer $CLAUDE_PLUGIN_ROOT, fall back to script location
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvPluginRoot = $env:CLAUDE_PLUGIN_ROOT

if ([string]::IsNullOrEmpty($MarketplaceRoot)) {
    if (-not [string]::IsNullOrEmpty($EnvPluginRoot)) {
        $MarketplaceRoot = $EnvPluginRoot -replace "/plugins$", "" -replace "\\plugins$", ""
    } else {
        # Fall back: marketplace.json should be alongside the script's parent
        # plugin-installer/scripts/plugin-audit-and-fix.ps1
        # plugin-installer/plugins/   (symlinks)
        # plugin-installer/.claude-plugin/marketplace.json
        $pluginRoot = Split-Path -Parent $ScriptRoot  # -> plugin-installer
        $MarketplaceRoot = $pluginRoot -replace "\\scripts$", ""
    }
}

$ErrorActionPreference = "Continue"
Write-Host "=== Claude Code Plugin Audit & Fix ===" -ForegroundColor Cyan
Write-Host "Marketplace: $MarketplaceRoot" -ForegroundColor Gray
Write-Host ""

# Helper: Validate JSON
function Test-JsonValid {
    param([string]$JsonString)
    try {
        $JsonString | ConvertFrom-Json -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Helper: Read and parse JSON
function Get-JsonContent {
    param([string]$Path)
    if (Test-Path $Path) {
        try {
            return Get-Content $Path -Raw | ConvertFrom-Json
        } catch {
            return $null
        }
    }
    return $null
}

# Helper: Write JSON
function Set-JsonContent {
    param([string]$Path, [object]$Object)
    $Object | ConvertTo-Json -Depth 10 | Set-Content $Path -Encoding UTF8
}

# === PART 1: Audit all plugins ===
Write-Host "PART 1: Auditing plugins..." -ForegroundColor Yellow
$pluginsDir = Join-Path $MarketplaceRoot "plugins"
if (-not (Test-Path $pluginsDir)) {
    Write-Host "ERROR: plugins directory not found at $pluginsDir" -ForegroundColor Red
    exit 1
}

$allPlugins = Get-ChildItem $pluginsDir -Directory
$issues = @()

foreach ($pluginDir in $allPlugins) {
    $pluginName = $pluginDir.Name
    $manifestPath = Join-Path $pluginDir ".claude-plugin\plugin.json"
    $hooksPath = Join-Path $pluginDir "hooks\hooks.json"

    Write-Host "`n--- Plugin: $pluginName ---" -ForegroundColor Cyan

    # Check plugin.json exists
    if (-not (Test-Path $manifestPath)) {
        Write-Host "  ⚠ No .claude-plugin/plugin.json found" -ForegroundColor Yellow
        continue
    }

    # Load plugin.json
    $manifest = Get-JsonContent $manifestPath
    if ($null -eq $manifest) {
        Write-Host "  ✗ plugin.json is not valid JSON" -ForegroundColor Red
        $issues += @{ Plugin = $pluginName; Issue = "Invalid JSON"; Severity = "ERROR" }
        continue
    }

    Write-Host "  ✓ plugin.json loads successfully" -ForegroundColor Green

    # Check required fields
    if (-not $manifest.name) {
        Write-Host "  ✗ Missing required field: name" -ForegroundColor Red
        $issues += @{ Plugin = $pluginName; Issue = "Missing 'name' field"; Severity = "ERROR" }
    }

    # Check for common mistakes
    $badFields = @()
    if ($manifest.PSObject.Properties.Name -contains 'source') {
        $badFields += "source"
    }
    if ($manifest.PSObject.Properties.Name -contains 'category') {
        $badFields += "category"
    }
    if ($manifest.PSObject.Properties.Name -contains 'keywords' -and $null -eq $manifest.keywords) {
        $badFields += "keywords (empty)"
    }

    if ($badFields.Count -gt 0) {
        Write-Host "  ⚠ Found non-plugin fields: $($badFields -join ', ')" -ForegroundColor Yellow
        Write-Host "    (These belong in marketplace.json, not plugin.json)" -ForegroundColor Gray
        $issues += @{ Plugin = $pluginName; Issue = "Non-plugin fields: $($badFields -join ', ')"; Severity = "WARNING" }
    }

    # Check skills field specifically
    if ($manifest.PSObject.Properties.Name -contains 'skills') {
        $skillsValue = $manifest.skills

        # Check if it's an array of strings (names) instead of paths
        if ($skillsValue -is [array]) {
            $hasNames = $false
            foreach ($item in $skillsValue) {
                if ($item -is [string] -and -not $item.StartsWith("./")) {
                    $hasNames = $true
                    break
                }
            }
            if ($hasNames) {
                Write-Host "  ✗ skills field contains skill names instead of paths" -ForegroundColor Red
                Write-Host "    Found: $($skillsValue -join ', ')" -ForegroundColor Gray
                $issues += @{ Plugin = $pluginName; Issue = "Invalid skills array (names not paths)"; Severity = "ERROR" }
            } else {
                Write-Host "  ✓ skills field is valid" -ForegroundColor Green
            }
        } elseif ($skillsValue -is [string]) {
            if (-not $skillsValue.StartsWith("./")) {
                Write-Host "  ✗ skills path does not start with './' : $skillsValue" -ForegroundColor Red
                $issues += @{ Plugin = $pluginName; Issue = "skills path missing './'"; Severity = "ERROR" }
            } else {
                Write-Host "  ✓ skills path is valid: $skillsValue" -ForegroundColor Green
            }
        }
    }

    # Check hooks.json
    if (Test-Path $hooksPath) {
        $hooksJson = Get-JsonContent $hooksPath
        if ($null -eq $hooksJson) {
            Write-Host "  ✗ hooks.json is not valid JSON" -ForegroundColor Red
            $issues += @{ Plugin = $pluginName; Issue = "Invalid hooks.json JSON"; Severity = "ERROR" }
        } elseif ($hooksJson -is [array]) {
            Write-Host "  ✗ hooks.json is an array, not an object" -ForegroundColor Red
            Write-Host "    Should be: { "hooks": { ... } }" -ForegroundColor Gray
            $issues += @{ Plugin = $pluginName; Issue = "hooks.json structure wrong (array not object)"; Severity = "ERROR" }
        } elseif ($null -eq $hooksJson.hooks) {
            Write-Host "  ✗ hooks.json missing top-level 'hooks' key" -ForegroundColor Red
            Write-Host "    Should wrap under: { "hooks": { ... } }" -ForegroundColor Gray
            $issues += @{ Plugin = $pluginName; Issue = "hooks.json missing 'hooks' wrapper"; Severity = "ERROR" }
        } else {
            Write-Host "  ✓ hooks.json structure valid" -ForegroundColor Green
        }
    }
}

# === PART 2: Validate marketplace.json ===
Write-Host "`n=== Validating marketplace.json ===" -ForegroundColor Yellow
$marketplaceManifestPath = Join-Path $MarketplaceRoot ".claude-plugin\marketplace.json"
if (-not (Test-Path $marketplaceManifestPath)) {
    Write-Host "✗ marketplace.json not found at $marketplaceManifestPath" -ForegroundColor Red
} else {
    $marketplace = Get-JsonContent $marketplaceManifestPath
    if ($null -eq $marketplace) {
        Write-Host "✗ marketplace.json is not valid JSON" -ForegroundColor Red
    } else {
        Write-Host "✓ marketplace.json loads successfully" -ForegroundColor Green

        if (-not $marketplace.name) {
            Write-Host "✗ marketplace.json missing 'name' field" -ForegroundColor Red
        } else {
            Write-Host "  Name: $($marketplace.name)" -ForegroundColor Gray
        }

        if ($marketplace.plugins -is [array]) {
            Write-Host "  Plugins listed: $($marketplace.plugins.Count)" -ForegroundColor Gray

            foreach ($pluginEntry in $marketplace.plugins) {
                $pname = $pluginEntry.name
                $source = $pluginEntry.source

                if ($source -and -not $source.StartsWith("./")) {
                    Write-Host "  ⚠ Plugin '$pname' source does not start with './': $source" -ForegroundColor Yellow
                    $issues += @{ Plugin = $pname; Issue = "marketplace source missing './'"; Severity = "WARNING" }
                }

                $sourcePath = Join-Path $MarketplaceRoot ($source -replace "^\./", "")
                if (-not (Test-Path $sourcePath)) {
                    Write-Host "  ✗ Plugin '$pname' source does not resolve: $source" -ForegroundColor Red
                    $issues += @{ Plugin = $pname; Issue = "marketplace source does not resolve"; Severity = "ERROR" }
                } else {
                    Write-Host "  ✓ Plugin '$pname' resolves to: $sourcePath" -ForegroundColor Green
                }
            }
        }
    }
}

# === PART 3: Summary and auto-fix ===
Write-Host "`n=== Issue Summary ===" -ForegroundColor Cyan
if ($issues.Count -eq 0) {
    Write-Host "✓ No issues found!" -ForegroundColor Green
} else {
    $errorCount = ($issues | Where-Object { $_.Severity -eq "ERROR" }).Count
    $warningCount = ($issues | Where-Object { $_.Severity -eq "WARNING" }).Count

    Write-Host "ERRORS: $errorCount | WARNINGS: $warningCount" -ForegroundColor Yellow

    foreach ($issue in $issues) {
        $color = if ($issue.Severity -eq "ERROR") { "Red" } else { "Yellow" }
        Write-Host "  [$($issue.Severity)] $($issue.Plugin): $($issue.Issue)" -ForegroundColor $color
    }
}

# === PART 3b: Scan for hardcoded paths in plugin source ===
if ($ScanForHardcodedPaths) {
    Write-Host "`n=== Scanning for hardcoded paths ===" -ForegroundColor Yellow

    $scannedPlugins = 0
    $scannedFiles = 0
    $pathIssues = @()

    # Patterns that indicate hardcoded absolute paths (not $CLAUDE_PLUGIN_ROOT or relative)
    $pathPatterns = @(
        @{ Pattern = 'P:\\|P:/'; Reason = "Hardcoded P:/ drive path - use `$CLAUDE_PLUGIN_ROOT`"; Severity = "ERROR" },
        @{ Pattern = 'C:\\Users\\'; Reason = "Hardcoded Windows user profile - use `$env:HOME` or `$env:USERPROFILE`"; Severity = "ERROR" },
        @{ Pattern = '\$HOME/packages'; Reason = "Hardcoded HOME/packages path - use `$env:CLAUDE_PLUGIN_ROOT`"; Severity = "ERROR" },
        @{ Pattern = '/p/packages/'; Reason = "Hardcoded /p/packages/ path - use `$env:CLAUDE_PLUGIN_ROOT`"; Severity = "ERROR" },
        @{ Pattern = '/p\\packages\\'; Reason = "Hardcoded /p/packages/ path (backslashes) - use `$env:CLAUDE_PLUGIN_ROOT`"; Severity = "ERROR" },
        @{ Pattern = '~\/packages'; Reason = "Hardcoded ~/packages - use `$env:CLAUDE_PLUGIN_ROOT`"; Severity = "ERROR" },
        @{ Pattern = 'C:/Users/'; Reason = "Hardcoded Windows path - use `$env:HOME` or `$env:USERPROFILE`"; Severity = "ERROR" },
        @{ Pattern = '/home/'; Reason = "Hardcoded Unix home path - use `$env:HOME`"; Severity = "WARNING" },
        @{ Pattern = '\\\\\\\\[pP]:\\\\'; Reason = "Double-backslash P:/ path - malformed absolute path"; Severity = "WARNING" }
    )

    # File extensions to scan
    $scanExtensions = @("*.md", "*.py", "*.sh", "*.ps1", "*.json", "*.txt")

    # Directories to skip
    $skipDirs = @(".git", "node_modules", "__pycache__", ".venv", "venv", "tests", "examples", "docs", "assets", "badges")

    foreach ($pluginDir in $allPlugins) {
        $pluginName = $pluginDir.Name
        $scannedPlugins++
        $skipThis = $false
        foreach ($skip in $skipDirs) {
            if ($pluginDir.Name -eq $skip) { $skipThis = $true; break }
        }
        if ($skipThis) { continue }

        foreach ($ext in $scanExtensions) {
            $files = Get-ChildItem -Path $pluginDir.FullName -Filter $ext -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
                $path = $_.FullName
                $skip = $false
                foreach ($s in $skipDirs) {
                    if ($path -match $s) { $skip = $true; break }
                }
                -not $skip
            }

            foreach ($file in $files) {
                $scannedFiles++
                $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
                if ($null -eq $content) { continue }

                foreach ($p in $pathPatterns) {
                    if ($content -match $p.Pattern) {
                        $pathIssues += @{
                            Plugin = $pluginName
                            File = $file.Name
                            Path = $file.FullName.Replace($pluginDir.FullName, "").TrimStart("\")
                            Issue = $p.Reason
                            Severity = $p.Severity
                            Pattern = $p.Pattern
                        }
                    }
                }
            }
        }
    }

    Write-Host "Scanned: $scannedPlugins plugins, $scannedFiles files" -ForegroundColor Gray

    if ($pathIssues.Count -eq 0) {
        Write-Host "✓ No hardcoded paths found!" -ForegroundColor Green
    } else {
        $pathErrorCount = ($pathIssues | Where-Object { $_.Severity -eq "ERROR" }).Count
        $pathWarnCount = ($pathIssues | Where-Object { $_.Severity -eq "WARNING" }).Count
        Write-Host "Hardcoded paths: ERRORs: $pathErrorCount | WARNings: $pathWarnCount" -ForegroundColor Yellow

        foreach ($issue in $pathIssues) {
            $color = if ($issue.Severity -eq "ERROR") { "Red" } else { "Yellow" }
            Write-Host "  [$($issue.Severity)] $($issue.Plugin)/$($issue.File): $($issue.Issue)" -ForegroundColor $color
        }

        $issues += @{ Plugin = "PATH-AUDIT"; Issue = "$pathErrorCount hardcoded path errors, $pathWarnCount warnings"; Severity = "ERROR" }
    }
}

# Auto-fix if requested
if ($AutoFix) {
    Write-Host "`n=== Auto-Fixing Issues ===" -ForegroundColor Yellow

    foreach ($pluginDir in $allPlugins) {
        $pluginName = $pluginDir.Name
        $manifestPath = Join-Path $pluginDir ".claude-plugin\plugin.json"
        $hooksPath = Join-Path $pluginDir "hooks\hooks.json"

        if (Test-Path $manifestPath) {
            $manifest = Get-JsonContent $manifestPath
            if ($null -ne $manifest) {
                $changed = $false

                # Fix 1: Remove invalid skills array (names instead of paths)
                if ($manifest.PSObject.Properties.Name -contains 'skills') {
                    $skillsValue = $manifest.skills
                    if ($skillsValue -is [array]) {
                        $hasNames = $false
                        foreach ($item in $skillsValue) {
                            if ($item -is [string] -and -not $item.StartsWith("./")) {
                                $hasNames = $true
                                break
                            }
                        }
                        if ($hasNames) {
                            Write-Host "  Removing invalid skills array from $pluginName" -ForegroundColor Cyan
                            $manifest.PSObject.Properties.Remove('skills')
                            $changed = $true
                        }
                    }
                }

                # Fix 2: Remove marketplace-only fields
                if ($manifest.PSObject.Properties.Name -contains 'source') {
                    Write-Host "  Removing 'source' field from $pluginName (belongs in marketplace.json)" -ForegroundColor Cyan
                    $manifest.PSObject.Properties.Remove('source')
                    $changed = $true
                }
                if ($manifest.PSObject.Properties.Name -contains 'category') {
                    Write-Host "  Removing 'category' field from $pluginName (belongs in marketplace.json)" -ForegroundColor Cyan
                    $manifest.PSObject.Properties.Remove('category')
                    $changed = $true
                }

                if ($changed) {
                    Set-JsonContent $manifestPath $manifest
                    Write-Host "  ✓ Fixed: $pluginName" -ForegroundColor Green
                }
            }
        }

        # Fix 3: Delete or fix hooks.json
        if (Test-Path $hooksPath) {
            if ($DeleteHooks) {
                Remove-Item $hooksPath -Force
                Write-Host "  Deleted hooks.json from $pluginName" -ForegroundColor Cyan
            } else {
                $hooksJson = Get-JsonContent $hooksPath
                if ($null -eq $hooksJson -or $hooksJson -is [array] -or $null -eq $hooksJson.hooks) {
                    Write-Host "  Fixing hooks.json structure in $pluginName" -ForegroundColor Cyan
                    Set-JsonContent $hooksPath @{ hooks = @{} }
                }
            }
        }
    }

    Write-Host "`n✓ Auto-fix complete. Re-validate plugins with: claude plugin validate <plugin-dir>" -ForegroundColor Green
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
if ($issues.Count -gt 0) {
    Write-Host "1. Run with -AutoFix to automatically fix safe issues" -ForegroundColor Gray
    Write-Host "2. Run with -ScanForHardcodedPaths to detect hardcoded paths" -ForegroundColor Gray
    Write-Host "3. Re-validate: claude plugin validate <plugin-dir>" -ForegroundColor Gray
    Write-Host "4. Update marketplace: /plugin marketplace update local" -ForegroundColor Gray
} else {
    Write-Host "1. All manifest checks passed!" -ForegroundColor Green
    Write-Host "2. Run with -ScanForHardcodedPaths to check source files" -ForegroundColor Gray
    Write-Host "3. Update marketplace: /plugin marketplace update local" -ForegroundColor Gray
}
