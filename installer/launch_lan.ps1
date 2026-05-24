$ErrorActionPreference = "SilentlyContinue"

$appDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $appDir ".venv\Scripts\python.exe"
$port = if ($env:APP_PORT) { $env:APP_PORT } else { "5000" }
$loginUrl = "http://127.0.0.1:$port/login"

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

Start-Process $loginUrl
