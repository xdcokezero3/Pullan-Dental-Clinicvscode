# Pullan Dental Clinic Installer

This package installs Pullan Dental Clinic on a Windows computer.

## Build The Installer While You Are Still Editing

Every time you finish a set of code edits and want a new installer ZIP, run this command from the project folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_installer.ps1 -Version 1.0.0
```

If you want to keep old installer builds, change the version:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_installer.ps1 -Version 1.0.1
```

The ZIP will be created in:

```text
dist\PullanDentalClinic-<version>.zip
```

After more edits, run the build command again. Then send the newest ZIP to the target computer.

## Install On Another Computer

1. Extract the ZIP file.
2. Open the extracted folder.
3. Run `installer\setup_windows.bat`.
4. Wait for the installer to finish.
5. Open the desktop shortcut named `Pullan Dental Clinic`.

You can also run the installer again later to update the app files. Existing local data in `instance\` and backup files in `backups\` are preserved.

The app is installed per user in:

```text
%LOCALAPPDATA%\PullanDentalClinic
```

The installer creates a local SQLite database on first run. This keeps each computer's data local to that computer.

## LAN Use

To let another computer on the same network open the system, run:

```text
Run Pullan Dental Clinic LAN.bat
```

The server window will show LAN URLs such as:

```text
http://192.168.x.x:5000
```

Open that URL on another computer connected to the same network.

## Desktop Shortcut Behavior

The desktop shortcut uses the LAN launcher, starts the server minimized, waits for the app to respond, then opens the browser directly to the computer's LAN address when one is available:

```text
http://192.168.x.x:5000/login
```

The shortcut uses `Pullan_LOGO.jpg` as its icon. Restore the minimized server window only when you need to see LAN IP addresses or logs.

## Requirements

- Windows 10 or Windows 11
- Internet connection during install, so Python packages can be installed
- Python 3.11 or newer

If Python is not installed, the installer tries to install it using `winget`. If that fails, install Python manually from:

```text
https://www.python.org/downloads/windows/
```

Then run `installer\setup_windows.bat` again.

## SMS Setup

By default, SMS reminders are configured for InfiniReach. For testing without sending real SMS, set `SMS_PROVIDER=console`.

To send real SMS, edit:

```text
%LOCALAPPDATA%\PullanDentalClinic\.env
```

Configure InfiniReach in `.env`:

```text
SMS_PROVIDER=infinireach
INFINIREACH_API_KEY=your_infinireach_api_key
INFINIREACH_FROM=+639XXXXXXXXX
INFINIREACH_DEVICE_ID=your_registered_device_uuid
INFINIREACH_CHANNEL=sms
```

InfiniReach sends through your registered device. The `INFINIREACH_FROM` value must be the registered SIM phone number in E.164 format, so a Philippine number like `09604712749` becomes `+639604712749`. If you only have the device UUID, set `INFINIREACH_DEVICE_ID` and the app will look up the SIM phone number automatically.

If InfiniReach blocks Python HTTP requests with Cloudflare Error 1010, the app automatically retries the same request through `curl`. The Windows installer checks for `curl` before installing so SMS remains functional on the installed PC.

When the project is copied through Git, `.env` may be missing because it is ignored by Git. On first run, the app creates `.env` from `.env.example`. The Windows installer also verifies the InfiniReach SMS settings in `.env` during installation.

After configuring real SMS credentials, restart the app. The reminder worker runs in the background while the system is open. Admin users can review SMS status from:

```text
Appointments > SMS Reminders
```
