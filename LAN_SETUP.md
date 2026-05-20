# LAN setup

Use one computer as the server, then open the app from the other computer through a browser.

## On the server computer

1. Connect both computers to the same network or directly with a LAN cable.
2. Open this project folder.
3. Run `start_lan.bat`.
4. Look for the printed `LAN access` address, for example:

   `http://192.168.1.10:5000`

## On the other computer

Open a browser and enter the `LAN access` address printed by the server computer.

## If it does not connect

1. Allow Python or port `5000` through Windows Defender Firewall on the server computer.
2. Make sure both computers have IP addresses on the same network.
3. Try opening `http://SERVER_IP:5000`, replacing `SERVER_IP` with the server computer's IPv4 address.

## Direct LAN cable without a router

If the computers are connected directly by cable and there is no router, set manual IPv4 addresses on the Ethernet adapter:

Server computer:

`IP address: 192.168.10.1`

`Subnet mask: 255.255.255.0`

Second computer:

`IP address: 192.168.10.2`

`Subnet mask: 255.255.255.0`

Then run `start_lan.bat` on the server computer and open this on the second computer:

`http://192.168.10.1:5000`

## Optional settings

You can change the port before starting:

```bat
set APP_PORT=8080
python app.py
```

The app uses the SQLite database file on the server computer by default, so the second computer only needs a browser.
