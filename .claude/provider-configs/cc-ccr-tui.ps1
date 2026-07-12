# cc-ccr-tui.ps1 — TUI for CCR model route overrides
#
# Usage:
#   . .\cc-ccr-tui.ps1               # Launch TUI to configure CCR routes
#   cc-ccr --config                  # Alias (requires cc-ccr.ps1 modification)
#   cc-ccr --tui                     # Alias (requires cc-ccr.ps1 modification)
#
# This TUI provides a simple interface to:
# 1. View current CCR model routes
# 2. Select new routes from predefined lists
# 3. Enter custom provider/model combinations
# 4. Update CCR config and restart

param(
    [switch]$SkipRestart
)

$ccrConfigPath = "$env:USERPROFILE\.claude-code-router\config.json"
$ccrCmd = "$env:APPDATA\npm\ccr.cmd"

# --- Predefined route options ---
$Routes = @{
    "Opus" = @(
        @{ Provider = "zai"; Model = "glm-5.2[1m]"; Description = "zai GLM 5.2 (1M context)" },
        @{ Provider = "zai"; Model = "glm-5.1"; Description = "zai GLM 5.1" },
        @{ Provider = "zai"; Model = "glm-4.7"; Description = "zai GLM 4.7" },
        @{ Provider = "minimax"; Model = "MiniMax-M3"; Description = "MiniMax M3 (high quality)" },
        @{ Provider = "minimax"; Model = "MiniMax-M2.7"; Description = "MiniMax M2.7 (faster)" },
        @{ Provider = "opencode-go"; Model = "deepseek-v4-pro"; Description = "DeepSeek V4 Pro" },
        @{ Provider = "opencode-go"; Model = "deepseek-v4-flash"; Description = "DeepSeek V4 Flash (faster)" }
    )
    "Sonnet" = @(
        @{ Provider = "zai"; Model = "glm-4.7"; Description = "zai GLM 4.7" },
        @{ Provider = "minimax"; Model = "MiniMax-M2.7"; Description = "MiniMax M2.7" },
        @{ Provider = "minimax"; Model = "MiniMax-M3"; Description = "MiniMax M3 (higher quality)" },
        @{ Provider = "opencode-go"; Model = "deepseek-v4-flash"; Description = "DeepSeek V4 Flash" },
        @{ Provider = "opencode-go"; Model = "deepseek-v4-pro"; Description = "DeepSeek V4 Pro" }
    )
    "Haiku" = @(
        @{ Provider = "opencode-go"; Model = "deepseek-v4-flash"; Description = "DeepSeek V4 Flash" },
        @{ Provider = "opencode-go"; Model = "deepseek-v4-pro"; Description = "DeepSeek V4 Pro" },
        @{ Provider = "zai"; Model = "glm-4.5-air"; Description = "zai GLM 4.5 Air" },
        @{ Provider = "minimax"; Model = "MiniMax-M2.7"; Description = "MiniMax M2.7" }
    )
    "Custom" = @(
        @{ Provider = "llama-cpp"; Model = "ornith-1.0-9b"; Description = "llama.cpp - Ornith 1.0 9B (local)" }
    )
}

$ModelMap = @{
    "claude-opus-4-8" = "Opus"
    "claude-sonnet-4-6" = "Sonnet"
    "claude-haiku-4-5" = "Haiku"
    "claude-haiku-4-5-20251001" = "Haiku"
    "claude-custom" = "Custom"
    "claude-local-gemma" = "Custom"
}

# --- Load current config ---
function Get-CurrentRoutes {
    if (-not (Test-Path $ccrConfigPath)) {
        return @{}
    }

    try {
        $cfg = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json
        $routes = @{}

        foreach ($modelId in $cfg.Router.PSObject.Properties.Name) {
            if ($ModelMap.ContainsKey($modelId)) {
                $routes[$ModelMap[$modelId]] = $cfg.Router.$modelId
            }
        }

        return $routes
    } catch {
        Write-Error "[TUI] Failed to read CCR config: $_"
        return @{}
    }
}

# --- Route selection UI ---
function Select-Route {
    param(
        [string]$ModelName,
        [string]$CurrentValue
    )

    Write-Host "`n=== Configure $ModelName Route ===" -ForegroundColor Cyan
    Write-Host "Current: $CurrentValue"
    Write-Host ""

    $options = $Routes[$ModelName]

    # Display options with numbers
    for ($i = 0; $i -lt $options.Count; $i++) {
        $opt = $options[$i]
        $marker = if ("$($opt.Provider),$($opt.Model)" -eq $CurrentValue) { " * " } else { "   " }
        Write-Host "$marker[$($i+1)] $($opt.Description)" -NoNewline
        Write-Host "  →  $($opt.Provider),$($opt.Model)" -ForegroundColor DarkGray
    }

    Write-Host "   [0] Enter custom route (provider,model)"
    Write-Host "   [X] Skip / keep current"

    $choice = Read-Host "`nSelect option (1-$($options.Count), 0=custom, X=skip, Enter=skip)"

    # Treat empty input as skip (user pressed Enter without typing)
    if ([string]::IsNullOrWhiteSpace($choice)) {
        Write-Host "[TUI] Skipping (keeping current)." -ForegroundColor DarkGray
        return $CurrentValue
    }

    if ($choice -eq "0") {
        $custom = Read-Host "Enter route (format: provider,model)"
        if ($custom -match '^[^,]+,.+$') {
            return $custom
        } else {
            Write-Warning "Invalid format. Keeping current."
            return $CurrentValue
        }
    } elseif ($choice -match "^[xX]$") {
        Write-Host "[TUI] Skipping (keeping current)." -ForegroundColor DarkGray
        return $CurrentValue
    } elseif ($choice -match '^\d+$' -and [int]$choice -ge 1 -and [int]$choice -le $options.Count) {
        $idx = [int]$choice - 1
        return "$($options[$idx].Provider),$($options[$idx].Model)"
    } else {
        Write-Warning "Invalid choice. Keeping current."
        return $CurrentValue
    }
}

