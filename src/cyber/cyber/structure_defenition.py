from abc import ABC, abstractmethod

class BaseAttack(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def get_attacks_params():
        raise NotImplementedError("")
    
    @abstractmethod
    def start_attack():
        raise NotImplementedError("")

    @property
    def get_name(self):
        return self.name