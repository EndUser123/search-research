param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]] $Args
)

# Bifrost AI Gateway Proxy Configuration Script
# Routes Claude Code through Bifrost's various LLM routes
# Usage: cc-bf [--sync] [model]
#
# --sync   : backup current config.json, then sync routing rules from DB to config.json
# --start  : start bifrost-http daemon
# --restart: stop then start the daemon
# --shutdown: stop the daemon
# --dashboard: open Bifrost dashboard in browser
#
# Available routes are dynamically loaded from the Bifrost DB at runtime.
# Run 'cc-bf' with no arguments to see all available routes.

$env:ANTHROPIC_BASE_URL = "http://localhost:8080/anthropic"
$env:ANTHROPIC_API_KEY = "sk-bf-49998d75-3b06-4e72-8547-741cb81b497e"

# Default: Sonnet=M27, Opus=GLM-5.1, Haiku=M27
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "M27"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "GLM-5.1"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "M27"

$doSync = $false
$doStart = $false
$doRestart = $false
$doShutdown = $false
$doDashboard = $false
$modelOverride = $null
$i = 0
while ($i -lt $Args.Count) {
    $arg = $Args[$i]
    if ($arg -eq "--sync") {
        $doSync = $true
    } elseif ($arg -eq "--start") {
        $doStart = $true
    } elseif ($arg -eq "--restart") {
        $doRestart = $true
    } elseif ($arg -eq "--shutdown") {
        $doShutdown = $true
    } elseif ($arg -eq "--dashboard") {
        $doDashboard = $true
    } elseif ($arg -eq "--model" -or $arg -eq "-m") {
        $i++
        if ($i -lt $Args.Count) { $modelOverride = $Args[$i] }
    } elseif ($arg -match "^--model=(.+)$") {
        $modelOverride = $matches[1]
    } elseif ($arg -match "^[a-zA-Z0-9_-]+$") {
        if (-not $modelOverride) { $modelOverride = $arg }
    }
    $i++
}

# Query the Bifrost DB using Python (since System.Data.SQLite isn't available in PowerShell)
function Get-BifrostRoutesFromDb {
    $dbPath = "$env:APPDATA\bifrost\config.db"
    if (-not (Test-Path $dbPath)) {
        return @{}
    }
    $pythonScript = @"
import sqlite3, json
conn = sqlite3.connect(r'$dbPath')
c = conn.cursor()
c.execute('''
    SELECT r.id, r.cel_expression, rt.provider, rt.model
    FROM routing_rules r
    LEFT JOIN routing_targets rt ON rt.rule_id = r.id
    WHERE r.cel_expression IS NOT NULL AND r.cel_expression != ''
    ORDER BY r.priority
''')
routes = {}
for row in c.fetchall():
    cel = row[1]
    provider = row[2]
    model = row[3]
    import re
    m = re.search(r'model\s*==\s*"([^"]+)"', cel)
    if m and provider and model:
        modelName = m.group(1)
        routes[modelName] = {'display': f'{provider}/{model}', 'sonnet': modelName, 'opus': modelName, 'haiku': modelName}
print(json.dumps(routes))
conn.close()
"@
    try {
        $json = python3 -c $pythonScript 2>$null
        if ($json) {
            $data = ConvertFrom-Json $json
            $ht = @{}
            try {
                $data.psobject.properties | ForEach-Object { $ht[$_.Name] = $_.Value }
            } catch {
                foreach ($prop in $data.PSObject.Properties) {
                    $ht[$prop.Name] = $prop.Value
                }
            }
            return $ht
        }
    } catch {
        Write-Host "[WARN] Failed to query DB: $_" -ForegroundColor Yellow
    }
    return @{}
}

