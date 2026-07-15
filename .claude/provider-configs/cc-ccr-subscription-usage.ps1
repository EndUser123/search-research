# Subscription-only usage collectors for cc-ccr.

function Get-OpenAISubscriptionUsage {
    param([string]$AuthPath = (Join-Path $env:USERPROFILE '.codex\auth.json'))

    if (-not (Test-Path -LiteralPath $AuthPath)) {
        return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = "Codex auth file not found: $AuthPath" }
    }

    try {
        $auth = Get-Content -LiteralPath $AuthPath -Raw -ErrorAction Stop | ConvertFrom-Json
        if ($auth.auth_mode -ne 'chatgpt' -or -not $auth.tokens.access_token) {
            return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = 'ChatGPT subscription login not available' }
        }

        $headers = @{
            Authorization       = "Bearer $($auth.tokens.access_token)"
            'ChatGPT-Account-Id' = [string]$auth.tokens.account_id
            Accept               = 'application/json'
        }
        $response = Invoke-RestMethod -Uri 'https://chatgpt.com/backend-api/wham/usage' -Headers $headers -TimeoutSec 15 -ErrorAction Stop
        $windows = @()
        foreach ($definition in @(
            @{ FallbackName = 'primary window'; Property = 'primary_window' }
            @{ FallbackName = 'secondary window'; Property = 'secondary_window' }
        )) {
            $window = $response.rate_limit.($definition.Property)
            $converted = Convert-OpenAIUsageWindow $definition.FallbackName $window
            if ($null -ne $converted) { $windows += $converted }
        }

        if ($windows.Count -eq 0) {
            return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = 'OpenAI response contained no subscription windows' }
        }

        $plan = if ($response.plan_type) { [string]$response.plan_type } else { 'subscription' }
        $hasFiveHour = @($windows | Where-Object Name -eq '5h window').Count -gt 0
        return [pscustomobject]@{
            Provider       = 'openai'
            Available      = $true
            Plan           = $plan
            Windows        = $windows
            MissingWindows = if ($hasFiveHour) { @() } else { @('5h window') }
            Source         = 'ChatGPT subscription session'
        }
    } catch {
        return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = $_.Exception.Message }
    }
}

function Convert-OpenAIUsageWindow {
    param([string]$FallbackName, $Window)

    if ($null -eq $Window -or $null -eq $Window.used_percent) { return $null }
    $duration = if ($null -ne $Window.limit_window_seconds) { [long]$Window.limit_window_seconds } else { 0L }
    $name = if ($duration -ge 4 * 3600 -and $duration -le 6 * 3600) {
        '5h window'
    } elseif ($duration -ge 6 * 24 * 3600 -and $duration -le 8 * 24 * 3600) {
        'weekly'
    } else {
        $FallbackName
    }
    $used = [int]$Window.used_percent
    return [pscustomobject]@{
        Name         = $name
        Remaining    = [Math]::Max(0, 100 - $used)
        ResetEpochMs = if ($Window.reset_at) { [long]$Window.reset_at * 1000 } else { 0 }
    }
}

function Convert-AnthropicUsageWindow {
    param([string]$Name, $Window)

    if ($null -eq $Window) { return $null }
    $rawUtilization = if ($null -ne $Window.utilization) {
        $value = [double]$Window.utilization
        if ($value -gt 1) { $value / 100 } else { $value }
    } elseif ($null -ne $Window.used_percentage) { [double]$Window.used_percentage / 100 } else { $null }
    if ($null -eq $rawUtilization) { return $null }
    $used = [int][Math]::Round([Math]::Min(1.0, [Math]::Max(0.0, $rawUtilization)) * 100)
    $resetValue = if ($Window.resets_at) { $Window.resets_at } elseif ($Window.reset_at) { $Window.reset_at } else { $null }
    $reset = 0L
    if ($resetValue) {
        if ($resetValue -is [byte] -or $resetValue -is [int16] -or $resetValue -is [int32] -or $resetValue -is [int64] -or $resetValue -is [single] -or $resetValue -is [double] -or $resetValue -is [decimal]) {
            $reset = [long]$resetValue * 1000
        } else {
            try { $reset = [DateTimeOffset]::Parse([string]$resetValue).ToUnixTimeMilliseconds() } catch { $reset = 0L }
        }
    }
    return [pscustomobject]@{ Name = $Name; Remaining = [Math]::Max(0, 100 - $used); ResetEpochMs = $reset }
}

