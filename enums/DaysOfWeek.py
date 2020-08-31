from enum import Enum

class DaysOfWeek(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

    @classmethod
    def has_value(cls, value):
        return value.lower() in cls._member_names_