# Adding a New Cyber Attack

This guide explains how to add an attack to the current codebase without changing the Manager protocol. The cyber subsystem does not currently load attacks from an `attacks.yaml` file. Attacks are defined in Python and selected in the WebApp.

## Current Attack Path

1. The user adds attacks in the WebApp attack dialog.
2. The WebApp stores each attack as an object with `name`, `occurrence`, and `duration`.
3. The WebApp sends the attack list in the `stage: "start"` message.
4. The Manager forwards the attack list to the cyber component during `stage: "prep"`.
5. `src/cyber/main.py` checks the current simulation minute and starts matching attacks.
6. Attack classes in `src/cyber/cyber/attacks.py` send command strings to the configured target.

## WebApp Attack Format

The WebApp sends attacks like this:

```json
{
  "name": "CPUHigh",
  "duration": "20,40",
  "occurrence": "10,30"
}
```

Rules:

- `occurrence` is measured in simulation minutes from the start.
- `duration` is passed to the attack implementation.
- Multiple values are comma-separated.
- `duration` and `occurrence` must contain the same number of values.

Example:

```text
occurrence: 10,30
duration: 20,40
```

This starts the attack at minute 10 for duration 20, then again at minute 30 for duration 40.

## Step 1: Add the Attack Class

Edit:

```text
src/cyber/cyber/attacks.py
```

Most current attacks inherit from `LocalMalwareAttack`, which sends a command to `ATTACK_TARGET.target_IP:target_PORT` from `cyber_config.ini`.

Example:

```python
class MyAttack(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("MyAttack", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
```

`webapp_params` is the dictionary built by `main.py` for the current scheduled occurrence. For example:

```python
{
    "duration": "20"
}
```

If your attack needs more fields, add them to the WebApp form or provide defaults in the attack implementation.

## Step 2: Add Dispatch Logic

Edit:

```text
src/cyber/main.py
```

Add a branch in `Attack.execute_attack()`:

```python
elif attack_name == "myattack":
    attack = MyAttack(params)
```

The code lowercases the selected attack name before dispatch, so compare against a lowercase string.

## Step 3: Add the Attack to the WebApp List

Edit:

```text
WebApp/TestBedWebApp/src/components/AttackManager/AttackManager.jsx
```

Add your display name to `predefinedAttacks`:

```javascript
const predefinedAttacks = [
  'HeaterUp',
  'malUP',
  'CPUHigh',
  'commdown',
  'RFLeakage',
  'CPUHighTarget',
  'camUpatk',
  'magUP',
  'MyAttack',
];
```

Keep the display name consistent with the class/dispatch name so the attack is easy to trace.

## Step 4: Confirm the Target Service Understands It

`LocalMalwareAttack.new_attack()` sends a comma-separated string to the configured target:

```text
<attack_name>,<param_value_1>,<param_value_2>,...
```

For example:

```text
MyAttack,20
```

The receiving service at `ATTACK_TARGET.target_IP:target_PORT` must know how to parse and execute that command.

## Optional: Add Parameters

Current WebApp UI fields support only:

- `name`
- `duration`
- `occurrence`

If your attack requires a field such as `target`, `frequency`, or `intensity`, add that input to `AttackManager.jsx` and make sure it is included in the attack object stored by `simActions.addAttack()`.

`main.py` automatically passes every attack key except `name` and `occurrence` into the attack parameter dictionary for that occurrence.

## Checklist

- Add class in `src/cyber/cyber/attacks.py`.
- Add branch in `src/cyber/main.py`.
- Add display name in `AttackManager.jsx`.
- Confirm `cyber/cyber_config.ini` points to the target service.
- Confirm the target service recognizes the command string.
- Test with a short occurrence, such as minute `1`, and a short duration.