function Get-BifrostRulesFromDb {
    $dbPath = "$env:APPDATA\bifrost\config.db"
    if (-not (Test-Path $dbPath)) {
        return @()
    }
    $pythonScript = @"
import sqlite3, json
conn = sqlite3.connect(r'$dbPath')
c = conn.cursor()
c.execute('''
    SELECT r.id, r.name, r.cel_expression, r.scope, r.priority, rt.provider, rt.model, rt.weight
    FROM routing_rules r
    LEFT JOIN routing_targets rt ON rt.rule_id = r.id
    ORDER BY r.priority
''')
rules = []
for row in c.fetchall():
    rules.append({
        'id': row[0],
        'name': row[1] or row[0],
        'cel_expression': row[2] or '',
        'scope': row[3] or 'global',
        'priority': row[4],
        'targets': [] if (row[5] is None or row[6] is None) else [{'provider': row[5], 'model': row[6], 'weight': row[7] or 1.0}]
    })
print(json.dumps({'rules': rules}))
conn.close()
"@
    try {
        $json = python3 -c $pythonScript 2>$null
        if ($json) {
            $data = ConvertFrom-Json $json
            return $data.rules
        }
    } catch {
        Write-Host "[WARN] Failed to query DB: $_" -ForegroundColor Yellow
    }
    return @()
}

function Sync-BifrostConfig {
    $configPath = "$env:APPDATA\bifrost\config.json"
    $backupPath = "$env:APPDATA\bifrost\config.backup_$(Get-Date -f 'yyyyMMdd-HHmmss').json"

    if (Test-Path $configPath) {
        Copy-Item $configPath $backupPath -Force
        Write-Host "   Backed up config.json -> $backupPath" -ForegroundColor White
    }

    $rules = Get-BifrostRulesFromDb
    if ($rules.Count -eq 0) {
        Write-Host "   [ERROR] No rules found in DB" -ForegroundColor Red
        return
    }

    $config = @{
        '$schema' = "https://www.getbifrost.ai/schema"
        version   = 1
        providers = @{}
        governance = @{
            routing_rules = @($rules)
        }
    }

    $cleanConfig = $config | ConvertTo-Json -Depth 10
    $cleanConfig | Set-Content $configPath -Encoding UTF8
    Write-Host "   Synced $($rules.Count) rules from DB -> config.json" -ForegroundColor Green
}

function Get-BifrostProcess {
    $proc = Get-Process -Name "bifrost-http*" -ErrorAction SilentlyContinue
    if ($proc) { return $proc }
    $allProcs = Get-Process -ErrorAction SilentlyContinue
    foreach ($p in $allProcs) {
        if ($p.Path -like "*bifrost*") { return $p }
    }
    return $null
}

function Start-BifrostDaemon {
    $proc = Get-BifrostProcess
    if ($proc) {
        Write-Host "   Bifrost already running (PID $($proc.Id))" -ForegroundColor Yellow
        return
    }
    $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.0-prerelease8\bin\bifrost-http.exe-0"
    if (-not (Test-Path $bifrostBin)) {
        $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.0-prerelease7\bin\bifrost-http.exe-0"
    }
    if (-not (Test-Path $bifrostBin)) {
        $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.0-prerelease6\bin\bifrost-http.exe-0"
    }
    if (-not (Test-Path $bifrostBin)) {
        Write-Host "   [ERROR] Bifrost binary not found at expected paths" -ForegroundColor Red
        return
    }
    $appDir = "$env:APPDATA\bifrost"
    $errLog = "$env:TEMP\bifrost_err.log"
    $proc = Start-Process -FilePath $bifrostBin -ArgumentList "-app-dir=$appDir -port=8080" -PassThru -RedirectStandardError $errLog
    Start-Sleep -Milliseconds 500
    $newProc = Get-BifrostProcess
    if ($newProc) {
        Write-Host "   Started Bifrost (PID $($newProc.Id)) on port 8080" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Failed to start Bifrost" -ForegroundColor Red
    }
}

function Stop-BifrostDaemon {
    $proc = Get-BifrostProcess
    if (-not $proc) {
        Write-Host "   Bifrost is not running" -ForegroundColor Yellow
        return
    }
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 300
    $remaining = Get-BifrostProcess
    if (-not $remaining) {
        Write-Host "   Stopped Bifrost (PID $($proc.Id))" -ForegroundColor Green
    } else {
        Write-Host "   [WARN] Bifrost process may still be running (PID $($remaining.Id))" -ForegroundColor Yellow
    }
}

function Restart-BifrostDaemon {
    Stop-BifrostDaemon
    Start-Sleep -Milliseconds 500
    Start-BifrostDaemon
}

