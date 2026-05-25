param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]] $Args
)

# Bifrost AI Gateway Proxy Configuration Script
# Routes Claude Code through Bifrost's various LLM routes
#
# Usage: cc-bf [model | --flag ...]
#
#   cc-bf                 show config + available routes
#   cc-bf <model>         switch all tiers to <model>
#   cc-bf -m <model>      same as above
#   cc-bf -m o=<model>   switch Opus only
#   cc-bf -m s=<model>   switch Sonnet only
#   cc-bf -m h=<model>   switch Haiku only
#   cc-bf -m c=<model>   set custom /model slot
#   cc-bf --start         start Bifrost daemon + re-enable rules
#   cc-bf --shutdown      stop Bifrost daemon
#   cc-bf --restart       stop + start + verify routing chain
#   cc-bf --status        health check: rules, keys, live probe
#   cc-bf --dashboard     open Bifrost dashboard in browser
#   cc-bf --routes              probe all routes (DB + runtime latency)
#   cc-bf --routes --only mistral          routed + unrouted for provider(s)
#   cc-bf --routes yes --only mistral      routed only for provider(s)
#   cc-bf --routes no --only mistral       unrouted only for provider(s)
#   cc-bf --routes no                      show all unrouted catalog models
#   cc-bf --routes no --latest-only        hide superseded versions
#   cc-bf --routes no --exclude X,Y        exclude models containing X or Y
#   cc-bf --routes --only all --exclude hugging  all providers except one
#   cc-bf --sync                backup + sync rules AND provider keys from config.json
#
# Available routes are dynamically loaded from the Bifrost DB at runtime.

# --- SECURITY: Load Secrets from Vault ---
$envPath = "P:\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
} else {
    Write-Host "[WARN] No .env file found at $envPath. Using fallbacks." -ForegroundColor Yellow
}

$env:ANTHROPIC_BASE_URL = "http://localhost:8080/anthropic"
if (-not $env:BIFROST_API_KEY) {
    $env:BIFROST_API_KEY = "sk-bf-49998d75-3b06-4e72-8547-741cb81b497e"
}
$env:ANTHROPIC_API_KEY = $env:BIFROST_API_KEY

if (-not $env:ANTHROPIC_AUTH_TOKEN) {
    $env:ANTHROPIC_AUTH_TOKEN = "sk-cp-KaSmY8e9E1Pw9XbCWOiVexNvnLGwmKJ8fBGf57gEvA3fb95gq73n7AGVyIL3zBrjvFzxRQFyocfa8QdgborzQoupFzI0UX5cjw7MCkIY3DCy5-kAFVza5z8"
}

# Default: all tiers to MiniMax-M2.7 (Bifrost routing key -> MiniMax/MiniMax-M2.7)
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "MiniMax-M2.7"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL = "GLM-5.1"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "MiniMax-M2.7"

$doSync = $false
$doStart = $false
$doRestart = $false
$doShutdown = $false
$doDashboard = $false
$doRoutes = $false
$doStatus = $false
$newOnly = $false
$latestOnly = $true  # default: hide superseded versions
$modelOverride = $null
$tierOverrides = @{}
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
        # Check if next arg is yes/no value
        if ($i + 1 -lt $Args.Count -and $Args[$i + 1] -match '^(yes|no)$') {
            $routesValue = $Args[$i + 1]
            $i++
        }
    } elseif ($arg -eq "--status") {
        $doStatus = $true
    } elseif ($arg -eq "--new-only") {
        $newOnly = $true
    } elseif ($arg -eq "--latest-only") {
        $latestOnly = $true
    } elseif ($arg -eq "--exclude") {
        $i++
        if ($i -lt $Args.Count) {
            $excludeTerms = $Args[$i]
        }
    } elseif ($arg -eq "--only") {
        $i++
        if ($i -lt $Args.Count) {
            $onlyProviders = $Args[$i]
        }
    } elseif ($arg -eq "--model" -or $arg -eq "-m") {
        $i++
        if ($i -lt $Args.Count) {
            $nextArg = $Args[$i]
            # Check for tier prefix: o=opus, s=sonnet, h=haiku, c=custom
            if ($nextArg -match "^([oshc])=(.+)$") {
                $tier = $matches[1]
                $tierModel = $matches[2]
                $tierOverrides[$tier] = $tierModel
            } else {
                $modelOverride = $nextArg
            }
        }
    } elseif ($arg -match "^--model=(.+)$") {
        $modelOverride = $matches[1]
    } elseif ($arg -match "^[a-zA-Z0-9_.\-]+$") {
        if (-not $modelOverride) { $modelOverride = $arg }
    }
    $i++
}

