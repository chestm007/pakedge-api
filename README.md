# Pakedge API Client

Python API client for Pakedge managed switches (SX-24P16, etc.).

## Install

```bash
cd ~/git/pakedge-api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```python
from pakedge_api import PakedgeClient

with PakedgeClient("10.0.0.1", username="username", password="password") as client:
    # Port status
    ports = client.get_port_status()
    for port in ports:
        print(f"Port {port.port}: pvid={port.pvid}, link={port.linkstatus}")

    # Firmware info
    fw = client.get_firmware_info()
    print(f"Firmware: {fw.version}, update: {fw.update_available}")
```

## API

All Pakedge CGI endpoints use GET requests with query parameters. Session state is managed via cookies.

| Method | Description |
|---|---|
| `login()` | Authenticate |
| `logout()` | Invalidate session |
| `get_port_status()` | Port status for all ports |
| `get_firmware_info()` | Firmware version and update status |
| `check_session()` | Verify session is alive |
