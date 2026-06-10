# Testbed Web Application

This folder contains frontend-related utilities and the main React application for the Satellite Security Testbed.

The active WebApp is:

```text
WebApp/TestBedWebApp
```

## Contents

| Path | Purpose |
| --- | --- |
| `TestBedWebApp/` | React/Vite application used by operators |
| `pyDummyClient.py` | Python WebSocket client useful for manual Manager/WebSocket testing |
| `loggerUtil.py` | Small logging helper |

## WebApp Features

- Simulation configuration form
- TLE upload and epoch extraction
- Attack selection and scheduling
- Per-run MongoDB save toggle
- Operational command-file save/load controls
- Start, stop, pause, and resume controls
- Automatic return to the configuration screen when a simulation completes
- Live satellite map using Leaflet
- Day/night terminator overlay
- Telemetry charts using Chart.js
- Command log panel
- Redux state management
- WebSocket communication with the Manager

## Running

```bash
cd WebApp/TestBedWebApp
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://localhost:5173
```

The frontend currently connects to:

```text
ws://127.0.0.1:8765
```

## Manual WebSocket Test Client

`pyDummyClient.py` can connect to the Manager WebSocket and send/receive MsgPack messages for debugging. It is not required for normal WebApp operation.

Run it from this folder after the Manager is running:

```bash
cd WebApp
python pyDummyClient.py
```

## Related Docs

- [../gui_guide.md](../gui_guide.md)
- [../web_guide.md](../web_guide.md)
- [TestBedWebApp/README.md](TestBedWebApp/README.md)
