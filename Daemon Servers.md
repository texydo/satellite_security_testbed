# Daemon Servers

Each testbed component has a daemon process that waits for the Manager to connect. The Manager does not directly run the component logic until a simulation starts; instead, it sends a small startup message to each daemon, and each daemon launches its subsystem process.

Start all daemons before pressing **Start** in the WebApp.

## Run Order

1. Start the orbital/data conversion daemon.
2. Start the cyber daemon.
3. Start the operational daemon.
4. Start the Manager.
5. Start the WebApp.
6. Configure and start the simulation from the WebApp.

## Orbital / Data Conversion

```bash
cd src/dataConv
python daemon_server.py
```

Configuration file:

```text
src/dataConv/dataConv_config.ini
```

Main settings:

- `DAEMON_SERVER.daemon_ip`
- `DAEMON_SERVER.daemon_port`
- `DATA_CONV_MANAGER.com_with_manager_port`
- DAQ channels and calibration values under `DATA_CONV_MANAGER`

When the Manager connects, the daemon launches:

```text
dataConvManager.py <manager_ip> <internet_connected_flag>
```

## Cyber

```bash
cd src/cyber
python daemon_server.py
```

Configuration file in the repository:

```text
src/cyber/cyber/cyber_config.ini
```

Main settings:

- `ATTACK_TARGET.target_IP`
- `ATTACK_TARGET.target_PORT`
- `DAEMON_SERVER.HOST`
- `DAEMON_SERVER.PORT`

When the Manager connects, the daemon launches:

```text
main.py <manager_ip>
```

The cyber code currently contains hard-coded/relative config paths. If the daemon cannot find its config, run it from the expected working directory or update the paths before deployment.

## Operational / RubySat

```bash
cd src/Operational/rubysat
python daemon_server.py
```

Configuration file:

```text
src/Operational/rubysat/sim_config.ini
```

Main settings:

- `DAEMON_SERVER.HOST`
- `DAEMON_SERVER.PORT`
- `MANAGER_COM.manager_client_PORT`
- `COSMOS_COM.*`
- `PI_METRICS_COM.*`

When the Manager connects, the daemon launches:

```text
main.py <manager_ip>
```

## Manager-Side Port Mapping

The Manager reads daemon addresses from:

```text
src/Manager/config/manager_config.ini
```

The important fields are:

| Field | Meaning |
| --- | --- |
| `dataConv_comp_IP` | IP of the orbital daemon host |
| `operational_comp_IP` | IP of the operational daemon host |
| `cyber_comp_IP` | IP of the cyber daemon host |
| `daemon_server_PORT_ENV` | Port used to contact the orbital daemon |
| `daemon_server_PORT_OP` | Port used to contact the operational daemon |
| `daemon_server_PORT_CYBER` | Port used to contact the cyber daemon |
| `manager_comp_ip` | IP that components use to connect back to the Manager |
| `manager_PORT` | TCP port where the Manager accepts component connections |
| `WEBAPP_COM.webapp_com_PORT` | WebSocket port used by the WebApp |

## Troubleshooting

- If the Manager prints that it cannot connect to a computer, confirm that the matching daemon is already running and that the IP/port values match on both sides.
- If a component starts but never connects back, confirm `manager_comp_ip` and `manager_PORT`.
- If the WebApp buttons stay disabled, confirm that `src/Manager/ManagerServer.py` is running and listening on `ws://127.0.0.1:8765`.
- If a config file is not found, run the daemon from the directory shown above. Several scripts use relative paths.
