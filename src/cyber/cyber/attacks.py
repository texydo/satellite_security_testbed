from .structure_defenition import BaseAttack
import socket
import configparser


class LocalMalwareAttack(BaseAttack):
    def __init__(self, name, webapp_params):
        super().__init__(name)
        self.webapp_params = webapp_params
    
    @staticmethod
    def new_attack(*params):
        config = configparser.ConfigParser()
        config.read(r"C:\Users\user\Desktop\cyber\cyber\cyber_config.ini")

        target_IP=config.get("ATTACK_TARGET", "target_IP")
        target_PORT=config.getint("ATTACK_TARGET", "target_PORT")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_IP, target_PORT))
            start_attack_msg = f"{params[0]},{','.join([str(v) for p, v in params[1].items()])}"
            s.sendall(start_attack_msg.encode())
            while True:
                data = s.recv(1024).decode()
                if not data or "break" in data:
                    break
                elif "ended" in data:
                    break
    

class CPUHigh(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("CPUHigh", webapp_params)

    def start_attack(self):
        print(f"inside start_attack {self.name}, {self.webapp_params}")
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
    
class HeaterUp(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("heaterUP", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
    
class CommDown(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("commdown", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
    
class MagUp(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("magUP", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
    
class CamUpatk(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("camUpatk", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }

class CPUHighTarget(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("CPUHighTarget", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "target": 3,
            "occurrence": 3
        }

class malUP(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("malUP", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }

class RFLeakage(LocalMalwareAttack):
    def __init__(self, webapp_params):
        super().__init__("RFLeakage", webapp_params)

    def start_attack(self):
        self.new_attack(self.name, self.webapp_params)

    @staticmethod
    def get_attacks_params():
        return {
            "duration": 3,
            "occurrence": 3
        }
