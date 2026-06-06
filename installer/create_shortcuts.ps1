param(
    [Parameter(Mandatory = $true)]
    [string]$AppDir
)

$ErrorActionPreference = "Stop"

function Convert-LogoToIcon {
    param(
        [string]$LogoPath,
        [string]$IconPath
    )

    if (-not (Test-Path -LiteralPath $LogoPath)) {
        return $null
    }

    try {
        Add-Type -AssemblyName System.Drawing

        $source = [System.Drawing.Image]::FromFile($LogoPath)
        try {
            $canvasSize = 256
            $bitmap = New-Object System.Drawing.Bitmap $canvasSize, $canvasSize
            try {
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                try {
                    $graphics.Clear([System.Drawing.Color]::Transparent)
                    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality

                    $scale = [Math]::Min($canvasSize / $source.Width, $canvasSize / $source.Height)
                    $width = [Math]::Max(1, [int]($source.Width * $scale))
                    $height = [Math]::Max(1, [int]($source.Height * $scale))
                    $x = [int](($canvasSize - $width) / 2)
                    $y = [int](($canvasSize - $height) / 2)
                    $graphics.DrawImage($source, $x, $y, $width, $height)
                } finally {
                    $graphics.Dispose()
                }

                $iconHandle = $bitmap.GetHicon()
                try {
                    $icon = [System.Drawing.Icon]::FromHandle($iconHandle)
                    try {
                        $stream = [System.IO.File]::Create($IconPath)
                        try {
                            $icon.Save($stream)
                        } finally {
                            $stream.Dispose()
                        }
                    } finally {
                        $icon.Dispose()
                    }
                } finally {
                    $nativeMethods = @"
using System;
using System.Runtime.InteropServices;
public static class IconNativeMethods {
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool DestroyIcon(IntPtr hIcon);
}
"@
                    if (-not ("IconNativeMethods" -as [type])) {
                        Add-Type -TypeDefinition $nativeMethods
                    }
                    [IconNativeMethods]::DestroyIcon($iconHandle) | Out-Null
                }
            } finally {
                $bitmap.Dispose()
            }
        } finally {
            $source.Dispose()
        }

        if (Test-Path -LiteralPath $IconPath) {
            return $IconPath
        }
    } catch {
        Write-Warning "Could not create shortcut icon from Pullan_LOGO.jpg: $($_.Exception.Message)"
    }

    return $null
}

function New-AppShortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$WorkingDirectory,
        [string]$IconPath
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.WindowStyle = 7
    if ($IconPath -and (Test-Path -LiteralPath $IconPath)) {
        $shortcut.IconLocation = $IconPath
    }
    $shortcut.Save()
}

$resolvedAppDir = (Resolve-Path -LiteralPath $AppDir).Path
$logoPath = Join-Path $resolvedAppDir "Pullan_LOGO.jpg"
$iconPath = Convert-LogoToIcon -LogoPath $logoPath -IconPath (Join-Path $resolvedAppDir "Pullan_LOGO.ico")

$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\Pullan Dental Clinic"
New-Item -ItemType Directory -Path $startMenu -Force | Out-Null

$localLauncher = Join-Path $resolvedAppDir "Run Pullan Dental Clinic.bat"
$lanLauncher = Join-Path $resolvedAppDir "Run Pullan Dental Clinic LAN.bat"

New-AppShortcut `
    -ShortcutPath (Join-Path $desktop "Pullan Dental Clinic.lnk") `
    -TargetPath $lanLauncher `
    -WorkingDirectory $resolvedAppDir `
    -IconPath $iconPath

New-AppShortcut `
    -ShortcutPath (Join-Path $startMenu "Pullan Dental Clinic.lnk") `
    -TargetPath $lanLauncher `
    -WorkingDirectory $resolvedAppDir `
    -IconPath $iconPath

New-AppShortcut `
    -ShortcutPath (Join-Path $startMenu "Pullan Dental Clinic LAN.lnk") `
    -TargetPath $lanLauncher `
    -WorkingDirectory $resolvedAppDir `
    -IconPath $iconPath

New-AppShortcut `
    -ShortcutPath (Join-Path $startMenu "Pullan Dental Clinic Local.lnk") `
    -TargetPath $localLauncher `
    -WorkingDirectory $resolvedAppDir `
    -IconPath $iconPath
