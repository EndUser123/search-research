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
$doRoutes = $false
$doStatus = $false
$newOnly = $false
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
    } elseif ($arg -eq "--routes") {
        $doRoutes = $true
    } elseif ($arg -eq "--status") {
        $doStatus = $true
    } elseif ($arg -eq "--new-only") {
        $newOnly = $true
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
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    $scriptContent = @"
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
    m = re.search('model==\"([^\"]+)\"', cel.replace(' ', ''))
    if m and provider and model:
        modelName = m.group(1)
        routes[modelName] = {'display': f'{provider}/{model}', 'sonnet': modelName, 'opus': modelName, 'haiku': modelName}
print(json.dumps(routes))
conn.close()
"@
    [System.IO.File]::WriteAllText($tmp, $scriptContent, [System.Text.Encoding]::UTF8)
    try {
        $json = python3 $tmp 2>$null
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
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
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    $scriptContent = @"
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
    [System.IO.File]::WriteAllText($tmp, $scriptContent, [System.Text.Encoding]::UTF8)
    try {
        $json = python3 $tmp 2>$null
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
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

    # Re-enable all routing rules (Bifrost sets enabled=0 on startup)
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    $pythonContent = @"
import sqlite3
conn = sqlite3.connect(r'$env:APPDATA\bifrost\config.db')
c = conn.cursor()
c.execute('UPDATE routing_rules SET enabled = 1')
conn.commit()
print(f'Enabled {c.rowcount} rules')
conn.close()
"@
    [System.IO.File]::WriteAllText($tmp, $pythonContent, [System.Text.Encoding]::UTF8)
    python3 $tmp 2>$null | ForEach-Object { Write-Host "   $_" -ForegroundColor DarkGray }
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
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
    # Wait for Bifrost HTTP endpoint to become responsive (bootstrap takes ~45-60s)
    Write-Host "   Waiting for Bifrost API..." -ForegroundColor DarkGray
    $ready = $false
    for ($i = 0; $i -lt 70; $i++) {
        Start-Sleep -Seconds 1
        try {
            $req = [System.Net.HttpWebRequest]::Create("http://localhost:8080/v1/models")
            $req.Timeout = 3000
            $req.Method = "GET"
            $resp = $req.GetResponse()
            $resp.Close()
            $ready = $true
            break
        } catch {}
    }
    if ($ready) {
        Write-Host "   Bifrost API ready" -ForegroundColor Green
    } else {
        Write-Host "   [WARN] Bifrost API not responding after 70s -- verification skipped" -ForegroundColor Yellow
        return
    }
    Verify-BifrostRouting
}

function Show-BifrostRoutes {
    $scriptPath = "$PSScriptRoot\scripts\routes_probe.py"
    if (-not (Test-Path $scriptPath)) {
        Write-Host "   [ERROR] routes_probe.py not found at $scriptPath" -ForegroundColor Red
        return
    }
    Write-Host ""
    Write-Host "=== CONFIGURED ROUTES ===" -ForegroundColor Yellow
    python3 -u $scriptPath 2>&1
}

function Show-BifrostDashboard {
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

function Show-BifrostStatus {
    Write-Host ""
    Write-Host "=== BIFROST STATUS ===" -ForegroundColor Yellow

    # Daemon status
    $proc = Get-BifrostProcess
    if ($proc) {
        Write-Host "   Daemon:            RUNNING (PID $($proc.Id))" -ForegroundColor Green
    } else {
        Write-Host "   Daemon:            NOT RUNNING" -ForegroundColor Red
    }

    # DB summary via temp file
    $statusCode = @'
import sqlite3, json, os

db = os.path.join(os.environ['APPDATA'], 'bifrost', 'config.db')
conn = sqlite3.connect(db)
c = conn.cursor()

# Rules count
c.execute('SELECT COUNT(*), SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END) FROM routing_rules')
total, enabled = c.fetchone()
enabled = enabled or 0

# Rules with targets
c.execute('SELECT COUNT(DISTINCT r.id) FROM routing_rules r JOIN routing_targets rt ON rt.rule_id = r.id WHERE r.enabled = 1 AND rt.provider IS NOT NULL')
rules_with_targets = c.fetchone()[0] or 0

# Providers that have enabled rules
c.execute('''
    SELECT DISTINCT rt.provider
    FROM routing_targets rt
    JOIN routing_rules r ON r.id = rt.rule_id
    WHERE r.enabled = 1 AND rt.provider IS NOT NULL
''')
providers_with_rules = sorted([row[0] for row in c.fetchall()])

# All config_keys deduplicated by normalized provider name
c.execute('SELECT LOWER(provider) as p, substr(value, 1, 12) FROM config_keys GROUP BY LOWER(provider)')
all_keys = [[row[0], row[1]] for row in c.fetchall()]

# Missing keys (case-insensitive comparison against normalized all_keys)
all_keys_lower = [k[0].lower() for k in all_keys]
missing = [p for p in providers_with_rules if p.lower() not in all_keys_lower]

print(json.dumps({
    'total': total,
    'enabled': enabled,
    'rules_with_targets': rules_with_targets,
    'providers_with_rules': providers_with_rules,
    'all_keys': all_keys,
    'missing_keys': missing
}))
conn.close()
'@

    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    [System.IO.File]::WriteAllText($tmp, $statusCode, [System.Text.Encoding]::UTF8)
    $jsonOut = python3 $tmp 2>$null
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue

    if ($jsonOut) {
        try {
            $data = ConvertFrom-Json $jsonOut
            $total = $data.total; $enabled = $data.enabled

            if ($enabled -eq $total -and $total -gt 0) {
                $ruleColor = "Green"
            } elseif ($enabled -eq 0) {
                $ruleColor = "Red"
            } else {
                $ruleColor = "Yellow"
            }
            Write-Host "   Rules:             $enabled / $total enabled" -ForegroundColor $ruleColor

            $rwt = $data.rules_with_targets
            if ($rwt -eq $total) {
                Write-Host "   Rules with targets: $rwt / $total" -ForegroundColor Green
            } else {
                Write-Host "   Rules with targets: $rwt / $total" -ForegroundColor Red
            }

            $missing = $data.missing_keys
            $keyCount = $data.all_keys.Count
            $pc = $keyCount
            if ($missing.Count -eq 0) {
                Write-Host "   Provider keys:     ALL ALIGNED $pc providers" -ForegroundColor Green
            } else {
                $missingList = $missing -join ", "
                Write-Host "   Provider keys:     MISSING for: $missingList" -ForegroundColor Red
            }

            Write-Host ""
            Write-Host "   Provider -> Key map:" -ForegroundColor White
            $data.all_keys | ForEach-Object {
                $name = $_[0]; $prefix = $_[1]
                Write-Host "     ${name}: ${prefix}..." -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "   [WARN] Could not parse DB output: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   [WARN] Could not query DB" -ForegroundColor Yellow
    }

    # Live probe
    Write-Host ""
    Write-Host "   Live probe:" -ForegroundColor White
    $probeCode = @'
import urllib.request, json

try:
    payload = json.dumps({
        'model': 'M27',
        'messages': [{'role': 'user', 'content': 'test'}],
        'max_tokens': 1,
    }).encode()
    req = urllib.request.Request(
        'http://localhost:8080/v1/chat/completions',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        extra = body.get('extra_fields', {})
        prov = extra.get('provider', '?')
        print('M27: OK  (provider=' + str(prov) + ')')
except urllib.error.HTTPError as e:
    print('HTTP ' + str(e.code) + ': ' + e.read().decode()[:200])
except Exception as e:
    print('ERROR: ' + str(e))
'@

    $tmp2 = [System.IO.Path]::GetTempFileName() + ".py"
    [System.IO.File]::WriteAllText($tmp2, $probeCode, [System.Text.Encoding]::UTF8)
    $probeOut = python3 $tmp2 2>&1
    Remove-Item $tmp2 -Force -ErrorAction SilentlyContinue
    if ($probeOut -match "M27: OK") {
        Write-Host "     $probeOut" -ForegroundColor Green
    } else {
        Write-Host "     $probeOut" -ForegroundColor Red
    }
}

# Verify-BifrostAfterRestart: probes routes after restart to confirm routing chain is functional
function Verify-BifrostRouting {
    Write-Host "   Verifying routes..." -ForegroundColor DarkGray

    $scriptPath = "$PSScriptRoot\scripts\routes_probe.py"
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    [System.IO.File]::WriteAllText($tmp, (Get-Content $scriptPath -Raw), [System.Text.Encoding]::UTF8)
    $out = python3 $tmp 2>&1
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    if ($out) {
        $out -split "`n" | ForEach-Object {
            if ($_ -match ": OK\b|: MISMATCH|: ERROR") {
                Write-Host "     $_" -ForegroundColor Yellow
            } else {
                Write-Host "     $_" -ForegroundColor DarkGray
            }
        }
    }
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

if ($doStatus) {
    Show-BifrostStatus
    return
}

if ($doRoutes) {
    $scriptPath = "$PSScriptRoot\scripts\routes_probe.py"
    if (-not (Test-Path $scriptPath)) {
        Write-Host "   [ERROR] routes_probe.py not found at $scriptPath" -ForegroundColor Red
        return
    }
    if ($newOnly) {
        $output = python3 $scriptPath "--new-only" 2>&1
    } else {
        $output = python3 $scriptPath 2>&1
    }
    $output | ForEach-Object { Write-Host $_ }
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
Write-Host "   cc-bf --routes              probe all routes (DB + runtime latency)" -ForegroundColor White
Write-Host "   cc-bf --routes --new-only   show catalog models with no routing rule" -ForegroundColor White
Write-Host "   cc-bf --status              health check: rules, keys, live probe" -ForegroundColor White
Write-Host "   cc-bf --restart             stop + start + verify routing chain" -ForegroundColor White
Write-Host "   cc-bf --sync                backup + sync rules AND provider keys from config.json" -ForegroundColor White
Write-Host ""
