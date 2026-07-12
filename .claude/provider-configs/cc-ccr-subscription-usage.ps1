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
            @{ Name = '5h window'; Property = 'primary_window' }
            @{ Name = 'weekly'; Property = 'secondary_window' }
        )) {
            $window = $response.rate_limit.($definition.Property)
            if ($null -eq $window -or $null -eq $window.used_percent) { continue }
            $used = [int]$window.used_percent
            $windows += [pscustomobject]@{
                Name        = $definition.Name
                Remaining   = [Math]::Max(0, 100 - $used)
                ResetEpochMs = if ($window.reset_at) { [long]$window.reset_at * 1000 } else { 0 }
            }
        }

        if ($windows.Count -eq 0) {
            return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = 'OpenAI response contained no subscription windows' }
        }

        $plan = if ($response.plan_type) { [string]$response.plan_type } else { 'subscription' }
        return [pscustomobject]@{ Provider = 'openai'; Available = $true; Plan = $plan; Windows = $windows; Source = 'ChatGPT subscription session' }
    } catch {
        return [pscustomobject]@{ Provider = 'openai'; Available = $false; Error = $_.Exception.Message }
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

function Get-GeminiSubscriptionUsage {
    $command = Get-Command antigravity-usage -ErrorAction SilentlyContinue
    if (-not $command) {
        return [pscustomobject]@{
            Provider  = 'antigravity'
            Available = $false
            Plan      = 'Google AI'
            Error     = 'antigravity-usage is not installed'
        }
    }

    try {
        # Use cloud mode deliberately: Antigravity is usually not running when
        # cc-ccr -Usage is requested. This uses the helper's own Google OAuth
        # login and Cloud Code quota endpoint, not the IDE language server.
        $raw = @(& $command.Source --method google --json 2>$null)
        if ($LASTEXITCODE -ne 0 -or $raw.Count -eq 0) {
            throw 'Antigravity cloud quota unavailable - run antigravity-usage login'
        }
        $snapshot = ($raw -join "`n") | ConvertFrom-Json -ErrorAction Stop
        $models = @($snapshot.models) | Where-Object { $null -ne $_.remainingPercentage }
        if ($models.Count -eq 0) {
            throw 'Antigravity returned no model quota information'
        }

        $seen = @{}
        $windows = foreach ($model in $models) {
            $reset = 0L
            if ($model.resetTime) {
                try { $reset = [DateTimeOffset]::Parse([string]$model.resetTime).ToUnixTimeMilliseconds() } catch { }
            }
            $name = if ($model.label) { [string]$model.label } else { [string]$model.modelId }
            $remaining = [Math]::Max(0, [Math]::Min(100, [int][Math]::Round([double]$model.remainingPercentage * 100)))
            $key = "{0}|{1}|{2}" -f $name, $remaining, $reset
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key] = $true
            [pscustomobject]@{
                Name         = $name
                Remaining    = $remaining
                ResetEpochMs = $reset
            }
        }
        $plan = if ($snapshot.planType) { [string]$snapshot.planType } else { 'Google AI' }
        return [pscustomobject]@{
            Provider  = 'antigravity'
            Available = $true
            Plan      = $plan
            Windows   = $windows
            Source    = 'antigravity-usage'
        }
    } catch {
        return [pscustomobject]@{
            Provider  = 'antigravity'
            Available = $false
            Plan      = 'Google AI'
            Error     = $_.Exception.Message
        }
    }
}
