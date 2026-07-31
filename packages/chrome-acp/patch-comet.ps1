$policyPath = "HKLM:\SOFTWARE\Policies\Perplexity\Comet"
$extensionSettings = '{"*":{"runtime_allowed_hosts":["*://*.perplexity.ai"],"runtime_blocked_hosts":[]}}'

if (-not (Test-Path $policyPath)) {
    New-Item -Path $policyPath -Force | Out-Null
}

New-ItemProperty -Path $policyPath -Name "ExtensionSettings" -Value $extensionSettings -PropertyType String -Force | Out-Null

$verify = Get-ItemProperty -Path $policyPath -Name "ExtensionSettings"
Write-Output "SUCCESS: $($verify.ExtensionSettings)"
Start-Sleep -Seconds 2