# --- Update CCR config ---
function Set-CCRRoute {
    param(
        [hashtable]$NewRoutes
    )

    $cfg = Get-Content $ccrConfigPath -Raw | ConvertFrom-Json

    foreach ($pair in $NewRoutes.GetEnumerator()) {
        $modelName = $pair.Key
        $routeValue = $pair.Value

        # Map display name back to model ID
        $modelId = switch ($modelName) {
            "Opus"   { "claude-opus-4-8" }
            "Sonnet" { "claude-sonnet-4-6" }
            "Haiku"  { "claude-haiku-4-5" }
            "Custom" { "claude-custom" }
            default { continue }
        }

        $cfg.Router | Add-Member -NotePropertyName $modelId -NotePropertyValue $routeValue -Force

        # Also set haiku-20251001 if setting Haiku
        if ($modelName -eq "Haiku") {
            $cfg.Router | Add-Member -NotePropertyName "claude-haiku-4-5-20251001" -NotePropertyValue $routeValue -Force
        }
    }

    # Write temp then move for atomicity
    $tmpPath = $ccrConfigPath + ".tmp"
    ($cfg | ConvertTo-Json -Depth 10) | Set-Content $tmpPath -Encoding UTF8
    Move-Item $tmpPath $ccrConfigPath -Force

    Write-Host "[TUI] CCR config updated." -ForegroundColor Green
}

# --- Restart CCR ---
function Restart-CCR {
    if ($SkipRestart) {
        Write-Host "[TUI] Skipping CCR restart." -ForegroundColor Yellow
        return
    }

    Write-Host "[TUI] Restarting CCR..." -ForegroundColor Cyan

    # Stop CCR
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        try { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" | Select-Object -ExpandProperty CommandLine) -match 'claude-code-router' } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds 500

    # Start CCR
    Start-Process pwsh -ArgumentList "-Command", "& '$ccrCmd' start" -WindowStyle Hidden
    Start-Sleep -Milliseconds 2000

    # Verify
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3456/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[TUI] CCR restarted successfully (HTTP $($r.StatusCode))." -ForegroundColor Green
    } catch {
        Write-Warning "[TUI] CCR health check failed. Check CCR manually."
    }
}

# --- Main UI ---
# Only clear screen if running in an interactive console (not piped/CI)
if ($Host.Name -eq 'ConsoleHost' -and $Host.UI.RawUI) {
    try { Clear-Host } catch { }
}
Write-Host "=== CCR Model Route Configuration ===" -ForegroundColor Green
Write-Host ""
Write-Host "Current CCR config: $ccrConfigPath"
Write-Host ""

$currentRoutes = Get-CurrentRoutes

# Helper for cross-version null coalescing (works on PS 5.1 and 7+)
function Get-ValueOrDefault {
    param($Value, $Default)
    if ($null -eq $Value -or $Value -eq '') { return $Default }
    return $Value
}

$selectedRoutes = @{}
$selectedRoutes["Opus"] = Select-Route -ModelName "Opus" -CurrentValue (Get-ValueOrDefault $currentRoutes["Opus"] "minimax,MiniMax-M3")
$selectedRoutes["Sonnet"] = Select-Route -ModelName "Sonnet" -CurrentValue (Get-ValueOrDefault $currentRoutes["Sonnet"] "minimax,MiniMax-M2.7")
$selectedRoutes["Haiku"] = Select-Route -ModelName "Haiku" -CurrentValue (Get-ValueOrDefault $currentRoutes["Haiku"] "opencode-go,deepseek-v4-flash")

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Opus:   $($selectedRoutes["Opus"])"
Write-Host "Sonnet: $($selectedRoutes["Sonnet"])"
Write-Host "Haiku:  $($selectedRoutes["Haiku"])"
Write-Host ""

$confirm = Read-Host "Apply changes? (Y/N, Enter=cancel)"
# Treat empty input as cancel (safer default for destructive action)
if ([string]::IsNullOrWhiteSpace($confirm)) {
    Write-Host "`n[TUI] Changes cancelled (empty input)." -ForegroundColor Yellow
} elseif ($confirm -match '^[yY]$') {
    Set-CCRRoute -NewRoutes $selectedRoutes
    Restart-CCR
    Write-Host "`n[TUI] Done. Routes updated." -ForegroundColor Green
} else {
    Write-Host "`n[TUI] Changes cancelled." -ForegroundColor Yellow
}
