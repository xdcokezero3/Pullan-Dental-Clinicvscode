$ErrorActionPreference = "SilentlyContinue"

$appDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $appDir ".venv\Scripts\python.exe"
$port = if ($env:APP_PORT) { $env:APP_PORT } else { "5000" }
$loginUrl = "http://127.0.0.1:$port/login"

function Get-LanUrl {
    try {
        $udp = New-Object System.Net.Sockets.UdpClient
        $udp.Connect("8.8.8.8", 80)
        $ip = $udp.Client.LocalEndPoint.Address.ToString()
        $udp.Close()
        if ($ip -and -not $ip.StartsWith("127.")) {
            return "http://$ip`:$port/login"
        }
    } catch {}

    try {
        $ip = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
            Where-Object { $_.AddressFamily -eq "InterNetwork" -and -not $_.IPAddressToString.StartsWith("127.") } |
            Select-Object -First 1
        if ($ip) {
            return "http://$($ip.IPAddressToString):$port/login"
        }
    } catch {}

    return $loginUrl
}

function Test-AppRunning {
    try {
        $response = Invoke-WebRequest -Uri $loginUrl -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -ge 200
    } catch {
        return $false
    }
}

if (-not (Test-AppRunning)) {
    $serverCommand = "cd /d `"$appDir`" && set APP_HOST=0.0.0.0&& set APP_PORT=$port&& set FLASK_DEBUG=false&& set SMS_REMINDER_WORKER=true&& `"$pythonPath`" app.py"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $serverCommand -WindowStyle Minimized

    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 750
        if (Test-AppRunning) {
            break
        }
    }
}

$lanUrl = Get-LanUrl
Write-Host ""
Write-Host "Pullan Dental Clinic LAN access:"
Write-Host "  $lanUrl"
Write-Host ""
Start-Process $lanUrl
