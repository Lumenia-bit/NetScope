# NetScope

NetScope is a lightweight, self-hosted scanner for discovering and monitoring devices on a local IPv4 network. It uses ARP for discovery, performs a small configurable TCP connect scan, and keeps device identity and state history in SQLite.

NetScope is intended only for networks you own or administer.

## Features

- Automatic local IPv4 subnet detection with a validated manual override
- ARP device discovery without external network services
- MAC-based device identity, online/offline tracking, and appearance history
- Hostname resolution and local, replaceable OUI vendor data
- Configurable TCP port checks with common service names
- Live scan progress and a responsive dark web interface
- Search, status/vendor filters, sorting, device details, and exact timestamps
- FastAPI serves the compiled React application for a single-process production setup

## Screenshots

Dashboard screenshot placeholder — add `docs/screenshots/dashboard.png` after running NetScope on your network.

Device details screenshot placeholder — add `docs/screenshots/device.png` after opening a discovered device.

## Requirements

- Linux
- Python 3.12 or newer
- Node.js 20.19+ or 22.12+ for building the frontend
- Root privileges or the `CAP_NET_RAW` capability for ARP discovery

ARP operates below the IP layer and generally requires raw-socket permission. Run the development server with `sudo` only when appropriate for your environment, or grant the Python interpreter raw-network capability. Be aware that capabilities applied directly to a virtual-environment interpreter can be lost when Python is upgraded or the environment is recreated.

## Installation

```bash
git clone <repository-url> netscope
cd netscope

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

## Running in development

Start the API from the repository root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

In a second terminal, start Vite:

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. Vite forwards API calls to FastAPI on port 8000.

## Production build

Build the frontend once, then start FastAPI. The backend automatically serves `frontend/dist` when it exists.

```bash
cd frontend
npm run build
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. Set `NETSCOPE_DB` to change the SQLite database location and `NETSCOPE_LOG_LEVEL` to adjust server logging.

## Architecture

- `backend/main.py` creates the FastAPI application and serves the production frontend.
- `backend/routes/` contains the small REST surface for devices, scans, network information, and settings.
- `backend/scanner/` contains network detection, ARP discovery, hostname/vendor lookup, TCP checks, and scan-state coordination.
- `backend/database.py` owns the SQLite schema and MAC-based device/history updates.
- `frontend/src/` contains the React dashboard, device page, settings form, and API client.
- `data/oui.csv` is a deliberately small local vendor database. It can be replaced with a larger licensed IEEE-derived CSV using the same `prefix,vendor` columns.

Network operations run outside the FastAPI event loop. Only one full scan can run at once; individual port rescans remain available from device detail pages.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/network` | Detected, configured, and effective subnet |
| `GET` | `/api/devices` | All known devices |
| `GET` | `/api/devices/{id}` | Device details and named open ports |
| `GET` | `/api/devices/{id}/history` | Detection and state events |
| `POST` | `/api/devices/{id}/scan-ports` | Recheck one device's configured ports |
| `POST` | `/api/scan` | Start a full network scan |
| `GET` | `/api/scan/status` | Current scan state and progress |
| `GET` | `/api/settings` | Scanner settings |
| `PUT` | `/api/settings` | Validate and replace scanner settings |

Interactive API documentation is available at `/docs` while FastAPI is running.

## Tests

The test suite uses temporary SQLite databases and does not send network traffic.

```bash
pip install -r requirements-dev.txt
pytest
```

## Limitations

- ARP discovers devices only on the directly connected broadcast domain; it does not cross routers.
- Firewalls and client isolation can hide devices or make ports appear closed.
- Hostname resolution depends on local DNS/reverse-DNS configuration.
- The bundled OUI sample is intentionally small. Unknown prefixes are shown as `Unknown`.
- Online/offline state changes only when a full scan completes.
- Large subnets take longer and are limited to `/16` or smaller ranges.

## Security scope

NetScope performs ARP discovery and TCP connection checks only. It does not exploit services, capture traffic, spoof ARP, collect credentials, brute-force authentication, or run user-provided shell commands. Subnets and port lists are validated before use. Do not expose the web interface to untrusted networks without placing it behind appropriate access controls.

## License

[MIT](LICENSE)