function Show-BifrostDashboard {
    $proc = Get-BifrostProcess
    if (-not $proc) {
        Write-Host "   [ERROR] Bifrost is not running -- start it first with /bf start" -ForegroundColor Red
        return
    }
    $port = "8080"
    try {
        $procId = $proc.Id
        $netstatLines = netstat -ano 2>$null
        foreach ($line in $netstatLines) {
            if ($line -match "127\.0\.0\.1:(\d+)\s+.*LISTENING\s+$procId") {
                $port = $matches[1]
                break
            }
        }
    } catch {}
    $url = "http://localhost:$port"
    Write-Host "   Opening dashboard: $url" -ForegroundColor Cyan
    Start-Process -FilePath $url
}

# Load routes from DB
$routingTable = Get-BifrostRoutesFromDb

if ($doSync) {
    Sync-BifrostConfig
    $routingTable = Get-BifrostRoutesFromDb
}

if ($doStart) {
    Start-BifrostDaemon
    return
}

if ($doRestart) {
    Restart-BifrostDaemon
    return
}

if ($doShutdown) {
    Stop-BifrostDaemon
    return
}

if ($doDashboard) {
    Show-BifrostDashboard
    return
}

# Build the $routes hashtable for alias resolution
$routes = @{}

foreach ($modelName in $routingTable.Keys) {
    $entry = $routingTable[$modelName]
    $routes[$modelName] = @($modelName, $modelName, $modelName, $entry.display)
}

$aliasMap = @{
    "DSv4"      = "DSv4-flash"
    "DeepSeek"  = "DSv4-flash"
    "ling"      = "OR-Ling-2.6-1t"
    "gh"        = "GH-GPT-5-mini"
    "gpt5"      = "GH-GPT-5-mini"
    "gemini"    = "Gemini-3.1-flash"
    "gemma"     = "OR-Gemma-4-31b"
}
foreach ($alias in $aliasMap.Keys) {
    $target = $aliasMap[$alias]
    if ($routingTable.ContainsKey($target)) {
        $entry = $routingTable[$target]
        $routes[$alias] = @($target, $target, $target, $entry.display)
    }
}

if ($modelOverride) {
    $normalizedKey = $modelOverride -replace "^glm-5.1$", "GLM-5.1" `
                                    -replace "^MiniMax-M2.7$", "M27" `
                                    -replace "^Nvidia-Deepseek-v4-flash$", "DSv4-flash" `
                                    -replace "^DSv4-flash$", "DSv4"

    if ($routes.ContainsKey($normalizedKey)) {
        $route = $routes[$normalizedKey]
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $route[0]
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = $route[1]
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $route[2]
        $displayName = $route[3]
    } else {
        $displayName = "Custom: $modelOverride"
    }
} else {
    $displayName = "Default (M27 + GLM-5.1)"
}

Write-Host ""
Write-Host "Bifrost Configuration:" -ForegroundColor Yellow
Write-Host "   - Provider:             Bifrost AI Gateway" -ForegroundColor White
Write-Host "   - Endpoint:            http://localhost:8080/anthropic" -ForegroundColor White
Write-Host "   - Sonnet:              $env:ANTHROPIC_DEFAULT_SONNET_MODEL" -ForegroundColor White
Write-Host "   - Opus:                $env:ANTHROPIC_DEFAULT_OPUS_MODEL" -ForegroundColor White
Write-Host "   - Haiku:               $env:ANTHROPIC_DEFAULT_HAIKU_MODEL" -ForegroundColor White
Write-Host ""
Write-Host "Available routes (from DB):" -ForegroundColor Yellow
if ($routes.Count -eq 0) {
    Write-Host "   [no routes loaded from DB]" -ForegroundColor Red
} else {
    $sortedKeys = $routes.Keys | Sort-Object
    foreach ($key in $sortedKeys) {
        $route = $routes[$key]
        $model = $route[0]
        $desc = $route[3]
        $line = "   cc-bf {0,-20} -> {1}" -f $key, $desc
        Write-Host $line -ForegroundColor Cyan
    }
}
Write-Host ""
Write-Host "Use 'cc-bf --sync' to backup and sync routing rules from DB to config.json" -ForegroundColor DarkGray
Write-Host ""
