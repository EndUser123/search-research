param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]] $Args
)

# Bifrost AI Gateway Proxy Configuration Script
# Routes Claude Code through Bifrost's various LLM routes
# Usage: cc-bf [--sync] [model]
#
# --sync   : backup current config.json, then sync routing rules from DB to config.json
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
$modelOverride = $null
$i = 0
while ($i -lt $Args.Count) {
    $arg = $Args[$i]
    if ($arg -eq "--sync") {
        $doSync = $true
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
    m = re.search(r'model\s*==\s*\"([^\"]+)\"', cel)
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
                # PowerShell 7+ with -AsHashtable
                $data.psobject.properties | ForEach-Object { $ht[$_.Name] = $_.Value }
            } catch {
                # Fallback: enumerate as PSCustomObject
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

# Load routes from DB
$routingTable = Get-BifrostRoutesFromDb

if ($doSync) {
    Sync-BifrostConfig
    # Reload after sync
    $routingTable = Get-BifrostRoutesFromDb
}

# Build the $routes hashtable for alias resolution
$routes = @{}

# Add all model names as their own aliases
foreach ($modelName in $routingTable.Keys) {
    $entry = $routingTable[$modelName]
    $routes[$modelName] = @($modelName, $modelName, $modelName, $entry.display)
}

# Aliases for routes with multiple shortcut names
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

# Apply model override
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