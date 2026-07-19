# Start the shared AgentGateway process once, in its own minimized console.

[CmdletBinding()]
param(
    [switch]$Run,
    [switch]$Stop
)

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $here 'agentgateway.exe'
$config = Join-Path $here 'config.yaml'
$envFile = 'P:\.env'
$mcpPort = 3000
$uiPort = 15000

if ($Stop) {
    & (Join-Path $here 'agentgateway-stop.ps1')
    return
}

if (-not (Test-Path -LiteralPath $exe)) {
    Write-Warning "[agentgateway] binary not found: $exe"
    Write-Host '[agentgateway] Download the Windows binary from:' -ForegroundColor Yellow
    Write-Host 'https://github.com/agentgateway/agentgateway/releases' -ForegroundColor Yellow
    return
}
if (-not (Test-Path -LiteralPath $config)) {
    Write-Warning "[agentgateway] config not found: $config"
    return
}

function Get-AgentGatewayListener {
    Get-NetTCPConnection -LocalPort $mcpPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

if (-not $Run) {
    $mutex = [System.Threading.Mutex]::new($false, 'Global\CodexAgentGatewayStart')
    $mutexHeld = $false
    try {
        try { $mutexHeld = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $mutexHeld = $true }
        if (-not $mutexHeld) {
            Write-Host '[agentgateway] another terminal is already checking or starting it' -ForegroundColor DarkGray
            return
        }

        $listener = Get-AgentGatewayListener
        if ($listener) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
            if ($owner -and $owner.CommandLine -match '(?i)agentgateway(\.exe)?') {
                Write-Host "[agentgateway] already running: PID $($listener.OwningProcess), MCP http://127.0.0.1:$mcpPort/mcp" -ForegroundColor DarkGray
                return
            }
            Write-Warning "[agentgateway] port $mcpPort is already owned by PID $($listener.OwningProcess); refusing to start."
            return
        }

        # Load only credentials required by the configured MCP targets.
        $allowedEnvKeys = @('CONTEXT7_API_KEY', 'BRAVE_API_KEY', 'ZAI_API_KEY', 'Z_AI_API_KEY', 'Z_AI_URL')
        if (Test-Path -LiteralPath $envFile) {
            Get-Content -LiteralPath $envFile | ForEach-Object {
                if ($_ -match '^\s*([^#=][^=]*)=(.*)$') {
                    $key = $Matches[1].Trim()
                    if ($key -notin $allowedEnvKeys) { return }
                    $value = $Matches[2].Trim()
                    if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                    [Environment]::SetEnvironmentVariable($key, $value, 'Process')
                }
            }
        }

        Start-Process -FilePath 'pwsh.exe' -ArgumentList @(
            '-NoProfile', '-NoLogo', '-NonInteractive', '-File', $MyInvocation.MyCommand.Path, '-Run'
        ) -WindowStyle Minimized | Out-Null

        $deadline = (Get-Date).AddSeconds(20)
        while ((Get-Date) -lt $deadline) {
            $listener = Get-AgentGatewayListener
            if ($listener) {
                Write-Host "[agentgateway] started: MCP http://127.0.0.1:$mcpPort/mcp (PID $($listener.OwningProcess)); UI http://127.0.0.1:$uiPort/ui" -ForegroundColor Green
                return
            }
            Start-Sleep -Milliseconds 500
        }
        Write-Warning '[agentgateway] process did not bind port 3000 within 20 seconds; check its console window.'
    } finally {
        if ($mutexHeld) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
    return
}

$Host.UI.RawUI.WindowTitle = 'AgentGateway MCP: 3000'
& $exe -f $config
