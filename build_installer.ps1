param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageName = "PullanDentalClinic-$Version"
$stagingRoot = Join-Path $root $OutputDir
$packageDir = Join-Path $stagingRoot $packageName
$zipPath = Join-Path $stagingRoot "$packageName.zip"

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}

New-Item -ItemType Directory -Path $packageDir | Out-Null

$itemsToCopy = @(
    "app.py",
    "db_connector.py",
    "requirements.txt",
    ".env",
    ".env.example",
    "Pullan_LOGO.jpg",
    "start_lan.bat",
    "LAN_SETUP.md",
    "static",
    "templates",
    "installer"
)

foreach ($item in $itemsToCopy) {
    $source = Join-Path $root $item
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination $packageDir -Recurse -Force
    }
}

$readmeSource = Join-Path $root "INSTALLER_README.md"
if (Test-Path $readmeSource) {
    Copy-Item -LiteralPath $readmeSource -Destination $packageDir -Force
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Installer package created:"
Write-Host "  $zipPath"
Write-Host ""
Write-Host "Send this ZIP to another Windows computer, extract it, then run:"
Write-Host "  installer\setup_windows.bat"
