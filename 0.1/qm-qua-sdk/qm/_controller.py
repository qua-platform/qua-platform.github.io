from dataclasses import dataclass


@dataclass
class Controller:
    name: str

    @staticmethod
    def build_from_message(message):
        return Controller(message.name)