# Query the Bifrost DB using the persistent helper script
$_db_script = "$PSScriptRoot\scripts\bifrost_db.py"

function Get-BifrostRoutesFromDb {
    if (-not (Test-Path $_db_script)) {
        Write-Host "[WARN] bifrost_db.py not found at $_db_script" -ForegroundColor Yellow
        return @{}
    }
    try {
        $json = python $_db_script --get-routes 2>$null
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
    if (-not (Test-Path $_db_script)) {
        Write-Host "[WARN] bifrost_db.py not found at $_db_script" -ForegroundColor Yellow
        return @()
    }
    try {
        $json = python $_db_script --get-rules 2>$null
        if ($json) {
            $data = ConvertFrom-Json $json
            return $data.rules
        }
    } catch {
        Write-Host "[WARN] Failed to query DB: $_" -ForegroundColor Yellow
    }
    return @()
}

# Known catalog provider names (case-sensitive — Bifrost catalog uses exact spelling)
$CATALOG_PROVIDERS = @{
    "cerebras" = $true
    "gemini"   = $true
    "groq"     = $true
    "mistral"  = $true
    "openrouter" = $true
    "Minimax"  = $true   # custom (capital M)
    "Nvidia"   = $true   # custom (capital N)
    "Z.AI"     = $true   # custom (with dot)
}

function Test-BifrostRuleTarget {
    param([hashtable]$rule)
    foreach ($target in @($rule.targets)) {
        $provider = $target.provider
        if ($provider -and -not $CATALOG_PROVIDERS.ContainsKey($provider)) {
            return $false
        }
        $model = $target.model
        if (-not $model -or $model.Trim() -eq "") {
            return $false
        }
    }
    return $true
}

function Sync-BifrostConfig {
    $configPath = "$env:APPDATA\bifrost\config.json"
    $backupPath = "$env:APPDATA\bifrost\config.backup_$(Get-Date -f 'yyyyMMdd-HHmmss').json"

    # Pre-write cleanup: remove stale keys and orphan providers before syncing
    $cleanupResult = & python "$PSScriptRoot\scripts\bifrost_db.py" --cleanup 2>$null
    if ($LASTEXITCODE -eq 0 -and $cleanupResult) {
        try {
            $j = $cleanupResult | ConvertFrom-Json
            $k = $j.stale_keys.deleted
            $p = $j.orphan_providers.deleted
            if ($k -gt 0 -or $p -gt 0) {
                Write-Host "   [CLEANUP] Removed $k stale key(s), $p orphan provider(s)" -ForegroundColor Cyan
            }
        } catch { }
    }

    if (Test-Path $configPath) {
        Copy-Item $configPath $backupPath -Force
        Write-Host "   Backed up config.json -> $backupPath" -ForegroundColor White
    }

    $rules = Get-BifrostRulesFromDb
    if ($rules.Count -eq 0) {
        Write-Host "   [ERROR] No rules found in DB" -ForegroundColor Red
        return
    }

    # Filter to catalog-valid targets only (clean_sync: skip rules referencing non-catalog providers)
    $cleanRules = @()
    $skipped = 0
    foreach ($rule in $rules) {
        if (Test-BifrostRuleTarget $rule) {
            $cleanRules += $rule
        } else {
            $skipped++
            $p = $rule.targets | ForEach-Object { $_.provider } | Sort-Object -Unique
            Write-Host "   [SKIP] Rule '$($rule.name)' references non-catalog provider(s): $($p -join ', ')" -ForegroundColor Yellow
        }
    }

    if ($skipped -gt 0) {
        Write-Host "   Skipped $skipped rules with non-catalog provider targets" -ForegroundColor Yellow
    }

    $config = @{
        '$schema' = "https://www.getbifrost.ai/schema"
        version   = 1
        providers = @{}
        governance = @{
            routing_rules = @($cleanRules)
        }
    }

    $cleanConfig = $config | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($configPath, $cleanConfig, [System.Text.Encoding]::UTF8)

    # Read-back verification to confirm write succeeded and Bifrost can parse it
    if (-not (Test-Path $configPath)) {
        Write-Host "   [ERROR] config.json write verification failed -- file not found after write" -ForegroundColor Red
        return
    }
    try {
        $verifyContent = Get-Content $configPath -Raw -ErrorAction Stop
        $verifyJson = ConvertFrom-Json $verifyContent -ErrorAction Stop
        if ($verifyJson.governance.routing_rules.Count -ne $cleanRules.Count) {
            Write-Host "   [ERROR] config.json write verification failed -- rule count mismatch" -ForegroundColor Red
            return
        }
    } catch {
        Write-Host "   [ERROR] config.json write verification failed -- parse error: $_" -ForegroundColor Red
        return
    }
    Write-Host "   Synced $($cleanRules.Count) catalog-valid rules ($skipped non-catalog skipped) -> config.json" -ForegroundColor Green
}

# --- ORCHESTRATION: Strict PID Management ---
$pidFile = "$env:APPDATA\bifrost\bifrost.pid"

function Get-BifrostProcess {
    # Check for active PowerShell job first (primary mechanism after sync-call change)
    $jobs = Get-Job -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Running' -and $_.Output.Count -eq 0 }
    foreach ($j in $jobs) {
        $info = Receive-Job -Job $j -Keep -ErrorAction SilentlyContinue
    }
    $runningJob = Get-Job -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Running' } | Select-Object -First 1
    if ($runningJob) { return $runningJob }

    # Fallback: check pidFile for legacy PID-based process
    if (Test-Path $pidFile) {
        $savedPid = Get-Content $pidFile
        $proc = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -like "*bifrost*") { return $proc }
        Remove-Item $pidFile -Force # Stale PID cleanup
    }

    # Last resort: scan for any bifrost-http process by name
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*bifrost*" }
    if ($procs) { return ($procs | Select-Object -First 1) }

    return $null
}

