# Cyber Subsystem

The cyber subsystem runs scheduled attack logic during a simulation. The Manager sends the configured attack list during the preparation phase, and `main.py` starts each attack when the simulation reaches the configured occurrence time.

## Files

| Path | Purpose |
| --- | --- |
| `daemon_server.py` | Listens for Manager startup messages and launches `main.py` |
| `main.py` | Connects to the Manager, receives attack schedule, tracks simulation time, launches attack threads |
| `client/cyberClient.py` | MsgPack TCP client used to communicate with the Manager |
| `client/utils.py` | MsgPack socket helpers and time utilities |
| `cyber/attacks.py` | Attack class implementations |
| `cyber/structure_defenition.py` | `BaseAttack` abstract class |
| `cyber/cyber_config.ini` | Attack target and daemon network settings |

## Installation

```bash
cd src/cyber
pip install -r requirements.txt
```

## Running

Start the daemon before the Manager starts a simulation:

```bash
cd src/cyber
python daemon_server.py
```

When the Manager sends the daemon a startup message, the daemon launches:

```text
python main.py <manager_ip>
```

`main.py` then connects back to the Manager on port `13020` and identifies itself as `cyber`.

## Configuration

Repository config file:

```text
src/cyber/cyber/cyber_config.ini
```

Fields:

| Field | Meaning |
| --- | --- |
| `ATTACK_TARGET.target_IP` | Host that receives attack commands |
| `ATTACK_TARGET.target_PORT` | Port that receives attack commands |
| `DAEMON_SERVER.HOST` | Interface where the cyber daemon listens |
| `DAEMON_SERVER.PORT` | Cyber daemon port, normally aligned with Manager `daemon_server_PORT_CYBER` |

Current code note: some cyber files use relative or absolute config paths. If configuration is not loaded, verify the process working directory and path values before deployment.

## Attack Schedule Format

The WebApp stores attacks as objects like:

```json
{
  "name": "CPUHigh",
  "duration": "20,40",
  "occurrence": "90,180",
  "scheduleUnit": "seconds"
}
```

Rules:

- `occurrence` values from the current WebApp are simulation seconds from the start.
- `scheduleUnit: "seconds"` marks the schedule as second-based.
- `duration` values are passed through to the attack target.
- Comma-separated fields must have the same number of values.
- When second `90` is reached, the first duration value is used; when second `180` is reached, the second duration value is used.

Older attack objects without `scheduleUnit` are treated as minute-based for their `occurrence` values.

## Available Attack Classes

Defined in `cyber/attacks.py` and dispatched in `main.py`:

- `CPUHigh`
- `HeaterUp`
- `CommDown`
- `MagUp`
- `CamUpatk`
- `CPUHighTarget`
- `malUP`
- `RFLeakage`

Attack names are matched case-insensitively in `main.py`, but the WebApp list should still use the names above for readability.

## Adding Attacks

See [../../New Attack.md](../../New%20Attack.md) for the full checklist. In short:

1. Add an attack class in `cyber/attacks.py`.
2. Add its dispatch branch in `main.py`.
3. Add its display name to `WebApp/TestBedWebApp/src/components/AttackManager/AttackManager.jsx`.
4. Ensure the target service understands the command string produced by `LocalMalwareAttack.new_attack()`.

## Troubleshooting

- If an attack never starts, confirm its `occurrence` time is reached and that the `name` matches a branch in `main.py`.
- If an attack starts but has no visible effect, confirm `ATTACK_TARGET.target_IP` and `target_PORT`.
- If the daemon starts but cannot read config, check the config path note above.
