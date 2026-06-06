param(
    [string]$EnvPath = ".env"
)

$ErrorActionPreference = "Stop"

$requiredValues = [ordered]@{
    "FLASK_DEBUG" = "false"
    "LIFECYCLE_BACKUPS" = "false"
    "SMS_PROVIDER" = "infinireach"
    "SMS_REMINDER_WORKER" = "true"
    "SMS_WORKER_INTERVAL_SECONDS" = "60"
    "SMS_SENDER_NAME" = "PullanDental"
    "CLINIC_NAME" = "Pullan Dental Clinic"
    "SMS_HTTP_USER_AGENT" = "curl/8.4.0"
    "INFINIREACH_API_KEY" = "smsrelay_650c61aff0f2c93dcf3027b531ec57a06eb3ad144a32b2dcfa73d57dd97dbbd4"
    "INFINIREACH_FROM" = "+639245542399"
    "INFINIREACH_DEVICE_ID" = "1e21eb4f-3178-4671-9256-4b7e9056146e"
    "INFINIREACH_CHANNEL" = "sms"
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
    New-Item -ItemType File -Path $EnvPath -Force | Out-Null
}

$lines = [System.Collections.Generic.List[string]]::new()
if ((Get-Item -LiteralPath $EnvPath).Length -gt 0) {
    Get-Content -LiteralPath $EnvPath | ForEach-Object { [void]$lines.Add($_) }
}

foreach ($key in $requiredValues.Keys) {
    $value = $requiredValues[$key]
    $pattern = "^\s*$([regex]::Escape($key))="
    $updated = $false

    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $lines[$i] = "$key=$value"
            $updated = $true
        }
    }

    if (-not $updated) {
        [void]$lines.Add("$key=$value")
    }
}

Set-Content -LiteralPath $EnvPath -Value $lines -Encoding UTF8
Write-Host "SMS automation settings verified in $EnvPath"
