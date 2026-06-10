from client.cyberClient import Client
from cyber.attacks import *
import threading
import sys
from threading import Lock
from collections import defaultdict


class Attack:
    def __init__(self):
        self.attack_started = False
        global current_attacks
        self.lock = Lock()

    def execute_attack(self, attack_name: str, params):
        attack_name = attack_name.lower()
        if attack_name == "cpuhigh":
            attack = CPUHigh(params)
        elif attack_name == "heaterup":
            attack = HeaterUp(params)
        elif attack_name == "cpuhightarget":
            attack = CPUHighTarget(params)
        elif attack_name == "magup":
            attack = MagUp(params)
        elif attack_name == "commdown":
            attack = CommDown(params)
        elif attack_name == "camupatk":
            attack = CamUpatk(params)
        elif attack_name == "malup":
            attack = malUP(params)
        elif attack_name == "rfleakage":
            attack = RFLeakage(params)    
        else:
            print(f"Attack {attack_name} is not defined!")
        with self.lock:
            if attack_name not in current_attacks:
                current_attacks[attack_name] = params
        print(f"################ attack {attack_name} starting")
        attack.start_attack()
        with self.lock:
            if attack_name in current_attacks:
                current_attacks.pop(attack_name)
        print(f"################ attack {attack_name} finished.")

    def start_attack_thread(self, name, params):
        attack_thread = threading.Thread(target=self.execute_attack, args=(name, params,), daemon=False)
        attack_thread.start()
 
executed_attacks = defaultdict(lambda: -1)
current_attacks = {}

def parse_schedule_values(attack, key):
    values = [
        int(float(value.strip()))
        for value in str(attack.get(key, "")).split(",")
        if value.strip()
    ]

    if key == "occurrence" and attack.get("scheduleUnit") != "seconds":
        return [value * 60 for value in values]

    return values

def main():
    client = Client(sys.argv[1], 13020, "cyber")
    client.run()
    
    attacks, current_minute = client.prep()
    running_attacks_index = {}
    for element in attacks:
        running_attacks_index[element['name']] = 0
    print(running_attacks_index)
    print(f"Simulation starts with following attacks setup:\n{attacks}\n")
    
    attack_manager = Attack()
    last_second = -1
    while True:
        """
        exe_data will contain `attacks` key when an attack execution is required from ATK client.
        Form:: exe_data['data']['attacks'] = {'Atk_name_1': {'param1': v11, 'param2': v12', ..},
                                              'Atk_name_2': {'param1': v21, 'param2': v22, ...},
                                               ...
                                              }
        """

        exe_data = client.execute({'attacks': current_attacks})
        exe_data_details = exe_data.get('data', {})
        current_minute = exe_data_details.get('current_minute', 0)
        current_second = exe_data_details.get('current_second')
        if current_second is None:
            current_second = int(current_minute) * 60

        if current_attacks:
            print(f'current_attacks: {current_attacks}')
        if current_second != last_second:
            last_second = current_second
            print(f"#### @{current_second}s Executed attacks: {executed_attacks.items()}")

        for attack in attacks:
            atk_name = attack['name']
            occurrences = parse_schedule_values(attack, 'occurrence')
            next_attack_index = running_attacks_index[atk_name]

            if next_attack_index >= len(occurrences):
                continue

            occurrence = occurrences[next_attack_index]
            if current_second >= occurrence and executed_attacks[atk_name] < occurrence:
                print(f"    executing {atk_name}")

                params = {
                    key: str(value).split(',')[next_attack_index]
                    for key, value in attack.items()
                    if key not in {'occurrence', 'name', 'scheduleUnit'}
                }
                running_attacks_index[atk_name] += 1
                print(f"{atk_name} -- Params: {params}, indx = {running_attacks_index[atk_name]}")

                attack_manager.start_attack_thread(atk_name, params)
                executed_attacks[atk_name] = occurrence


if __name__ == "__main__":
    main()
