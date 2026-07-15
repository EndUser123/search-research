$collectorPath = Join-Path $PSScriptRoot 'cc-ccr-subscription-usage.ps1'
. $collectorPath

Describe 'Antigravity quota conversion' {
    It 'groups model aliases by family, remaining quota, and reset time' {
        $snapshot = @'
{
  "timestamp": "2026-07-12T05:00:00Z",
  "models": [
    { "label": "Gemini 3 Flash", "remainingPercentage": 0.93, "resetTime": "2026-07-12T06:00:00Z" },
    { "label": "Gemini 3 Pro", "remainingPercentage": 0.93, "resetTime": "2026-07-12T06:00:00Z" },
    { "label": "Claude Sonnet", "remainingPercentage": 1, "resetTime": "2026-07-12T10:00:00Z" },
    { "label": "GPT-OSS", "remainingPercentage": 1, "resetTime": "2026-07-12T10:00:00Z" }
  ]
}
'@ | ConvertFrom-Json

        $result = Convert-AntigravitySnapshot $snapshot

        $result.Available | Should Be $true
        $result.Windows.Count | Should Be 2
        ($result.Windows | Where-Object Name -eq 'Gemini (2 aliases)').Remaining | Should Be 93
        ($result.Windows | Where-Object Name -eq 'Other models (2 aliases)').Remaining | Should Be 100
        (($result.Windows | Where-Object Name -eq 'Gemini (2 aliases)').Aliases -join ', ') | Should Be 'Gemini 3 Flash, Gemini 3 Pro'
    }

    It 'preserves reset timestamps and marks cached data stale' {
        $snapshot = [pscustomobject]@{
            timestamp = '2026-07-12T05:00:00Z'
            models = @([pscustomobject]@{
                label = 'Gemini 3 Flash'
                remainingPercentage = 0.5
                resetTime = '2026-07-12T06:00:00Z'
            })
        }

        $result = Convert-AntigravitySnapshot $snapshot -Source 'antigravity-usage cache'

        $result.Stale | Should Be $true
        $result.UpdatedAt.ToUnixTimeSeconds() | Should Be ([DateTimeOffset]::Parse('2026-07-12T05:00:00Z').ToUnixTimeSeconds())
        $result.Windows[0].ResetEpochMs | Should Be ([DateTimeOffset]::Parse('2026-07-12T06:00:00Z').ToUnixTimeMilliseconds())
    }

    It 'rejects snapshots without quota-bearing models' {
        $thrown = $false
        try { Convert-AntigravitySnapshot ([pscustomobject]@{ timestamp = '2026-07-12T05:00:00Z'; models = @() }) } catch { $thrown = $true }
        $thrown | Should Be $true
    }
}

Describe 'OpenAI quota window conversion' {
    It 'classifies windows by duration rather than primary or secondary field name' {
        $weekly = Convert-OpenAIUsageWindow 'primary window' ([pscustomobject]@{
            used_percent = 57
            limit_window_seconds = 604800
            reset_at = 1784489949
        })
        $short = Convert-OpenAIUsageWindow 'secondary window' ([pscustomobject]@{
            used_percent = 22
            limit_window_seconds = 18000
            reset_at = 1784470000
        })

        $weekly.Name | Should Be 'weekly'
        $weekly.Remaining | Should Be 43
        $short.Name | Should Be '5h window'
        $short.Remaining | Should Be 78
    }

    It 'returns no fabricated window when the provider omits it' {
        (Convert-OpenAIUsageWindow 'secondary window' $null) | Should Be $null
    }
}

Describe 'Antigravity cache persistence' {
    It 'allow-lists quota metadata and excludes account or unknown fields' {
        $snapshot = [pscustomobject]@{
            timestamp = '2026-07-13T12:00:00Z'
            method = 'google'
            email = 'account@example.invalid'
            accessToken = 'must-not-persist'
            models = @([pscustomobject]@{
                label = 'Gemini 3 Flash'
                modelId = 'gemini-3-flash'
                remainingPercentage = 0.75
                resetTime = '2026-07-13T17:00:00Z'
                isAutocompleteOnly = $false
                unexpected = 'must-not-persist'
            })
        }

        $safe = ConvertTo-AntigravityCacheSnapshot $snapshot
        ($safe.psobject.Properties.Name -join ',') | Should Be 'timestamp,method,models'
        ($safe.models[0].psobject.Properties.Name -join ',') | Should Be 'label,modelId,remainingPercentage,resetTime,isAutocompleteOnly'
        $safe.email | Should Be $null
        $safe.accessToken | Should Be $null
        $safe.models[0].remainingPercentage | Should Be 0.75
        $safe.models[0].unexpected | Should Be $null
    }

    It 'writes a valid sanitized snapshot and leaves no temporary file' {
        $directory = Join-Path $env:TEMP ('cc-ccr-cache-test-' + [guid]::NewGuid().ToString('N'))
        $path = Join-Path $directory 'antigravity-usage.json'
        try {
            $snapshot = [pscustomobject]@{
                timestamp = '2026-07-13T12:00:00Z'
                method = 'google'
                email = 'account@example.invalid'
                models = @([pscustomobject]@{
                    label = 'Gemini 3 Flash'
                    modelId = 'gemini-3-flash'
                    remainingPercentage = 0.75
                    resetTime = '2026-07-13T17:00:00Z'
                    isAutocompleteOnly = $false
                })
            }

            Write-AntigravityCacheSnapshot -Snapshot $snapshot -Path $path
            $snapshot.models[0].remainingPercentage = 0.5
            Write-AntigravityCacheSnapshot -Snapshot $snapshot -Path $path

            Test-Path -LiteralPath $path | Should Be $true
            $written = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
            $written.email | Should Be $null
            $written.models[0].remainingPercentage | Should Be 0.5
            @(Get-ChildItem -LiteralPath $directory -Filter '*.tmp' -ErrorAction SilentlyContinue).Count | Should Be 0
            @(Get-ChildItem -LiteralPath $directory -Filter '*.bak' -ErrorAction SilentlyContinue).Count | Should Be 0
        } finally {
            if (Test-Path -LiteralPath $directory) { Remove-Item -LiteralPath $directory -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }
}
