# Orbital Computer / Data Conversion

The `dataConv` subsystem represents the orbital/environment computer. It receives the TLE, simulation time, and solar intensity range from the Manager, computes environment values for the current satellite position, and can output those values to NI DAQ hardware.

## Files

| Path | Purpose |
| --- | --- |
| `daemon_server.py` | Listens for Manager startup messages and launches `dataConvManager.py` |
| `dataConvManager.py` | Main orbital/environment runtime and DAQ output loop |
| `convClient.py` | MsgPack TCP client used to communicate with the Manager |
| `utils.py` | MsgPack helpers, TLE processing, solar intensity, magnetic field helpers |
| `live_mapbox_display.py` | Optional satellite ground-view image display |
| `dataConv_config.ini` | Network, calibration, DAQ, and demo configuration |
| `de421.bsp` | Skyfield ephemeris file |
| `CSVs/` | Sample/generated satellite data files |

## Installation

```bash
cd src/dataConv
pip install -r requirements.txt
```

The non-demo path depends on NI DAQ support through `nidaqmx`. Install the required NI drivers on the machine connected to the DAQ hardware.

## Running

Start the daemon:

```bash
cd src/dataConv
python daemon_server.py
```

When the Manager starts a simulation, the daemon launches:

```text
python dataConvManager.py <manager_ip> <internet_connected_flag>
```

`dataConvManager.py` connects back to the Manager on `DATA_CONV_MANAGER.com_with_manager_port` and identifies itself as `orbital`.

## Preparation Data

The Manager sends:

| Field | Meaning |
| --- | --- |
| `tle` | Three-line TLE list |
| `time` | UTC time list `[year, month, day, hour, minute, second]` |
| `min` | Minimum solar intensity expected for the simulation |
| `max` | Maximum solar intensity expected for the simulation |
| `demo` | Demo-mode flag |

## Execution Loop

During each execution cycle, the component:

1. Receives current simulation time from the Manager.
2. Converts that time into a Skyfield timestamp.
3. Computes latitude, longitude, altitude, solar intensity, and magnetic field values.
4. Scales solar intensity to configured voltage ranges.
5. Converts magnetic field values to coil voltages.
6. Writes analog and digital values to NI DAQ channels.
7. In non-demo mode with internet access, updates the optional Mapbox display queue.

## Configuration

Edit:

```text
src/dataConv/dataConv_config.ini
```

### Daemon

- `DAEMON_SERVER.daemon_ip`
- `DAEMON_SERVER.daemon_port`

### Manager Communication

- `DATA_CONV_MANAGER.com_with_manager_port`

### Solar Intensity

- `solar_intensity_scale0_min`
- `solar_intensity_scale0_max`
- `solar_intensity_scale1_min`
- `solar_intensity_scale1_max`

### Magnetic Field / Coil Conversion

- `resistance_r`
- `resistance_l`
- `rmm_x`, `rmm_y`, `rmm_z`
- `n_x`, `n_y`, `n_z`
- `reset_x`, `reset_y`, `reset_z`

### DAQ Channels

- `sun_01`
- `sun_02`
- `helmholtz_coil_x`
- `helmholtz_coil_y`
- `helmholtz_coil_z`
- `relay`

### Demo / Display

- `is_demo_running`
- `demo_video_path`
- `full_cyclevideo_path`

Current code note: the repository file is named `dataConv_config.ini`, while some reads use `DataConv_config.ini`. This works on Windows, but must be normalized for case-sensitive systems.

## Troubleshooting

- If the daemon cannot bind, check `daemon_ip` and `daemon_port`.
- If the component cannot connect to the Manager, check `com_with_manager_port` and Manager `manager_PORT`.
- If DAQ output fails, confirm NI drivers, hardware names, and channel names.
- If Mapbox display does not update, confirm internet access and any API/display prerequisites used by `live_mapbox_display.py`.
- If demo video does not start, replace placeholder video paths in the config.