function Get-AnthropicSubscriptionToken {
    param([string]$CredentialsPath = (Join-Path $env:USERPROFILE '.claude\.credentials.json'))

    if ($env:CLAUDE_CODE_OAUTH_TOKEN) {
        return [pscustomobject]@{ Token = $env:CLAUDE_CODE_OAUTH_TOKEN; Plan = 'subscription'; Source = 'CLAUDE_CODE_OAUTH_TOKEN' }
    }
    if (-not (Test-Path -LiteralPath $CredentialsPath)) { return $null }
    try {
        $credentials = Get-Content -LiteralPath $CredentialsPath -Raw -ErrorAction Stop | ConvertFrom-Json
        if ($credentials.claudeAiOauth.accessToken) {
            $plan = if ($credentials.claudeAiOauth.subscriptionType) { [string]$credentials.claudeAiOauth.subscriptionType } else { 'subscription' }
            return [pscustomobject]@{ Token = [string]$credentials.claudeAiOauth.accessToken; Plan = $plan; Source = 'Claude Code OAuth credentials' }
        }
    } catch { }

    $desktopRoot = Join-Path $env:APPDATA 'Claude'
    $desktopStatePath = Join-Path $desktopRoot 'Local State'
    $desktopConfigPath = Join-Path $desktopRoot 'config.json'
    if ((Test-Path -LiteralPath $desktopStatePath) -and (Test-Path -LiteralPath $desktopConfigPath)) {
        try {
            Add-Type -AssemblyName System.Security.Cryptography.ProtectedData -ErrorAction Stop
            $state = Get-Content -LiteralPath $desktopStatePath -Raw -ErrorAction Stop | ConvertFrom-Json
            $encryptedMaster = [Convert]::FromBase64String([string]$state.os_crypt.encrypted_key)
            if ([Text.Encoding]::ASCII.GetString($encryptedMaster[0..4]) -ne 'DPAPI') { throw 'Claude Desktop encryption key format not recognized' }
            $master = [System.Security.Cryptography.ProtectedData]::Unprotect($encryptedMaster[5..($encryptedMaster.Length - 1)], $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
            $config = Get-Content -LiteralPath $desktopConfigPath -Raw -ErrorAction Stop | ConvertFrom-Json
            $encoded = [string]$config.'oauth:tokenCacheV2'
            if (-not $encoded) { throw 'Claude Desktop OAuth cache not found' }
            $encrypted = [Convert]::FromBase64String($encoded)
            if ([Text.Encoding]::ASCII.GetString($encrypted[0..2]) -ne 'v10') { throw 'Claude Desktop OAuth cache format not recognized' }
            $nonce = $encrypted[3..14]
            $ciphertext = $encrypted[15..($encrypted.Length - 17)]
            $tag = $encrypted[($encrypted.Length - 16)..($encrypted.Length - 1)]
            $plaintext = New-Object byte[] $ciphertext.Length
            $aes = [System.Security.Cryptography.AesGcm]::new($master)
            $aes.Decrypt($nonce, $ciphertext, $tag, $plaintext)
            $cache = [Text.Encoding]::UTF8.GetString($plaintext) | ConvertFrom-Json
            foreach ($entry in $cache.psobject.Properties) {
                if ($entry.Value.token) {
                    $plan = if ($entry.Value.subscriptionType) { [string]$entry.Value.subscriptionType } else { 'subscription' }
                    return [pscustomobject]@{ Token = [string]$entry.Value.token; Plan = $plan; Source = 'Claude Desktop OAuth cache' }
                }
            }
        } catch { }
    }
    return $null
}

function Get-AnthropicSubscriptionUsage {
    param(
        [string]$CredentialsPath = (Join-Path $env:USERPROFILE '.claude\.credentials.json'),
        [string]$SnapshotPath = (Join-Path $env:USERPROFILE '.claude\state\subscription-usage.json'),
        [int]$MaxAgeMinutes = 30
    )

    $directError = $null
    try {
        $auth = Get-AnthropicSubscriptionToken -CredentialsPath $CredentialsPath
        if (-not $auth) { throw 'Claude subscription OAuth credentials not found' }
        $headers = @{
            Authorization = "Bearer $($auth.Token)"
            'anthropic-beta' = 'oauth-2025-04-20'
            Accept = 'application/json'
        }
        $response = Invoke-RestMethod -Uri 'https://api.anthropic.com/api/oauth/usage' -Headers $headers -TimeoutSec 15 -ErrorAction Stop
        $windows = @(
            (Convert-AnthropicUsageWindow '5h window' $response.five_hour)
            (Convert-AnthropicUsageWindow 'weekly' $response.seven_day)
        ) | Where-Object { $null -ne $_ }
        if ($windows.Count -gt 0) {
            return [pscustomobject]@{ Provider = 'anthropic'; Available = $true; Plan = $auth.Plan; Windows = $windows; Source = $auth.Source }
        }
        throw 'Anthropic response contained no subscription windows'
    } catch {
        $directError = $_.Exception.Message
    }

    if (Test-Path -LiteralPath $SnapshotPath) {
        try {
            $snapshot = Get-Content -LiteralPath $SnapshotPath -Raw -ErrorAction Stop | ConvertFrom-Json
            $updated = [DateTimeOffset]::Parse([string]$snapshot.updated_at)
            $age = [DateTimeOffset]::UtcNow - $updated.ToUniversalTime()
            if ($age.TotalMinutes -le $MaxAgeMinutes) {
                $rateLimits = if ($snapshot.rate_limits) { $snapshot.rate_limits } else { $snapshot }
                $windows = @(
                    (Convert-AnthropicUsageWindow '5h window' $rateLimits.five_hour)
                    (Convert-AnthropicUsageWindow 'weekly' $rateLimits.seven_day)
                ) | Where-Object { $null -ne $_ }
                if ($windows.Count -gt 0) {
                    return [pscustomobject]@{ Provider = 'anthropic'; Available = $true; Plan = 'subscription'; Windows = $windows; Source = 'Claude statusline snapshot' }
                }
            }
        } catch { }
    }

    return [pscustomobject]@{ Provider = 'anthropic'; Available = $false; Error = $directError }
}

function Convert-AntigravitySnapshot {
    param($Snapshot, [string]$Source = 'antigravity-usage')

    $models = @($Snapshot.models) | Where-Object { $null -ne $_.remainingPercentage }
    if ($models.Count -eq 0) { throw 'Antigravity returned no model quota information' }

    $groups = @{}
    foreach ($model in $models) {
        $reset = 0L
        if ($model.resetTime) {
            try { $reset = [DateTimeOffset]::Parse([string]$model.resetTime).ToUnixTimeMilliseconds() } catch { }
        }
        $name = if ($model.label) { [string]$model.label } else { [string]$model.modelId }
        $remaining = [Math]::Max(0, [Math]::Min(100, [int][Math]::Round([double]$model.remainingPercentage * 100)))
        $family = if ("$name $($model.modelId)" -match '(?i)gemini') { 'Gemini' } else { 'Other models' }
        $key = "{0}|{1}|{2}" -f $family, $remaining, $reset
        if (-not $groups.ContainsKey($key)) {
            $groups[$key] = [pscustomobject]@{
                Family       = $family
                Remaining    = $remaining
                ResetEpochMs = $reset
                Models       = [System.Collections.Generic.List[string]]::new()
            }
        }
        $groups[$key].Models.Add($name)
    }

    $windows = foreach ($group in $groups.Values | Sort-Object Family) {
        $label = if ($group.Models.Count -gt 1) { '{0} ({1} aliases)' -f $group.Family, $group.Models.Count } else { $group.Family }
        [pscustomobject]@{
            Name         = $label
            Remaining    = $group.Remaining
            ResetEpochMs = $group.ResetEpochMs
            Aliases      = @($group.Models)
        }
    }
    $plan = if ($Snapshot.planType) { [string]$Snapshot.planType } else { 'Google AI' }
    return [pscustomobject]@{
        Provider  = 'antigravity'
        Available = $true
        Plan      = $plan
        Windows   = @($windows)
        Source    = $Source
        UpdatedAt = if ($Snapshot.timestamp) { [DateTimeOffset]::Parse([string]$Snapshot.timestamp) } else { [DateTimeOffset]::UtcNow }
        Stale     = ($Source -ne 'antigravity-usage')
        Error     = $null
    }
}

function ConvertTo-AntigravityCacheSnapshot {
    param($Snapshot)

    $models = @($Snapshot.models) | Where-Object { $null -ne $_.remainingPercentage } | ForEach-Object {
        [pscustomobject]@{
            label               = if ($null -ne $_.label) { [string]$_.label } else { $null }
            modelId             = if ($null -ne $_.modelId) { [string]$_.modelId } else { $null }
            remainingPercentage = [double]$_.remainingPercentage
            resetTime           = if ($_.resetTime) { [string]$_.resetTime } else { $null }
            isAutocompleteOnly  = [bool]$_.isAutocompleteOnly
        }
    }
    if (@($models).Count -eq 0) { throw 'Antigravity returned no model quota information' }

    return [pscustomobject]@{
        timestamp = if ($Snapshot.timestamp) { [string]$Snapshot.timestamp } else { [DateTimeOffset]::UtcNow.ToString('o') }
        method    = if ($Snapshot.method) { [string]$Snapshot.method } else { 'google' }
        models    = @($models)
    }
}

function Write-AntigravityCacheSnapshot {
    param(
        [Parameter(Mandatory)]$Snapshot,
        [Parameter(Mandatory)][string]$Path
    )

    $safeSnapshot = ConvertTo-AntigravityCacheSnapshot $Snapshot
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force -ErrorAction Stop | Out-Null
    $temporaryPath = '{0}.{1}.{2}.tmp' -f $Path, $PID, ([guid]::NewGuid().ToString('N'))
    $backupPath = '{0}.{1}.{2}.bak' -f $Path, $PID, ([guid]::NewGuid().ToString('N'))
    try {
        $safeSnapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $temporaryPath -Encoding utf8 -ErrorAction Stop
        if (Test-Path -LiteralPath $Path) {
            [System.IO.File]::Replace($temporaryPath, $Path, $backupPath, $true)
        } else {
            [System.IO.File]::Move($temporaryPath, $Path)
        }
    } finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $backupPath) {
            Remove-Item -LiteralPath $backupPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Get-AntigravityUsage {
    param(
        [string]$CachePath = (Join-Path $env:USERPROFILE '.claude\state\antigravity-usage.json'),
        [int]$CacheMaxAgeMinutes = 15,
        [int]$TimeoutSeconds = 20
    )
    $command = Get-Command antigravity-usage -ErrorAction SilentlyContinue
    if (-not $command) {
        return [pscustomobject]@{ Provider = 'antigravity'; Available = $false; Plan = 'Google AI'; Error = 'antigravity-usage is not installed' }
    }

    $directError = $null
    $job = $null
    try {
        $job = Start-Job -ScriptBlock {
            param($CommandPath)
            & $CommandPath --method google --json 2>&1
        } -ArgumentList $command.Source
        if (-not (Wait-Job -Job $job -Timeout $TimeoutSeconds)) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            throw "Antigravity quota command timed out after $TimeoutSeconds seconds"
        }
        $raw = Receive-Job -Job $job -ErrorAction SilentlyContinue
        $snapshot = ($raw -join "`n") | ConvertFrom-Json -ErrorAction Stop
        $result = Convert-AntigravitySnapshot -Snapshot $snapshot
        Write-AntigravityCacheSnapshot -Snapshot $snapshot -Path $CachePath
        return $result
    } catch { $directError = $_.Exception.Message }
    finally {
        if ($job) { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue }
    }

    if (Test-Path -LiteralPath $CachePath) {
        try {
            $cached = Get-Content -LiteralPath $CachePath -Raw -ErrorAction Stop | ConvertFrom-Json
            $updated = [DateTimeOffset]::Parse([string]$cached.timestamp)
            if (([DateTimeOffset]::UtcNow - $updated.ToUniversalTime()).TotalMinutes -le $CacheMaxAgeMinutes) {
                $result = Convert-AntigravitySnapshot -Snapshot $cached -Source 'antigravity-usage cache'
                $result.Error = $directError
                return $result
            }
        } catch { }
    }
    return [pscustomobject]@{ Provider = 'antigravity'; Available = $false; Plan = 'Google AI'; Error = $directError }
}