function Start-BifrostDaemon {
    $proc = Get-BifrostProcess
    if ($proc) {
        $id = if ($proc.Id) { $proc.Id } else { $proc.InstanceId }
        Write-Host "   Bifrost already running (Job/PID $id)" -ForegroundColor Yellow
        return
    }
    $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.4\bin\bifrost-http.exe-0"
    if (-not (Test-Path $bifrostBin)) {
        $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.2\bin\bifrost-http.exe-0"
    }
    if (-not (Test-Path $bifrostBin)) {
        $bifrostBin = "$env:LOCALAPPDATA\bifrost\v1.5.0-prerelease8\bin\bifrost-http.exe-0"
    }
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
    $env:BIFROST_ENV = "1"
    $proc = Start-Process -FilePath $bifrostBin -ArgumentList "-app-dir=$appDir","-port=8080" -NoNewWindow -PassThru -RedirectStandardError $errLog
    Start-Sleep -Milliseconds 500
    if ($proc.HasExited) {
        Write-Host "   [ERROR] Failed to start Bifrost. Exit code: $($proc.ExitCode). Check $errLog" -ForegroundColor Red
    } else {
        $proc.Id | Out-File $pidFile -Encoding UTF8
        Write-Host "   Started Bifrost (PID $($proc.Id)) on port 8080" -ForegroundColor Green
        try { python $_db_script --enable-rules 2>$null | Out-Null } catch {}
    }
}

