<#
.SYNOPSIS
    Shared library for claude-code-proxy management scripts.
    Provides state tracking for running proxies.

.NOTES
    State file: proxy-state.json in the same directory as the caller.
#>
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateFile = Join-Path $ScriptDir "proxy-state.json"

# ─── Config metadata ────────────────────────────────────────────────────────────
# Maps config name → orchestrator label shown in menus
$Global:ConfigLabels = @{
    anthropic = "Anthropic"
    glm       = "GLM-4.7"
    m27       = "MiniMax-M2.7"
}

# ─── State file helpers ───────────────────────────────────────────────────────

function Get-RunningProxies {
    if (-not (Test-Path $StateFile)) { return @() }
    try {
        $json = Get-Content $StateFile -Raw -ErrorAction Stop
        $data = $json | ConvertFrom-Json -ErrorAction Stop
        $result = @()
        foreach ($prop in $data.PSObject.Properties) {
            $rawName = $prop.Name
            # Skip PSObject metadata properties
            if ($rawName -match '^(IsReadOnly|Keys|Count|IsFixedSize|Values|SyncRoot|IsSynchronized)$') { continue }
            # Normalize port: handle both clean "3001" and corrupted "[string]3001" keys
            if ($rawName -match '^\[string\](\d+)$') { $port = [int]$Matches[1] }
            elseif ($rawName -match '^\d+$') { $port = [int]$rawName }
            else { continue }
            $entry = $prop.Value
            $result += [PSCustomObject]@{
                Port    = $port
                Config  = $entry.config
                PID     = [int]$entry.pid
                Started = $entry.started
            }
        }
        return $result
    } catch {
        return @()
    }
}

function Update-ProxyState {
    param([int]$Port, [string]$Config, [int]$NewPID)

    $data = @{}
    if (Test-Path $StateFile) {
        try {
            $json = Get-Content $StateFile -Raw -ErrorAction Stop
            $data = $json | ConvertFrom-Json -ErrorAction Stop
        } catch { }
    }

    # Use "$Port" (string value of port number) as key — NOT "[string]$Port"
    $data | Add-Member -Force -NotePropertyName "$Port" -NotePropertyValue ([PSCustomObject]@{
        config  = $Config
        pid     = $NewPID
        started = (Get-Date -Format "o")
    }) -ErrorAction SilentlyContinue

    # Rebuild as a clean hashtable for JSON serialization
    $clean = @{}
    foreach ($prop in $data.PSObject.Properties) {
        $rawName = $prop.Name
        if ($rawName -match '^(IsReadOnly|Keys|Count|IsFixedSize|Values|SyncRoot|IsSynchronized)$') { continue }
        if ($rawName -match '^\[string\](\d+)$') { $clean[$Matches[1]] = $prop.Value }
        elseif ($rawName -match '^\d+$') { $clean[$rawName] = $prop.Value }
    }
    $clean | ConvertTo-Json -Depth 3 | Set-Content $StateFile -Encoding UTF8
}

function Remove-FromProxyState {
    param([int]$Port)

    if (-not (Test-Path $StateFile)) { return }
    try {
        $json = Get-Content $StateFile -Raw -ErrorAction Stop
        $data = $json | ConvertFrom-Json -ErrorAction Stop
        $data.PSObject.Properties.Remove("$Port")
        $clean = @{}
        foreach ($prop in $data.PSObject.Properties) {
            $rawName = $prop.Name
            if ($rawName -match '^(IsReadOnly|Keys|Count|IsFixedSize|Values|SyncRoot|IsSynchronized)$') { continue }
            if ($rawName -match '^\[string\](\d+)$') { $clean[$Matches[1]] = $prop.Value }
            elseif ($rawName -match '^\d+$') { $clean[$rawName] = $prop.Value }
        }
        if ($clean.Count -eq 0) {
            Remove-Item $StateFile -Force -ErrorAction SilentlyContinue
        } else {
            $clean | ConvertTo-Json -Depth 3 | Set-Content $StateFile -Encoding UTF8
        }
    } catch { }
}

function Get-PidForPort {
    param([int]$Port)
    $netstat = netstat -ano | Select-String "LISTENING" | Select-String ":$Port\b"
    if (-not $netstat) { return $null }
    foreach ($line in $netstat) {
        $parts = $line -split '\s+'
        $pidCandidate = $parts[-1]
        if ($pidCandidate -match '^\d+$') { return [int]$pidCandidate }
    }
    return $null
}

# ─── Config summary helper ─────────────────────────────────────────────────────
function Get-ConfigSummary {
    param([string]$Config)

    $cfgFile = Join-Path $ScriptDir "config-$Config.yaml"
    if (-not (Test-Path $cfgFile)) { return $null }

    try {
        $yaml = Get-Content $cfgFile -Raw

        # Extract anthropic.base_url (the orchestrator/driver URL)
        # Use positional extraction: find providers block, then anthropic within it,
        # then base_url after anthropic. Avoids regex non-greedy ambiguity issues.
        $orchUrl = $null
        $provIdx = $yaml.IndexOf('providers:')
        if ($provIdx -ge 0) {
            $endIdx = $yaml.IndexOf('storage:', $provIdx)
            if ($endIdx -lt 0) { $endIdx = $yaml.Length }
            $providersBlock = $yaml.Substring($provIdx, $endIdx - $provIdx)
            $anthIdx = $providersBlock.IndexOf('anthropic:')
            if ($anthIdx -ge 0) {
                $afterAnth = $providersBlock.Substring($anthIdx)
                if ($afterAnth -match 'base_url\s*:\s*"([^"]+)"') {
                    $orchUrl = $matches[1]
                }
            }
        }

        # Extract subagent mappings
        # Use [\w-]+ for key names (subagents like tdd-test-writer contain hyphens)
        # Stop at \nstorage: boundary to avoid regex non-greedy ambiguity with comments
        $subagents = @{}
        if ($yaml -match 'subagents[\s\S]*?mappings\s*:\s*([\s\S]*?)(?=\nstorage:|\Z)') {
            $mappingBlock = $matches[1]
            foreach ($line in $mappingBlock -split '\n') {
                if ($line -match '^\s*([\w-]+)\s*:\s*"([^"]+)"') {
                    $subagents[$matches[1]] = $matches[2]
                }
            }
        }

        return @{
            OrchUrl   = $orchUrl
            Subagents = $subagents
        }
    } catch {
        return $null
    }
}
