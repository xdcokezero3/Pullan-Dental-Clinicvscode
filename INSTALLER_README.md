# Pullan Dental Clinic Installer

This package installs Pullan Dental Clinic on a Windows computer.

## Install On Another Computer

1. Extract the ZIP file.
2. Open the extracted folder.
3. Run `installer\setup_windows.bat`.
4. Wait for the installer to finish.
5. Open the desktop shortcut named `Pullan Dental Clinic`.

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

By default, SMS reminders use `SMS_PROVIDER=console`, which logs messages instead of sending real SMS.

To send real SMS, edit:

```text
%LOCALAPPDATA%\PullanDentalClinic\.env
```

Supported providers:

- `twilio`
- `semaphore`
- `console`

Configure the matching API keys in `.env`.
