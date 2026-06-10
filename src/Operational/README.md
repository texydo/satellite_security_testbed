# Operational Subsystem

The operational subsystem emulates spacecraft command and telemetry flow. It schedules commands from `commands.yml`, communicates with COSMOS/RubySat processes, sends commands to the simulated satellite, receives telemetry, and reports command/telemetry updates to the Manager.

Most runtime code lives in:

```text
src/Operational/rubysat
```

## Files

| Path | Purpose |
| --- | --- |
| `rubysat/daemon_server.py` | Listens for Manager startup messages and launches `main.py` |
| `rubysat/main.py` | Main operational runtime; connects Manager, command handler, COSMOS receiver, and Pi metrics server |
| `rubysat/command_handler.py` | Loads command YAML, builds command timeline, sends commands to the command server |
| `rubysat/command_class.py` | Command model used by the scheduler |
| `rubysat/commands.yml` | Command definitions with frequency and duration ranges |
| `rubysat/client/rubySatClient.py` | MsgPack TCP client used to communicate with the Manager |
| `rubysat/main.rb` | Ruby TCP command receiver/sender side used with COSMOS/RubySat integration |
| `rubysat/datacollector.rb` | Ruby telemetry collector that forwards COSMOS packets |
| `rubysat/*_module.py` | Command modules for ADCS, COM, TPL, PI payload, and related satellite functions |
| `rubysat/sim_config.ini` | Operational runtime configuration |
| `tlmcheck.rb` | Helper for collecting telemetry snapshots |
| `ADCS_calibration.rb` | ADCS calibration support script |

## Installation

```bash
cd src/Operational
pip install -r requirements.txt
```

The operational machine also needs the COSMOS/RubySat environment expected by the Ruby scripts.

## Running

Start the daemon before the Manager starts the simulation:

```bash
cd src/Operational/rubysat
python daemon_server.py
```

When the Manager connects, the daemon launches:

```text
python main.py <manager_ip>
```

`main.py` connects back to the Manager using `MANAGER_COM.manager_client_PORT` and identifies itself as `operational`.

## Runtime Flow

1. `main.py` starts `PiMetricsServer` using `PI_METRICS_COM`.
2. It reads `commands.yml` through `CommandHandler`.
3. It receives TLE, start time, night probability, and simulation duration from the Manager.
4. It either generates a command timeline or loads one sent by the Manager.
5. It writes the active timeline to `SIM_CONFIG.simulation_text_file`.
6. It starts the command server used by the Ruby/COSMOS command path.
7. It starts `DataFromCosmos` to receive telemetry from the configured COSMOS data endpoint.
8. It iterates through scheduled commands, sends updates to the Manager, receives current simulation state, and executes commands when their scheduled simulation time is reached.
9. It forwards optional Raspberry Pi metrics to the Manager when received.

The WebApp duration is entered in minutes. The Manager converts it to seconds and sends that value during prep. If the Manager does not send a duration, the operational component falls back to `SIM_CONFIG.simulation_duration`.

When the Manager sends loaded command-file content, the operational component writes that content to `SIM_CONFIG.simulation_text_file` and loads it instead of generating a new random command schedule. Otherwise, it generates a new schedule from `commands.yml`, writes it to the same file, and sends the generated file content back to the Manager so it can be saved if requested.

## Command File Format

`rubysat/commands.yml` is a list of command definitions:

```yaml
- command: TPL SET TPL_SET_TARGET_TEMPERATURE 50
  frequency: [10, 500]
  duration: [15, 30]
```

Fields:

- `command` - command string sent through the configured communication channel
- `frequency` - `[min, max]` range used to randomize how often the command appears
- `duration` - `[min, max]` range used to randomize how long duration-limited commands remain active

The scheduler validates that every item has `frequency` and `duration`.

## Configuration

Edit:

```text
src/Operational/rubysat/sim_config.ini
```

### Simulation

- `SIM_CONFIG.commands_file_name` - YAML file loaded by `CommandHandler`
- `SIM_CONFIG.simulation_duration` - fallback operational timeline length in seconds when the Manager does not send a duration
- `SIM_CONFIG.com_channel` - satellite/COSMOS communication channel
- `SIM_CONFIG.simulation_text_file` - generated command timeline output

### COSMOS

- `COSMOS_COM.cosmos_com_IP`
- `COSMOS_COM.cosmos_com_PORT`
- `COSMOS_COM.cosmos_command_sender_IP`
- `COSMOS_COM.cosmos_com_sender_PORT`
- `COSMOS_COM.cosmos_dir_PATH`

### Manager

- `MANAGER_COM.manager_client_PORT`

### Daemon

- `DAEMON_SERVER.HOST`
- `DAEMON_SERVER.PORT`

### Raspberry Pi Metrics

- `PI_METRICS_COM.host`
- `PI_METRICS_COM.port`

## COSMOS / Ruby Notes

The Ruby files are part of the COSMOS/RubySat integration. `main.py` expects a command path and telemetry path to be available:

- command sender endpoint configured by `cosmos_command_sender_IP` and `cosmos_com_sender_PORT`
- telemetry receiver endpoint configured by `cosmos_com_IP` and `cosmos_com_PORT`

The repository docs previously referenced files such as `satellite_model.rb` and `telemetry_generator.rb`; those are not present in this tree. The current implementation uses the Ruby and Python files listed above.

## Troubleshooting

- If `commands.yml` is rejected, confirm every command item has both `frequency` and `duration`.
- If commands are generated but not sent, check the COSMOS command sender host and port.
- If telemetry graphs do not update, check the COSMOS telemetry endpoint and confirm `DataFromCosmos` is receiving packets.
- If component prep fails, check `MANAGER_COM.manager_client_PORT` against the Manager `manager_PORT`.
- If Pi metrics are missing, verify the process that sends MsgPack metrics is targeting `PI_METRICS_COM.host:port`.