function Stop-BifrostDaemon {
    $proc = Get-BifrostProcess
    if (-not $proc) {
        Write-Host "   Bifrost is not running" -ForegroundColor Yellow
        return
    }
    if ($proc -is [System.Management.Automation.Job2]) {
        # PowerShell job
        Stop-Job -Id $proc.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        Write-Host "   Stopped Bifrost (Job ID $($proc.Id))" -ForegroundColor Green
    } else {
        # Legacy PID-based process
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        Write-Host "   Stopped Bifrost (PID $($proc.Id))" -ForegroundColor Green
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
        Write-Host "   [ERROR] Bifrost API not responding after 70s -- restart failed" -ForegroundColor Red
        exit 1
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
    python -u $scriptPath 2>&1
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

    # DB summary via bifrost_db.py
    try {
        $jsonOut = python $_db_script --status 2>$null
    } catch {
        $jsonOut = $null
    }

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
import urllib.request, json, sys

models = ['M27', 'GLM-5.1']
for model in models:
    try:
        payload = json.dumps({
            'model': model,
            'messages': [{'role': 'user', 'content': 'test'}],
            'max_tokens': 1,
        }).encode()
        req = urllib.request.Request(
            'http://localhost:8080/v1/chat/completions',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            extra = body.get('extra_fields', {})
            prov = extra.get('provider', '?')
            lat = extra.get('latency', '?')
            print(f'{model}: OK  (provider={prov}, latency={lat}ms)')
    except urllib.error.HTTPError as e:
        print(f'{model}: HTTP {e.code} - {e.read().decode()[:200]}')
    except Exception as e:
        print(f'{model}: ERROR - {e}')
'@

    $tmp2 = $null
    try {
        $tmp2 = [System.IO.Path]::GetTempFileName() + ".py"
        [System.IO.File]::WriteAllText($tmp2, $probeCode, [System.Text.Encoding]::UTF8)
        $probeOut = python $tmp2 2>&1
    } finally {
        if ($tmp2 -and (Test-Path $tmp2)) {
            Remove-Item $tmp2 -Force -ErrorAction SilentlyContinue
        }
    }
    $probeOut | ForEach-Object {
        if ($_ -match ": OK\b") {
            Write-Host "     $_" -ForegroundColor Green
        } else {
            Write-Host "     $_" -ForegroundColor Red
        }
    }
}

# Verify-BifrostAfterRestart: probes routes after restart to confirm routing chain is functional
function Verify-BifrostRouting {
    Write-Host "   Verifying routes..." -ForegroundColor DarkGray

    $scriptPath = "$PSScriptRoot\scripts\routes_probe.py"
    $tmp = $null
    try {
        $tmp = [System.IO.Path]::GetTempFileName() + ".py"
        [System.IO.File]::WriteAllText($tmp, (Get-Content $scriptPath -Raw), [System.Text.Encoding]::UTF8)
        $out = python $tmp 2>&1
    } finally {
        if ($tmp -and (Test-Path $tmp)) {
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        }
    }
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
    $pyArgs = @()
    if ($newOnly) { $pyArgs += "--new-only" }
    if ($routesValue) { $pyArgs += "--routes", $routesValue }
    if ($latestOnly) { $pyArgs += "--latest-only" }
    if ($excludeTerms) { $pyArgs += "--exclude", $excludeTerms }
    if ($onlyProviders) { $pyArgs += "--only", $onlyProviders }
    $output = python $scriptPath @pyArgs 2>&1
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
}
foreach ($alias in $aliasMap.Keys) {
    $target = $aliasMap[$alias]
    if ($routingTable.ContainsKey($target)) {
        $entry = $routingTable[$target]
        $routes[$alias] = @($target, $target, $target, $entry.display)
    }
}

function Resolve-ModelName($name) {
    $normalized = $name -replace "^glm-5.1$", "GLM-5.1" `
                       -replace "^MiniMax-M2.7$", "M27" `
                       -replace "^Nvidia-Deepseek-v4-flash$", "DSv4-flash" `
                       -replace "^DSv4-flash$", "DSv4"
    if ($routes.ContainsKey($normalized)) {
        return $routes[$normalized][3]  # display name (provider/model)
    }
    return $name
}

if ($modelOverride) {
    $normalizedKey = $modelOverride -replace "^glm-5.1$", "GLM-5.1" `
                                    -replace "^MiniMax-M2.7$", "M27" `
                                    -replace "^Nvidia-Deepseek-v4-flash$", "DSv4-flash" `
                                    -replace "^DSv4-flash$", "DSv4"

    if ($routes.ContainsKey($normalizedKey)) {
        $route = $routes[$normalizedKey]
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $normalizedKey  # routing key — ensures CEL rule fires
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = $normalizedKey
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $normalizedKey
        $displayName = "$normalizedKey → $($route[3])"
    } else {
        # Unknown model — pass through as-is (Bifrost will reject or route as-is)
        $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $modelOverride
        $env:ANTHROPIC_DEFAULT_OPUS_MODEL = $modelOverride
        $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $modelOverride
        $displayName = "Custom: $modelOverride"
    }
}

# Per-tier overrides: -m o=<model>, -m s=<model>, -m h=<model>
if ($tierOverrides.ContainsKey("o")) {
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL = $tierOverrides["o"]
}
if ($tierOverrides.ContainsKey("s")) {
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $tierOverrides["s"]
}
if ($tierOverrides.ContainsKey("h")) {
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = $tierOverrides["h"]
}
if ($tierOverrides.ContainsKey("c")) {
    $customModel = $tierOverrides["c"]
    # Normalize only for the API model name
    $normalizedC = $customModel -replace "^glm-5.1$", "GLM-5.1" `
                                -replace "^MiniMax-M2.7$", "M27" `
                                -replace "^Nvidia-Deepseek-v4-flash$", "DSv4-flash" `
                                -replace "^DSv4-flash$", "DSv4"
    $env:ANTHROPIC_CUSTOM_MODEL_OPTION = $normalizedC
    $env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME = $customModel  # show original name
    # Check routes using the original input key (DB stores N-DSv4-flash, not DSv4)
    if ($routes.ContainsKey($customModel)) {
        $env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "Bifrost: $($routes[$customModel][3])"
    } else {
        $env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION = "Custom route via Bifrost"
    }
}

if (-not $modelOverride -and $tierOverrides.Count -eq 0) {
    $displayName = "Default (M27)"
} elseif ($tierOverrides.Count -gt 0) {
    $displayName = "Custom tiers"
}

Write-Host ""
Write-Host "Bifrost Configuration:" -ForegroundColor Yellow
$baseRows = @(
    @{ Label = "   - Sonnet:"; Value = $env:ANTHROPIC_DEFAULT_SONNET_MODEL },
    @{ Label = "   - Opus:"; Value = $env:ANTHROPIC_DEFAULT_OPUS_MODEL },
    @{ Label = "   - Haiku:"; Value = $env:ANTHROPIC_DEFAULT_HAIKU_MODEL }
)
$configRows = @(
    @{ Label = "   - Provider:"; Value = "Bifrost AI Gateway" },
    @{ Label = "   - Endpoint:"; Value = "http://localhost:8080/anthropic" }
)
$customName = if ($env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME) { $env:ANTHROPIC_CUSTOM_MODEL_OPTION_NAME } elseif ($env:ANTHROPIC_CUSTOM_MODEL_OPTION) { $env:ANTHROPIC_CUSTOM_MODEL_OPTION } else { "—" }
$customDesc = if ($env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION) { $env:ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION } else { "" }
$configRows += @{ Label = "   - Custom:"; Value = $customName }
if ($customDesc) {
    $configRows += @{ Label = "     Description:"; Value = $customDesc }
}
foreach ($row in $baseRows) { $configRows += $row }
$configRows | ForEach-Object {
    $row = $_
    $padLabel = $row.Label.PadRight(20)
    Write-Host "$padLabel $($row.Value)" -ForegroundColor White
}
Write-Host ""
Write-Host "Available routes (from DB):" -ForegroundColor Yellow
if ($routes.Count -eq 0) {
    Write-Host "   [no routes loaded from DB]" -ForegroundColor Red
} else {
    # Build reverse map: target display -> list of keys that point to it
    # Use dot notation to access JSON field names (PowerShell deserializes JSON dict values as PSObjects)
    $targetGroups = @{}
    foreach ($key in $routes.Keys) {
        $route = $routes[$key]
        $targetKey = $route[3]
        if ([string]::IsNullOrWhiteSpace($targetKey)) { continue }
        if (-not $targetGroups.ContainsKey($targetKey)) {
            $targetGroups[$targetKey] = [System.Collections.ArrayList]@()
        }
        [void]$targetGroups[$targetKey].Add($key)
    }
    # Find which keys are aliases (not in routingTable directly)
    $aliasKeys = @()
    foreach ($alias in $aliasMap.Keys) {
        $aliasKeys += $alias
    }
    # Collect canonical names for each unique target
    $seen = @{}
    $canonicalNames = @()
    foreach ($key in $routes.Keys) {
        $route = $routes[$key]
        $desc = $route[3]
        if ([string]::IsNullOrWhiteSpace($desc)) { continue }
        if ($seen.ContainsKey($desc)) { continue }
        $seen[$desc] = $true
        $group = $targetGroups[$desc]
        $canonicals = @($group | Where-Object { $_ -notin $aliasKeys } | Sort-Object { $_.Length } -Descending)
        $canonical = if ($canonicals.Count -gt 0) { $canonicals[0] } else { @($group | Sort-Object { $_.Length } -Descending)[0] }
        $canonicalNames += $canonical
    }

    # Sort canonical names by priority (ascending = lowest priority first, matches UI)
    # Filter to enabled-only rules
    # Route canonical names differ from rule names (rule name = "zai-glm-5.1", route key = "glm-5.1")
    # Build a display-name -> priority map from rules to enable matching
    $rulesData = Get-BifrostRulesFromDb | Where-Object { $_.enabled -eq 1 }
    $displayPriority = @{}
    foreach ($r in $rulesData) {
        if ($r.targets.Count -gt 0) {
            $target = $r.targets[0]
            $displayName = "$($target.provider)/$($target.model)"
            $displayPriority[$displayName] = $r.priority
        }
    }
    # Use display priority for sort (routes point to same display target)
    $enabledCanons = $canonicalNames | Where-Object {
        $canonical = $_
        $route = $routes[$canonical]
        $desc = $route[3]
        $displayPriority.ContainsKey($desc)
    }
    $sortedCanonicalNames = $enabledCanons | Sort-Object {
        $canonical = $_
        $displayPriority[$routes[$canonical][3]]
    }

    # Format-Table handles column widths automatically
    $tableData = foreach ($canonical in $sortedCanonicalNames) {
        $route = $routes[$canonical]
        if (-not $route) { continue }
        $desc = $route[3]
        if ([string]::IsNullOrWhiteSpace($desc)) { continue }
        $group = $targetGroups[$desc]
        $aliases = @($group | Where-Object { $_ -ne $canonical })
        $aliasStr = if ($aliases.Count -gt 0) { "  ($($aliases -join ', '))" } else { "" }
        [PSCustomObject]@{
            Command = "cc-bf $canonical"
            Route   = "-> $desc$aliasStr"
        }
    }

    $tableData | Format-Table -AutoSize | Out-String | ForEach-Object { Write-Host $_ -ForegroundColor Cyan }
}
function Get-DisplayWidth($s) {
    $w = 0
    foreach ($c in $s.GetEnumerator()) {
        $o = [int]$c
        if ($o -ge 0x110000) { $w += 2 }
        elseif ($o -ge 0x100 -and $o -le 0x115F) { $w += 1 }
        elseif ($o -eq 0x2329 -or $o -eq 0x232A) { $w += 2 }
        elseif ($o -ge 0xAC00 -and $o -le 0xD7A3) { $w += 2 }
        elseif ($o -ge 0x3000 -and $o -le 0x303F) { $w += 2 }
        elseif ($o -ge 0xFF00 -and $o -le 0xFF60) { $w += 2 }
        elseif ($o -ge 0xFFE0 -and $o -le 0xFFE6) { $w += 2 }
        else { $w += 1 }
    }
    return $w
}

function Write-HelpRow($cmd, $desc, $totalWidth) {
    $displayLen = Get-DisplayWidth($cmd)
    $spaces = $totalWidth - $displayLen
    Write-Host ($cmd + (' ' * $spaces) + $desc) -ForegroundColor White
}

Write-Host "Commands:" -ForegroundColor Yellow

$shortMaxDisplay = 24
$shortItems = @(
    @{Cmd="cc-bf";                        Desc="show config + available routes"},
    @{Cmd="cc-bf <model>";               Desc="switch all tiers to <model>"},
    @{Cmd="cc-bf -m <model>";            Desc="same as above"},
    @{Cmd="cc-bf -m o=<model>";          Desc="switch Opus only"},
    @{Cmd="cc-bf -m s=<model>";          Desc="switch Sonnet only"},
    @{Cmd="cc-bf -m h=<model>";          Desc="switch Haiku only"},
    @{Cmd="cc-bf -m c=<model>";          Desc="set custom /model slot"}
)

$shortItems | ForEach-Object { Write-HelpRow $_.Cmd $_.Desc $shortMaxDisplay }
Write-Host ""

$daemonMaxDisplay = 24
$daemonItems = @(
    @{Cmd="cc-bf --start";               Desc="start Bifrost daemon + re-enable rules"},
    @{Cmd="cc-bf --shutdown";            Desc="stop Bifrost daemon"},
    @{Cmd="cc-bf --restart";             Desc="stop + start + verify routing chain"},
    @{Cmd="cc-bf --status";             Desc="health check: rules, keys, live probe"},
    @{Cmd="cc-bf --dashboard";           Desc="open Bifrost dashboard in browser"}
)

$daemonItems | ForEach-Object { Write-HelpRow $_.Cmd $_.Desc $daemonMaxDisplay }
Write-Host ""

$routeMaxDisplay = 50
$routeItems = @(
    @{Cmd="cc-bf --routes";                            Desc="probe all routes (DB + runtime latency)"},
    @{Cmd="cc-bf --routes --only <provider>";          Desc="filter routes to one provider (mistral/oprouter/groq/nvidia/zai/minimax)"},
    @{Cmd="cc-bf --routes yes --only <provider>";       Desc="show only routed models for a provider"},
    @{Cmd="cc-bf --routes no --only <provider>";       Desc="show only unrouted models for a provider"},
    @{Cmd="cc-bf --routes no";                        Desc="show all unrouted catalog models"},
    @{Cmd="cc-bf --routes no --latest-only";          Desc="hide superseded versions"},
    @{Cmd="cc-bf --routes no --exclude X,Y";          Desc="exclude models containing X or Y"},
    @{Cmd="cc-bf --routes --only all --exclude hugging"; Desc="all providers except one"},
    @{Cmd="cc-bf --sync";                             Desc="backup + sync rules AND provider keys from config.json"}
)
$routeItems | ForEach-Object { Write-HelpRow $_.Cmd $_.Desc $routeMaxDisplay }
