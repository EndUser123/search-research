# grok.ps1 — PowerShell wrapper that loads P:/.env into the process environment
# before launching the real Grok Build binary.
#
# This makes env_key references in config.toml work for model entries that use
# env_key instead of literal api_key. It also makes all keys in P:/.env available
# to every tool and subagent that Grok spawns.
#
# Install: put this script in a directory that is earlier on $PATH than
# ~/.grok/bin/, or shadow the binary by placing this in the same bin/ dir
# and renaming the real binary to grok-real.exe. The simplest approach is
# to add a directory like ~/bin or P:/scripts to the front of $PATH and
# place this file there.
#
# Existing env vars take precedence over .env values — if you set a var
# manually in your shell, it wins over what's in .env.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$envFile = "P:/.env"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        # Skip blank lines and comments
        if (-not $line -or $line.StartsWith('#')) { return }

        # Match KEY="value" (quoted)
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"\s*$') {
            $key = $Matches[1]
            $val = $Matches[2]
            # Only set if not already in env (manual shell values win)
            if (-not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
                Set-Item -Path "Env:$key" -Value $val
            }
        }
        # Match KEY=value (unquoted)
        elseif ($line -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$') {
            $key = $Matches[1]
            $val = $Matches[2]
            if (-not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
                Set-Item -Path "Env:$key" -Value $val
            }
        }
    }
}

# Launch the real Grok binary with all passed arguments
$grokExe = "$env:USERPROFILE/.grok/bin/grok.exe"
if (-not (Test-Path $grokExe)) {
    Write-Error "grok.exe not found at $grokExe"
    exit 1
}

& $grokExe @Arguments
