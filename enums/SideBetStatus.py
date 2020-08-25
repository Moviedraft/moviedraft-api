from enum import Enum

class SideBetStatus(Enum):
    current = 1
    previous = 2
    old = 3

    @classmethod
    def has_value(cls, value):
        return value.lower() in cls._member_names_